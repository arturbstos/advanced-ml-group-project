"""Evaluation runner for the Veritas gold annotation set.

Calls the /analyze endpoint with single-clause synthetic PDFs (via the
internal analysis pipeline directly) and compares results against
tests/evaluation/gold_set.json.

Usage:
    # Direct import (requires OPENAI_API_KEY + Firebase env set):
    python tests/evaluation/run_eval.py

    # Against a running server:
    python tests/evaluation/run_eval.py --mode http --url http://localhost:8000 --token <id_token>

Metrics reported:
    - Risk-tier accuracy   : fraction where predicted risk == expected risk
    - Statute hit rate     : fraction where at least one expected statute
                             substring appears in the finding's statute field
    - Keyword hit rate     : fraction where at least one expected keyword
                             appears in title OR body (case-insensitive)
    - Overall precision    : mean of risk_accuracy + statute_hit + keyword_hit

Exit code 0 if precision >= 0.70, else 1 (useful for CI gates).
"""
import argparse
import json
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

GOLD_PATH    = Path(__file__).parent / "gold_set.json"
RESULTS_PATH = Path(__file__).parent / "last_eval_results.json"
HISTORY_PATH = Path(__file__).parent / "eval_history.json"
PASS_THRESHOLD = 0.70


# ── Direct-import mode (uses the internal pipeline) ────────────────────────

async def _analyze_clause_direct(clause: str, lang: str = "en") -> dict:
    """Run a single clause through the internal analysis pipeline."""
    root = str(Path(__file__).parent.parent.parent)
    if root not in sys.path:
        sys.path.insert(0, root)
    # Load .env and point to the service account before pipeline modules instantiate clients.
    from dotenv import load_dotenv
    load_dotenv(Path(root) / ".env")
    sa_path = Path(root) / "firebase-adminsdk.json"
    if sa_path.exists() and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(sa_path)
    from app.services.ingestion import ContractExtraction
    from app.services.clause_analyzer import analyze

    dummy_extraction = ContractExtraction(
        skill_category="Software Development",
        region="Germany",
        experience_level="mid",
        hourly_rate_eur=0.0,
        payment_terms_days=30,
    )
    findings, _ = await analyze(dummy_extraction, [clause], target_language=lang)
    if not findings:
        return {"risk": "low", "title": "", "body": "", "statute": None}
    f = findings[0]
    return {
        "risk": f.risk,
        "title": f.title,
        "body": f.body,
        "statute": f.statute,
        "source": f.source,
    }


# ── HTTP mode (calls a running server) ─────────────────────────────────────

def _analyze_clause_http(clause: str, base_url: str, token: str) -> dict:
    import io
    import tempfile
    import requests
    from reportlab.pdfgen import canvas

    # Build a minimal single-page PDF containing just the clause text
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 720, clause[:200])
    c.save()
    buf.seek(0)

    resp = requests.post(
        f"{base_url}/analyze",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("eval.pdf", buf, "application/pdf")},
        data={"target_language": "en"},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    findings = data.get("findings", [])
    if not findings:
        return {"risk": "low", "title": "", "body": "", "statute": None}
    f = findings[0]
    return f


# ── Evaluation logic ────────────────────────────────────────────────────────

def _check_risk(result: dict, gold: dict) -> bool:
    return result.get("risk", "").lower() == gold["expected_risk"]


def _check_statute(result: dict, gold: dict) -> bool:
    if not gold["expected_statute_contains"]:
        return True  # no statute requirement for this case
    statute = (result.get("statute") or "").lower()
    body = (result.get("body") or "").lower()
    combined = statute + " " + body
    return any(s.lower() in combined for s in gold["expected_statute_contains"])


def _check_keywords(result: dict, gold: dict) -> bool:
    if not gold["expected_keywords_any"]:
        return True
    title = (result.get("title") or "").lower()
    body = (result.get("body") or "").lower()
    combined = title + " " + body
    return any(kw.lower() in combined for kw in gold["expected_keywords_any"])


def _run_evaluation(clauses, results) -> dict:
    rows = []
    for gold, result in zip(clauses, results):
        risk_ok    = _check_risk(result, gold)
        statute_ok = _check_statute(result, gold)
        keyword_ok = _check_keywords(result, gold)
        rows.append({
            "id":          gold["id"],
            "category":    gold["category"],
            "expected":    gold["expected_risk"],
            "predicted":   result.get("risk", "—"),
            "risk_ok":     risk_ok,
            "statute_ok":  statute_ok,
            "keyword_ok":  keyword_ok,
            "statute":     result.get("statute"),
            "title":       result.get("title"),
        })

    n = len(rows)
    risk_acc    = sum(r["risk_ok"]    for r in rows) / n
    statute_hit = sum(r["statute_ok"] for r in rows) / n
    keyword_hit = sum(r["keyword_ok"] for r in rows) / n
    precision   = (risk_acc + statute_hit + keyword_hit) / 3

    return {
        "n":           n,
        "risk_acc":    risk_acc,
        "statute_hit": statute_hit,
        "keyword_hit": keyword_hit,
        "precision":   precision,
        "rows":        rows,
    }


