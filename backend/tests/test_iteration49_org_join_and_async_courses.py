"""Iteration 49 tests.

Covers:
  (A) Organization Public Join Link feature (org_join_routes.py)
  (B) Async course generation (/api/courses/generate-custom, /api/org-admin/create-course-from-pdf, /api/courses/{id}/generation-status)
  (C) Mark-orphans idempotency
  (D) Regression: /api/payments/status
"""
from __future__ import annotations
import io
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://knowledge-sync-9.preview.emergentagent.com").rstrip("/")
SLUG = "harare-institute-of-technology"
ORG_ID = "713d6714-6851-48e9-83af-acda6f1a83a7"
SUPER_EMAIL = "takuechakanyuka@gmail.com"
SUPER_PASSWORD = "SuperAdmin@2026!"

RUN_TAG = uuid.uuid4().hex[:8]


# ---------- fixtures ----------
@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def super_token(api):
    r = api.post(f"{BASE_URL}/api/auth/login", json={
        "email": SUPER_EMAIL, "password": SUPER_PASSWORD})
    assert r.status_code == 200, f"super admin login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def super_hdr(super_token):
    return {"Authorization": f"Bearer {super_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module", autouse=True)
def restore_join_settings(super_hdr):
    """Ensure default join settings are restored after all tests."""
    yield
    try:
        requests.put(f"{BASE_URL}/api/org-admin/join-settings",
                     headers=super_hdr,
                     json={"enabled": True, "require_approval": True, "allowed_domains": []},
                     timeout=30)
    except Exception:
        pass


# ============================================================
#  (A) Organization Public Join Link
# ============================================================
class TestPublicOrgLanding:
    def test_landing_ok(self, api):
        r = api.get(f"{BASE_URL}/api/public/org/{SLUG}")
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["org"]["id"] == ORG_ID
        assert "member_count" in d
        assert isinstance(d.get("public_courses"), list)
        assert d.get("join_slug")
        assert d.get("require_approval") is True

    def test_landing_404(self, api):
        r = api.get(f"{BASE_URL}/api/public/org/nonexistent-{RUN_TAG}")
        assert r.status_code == 404


