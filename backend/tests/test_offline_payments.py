"""In-process endpoint tests for the Organisation Admin offline/EcoCash payment
workflow (BRD section 6) — backend/server.py's org_admin_router.

Uses FastAPI's TestClient against the real `server.app`, with `server.db`
monkeypatched to the in-memory fake_db (see conftest.py) and `get_current_user`
overridden via FastAPI's dependency_overrides, so no live MongoDB or deployed
server is required. This exercises the full route — request validation, role
checks, org-scoping (BR-08), and the audit trail — not just the service layer
already covered by test_payment_status_service.py.
"""
import os
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "test_db")
os.environ.setdefault("PAYMENT_ENCRYPTION_KEY", "bB8dGUMRvGxiAbODPEPSQaFmfaS8mPf50CsFZjHjcD0=")

from fastapi.testclient import TestClient
import server
from conftest import FakeDB


@pytest.fixture
def client_and_db(monkeypatch):
    fake = FakeDB()
    monkeypatch.setattr(server, "db", fake)
    client = TestClient(server.app)
    return client, fake


def _as_org_admin(client, fake_db, org_id="org-1"):
    admin = {"id": "admin-1", "role": "org_admin", "organization_id": org_id, "full_name": "Org Admin"}
    server.app.dependency_overrides[server.get_current_user] = lambda: admin
    return admin


def _seed_learner(fake_db, org_id="org-1", learner_id=None):
    learner_id = learner_id or str(uuid.uuid4())
    fake_db.users.docs.append({
        "id": learner_id, "email": "learner@example.com", "phone_number": "+263771111111",
        "full_name": "Test Learner", "role": "student", "organization_id": org_id,
        "phone_verified": False, "is_active": True,
    })
    return learner_id


def _seed_course(fake_db, course_id=None, price=300, duration_months=6):
    course_id = course_id or str(uuid.uuid4())
    fake_db.courses.docs.append({
        "id": course_id, "name": "AI Fundamentals", "price": price,
        "duration_months": duration_months, "is_paid": True, "organization_id": "org-1",
    })
    return course_id


def test_record_manual_payment_partial_then_qualifying(client_and_db):
    client, fake = client_and_db
    _as_org_admin(client, fake)
    learner_id = _seed_learner(fake)
    course_id = _seed_course(fake, price=300, duration_months=6)  # minimum = $50

    resp1 = client.post("/api/org-admin/payments/manual", json={
        "learner_id": learner_id, "course_id": course_id, "amount": 30,
        "method": "ecocash", "reference": "EC-001",
    })
    assert resp1.status_code == 201, resp1.text
    body1 = resp1.json()
    assert body1["assessment_access_activated"] is False
    assert body1["enrollment"]["payment_status"] == "partially_paid"

    resp2 = client.post("/api/org-admin/payments/manual", json={
        "learner_id": learner_id, "course_id": course_id, "amount": 20,
        "method": "ecocash", "reference": "EC-002",
    })
    assert resp2.status_code == 201, resp2.text
    body2 = resp2.json()
    assert body2["assessment_access_activated"] is True
    assert body2["enrollment"]["payment_status"] == "current"

    server.app.dependency_overrides.clear()


def test_manual_payment_rejects_amount_not_silently_altered(client_and_db):
    """BR-07: the recorded amount is exactly what's given — not rounded up to the minimum."""
    client, fake = client_and_db
    _as_org_admin(client, fake)
    learner_id = _seed_learner(fake)
    course_id = _seed_course(fake, price=120, duration_months=3)  # minimum = $40

    resp = client.post("/api/org-admin/payments/manual", json={
        "learner_id": learner_id, "course_id": course_id, "amount": 15, "method": "ecocash",
    })
    assert resp.status_code == 201
    payments = fake.manual_payments.docs
    assert len(payments) == 1
    assert payments[0]["amount"] == 15  # exact amount, not bumped to the $40 minimum

    server.app.dependency_overrides.clear()


def test_manual_payment_writes_audit_entry(client_and_db):
    """AC-13: every manual payment appears in the audit log."""
    client, fake = client_and_db
    _as_org_admin(client, fake)
    learner_id = _seed_learner(fake)
    course_id = _seed_course(fake)

    resp = client.post("/api/org-admin/payments/manual", json={
        "learner_id": learner_id, "course_id": course_id, "amount": 50, "method": "ecocash",
    })
    assert resp.status_code == 201
    audit_entries = [d for d in fake.audit_logs.docs if d["entity"] == "payment"]
    assert len(audit_entries) == 1
    assert audit_entries[0]["actor_id"] == "admin-1"
    assert audit_entries[0]["action"] == "record_manual_payment"

    server.app.dependency_overrides.clear()


def test_org_admin_cannot_act_on_other_organisations_learner(client_and_db):
    """BR-08: an Organisation Admin may only manage learners within their own org."""
    client, fake = client_and_db
    _as_org_admin(client, fake, org_id="org-1")
    other_org_learner = _seed_learner(fake, org_id="org-2")
    course_id = _seed_course(fake)

    resp = client.post("/api/org-admin/payments/manual", json={
        "learner_id": other_org_learner, "course_id": course_id, "amount": 50, "method": "ecocash",
    })
    assert resp.status_code == 403

    server.app.dependency_overrides.clear()


def test_manual_payment_rejects_invalid_method(client_and_db):
    client, fake = client_and_db
    _as_org_admin(client, fake)
    learner_id = _seed_learner(fake)
    course_id = _seed_course(fake)

    resp = client.post("/api/org-admin/payments/manual", json={
        "learner_id": learner_id, "course_id": course_id, "amount": 50, "method": "paynow",
    })
    assert resp.status_code == 400

    server.app.dependency_overrides.clear()


def test_void_payment_is_reversal_not_deletion(client_and_db):
    """section 8: prefer reversal/void over hard deletion of financial records."""
    client, fake = client_and_db
    _as_org_admin(client, fake)
    learner_id = _seed_learner(fake)
    course_id = _seed_course(fake)

    create_resp = client.post("/api/org-admin/payments/manual", json={
        "learner_id": learner_id, "course_id": course_id, "amount": 50, "method": "ecocash",
    })
    payment_id = create_resp.json()["payment"]["id"]

    void_resp = client.post(f"/api/org-admin/payments/{payment_id}/void", json={"reason": "duplicate entry"})
    assert void_resp.status_code == 200
    assert void_resp.json()["status"] == "voided"

    stored = next(p for p in fake.manual_payments.docs if p["id"] == payment_id)
    assert stored["status"] == "voided"  # still present, not deleted
    assert stored["void_reason"] == "duplicate entry"

    server.app.dependency_overrides.clear()


def test_learner_search_scoped_to_admin_organisation(client_and_db):
    client, fake = client_and_db
    _as_org_admin(client, fake, org_id="org-1")
    _seed_learner(fake, org_id="org-1", learner_id="learner-in-org")
    _seed_learner(fake, org_id="org-2", learner_id="learner-other-org")

    resp = client.get("/api/org-admin/learners/search", params={"q": "learner@example.com"})
    assert resp.status_code == 200
    ids = [l["id"] for l in resp.json()]
    assert "learner-in-org" in ids
    assert "learner-other-org" not in ids

    server.app.dependency_overrides.clear()