def _print_report(metrics: dict):
    rows = metrics["rows"]
    print("\n" + "─" * 72)
    print(f"{'ID':<10} {'CAT':<25} {'EXP':<8} {'GOT':<8} RISK STAT  KW")
    print("─" * 72)
    for r in rows:
        ok  = lambda b: "✓" if b else "✗"
        print(
            f"{r['id']:<10} {r['category']:<25} {r['expected']:<8} "
            f"{r['predicted']:<8} {ok(r['risk_ok'])}    {ok(r['statute_ok'])}     {ok(r['keyword_ok'])}"
        )
    print("─" * 72)
    print(f"Risk-tier accuracy : {metrics['risk_acc']:.0%}  ({sum(r['risk_ok'] for r in rows)}/{metrics['n']})")
    print(f"Statute hit rate   : {metrics['statute_hit']:.0%}  ({sum(r['statute_ok'] for r in rows)}/{metrics['n']})")
    print(f"Keyword hit rate   : {metrics['keyword_hit']:.0%}  ({sum(r['keyword_ok'] for r in rows)}/{metrics['n']})")
    print(f"Overall precision  : {metrics['precision']:.0%}")
    print("─" * 72)
    verdict = "PASS" if metrics["precision"] >= PASS_THRESHOLD else "FAIL"
    print(f"{'✓ ' + verdict if verdict == 'PASS' else '✗ ' + verdict}  (threshold: {PASS_THRESHOLD:.0%})")
    print()


async def main_direct(gold_clauses):
    print(f"\nRunning {len(gold_clauses)} clauses through internal pipeline …")
    results = []
    for item in gold_clauses:
        print(f"  {item['id']} {item['category']} …", end=" ", flush=True)
        try:
            r = await _analyze_clause_direct(item["clause"])
            results.append(r)
            print(r.get("risk", "?"))
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({"risk": "error", "title": "", "body": "", "statute": None})
    return results


def main_http(gold_clauses, url: str, token: str):
    print(f"\nRunning {len(gold_clauses)} clauses against {url} …")
    results = []
    for item in gold_clauses:
        print(f"  {item['id']} {item['category']} …", end=" ", flush=True)
        try:
            r = _analyze_clause_http(item["clause"], url, token)
            results.append(r)
            print(r.get("risk", "?"))
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({"risk": "error", "title": "", "body": "", "statute": None})
    return results


def _append_history(metrics: dict, mode: str):
    """Append a timestamped summary to eval_history.json for trend tracking."""
    entry = {
        "timestamp":   datetime.utcnow().isoformat() + "Z",
        "mode":        mode,
        "n":           metrics["n"],
        "risk_acc":    round(metrics["risk_acc"],    4),
        "statute_hit": round(metrics["statute_hit"], 4),
        "keyword_hit": round(metrics["keyword_hit"], 4),
        "precision":   round(metrics["precision"],   4),
        "pass":        metrics["precision"] >= PASS_THRESHOLD,
    }
    history = []
    if HISTORY_PATH.exists():
        with open(HISTORY_PATH) as f:
            history = json.load(f)
    history.append(entry)
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2)
    print(f"History entry appended to {HISTORY_PATH}  ({len(history)} runs total)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Veritas gold-set evaluator")
    parser.add_argument("--mode", choices=["direct", "http"], default="direct",
                        help="'direct' imports the pipeline; 'http' calls a running server")
    parser.add_argument("--url",   default="http://localhost:8000", help="Base URL (http mode only)")
    parser.add_argument("--token", default="",                       help="Firebase ID token (http mode only)")
    parser.add_argument("--no-history", action="store_true",
                        help="Skip appending results to eval_history.json")
    args = parser.parse_args()

    with open(GOLD_PATH) as f:
        gold = json.load(f)
    clauses = gold["clauses"]

    if args.mode == "direct":
        results = asyncio.run(main_direct(clauses))
    else:
        if not args.token:
            print("--token is required for http mode", file=sys.stderr)
            sys.exit(2)
        results = main_http(clauses, args.url, args.token)

    metrics = _run_evaluation(clauses, results)
    _print_report(metrics)

    # Persist latest results for CI artifact inspection
    with open(RESULTS_PATH, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    print(f"Results written to {RESULTS_PATH}")

    # Append to history for trend tracking
    if not args.no_history:
        _append_history(metrics, args.mode)

    sys.exit(0 if metrics["precision"] >= PASS_THRESHOLD else 1)
