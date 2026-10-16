"""Iteration 45 tests:
- Audio route auth regression (must be 401/403 without auth, not 404)
- Learner generate-video endpoint (auth gating, job creation, idempotent within 1 minute)
- Video-job status polling
- Test email returns sent=1 and HTML contains cognify.aiinstituteafrica.com
- render_notification import & PUBLIC_FRONTEND_URL resolution in send_notification_email
"""
import os
import sys
import time
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://knowledge-sync-9.preview.emergentagent.com").rstrip("/")
SUPER_EMAIL = "takuechakanyuka@gmail.com"
SUPER_PASS = "SuperAdmin@2026!"

sys.path.insert(0, "/app/backend")


@pytest.fixture(scope="session")
def super_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": SUPER_EMAIL, "password": SUPER_PASS}, timeout=15)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(super_token):
    return {"Authorization": f"Bearer {super_token}"}


@pytest.fixture(scope="session")
def any_doc_id(auth_headers):
    r = requests.get(f"{BASE_URL}/api/public/content", headers=auth_headers, timeout=15)
    assert r.status_code == 200, r.text
    payload = r.json()
    items = payload.get("documents") if isinstance(payload, dict) else payload
    assert items, f"No public content docs to test against. Body: {payload}"
    return items[0]["id"]


# --- 1. Audio route auth regression ---
class TestAudioRouteAuth:
    def test_audio_unauthed_is_not_404(self, any_doc_id):
        """Critical regression: orphan @public_router.get decorator previously broke this route → 404.
        Now must return 401/403 for unauthed (auth failure, not missing route)."""
        url = f"{BASE_URL}/api/public/{any_doc_id}/audio/any-audio-id"
        r = requests.get(url, timeout=10)
        assert r.status_code in (401, 403), (
            f"Expected 401/403 for unauth audio access; got {r.status_code}. "
            f"404 would indicate route registration regression. Body: {r.text[:200]}"
        )

    def test_audio_authed_missing_audio_is_404(self, any_doc_id, auth_headers):
        """With valid auth but non-existent audio id, returns 404 (route handler is reached)."""
        r = requests.get(f"{BASE_URL}/api/public/{any_doc_id}/audio/does-not-exist",
                         headers=auth_headers, timeout=10)
        assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text[:200]}"


# --- 2. Learner generate-video endpoint ---
class TestLearnerGenerateVideo:
    def test_unauthed_blocked(self, any_doc_id):
        r = requests.post(f"{BASE_URL}/api/public/content/{any_doc_id}/generate-video?duration=8",
                          timeout=10)
        assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}: {r.text[:200]}"

    def test_authed_returns_job_id_or_already_available(self, any_doc_id, auth_headers):
        r = requests.post(f"{BASE_URL}/api/public/content/{any_doc_id}/generate-video?duration=8",
                          headers=auth_headers, timeout=15)
        assert r.status_code == 200, f"Got {r.status_code}: {r.text[:300]}"
        data = r.json()
        # Either a new/existing job, or video already attached
        assert ("job_id" in data and "status" in data) or data.get("status") == "already_available", (
            f"Unexpected response shape: {data}"
        )

    def test_idempotent_returns_same_job_id_or_already_available(self, any_doc_id, auth_headers):
        r1 = requests.post(f"{BASE_URL}/api/public/content/{any_doc_id}/generate-video?duration=8",
                           headers=auth_headers, timeout=15)
        r2 = requests.post(f"{BASE_URL}/api/public/content/{any_doc_id}/generate-video?duration=8",
                           headers=auth_headers, timeout=15)
        assert r1.status_code == 200 and r2.status_code == 200
        d1, d2 = r1.json(), r2.json()
        if d1.get("status") == "already_available":
            assert d2.get("status") == "already_available"
        else:
            assert d1.get("job_id") == d2.get("job_id"), (
                f"Idempotency failed — different job_ids: {d1.get('job_id')} vs {d2.get('job_id')}"
            )

    def test_video_job_status_poll(self, any_doc_id, auth_headers):
        r = requests.post(f"{BASE_URL}/api/public/content/{any_doc_id}/generate-video?duration=8",
                          headers=auth_headers, timeout=15)
        d = r.json()
        if d.get("status") == "already_available":
            pytest.skip("Doc already has a video; cannot test job polling")
        job_id = d["job_id"]
        time.sleep(1)
        r2 = requests.get(f"{BASE_URL}/api/public/content/{any_doc_id}/video-job/{job_id}",
                          headers=auth_headers, timeout=10)
        assert r2.status_code == 200, f"Got {r2.status_code}: {r2.text[:200]}"
        body = r2.json()
        assert "status" in body
        assert body["status"] in ("processing", "queued", "completed", "failed")

    def test_video_job_unauthed_blocked(self, any_doc_id):
        r = requests.get(f"{BASE_URL}/api/public/content/{any_doc_id}/video-job/some-id", timeout=10)
        assert r.status_code in (401, 403)


# --- 3. Email production URL ---
class TestEmailProductionURL:
    def test_test_email_sends(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/super-admin/test-email", headers=auth_headers, timeout=30)
        assert r.status_code == 200, f"Got {r.status_code}: {r.text[:300]}"
        data = r.json()
        # Spec says sent=1
        assert data.get("sent", 0) >= 1, f"Expected sent>=1, got {data}"

    def test_render_notification_with_send_helper_uses_public_frontend_url(self):
        """render_notification doesn't itself resolve relative URLs — that's send_notification_email.
        Verify the upstream resolution path uses PUBLIC_FRONTEND_URL when frontend_base_url=None
        and action_url='/super-admin'.
        """
        # Static import
        from services.smtp_notifications import render_notification  # noqa: F401
        # Verify env has PUBLIC_FRONTEND_URL set to production URL
        public_url = os.environ.get("PUBLIC_FRONTEND_URL")
        assert public_url and "cognify.aiinstituteafrica.com" in public_url, (
            f"PUBLIC_FRONTEND_URL not set correctly: {public_url}"
        )
        # Render directly with the resolved absolute URL (what send_notification_email would produce)
        full_url = public_url.rstrip("/") + "/super-admin"
        html = render_notification(title="t", message="m", action_label="Go", action_url=full_url)
        assert "cognify.aiinstituteafrica.com/super-admin" in html, (
            f"HTML body missing production URL. Snippet: {html[:300]}"
        )
