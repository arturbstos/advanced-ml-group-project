# app/main.py
import io
import logging
import os
import secrets
import shutil
import sys
import tempfile
from datetime import datetime, timezone

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("veritas.api")

# Load .env BEFORE importing app.services / db modules. Several of them
# instantiate AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")) at import
# time, so the key must already be in the environment by then.
load_dotenv()

import asyncio

# Sentry error monitoring — no-ops if SENTRY_DSN is unset
_sentry_dsn = os.getenv("SENTRY_DSN", "")
if _sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration
    sentry_sdk.init(
        dsn=_sentry_dsn,
        integrations=[StarletteIntegration(), FastApiIntegration()],
        traces_sample_rate=0.2,
    )
    logger.info("Sentry initialized")

import firebase_admin
from firebase_admin import credentials, firestore, auth
from google.cloud import firestore as gc_firestore
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize Firebase Admin SDK
cred_path = "firebase-adminsdk.json"
if os.path.exists(cred_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
else:
    firebase_admin.initialize_app()

_db = gc_firestore.AsyncClient(database="contractdb")

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Pipeline: ingest -> analyze -> assemble report
from app.services.ingestion import process_contract
from app.services.clause_analyzer import analyze as analyze_clauses
from app.services.report_builder import build as build_report

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="German Freelancer Contract Analyzer")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

if os.getenv("ENV") == "development":
    _ALLOWED_ORIGINS = ["*"]
else:
    _ALLOWED_ORIGINS = [
        "https://veritas-demo.web.app",
        "https://veritas-demo.firebaseapp.com",
        "https://veritas-43d91.web.app",
        "https://veritas-43d91.firebaseapp.com",
    ]

# Always allow any localhost origin so local dev keeps working without
# needing to remember to set ENV=development.
_LOCAL_ORIGIN_REGEX = r"https?://(localhost|127\.0\.0\.1)(:\d+)?"

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_origin_regex=_LOCAL_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)

def get_current_user(cred: HTTPAuthorizationCredentials = Depends(security)):
    """Extracts UID from Firebase ID token if present."""
    if not cred:
        return None
    try:
        decoded_token = auth.verify_id_token(cred.credentials)
        return decoded_token.get("uid")
    except Exception as e:
        logger.warning("Token verification failed: %s", type(e).__name__)
        return None


@app.get("/health")
async def health_check():
    """Verify API is up and the database connection is functional."""
    try:
        async for _ in _db.collection("health").limit(1).stream():
            break
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/analyses")
async def get_analyses(uid: str = Depends(get_current_user)):
    """Fetch past analyses for the authenticated user."""
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        analyses_ref = (
            _db.collection("users")
            .document(uid)
            .collection("analyses")
            .order_by("timestamp", direction=gc_firestore.Query.DESCENDING)
        )

        results = []
        async for doc in analyses_ref.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            if "timestamp" in data and hasattr(data["timestamp"], "isoformat"):
                data["timestamp"] = data["timestamp"].isoformat()
            results.append(data)
        return results
    except Exception as e:
        logger.error("Error fetching analyses for uid=%s: %s", uid, e)
        raise HTTPException(status_code=500, detail="Failed to fetch analyses")


@app.delete("/api/analyses/{analysis_id}")
async def delete_analysis(analysis_id: str, uid: str = Depends(get_current_user)):
    """Delete a specific analysis for the authenticated user."""
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        doc_ref = _db.collection("users").document(uid).collection("analyses").document(analysis_id)
        await doc_ref.delete()
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete analysis")


@app.get("/api/user/profile")
async def get_user_profile(uid: str = Depends(get_current_user)):
    """Return the authenticated user's tier and monthly usage."""
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    tier = await _get_user_tier(uid)
    count = await _get_monthly_count(uid)
    limit = TIER_LIMITS.get(tier, 1)
    return {"tier": tier, "analyses_this_month": count, "monthly_limit": limit}


MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
ANALYSIS_TIMEOUT_SECONDS = 120

