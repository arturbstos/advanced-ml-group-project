# German Freelancer Contract Analyzer

## Architecture Overview

This project is a cloud-native Contract Analyzer designed to catch legal and commercial risks in German freelance contracts. It replaces a legacy PostgreSQL/pgvector and Streamlit stack with a fully managed Google Cloud infrastructure.

*   **Backend:** FastAPI application running on **Google Cloud Run**.
*   **Database:** **Firebase Firestore** with native Vector Search (`find_nearest`) for semantic matching.
*   **Frontend:** Custom Vanilla HTML/JS/CSS frontend deployed to **Firebase Hosting**.
*   **AI Integration:** Uses OpenAI (`text-embedding-3-small` and `gpt-4o-mini`) for embeddings and extraction.

---

## Setup Instructions (Local & Cloud)

### 1. Prerequisites
You need a Google Cloud Project with Firestore enabled.
Make sure you have `firebase-tools` and `gcloud` CLI installed.

```bash
# Authenticate with Google Cloud
gcloud auth login
gcloud config set project [YOUR_PROJECT_ID]

# Authenticate with Firebase
firebase login
```

### 2. Environment & Dependencies

1. **Create Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Python Packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Keys**:
   - Copy `.env.example` to a new `.env` file.
   - Insert your real `OPENAI_API_KEY`.
   - Download your Firebase Service Account JSON and save it as `firebase-adminsdk.json` in the root folder.
   - Ensure `GOOGLE_APPLICATION_CREDENTIALS="firebase-adminsdk.json"` is exported in your environment.

### 3. Database Seeding

The application relies on two data sets in Firestore: **Rates** and the **Playbook**.

#### Seed Rates
```bash
python scripts/seed_firestore.py
```
*This script will provision the `rate_benchmarks` collection in Firestore with the baseline data from Freelancer-Kompass 2025.*

#### Seed Playbook & Vectors
The Layer 2 playbook contains the curated risky-clause patterns. We use a python script to parse the 66 entries from the legacy SQL seed file, generate OpenAI embeddings on the fly, and insert them natively into Firestore:
```bash
python scripts/parse_and_seed_firestore.py
```

---

## Running the Application Locally

The analyzer consists of a FastAPI backend and a Firebase static frontend. They can be run simultaneously in **two separate terminal windows**.

### Window 1: Start the Backend server
The backend handles the PDF data extraction, LLM structuring, and vector comparison computations.

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```
*This server will run at `http://localhost:8000`.*

### Window 2: Start the Frontend UI
The static frontend is built with vanilla web technologies. You can serve it locally using python's built-in HTTP server or Firebase emulators.

```bash
# Quickest way to serve locally
python -m http.server 3000 --directory frontend/
```
*(Ensure `frontend/app.js` is pointed to your local `http://localhost:8000` API if testing locally).*

---

## Cloud Deployment

### 1. Backend (Cloud Run)
Deploy the FastAPI application to Google Cloud Run. Ensure you have your `firebase-adminsdk.json` stored securely (e.g., in Secret Manager) and mounted into the container at `/secrets/firebase-adminsdk.json`.
```bash
gcloud run deploy contract-analyzer \
  --source . \
  --region europe-west1 \
  --set-env-vars OPENAI_API_KEY="your-key-here"
```
*Note: The container uses `startup.py` as its entrypoint to properly configure Python module paths in the root `/code` directory.*

### 2. Frontend (Firebase Hosting)
Update the `API_URL` constant in `frontend/app.js` to point to your new Cloud Run URL.
```javascript
const API_URL = 'https://contract-analyzer-XXXXX.run.app';
```
Then, deploy the frontend using Firebase CLI:
```bash
firebase deploy --only hosting
```

---

## Testing with Sample Data

A mock contract exists under `tests/samples/sample.pdf` that triggers simulated risk warnings for hourly rates, IP, Scheinselbstständigkeit, and payment terms. Simply drop it into the web interface to see the pipeline end to end!

For a script-based smoke test comparing our Playbook-Driven Analyzer against a generic LLM baseline (GPT-4o), see the artifacts in `tests/samples/side_by_side_demo.md`.
