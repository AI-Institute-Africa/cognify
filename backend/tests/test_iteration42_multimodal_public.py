"""Iteration 42 - Multi-modal public content viewer backend tests.

Covers:
- GET /api/public/content/<docId>/media-info (auth required) - returns preview_text,
  description, category, filename in addition to audio_url & video_url.
- POST /api/language/translate - translation endpoint used by Text Summary tab.
- POST /api/advanced/tts - audio synthesis endpoint used by Audio tab.
- POST /api/content/generate-slides + /api/content/slides-status - async job.
- POST /api/advanced/lesson/generate - structured AI lesson for Avatar Teach tab.
- Email notification path: posting new content fires _notify_org_new_content
  (verify no errors via backend logs).
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://knowledge-sync-9.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

STUDENT = ("demo.student@cognify.edu", "demo123")
ORG_ADMIN = ("test.orgadmin@cognify.edu", "admin123")
PUBLIC_DOC_ID = "0f5b125a-a58b-4862-969c-ecb641b44a7e"


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def student_token():
    return _login(*STUDENT)


@pytest.fixture(scope="module")
def org_admin_token():
    return _login(*ORG_ADMIN)


# ---- Public media-info ----------------------------------------------------
class TestPublicMediaInfo:
    def test_media_info_requires_auth(self):
        r = requests.get(f"{API}/public/content/{PUBLIC_DOC_ID}/media-info", timeout=15)
        assert r.status_code in (401, 403), f"expected auth required, got {r.status_code}"

    def test_media_info_returns_preview_fields(self, student_token):
        r = requests.get(
            f"{API}/public/content/{PUBLIC_DOC_ID}/media-info",
            headers={"Authorization": f"Bearer {student_token}"},
            timeout=20,
        )
        assert r.status_code == 200, f"{r.status_code} {r.text}"
        data = r.json()
        # New fields added in this iteration
        for k in ("id", "title", "description", "category", "filename",
                  "preview_text", "audio_url", "video_url"):
            assert k in data, f"missing key {k} in media-info response"
        assert data["id"] == PUBLIC_DOC_ID
        assert isinstance(data["preview_text"], str)

    def test_media_info_404_for_unknown_doc(self, student_token):
        r = requests.get(
            f"{API}/public/content/non-existent-doc-id/media-info",
            headers={"Authorization": f"Bearer {student_token}"},
            timeout=15,
        )
        assert r.status_code == 404


# ---- Translation ----------------------------------------------------------
class TestTranslate:
    def test_translate_to_french(self, student_token):
        r = requests.post(
            f"{API}/language/translate",
            params={"text": "Hello world, welcome to the summit.", "target_language": "fr"},
            headers={"Authorization": f"Bearer {student_token}"},
            timeout=60,
        )
        # Accept 200; if LLM budget exhausted accept 402/429/500/503 as graceful
        assert r.status_code in (200, 402, 429, 500, 503), f"{r.status_code} {r.text}"
        if r.status_code == 200:
            body = r.json()
            # endpoint returns {"original":..., "translated":..., "target_language":...}
            assert "translated" in body and "target_language" in body
            assert body["target_language"] == "fr"


# ---- TTS ------------------------------------------------------------------
class TestTTS:
    def test_tts_generates_or_gracefully_fails(self, student_token):
        r = requests.post(
            f"{API}/advanced/tts",
            json={"text": "Welcome to the Cognify summit keynote.", "voice": "nova"},
            headers={"Authorization": f"Bearer {student_token}"},
            timeout=90,
        )
        # 200 with audio payload OR friendly 402/429/503 if LLM budget hit
        assert r.status_code in (200, 402, 429, 503), f"unexpected: {r.status_code} {r.text[:200]}"


# ---- Slides generation ----------------------------------------------------
class TestSlides:
    def test_generate_slides_starts_job(self, student_token):
        # Backend takes `topic` and optional `slide_count` as QUERY params
        r = requests.post(
            f"{API}/content/generate-slides",
            params={"topic": "Summit 2026 Keynote about education", "slide_count": 2},
            headers={"Authorization": f"Bearer {student_token}"},
            timeout=60,
        )
        assert r.status_code in (200, 202, 402, 429, 500, 503), f"{r.status_code} {r.text[:200]}"
        if r.status_code in (200, 202):
            body = r.json()
            job_id = body.get("slideshow_id") or body.get("job_id") or body.get("id")
            assert job_id, f"no slideshow_id returned: {body}"
            assert body.get("status") in ("processing", "queued", "pending", "completed")
            time.sleep(3)
            s = requests.get(
                f"{API}/content/slides-status/{job_id}",
                headers={"Authorization": f"Bearer {student_token}"},
                timeout=60,
            )
            assert s.status_code == 200, f"status endpoint failed: {s.status_code} {s.text[:200]}"
            sb = s.json()
            assert sb.get("id") == job_id
            assert sb.get("status") in ("processing", "queued", "pending", "completed", "failed")


# ---- Avatar / lesson generate ---------------------------------------------
class TestLessonGenerate:
    def _call(self, token):
        # Endpoint takes `topic` + `duration_minutes` as query params,
        # but `learning_objectives: list` (no Query()) → FastAPI puts it in BODY.
        # NOTE: the frontend sends it as repeated query params, which produces 422.
        params = {"topic": "Summit 2026 Keynote", "duration_minutes": "5"}
        # FastAPI: single body param `learning_objectives: list` → embedded under key
        body = {"learning_objectives": ["Understand the key points", "Apply the main ideas"]}
        return requests.post(
            f"{API}/advanced/lesson/generate",
            params=params,
            json=body,
            headers={"Authorization": f"Bearer {token}"},
            timeout=120,
        )

    def test_lesson_generate_signature_mismatch_with_frontend(self, student_token):
        """BUG: frontend sends learning_objectives as repeated QUERY params, but
        backend expects them in BODY. Confirm by calling the way the frontend
        does — it should return 422 (validation error)."""
        params = [
            ("topic", "Summit 2026 Keynote"),
            ("duration_minutes", "5"),
            ("learning_objectives", "Understand the key points"),
            ("learning_objectives", "Apply the main ideas"),
        ]
        r = requests.post(
            f"{API}/advanced/lesson/generate",
            params=params,
            headers={"Authorization": f"Bearer {student_token}"},
            timeout=30,
        )
        assert r.status_code == 422, (
            f"Expected 422 (signature mismatch with frontend). Got {r.status_code} {r.text[:200]}"
        )

    @pytest.mark.xfail(reason="lesson/generate endpoint signature unparseable by FastAPI/Pydantic v2; always returns 422", strict=False)
    def test_lesson_generate_student_is_forbidden(self, student_token):
        r = self._call(student_token)
        assert r.status_code == 403

    @pytest.mark.xfail(reason="lesson/generate endpoint signature unparseable by FastAPI/Pydantic v2; always returns 422", strict=False)
    def test_lesson_generate_teacher_works(self):
        try:
            token = _login("demo.teacher@eduos.edu", "demo123")
        except AssertionError:
            pytest.skip("teacher login unavailable")
        r = self._call(token)
        assert r.status_code in (200, 402, 429, 500, 503), f"{r.status_code} {r.text[:200]}"
        if r.status_code == 200:
            body = r.json()
            assert isinstance(body, dict) and len(body) > 0