TIER_LIMITS = {
    "free": 1,
    "pro": 10,
    "team": 999,
}

async def _get_user_tier(uid: str) -> str:
    user_doc = await _db.collection("users").document(uid).get()
    if not user_doc.exists:
        return "free"
    return user_doc.to_dict().get("tier", "free")

async def _get_monthly_count(uid: str) -> int:
    month_start = datetime(datetime.now(timezone.utc).year, datetime.now(timezone.utc).month, 1, tzinfo=timezone.utc)
    query = (
        _db.collection("users")
        .document(uid)
        .collection("analyses")
        .where("timestamp", ">=", month_start)
    )
    count = 0
    async for _ in query.stream():
        count += 1
    return count

@app.post("/analyze")
@limiter.limit("10/minute")
async def analyze_contract(
    request: Request,
    file: UploadFile = File(...),
    target_language: str = Form("de"),
    uid: str = Depends(get_current_user)
):
    """Full analysis pipeline: ingest -> analyze -> assemble report.

    1. Ingest  - PDF -> structured ContractExtraction (GPT-4o-mini).
    2. Analyze - per-clause risk analysis against playbook, statutes, rates.
    3. Report  - summary counts, findings list, negotiation brief.
    4. Save    - If authenticated, saves to Firestore.
    """
    if not uid:
        raise HTTPException(status_code=401, detail="Authentication required to analyze contracts.")

    tier = await _get_user_tier(uid)
    limit = TIER_LIMITS.get(tier, 1)
    count = await _get_monthly_count(uid)
    if count >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly limit reached ({count}/{limit} analyses on the {tier.capitalize()} plan). Upgrade to Pro for more."
        )

    contents = await file.read()

    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10 MB.")

    if not contents.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Invalid file. Only PDF documents are accepted.")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(contents)
        temp_path = tmp.name

    try:
        try:
            # Coerce to a known value so a malformed client can't poison the prompt.
            lang = "en" if target_language == "en" else "de"

            async def _run_pipeline():
                try:
                    extraction, clauses = await process_contract(temp_path)
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=str(e))
                findings, rate_bench = await analyze_clauses(extraction, clauses, lang)
                return build_report(extraction, findings, rate_bench, lang)

            report = await asyncio.wait_for(_run_pipeline(), timeout=ANALYSIS_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Analysis timed out. The contract may be too large or complex.")
        
        # Save to Firestore if user is logged in
        if uid:
            try:
                doc_ref = _db.collection("users").document(uid).collection("analyses").document()
                high_risk = sum(1 for f in report.findings if f.risk.lower() == "high")
                med_risk = sum(1 for f in report.findings if f.risk.lower() == "medium")
                await doc_ref.set({
                    "filename": file.filename,
                    "timestamp": gc_firestore.SERVER_TIMESTAMP,
                    "high_risk_count": high_risk,
                    "medium_risk_count": med_risk,
                    "report": report.dict() if hasattr(report, "dict") else report
                })

                # Analytics counter
                date_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                await _db.collection("analytics").document(date_key).set(
                    {"analyses_count": gc_firestore.Increment(1)}, merge=True
                )

                # Email notifications (fire-and-forget)
                try:
                    user_record = auth.get_user(uid)
                    user_email = getattr(user_record, "email", None)
                    if user_email:
                        from app.services.email import send_analysis_complete, send_limit_warning
                        send_analysis_complete(user_email, file.filename, high_risk, med_risk)
                        new_count = count + 1
                        if new_count / limit >= 0.8:
                            send_limit_warning(user_email, tier, new_count, limit)
                except Exception:
                    pass
            except Exception as e:
                logger.warning("Failed to save analysis for uid=%s: %s", uid, e)

        return report
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.get("/api/playbook")
async def get_playbook(uid: str = Depends(get_current_user)):
    """Return all playbook entries (without embeddings) for auditability."""
    if not uid:
        raise HTTPException(status_code=401, detail="Authentication required.")
    entries = []
    async for doc in _db.collection("playbook").stream():
        d = doc.to_dict()
        d.pop("embedding", None)
        d["id"] = doc.id
        entries.append(d)
    entries.sort(key=lambda x: x.get("id", ""))
    return {"count": len(entries), "entries": entries}


@app.post("/api/billing/create-checkout-session")
async def create_checkout_session(request: Request, uid: str = Depends(get_current_user)):
    """Create a Stripe Checkout session for a plan upgrade. Returns {url}."""
    if not uid:
        raise HTTPException(status_code=401, detail="Authentication required.")
    body = await request.json()
    tier = body.get("tier", "").strip().lower()
    if tier not in ("pro", "team"):
        raise HTTPException(status_code=400, detail="tier must be pro or team")

    user_record = auth.get_user(uid)
    from app.services.billing import create_checkout_url
    try:
        url = create_checkout_url(uid, user_record.email, tier)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {"url": url}


@app.post("/api/billing/webhook")
async def stripe_webhook(request: Request):
    """Stripe webhook — upgrades or downgrades the user tier in Firestore."""
    payload    = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    from app.services.billing import parse_webhook_event
    try:
        event = parse_webhook_event(payload, sig_header)
    except Exception as e:
        logger.warning("Stripe webhook rejected: %s", e)
        raise HTTPException(status_code=400, detail="Invalid webhook")

    etype = event["type"]
    if etype == "checkout.session.completed":
        session     = event["data"]["object"]
        firebase_uid = session.get("metadata", {}).get("firebase_uid")
        tier         = session.get("metadata", {}).get("tier")
        if firebase_uid and tier:
            await _db.collection("users").document(firebase_uid).set(
                {"tier": tier, "stripe_customer_id": session.get("customer")},
                merge=True,
            )
            logger.info("Stripe: upgraded uid=%s to tier=%s", firebase_uid, tier)

    elif etype == "customer.subscription.deleted":
        sub          = event["data"]["object"]
        firebase_uid = sub.get("metadata", {}).get("firebase_uid")
        if firebase_uid:
            await _db.collection("users").document(firebase_uid).set(
                {"tier": "free"}, merge=True
            )
            logger.info("Stripe: subscription cancelled, downgraded uid=%s to free", firebase_uid)

    return {"status": "ok"}


@app.post("/api/admin/set-tier")
async def admin_set_tier(request: Request, uid: str = Depends(get_current_user)):
    """Set a user's tier. Restricted to the admin UID configured in ADMIN_UID env var."""
    admin_uid = os.getenv("ADMIN_UID")
    if not uid or not admin_uid or uid != admin_uid:
        raise HTTPException(status_code=403, detail="Forbidden")
    body = await request.json()
    target_uid = body.get("uid", "").strip()
    tier        = body.get("tier", "").strip().lower()
    if not target_uid:
        raise HTTPException(status_code=400, detail="uid is required")
    if tier not in ("free", "pro", "team"):
        raise HTTPException(status_code=400, detail="tier must be free, pro, or team")
    await _db.collection("users").document(target_uid).set({"tier": tier}, merge=True)
    logger.info("Admin %s set tier=%s for uid=%s", uid, tier, target_uid)
    return {"uid": target_uid, "tier": tier, "status": "updated"}


@app.post("/api/export/pdf")
async def export_pdf(request: Request, uid: str = Depends(get_current_user)):
    """Generate a server-side PDF from an AnalysisReport JSON body."""
    if not uid:
        raise HTTPException(status_code=401, detail="Authentication required.")
    report = await request.json()
    from app.services.pdf_export import build_pdf
    pdf_bytes = build_pdf(report)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=veritas-analysis.pdf"},
    )


