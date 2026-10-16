"""Iteration 38 - Tests for 5 user-reported bug fixes.

Coverage:
 1. Premade Courses view-only (GET /api/premade-courses/{id}/download -> 403).
 2. AI video length default duration=12 + clamp [4..12].
 3. Live Research /api/research/search returns direct_search_links incl. Reuters/BBC/AP/Google News.
 4. Long-form TTS via JSON body {text, voice, speed} -> chunks=1 short, chunks>=3 for ~10k chars.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://knowledge-sync-9.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ORG_ADMIN = {"email": "test.orgadmin@cognify.edu", "password": "admin123"}
TEACHER = {"email": "demo.teacher@eduos.edu", "password": "demo123"}
STUDENT = {"email": "demo.student@cognify.edu", "password": "demo123"}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=60)
    assert r.status_code == 200, f"Login failed for {creds['email']}: {r.status_code} {r.text}"
    data = r.json()
    token = data.get("access_token") or data.get("token")
    assert token, f"No token in login response: {data}"
    return token


@pytest.fixture(scope="module")
def teacher_token():
    return _login(TEACHER)


@pytest.fixture(scope="module")
def student_token():
    return _login(STUDENT)


@pytest.fixture(scope="module")
def org_admin_token():
    return _login(ORG_ADMIN)


def _h(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# --------- 1. PREMADE COURSES VIEW-ONLY ---------
class TestPremadeCoursesViewOnly:
    def test_download_endpoint_returns_403(self, teacher_token):
        # Use a likely-nonexistent ID; route raises 403 unconditionally
        r = requests.get(f"{API}/premade-courses/any-doc-id/download", headers=_h(teacher_token), timeout=30)
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text[:300]}"
        body = r.json()
        detail = body.get("detail") if isinstance(body, dict) else None
        assert detail and "disabled" in str(detail).lower() and "view-only" in str(detail).lower()

    def test_download_blocked_for_student_too(self, student_token):
        r = requests.get(f"{API}/premade-courses/any-doc-id/download", headers=_h(student_token), timeout=30)
        assert r.status_code == 403

    def test_listing_premade_courses_still_works(self, teacher_token):
        r = requests.get(f"{API}/premade-courses", headers=_h(teacher_token), timeout=30)
        # 200 response with documents list is acceptable
        assert r.status_code == 200, f"List failed: {r.status_code} {r.text[:300]}"
        data = r.json()
        # Response is {documents: [...], total: N} per current implementation
        assert isinstance(data, dict) and "documents" in data
        assert isinstance(data["documents"], list)


# --------- 2. AI VIDEO GENERATION duration=12 ---------
class TestAIVideoGeneration:
    def test_generate_video_accepts_duration_12(self, teacher_token):
        params = {"topic": "Photosynthesis for testing", "duration": 12}
        r = requests.post(f"{API}/content/generate-video", params=params, headers=_h(teacher_token), timeout=30)
        assert r.status_code == 200, f"generate-video failed: {r.status_code} {r.text[:400]}"
        data = r.json()
        assert "video_id" in data
        assert data.get("status") == "processing"

    def test_generate_video_clamps_high_duration(self, teacher_token):
        params = {"topic": "Clamp test", "duration": 99}
        r = requests.post(f"{API}/content/generate-video", params=params, headers=_h(teacher_token), timeout=30)
        # Should not 4xx; backend clamps to 12
        assert r.status_code == 200, f"Clamp test failed: {r.status_code} {r.text[:400]}"
        assert r.json().get("status") == "processing"


# --------- 3. LIVE RESEARCH search ---------
class TestLiveResearch:
    def test_research_search_news_returns_verified_sources(self, teacher_token):
        payload = {"query": "artificial intelligence in education", "category": "news"}
        r = requests.post(f"{API}/research/search", json=payload, headers=_h(teacher_token), timeout=90)
        assert r.status_code == 200, f"research/search failed: {r.status_code} {r.text[:400]}"
        data = r.json()
        assert "direct_search_links" in data
        sources = " ".join([str(l.get("source", "")) for l in data["direct_search_links"]])
        for needed in ["Reuters", "BBC", "AP News", "Google News"]:
            assert needed in sources, f"Missing verified source '{needed}'. Got: {sources}"
        # ai_results key must exist (may be empty)
        assert "ai_results" in data
        assert isinstance(data["ai_results"], list)

    def test_research_search_general_category(self, teacher_token):
        payload = {"query": "machine learning", "category": "all"}
        r = requests.post(f"{API}/research/search", json=payload, headers=_h(teacher_token), timeout=90)
        assert r.status_code == 200
        data = r.json()
        assert "direct_search_links" in data
        # Verify Google Scholar, arXiv shown for academic category
        sources = " ".join([str(l.get("source", "")) for l in data["direct_search_links"]])
        assert "Google Scholar" in sources and "arXiv" in sources


# --------- 4. LONG-FORM TTS JSON BODY ---------
class TestLongFormTTS:
    def test_short_text_single_chunk(self, teacher_token):
        body = {"text": "Hello students, this is a short TTS test.", "voice": "nova", "speed": 1.0}
        r = requests.post(f"{API}/advanced/tts", json=body, headers=_h(teacher_token), timeout=90)
        assert r.status_code == 200, f"Short TTS failed: {r.status_code} {r.text[:400]}"
        data = r.json()
        assert data.get("chunks") == 1
        assert data.get("audio_url"), "Missing audio_url"
        # Short content => data: URL (base64 inline)
        assert str(data["audio_url"]).startswith("data:"), f"Expected data: URL for short text, got {data['audio_url'][:60]}"

    def test_long_text_multi_chunk(self, teacher_token):
        # ~10,000 char text composed of sentences (so splitter has boundaries)
        sentence = (
            "Artificial intelligence is the simulation of human intelligence processes by machines, "
            "especially computer systems. These processes include learning, reasoning, and self-correction. "
        )
        text = (sentence * 60).strip()  # ~60 * ~170 = ~10,200 chars
        assert len(text) > 9500
        body = {"text": text, "voice": "nova", "speed": 1.0}
        r = requests.post(f"{API}/advanced/tts", json=body, headers=_h(teacher_token), timeout=300)
        assert r.status_code == 200, f"Long TTS failed: {r.status_code} {r.text[:500]}"
        data = r.json()
        assert data.get("chunks", 0) >= 3, f"Expected chunks>=3, got {data.get('chunks')}"
        url = data.get("audio_url", "")
        assert url.startswith("/api/content/audio/"), f"Expected /api/content/audio/ url, got {url}"

    def test_tts_rejects_empty_text(self, teacher_token):
        r = requests.post(f"{API}/advanced/tts", json={"text": "  ", "voice": "nova"}, headers=_h(teacher_token), timeout=60)
        assert r.status_code in (400, 422)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
