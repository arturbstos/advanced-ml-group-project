"""Entrypoint that guarantees /code is on sys.path before uvicorn loads the app."""
import sys, os

# Ensure the project root (/code) is the first entry in sys.path
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