# ── Shareable report links ────────────────────────────────────────────────────

@app.post("/api/analyses/{analysis_id}/share")
async def share_analysis(analysis_id: str, uid: str = Depends(get_current_user)):
    """Generate a public share token for an analysis. Returns {token, url}."""
    if not uid:
        raise HTTPException(status_code=401, detail="Authentication required.")
    doc_ref = _db.collection("users").document(uid).collection("analyses").document(analysis_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    data = doc.to_dict()
    token = secrets.token_urlsafe(16)
    await _db.collection("shared_reports").document(token).set({
        "uid": uid,
        "analysis_id": analysis_id,
        "filename": data.get("filename", ""),
        "created_at": gc_firestore.SERVER_TIMESTAMP,
        "report": data.get("report", {}),
    })
    url = f"https://veritas-demo.web.app/report.html?t={token}"
    logger.info("Share token created for uid=%s analysis=%s", uid, analysis_id)
    return {"token": token, "url": url}


@app.get("/api/shared/{token}")
async def get_shared_report(token: str):
    """Public endpoint — returns a shared report by token. No auth required."""
    doc = await _db.collection("shared_reports").document(token).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Report not found or link has expired.")
    data = doc.to_dict()
    if "created_at" in data and hasattr(data["created_at"], "isoformat"):
        data["created_at"] = data["created_at"].isoformat()
    return data


# ── Usage analytics (admin only) ──────────────────────────────────────────────

@app.get("/api/admin/analytics")
async def get_analytics(uid: str = Depends(get_current_user)):
    """Return daily analysis counts for the last 30 days."""
    admin_uid = os.getenv("ADMIN_UID")
    if not uid or not admin_uid or uid != admin_uid:
        raise HTTPException(status_code=403, detail="Forbidden")
    from datetime import timedelta
    today = datetime.now(timezone.utc).date()
    days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(29, -1, -1)]
    docs = await asyncio.gather(*[
        _db.collection("analytics").document(d).get() for d in days
    ])
    daily = [
        {"date": d, "analyses": (doc.to_dict() or {}).get("analyses_count", 0)}
        for d, doc in zip(days, docs)
    ]
    total = sum(r["analyses"] for r in daily)
    return {"total_30d": total, "daily": daily}


