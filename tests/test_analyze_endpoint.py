"""Integration test for POST /analyze.

External dependencies (Firebase Auth, Firestore, OpenAI) are stubbed so the
test runs offline and deterministically. Run with:

    pip install pytest pytest-asyncio httpx
    pytest tests/test_analyze_endpoint.py -v
"""
import os
import sys
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# Minimal valid PDF byte string — passes the magic-bytes check in /analyze.
# We never actually parse it because process_contract is mocked.
_FAKE_PDF_BYTES = b"%PDF-1.4\n%fake\n%%EOF\n"


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("ENV", "development")


@pytest.fixture
def patched_app(monkeypatch):
    """Import app.main with all external services stubbed out."""
    # Stub firebase_admin BEFORE app.main is imported, since app.main calls
    # firebase_admin.initialize_app() at import time.
    import firebase_admin
    from firebase_admin import auth as fb_auth, credentials as fb_cred

    monkeypatch.setattr(firebase_admin, "initialize_app", lambda *a, **k: None)
    monkeypatch.setattr(fb_cred, "Certificate", lambda *_a, **_k: object())
    monkeypatch.setattr(
        fb_auth,
        "verify_id_token",
        lambda _t: {"uid": "test-user"},
    )

    # Stub the Firestore AsyncClient before app.main creates a singleton.
    class _FakeQuery:
        def where(self, *_a, **_k): return self
        def order_by(self, *_a, **_k): return self
        def limit(self, *_a, **_k): return self

        async def stream(self):
            return
            yield  # pragma: no cover — keep this an async generator

    class _FakeDoc:
        async def set(self, *_a, **_k): return None
        async def delete(self, *_a, **_k): return None

        async def get(self, *_a, **_k):
            class _Snapshot:
                exists = False
                def to_dict(self): return {}
            return _Snapshot()

        def collection(self, *_a, **_k): return _FakeColl()

    class _FakeColl(_FakeQuery):
        def document(self, *_a, **_k): return _FakeDoc()

    class _FakeDB:
        def collection(self, *_a, **_k): return _FakeColl()

    from google.cloud import firestore as gc_firestore
    monkeypatch.setattr(
        gc_firestore,
        "AsyncClient",
        lambda *a, **k: _FakeDB(),
    )

    # Now safe to import the app.
    from app import main as main_module

    # Stub the pipeline so we never hit OpenAI.
    from app.services.ingestion import ContractExtraction
    from app.services.clause_analyzer import Finding

    async def fake_process_contract(_path: str):
        return (
            ContractExtraction(
                skill_category="Software Development",
                region="Berlin",
                experience_level="mid",
                hourly_rate_eur=80.0,
                payment_terms_days=30,
            ),
            ["Sample clause text for the test."],
        )

    async def fake_analyze_clauses(_extraction, _clauses):
        finding = Finding(
            risk="medium",
            title="Sample finding",
            clause="Sample clause text for the test.",
            body="Test body that explains the risk in 2-3 sentences.",
            redline=None,
            statute="§ 7 SGB IV",
            source="Playbook PB-001",
        )
        return [finding], None

    monkeypatch.setattr(main_module, "process_contract", fake_process_contract)
    monkeypatch.setattr(main_module, "analyze_clauses", fake_analyze_clauses)

    # Tier check + monthly count — bypass quota.
    async def _tier(_uid): return "pro"
    async def _count(_uid): return 0
    monkeypatch.setattr(main_module, "_get_user_tier", _tier)
    monkeypatch.setattr(main_module, "_get_monthly_count", _count)

    # Replace the singleton DB so the post-analysis save doesn't hit Firestore.
    monkeypatch.setattr(main_module, "_db", _FakeDB())

    return main_module.app


@pytest.mark.asyncio
async def test_analyze_returns_structured_report(patched_app):
    transport = ASGITransport(app=patched_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.post(
            "/analyze",
            files={"file": ("sample.pdf", _FAKE_PDF_BYTES, "application/pdf")},
            headers={"Authorization": "Bearer test-token"},
        )

    assert resp.status_code == 200, resp.text
    data: dict[str, Any] = resp.json()

    findings = data.get("findings")
    assert isinstance(findings, list) and len(findings) >= 1, "expected at least one finding"

    for f in findings:
        assert f.get("risk"), "finding.risk must be non-empty"
        assert f.get("title"), "finding.title must be non-empty"
        assert f.get("body"), "finding.body must be non-empty"


@pytest.mark.asyncio
async def test_analyze_rejects_unauthenticated_request(patched_app, monkeypatch):
    from firebase_admin import auth as fb_auth
    monkeypatch.setattr(
        fb_auth, "verify_id_token", lambda _t: (_ for _ in ()).throw(ValueError("bad")),
    )

    transport = ASGITransport(app=patched_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.post(
            "/analyze",
            files={"file": ("sample.pdf", _FAKE_PDF_BYTES, "application/pdf")},
            headers={"Authorization": "Bearer broken-token"},
        )

    assert resp.status_code == 401
