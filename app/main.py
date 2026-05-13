# app/main.py
import io
import logging
import os
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