# --- signup flow (module-scoped so approve/reject tests share the user) ---
@pytest.fixture(scope="module")
def pending_user(api):
    email = f"test.pending.{RUN_TAG}@example.com"
    r = api.post(f"{BASE_URL}/api/public/org/{SLUG}/signup", json={
        "email": email, "password": "TestPass1234", "full_name": "Pending Tester"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["status"] == "pending"
    assert "access_token" not in d
    return {"email": email, "password": "TestPass1234", "user_id": d["user_id"]}


class TestPublicSignup:
    def test_signup_pending(self, pending_user):
        assert pending_user["user_id"]

    def test_duplicate_email(self, api, pending_user):
        r = api.post(f"{BASE_URL}/api/public/org/{SLUG}/signup", json={
            "email": pending_user["email"], "password": "TestPass1234",
            "full_name": "Dup"})
        assert r.status_code == 400
        assert "already exists" in r.text.lower()

    def test_pending_login_blocked(self, api, pending_user):
        r = api.post(f"{BASE_URL}/api/auth/login", json={
            "email": pending_user["email"], "password": pending_user["password"]})
        assert r.status_code == 403
        assert "pending" in r.text.lower()


class TestOrgAdminPending:
    def test_list_pending(self, super_hdr, pending_user):
        r = requests.get(f"{BASE_URL}/api/org-admin/pending-members", headers=super_hdr)
        assert r.status_code == 200, r.text
        d = r.json()
        ids = [p["id"] for p in d.get("pending", [])]
        assert pending_user["user_id"] in ids

    def test_approve_and_login(self, super_hdr, pending_user):
        uid = pending_user["user_id"]
        r = requests.post(f"{BASE_URL}/api/org-admin/pending-members/{uid}/approve",
                          headers=super_hdr, timeout=30)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "approved"
        # Now login should work
        lr = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": pending_user["email"], "password": pending_user["password"]})
        assert lr.status_code == 200, lr.text
        assert lr.json()["user"]["organization_id"] == ORG_ID


@pytest.fixture(scope="module")
def rejected_user(api):
    email = f"test.reject.{RUN_TAG}@example.com"
    r = api.post(f"{BASE_URL}/api/public/org/{SLUG}/signup", json={
        "email": email, "password": "TestPass1234", "full_name": "Reject Tester"})
    assert r.status_code == 200
    return {"email": email, "password": "TestPass1234", "user_id": r.json()["user_id"]}


class TestReject:
    def test_reject_marks_and_blocks_login(self, super_hdr, rejected_user):
        uid = rejected_user["user_id"]
        r = requests.post(f"{BASE_URL}/api/org-admin/pending-members/{uid}/reject",
                          headers=super_hdr, json={"reason": "test reject"}, timeout=30)
        assert r.status_code == 200
        assert r.json()["status"] == "rejected"
        lr = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": rejected_user["email"], "password": rejected_user["password"]})
        assert lr.status_code == 403
        assert "not accepted" in lr.text.lower() or "reject" in lr.text.lower()


class TestJoinSettings:
    def test_domain_allowlist(self, super_hdr, api):
        # set allow-list to hit.ac.zw
        r = requests.put(f"{BASE_URL}/api/org-admin/join-settings",
                         headers=super_hdr,
                         json={"enabled": True, "require_approval": True,
                               "allowed_domains": ["hit.ac.zw"]})
        assert r.status_code == 200
        # sign-up from example.com should fail
        email = f"test.dom.{RUN_TAG}@example.com"
        sr = api.post(f"{BASE_URL}/api/public/org/{SLUG}/signup", json={
            "email": email, "password": "TestPass1234", "full_name": "Dom Tester"})
        assert sr.status_code == 400
        assert "hit.ac.zw" in sr.text
        # restore
        requests.put(f"{BASE_URL}/api/org-admin/join-settings", headers=super_hdr,
                     json={"enabled": True, "require_approval": True, "allowed_domains": []})

    def test_disabled_link(self, super_hdr, api):
        requests.put(f"{BASE_URL}/api/org-admin/join-settings", headers=super_hdr,
                     json={"enabled": False, "require_approval": True, "allowed_domains": []})
        r = api.get(f"{BASE_URL}/api/public/org/{SLUG}")
        assert r.status_code == 403
        sr = api.post(f"{BASE_URL}/api/public/org/{SLUG}/signup", json={
            "email": f"test.dis.{RUN_TAG}@example.com", "password": "TestPass1234",
            "full_name": "Dis"})
        assert sr.status_code == 403
        # re-enable
        requests.put(f"{BASE_URL}/api/org-admin/join-settings", headers=super_hdr,
                     json={"enabled": True, "require_approval": True, "allowed_domains": []})

    def test_auto_approval(self, super_hdr, api):
        requests.put(f"{BASE_URL}/api/org-admin/join-settings", headers=super_hdr,
                     json={"enabled": True, "require_approval": False, "allowed_domains": []})
        email = f"test.auto.{RUN_TAG}@example.com"
        sr = api.post(f"{BASE_URL}/api/public/org/{SLUG}/signup", json={
            "email": email, "password": "TestPass1234", "full_name": "Auto"})
        assert sr.status_code == 200, sr.text
        d = sr.json()
        assert d["status"] == "active"
        assert d.get("access_token")
        # restore
        requests.put(f"{BASE_URL}/api/org-admin/join-settings", headers=super_hdr,
                     json={"enabled": True, "require_approval": True, "allowed_domains": []})


# ============================================================
#  (B) Async course generation
# ============================================================
class TestAsyncCourseGen:
    def test_generate_custom_fast(self, super_hdr):
        payload = {
            "title": f"Test Course Async {RUN_TAG}",
            "description": "Async fix test",
            "learning_goal": "Verify async generation returns fast",
            "target_audience": "beginner",
            "duration_weeks": 2,
            "num_lessons": 3,
            "course_type": "free_custom",
            "language": "en",
        }
        t0 = time.time()
        r = requests.post(f"{BASE_URL}/api/courses/generate-custom",
                          headers=super_hdr, json=payload, timeout=30)
        dt = time.time() - t0
        assert r.status_code == 200, r.text
        assert dt < 15, f"Expected <15s, took {dt:.1f}s"
        d = r.json()
        assert d["generation_status"] == "generating"
        cid = d["course_id"]

        # poll for readiness
        pytest.async_course_id = cid
        status = None
        deadline = time.time() + 90
        while time.time() < deadline:
            pr = requests.get(f"{BASE_URL}/api/courses/{cid}/generation-status",
                              headers=super_hdr, timeout=20)
            assert pr.status_code == 200
            pd = pr.json()
            status = pd["status"]
            if status in ("ready", "failed"):
                break
            time.sleep(4)
        assert status == "ready", f"final status={status}"
        assert pd.get("num_lessons_generated", 0) > 0

    def test_publish_after_ready(self, super_hdr):
        cid = getattr(pytest, "async_course_id", None)
        if not cid:
            pytest.skip("prior test did not produce course")
        r = requests.post(f"{BASE_URL}/api/courses/{cid}/publish",
                          headers=super_hdr, timeout=30)
        # publish must succeed (200) or return a well-formed error, not 5xx
        assert r.status_code in (200, 400), r.text

    def test_pdf_course_fast(self, super_token):
        # Build a minimal PDF in memory using reportlab if available; otherwise a raw pdf skeleton
        try:
            from reportlab.pdfgen import canvas
            buf = io.BytesIO()
            c = canvas.Canvas(buf)
            c.drawString(72, 720, "Chapter 1: Intro")
            c.drawString(72, 700, "This is a test PDF used to generate a course.")
            c.showPage()
            c.save()
            pdf_bytes = buf.getvalue()
        except Exception:
            pdf_bytes = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
                         b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
                         b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
                         b"xref\n0 4\n0000000000 65535 f\n"
                         b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n0\n%%EOF\n")

        t0 = time.time()
        r = requests.post(
            f"{BASE_URL}/api/org-admin/create-course-from-pdf",
            headers={"Authorization": f"Bearer {super_token}"},
            files={"file": (f"test_{RUN_TAG}.pdf", pdf_bytes, "application/pdf")},
            data={"title": f"Test Course PDF {RUN_TAG}", "category": "certificate", "price": 0},
            timeout=30,
        )
        dt = time.time() - t0
        assert r.status_code == 200, r.text
        assert dt < 15, f"Expected <15s, took {dt:.1f}s"
        d = r.json()
        assert d["generation_status"] == "generating"
        cid = d["course_id"]

        # poll
        deadline = time.time() + 90
        status = None
        while time.time() < deadline:
            pr = requests.get(f"{BASE_URL}/api/courses/{cid}/generation-status",
                              headers={"Authorization": f"Bearer {super_token}"}, timeout=20)
            assert pr.status_code == 200
            status = pr.json()["status"]
            if status in ("ready", "failed"):
                break
            time.sleep(4)
        # Allow either ready or failed but not stuck generating
        assert status in ("ready", "failed"), f"final status={status}"


# ============================================================
#  (C) Mark-orphans idempotency
# ============================================================
class TestMarkOrphans:
    def test_idempotent_mark(self, super_hdr):
        """Create an orphan, call mark twice; 2nd call must return marked_lost=0."""
        # Pick an active public content doc and simulate orphan by moving file aside
        # Simpler: force via DB manipulation is out-of-scope here, so we just call
        # mark twice and assert 2nd call is 0 relative to 1st.
        r1 = requests.post(f"{BASE_URL}/api/super-admin/public-content/orphans/mark",
                           headers=super_hdr, timeout=90)
        assert r1.status_code == 200, r1.text
        d1 = r1.json()
        assert "marked_lost" in d1

        r2 = requests.post(f"{BASE_URL}/api/super-admin/public-content/orphans/mark",
                           headers=super_hdr, timeout=90)
        assert r2.status_code == 200
        d2 = r2.json()
        # Idempotency: whatever was marked on the first call must NOT be re-marked
        assert d2["marked_lost"] == 0, (
            f"Idempotency broken: 2nd call marked_lost={d2['marked_lost']} (should be 0). "
            f"1st={d1}")


# ============================================================
#  (D) Regression: /api/payments/status
# ============================================================
class TestPaymentsStatus:
    def test_status(self, api):
        r = api.get(f"{BASE_URL}/api/payments/status")
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("fail_open") is True