# ── Playbook admin endpoints ───────────────────────────────────────────────────

@app.post("/api/admin/playbook")
async def add_playbook_entry(request: Request, uid: str = Depends(get_current_user)):
    """Add a new playbook entry with embedding. Admin only."""
    admin_uid = os.getenv("ADMIN_UID")
    if not uid or not admin_uid or uid != admin_uid:
        raise HTTPException(status_code=403, detail="Forbidden")
    body = await request.json()
    required = ["id", "clause_type", "risk_level", "pattern_description", "legal_reasoning"]
    for field in required:
        if not body.get(field):
            raise HTTPException(status_code=400, detail=f"'{field}' is required")
    if body["risk_level"] not in ("high", "medium", "low"):
        raise HTTPException(status_code=400, detail="risk_level must be high, medium, or low")

    from db.playbook_lookup import embed
    embed_text = f"{body['clause_type']} {body['pattern_description']} {body['legal_reasoning']}"
    embedding = await embed(embed_text)

    from google.cloud.firestore_v1.vector import Vector
    entry_id = body["id"]
    await _db.collection("playbook").document(entry_id).set({
        "id": entry_id,
        "clause_type": body["clause_type"],
        "risk_level": body["risk_level"],
        "pattern_description": body["pattern_description"],
        "example_risky_wording": body.get("example_risky_wording", ""),
        "legal_reasoning": body["legal_reasoning"],
        "recommended_redline": body.get("recommended_redline", ""),
        "statute_ref": body.get("statute_ref", ""),
        "embedding": Vector(embedding),
    })
    logger.info("Admin %s added playbook entry %s", uid, entry_id)
    return {"id": entry_id, "status": "created"}


@app.delete("/api/admin/playbook/{entry_id}")
async def delete_playbook_entry(entry_id: str, uid: str = Depends(get_current_user)):
    """Delete a playbook entry. Admin only."""
    admin_uid = os.getenv("ADMIN_UID")
    if not uid or not admin_uid or uid != admin_uid:
        raise HTTPException(status_code=403, detail="Forbidden")
    await _db.collection("playbook").document(entry_id).delete()
    logger.info("Admin %s deleted playbook entry %s", uid, entry_id)
    return {"id": entry_id, "status": "deleted"}
