# app/main.py
import os
import shutil
import tempfile

from dotenv import load_dotenv

# Load .env BEFORE importing app.services / db modules. Several of them
# instantiate AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")) at import
# time, so the key must already be in the environment by then.
load_dotenv()

import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin SDK
cred_path = "firebase-adminsdk.json"
if os.path.exists(cred_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
else:
    firebase_admin.initialize_app()

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# Pipeline: ingest -> analyze -> assemble report
from app.services.ingestion import process_contract
from app.services.clause_analyzer import analyze as analyze_clauses
from app.services.report_builder import build as build_report

app = FastAPI(title="German Freelancer Contract Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for local web development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Verify API is up and the database connection is functional."""
    try:
        from google.cloud import firestore
        db = firestore.Client(database="contractdb")
        db.collection("health").limit(1).get()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/analyze")
async def analyze_contract(
    file: UploadFile = File(...),
):
    """Full analysis pipeline: ingest -> analyze -> assemble report.

    1. Ingest  - PDF -> structured ContractExtraction (GPT-4o-mini).
    2. Analyze - per-clause risk analysis against playbook, statutes, rates.
    3. Report  - summary counts, findings list, negotiation brief.
    """
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name

    try:
        try:
            extraction = await process_contract(temp_path)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        findings = await analyze_clauses(extraction)
        report = build_report(extraction, findings)
        return report
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
