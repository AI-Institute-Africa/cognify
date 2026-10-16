"""Iteration 40 backend tests:
  - Strict org-isolation on /api/premade-courses list & item
  - PPTX slides_json fallback when LibreOffice is missing
  - Budget-friendly error messages for /api/content/generate-video and /api/content/generate-slides
"""
import io
import os
import json
import time
import base64
import shutil
import subprocess
import pytest
import requests
from pptx import Presentation

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://knowledge-sync-9.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

TEACHER = {"email": "demo.teacher@eduos.edu", "password": "demo123"}
STUDENT = {"email": "demo.student@cognify.edu", "password": "demo123"}
ORG_ADMIN = {"email": "test.orgadmin@cognify.edu", "password": "admin123"}


def login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=30)
    assert r.status_code == 200, f"login failed for {creds['email']}: {r.status_code} {r.text}"
    data = r.json()
    return data["access_token"], data.get("user", {})


def headers(tok):
    return {"Authorization": f"Bearer {tok}"}


def make_sample_pptx_bytes():
    prs = Presentation()
    layout = prs.slide_layouts[1]
    for i in range(3):
        slide = prs.slides.add_slide(layout)
        slide.shapes.title.text = f"Slide {i+1} Title"
        body = slide.placeholders[1].text_frame
        body.text = f"Bullet A for slide {i+1}"
        body.add_paragraph().text = f"Bullet B for slide {i+1}"
    bio = io.BytesIO()
    prs.save(bio)
    return bio.getvalue()


# ---------- ORG ISOLATION ----------
class TestOrgIsolation:
    def test_org_admin_login(self):
        tok, user = login(ORG_ADMIN)
        assert tok
        assert user.get("organization_id"), "org_admin should have an organization_id"

    def test_teacher_has_no_org_or_separate_org(self):
        """NOTE: demo.teacher@eduos.edu has organization_id=None in seed data.
        This makes them a great 'other org' user for testing the strict isolation:
        with no org, they should see ZERO premade courses."""
        tok, user = login(TEACHER)
        assert tok
        assert user.get("organization_id") in (None, ""), (
            "Test plan assumes teacher has no org (acts as out-of-org user). "
            f"Got organization_id={user.get('organization_id')}"
        )

    def test_premade_courses_list_org_scoped(self):
        """Student and OrgAdmin (Cognify org) must see the same docs.
        Teacher (no org, role=teacher, NOT platform admin) must see NOTHING."""
        t_tok, t_user = login(TEACHER)
        s_tok, s_user = login(STUDENT)
        a_tok, a_user = login(ORG_ADMIN)

        rt = requests.get(f"{API}/premade-courses", headers=headers(t_tok), timeout=30)
        rs = requests.get(f"{API}/premade-courses", headers=headers(s_tok), timeout=30)
        ra = requests.get(f"{API}/premade-courses", headers=headers(a_tok), timeout=30)

        assert rt.status_code == 200, rt.text
        assert rs.status_code == 200, rs.text
        assert ra.status_code == 200, ra.text

        teacher_docs = {d["id"] for d in rt.json()["documents"]}
        student_docs = {d["id"] for d in rs.json()["documents"]}
        admin_docs = {d["id"] for d in ra.json()["documents"]}

        # Cognify org users see same set
        assert student_docs == admin_docs, (
            f"Org-mate docs differ between student and org_admin. "
            f"student={len(student_docs)} admin={len(admin_docs)}"
        )
        # Teacher (no org) sees nothing from Cognify org
        assert teacher_docs.isdisjoint(student_docs), (
            f"LEAK: out-of-org teacher sees Cognify docs. teacher={teacher_docs} cognify={student_docs}"
        )

        # Every doc the org_admin sees must have organization_id == cognify org
        cognify_org = a_user["organization_id"]
        for d in ra.json()["documents"]:
            assert d.get("organization_id") == cognify_org, (
                f"Doc {d.get('id')} has org {d.get('organization_id')} but cognify is {cognify_org}"
            )

    def test_premade_course_item_403_when_other_org(self):
        """Cross-org access: org_admin (Cognify) uploads a doc; teacher (no org)
        must get 403 on both /{id} and /{id}/view. Also tests bogus-org flip."""
        a_tok, _ = login(ORG_ADMIN)
        t_tok, _ = login(TEACHER)
        list_r = requests.get(f"{API}/premade-courses", headers=headers(a_tok), timeout=30)
        docs = list_r.json()["documents"]
        if not docs:
            pytest.skip("No premade docs available to test cross-org 403 path")
        doc_id = docs[0]["id"]

        # Positive: org_admin can fetch own-org doc
        r_ok = requests.get(f"{API}/premade-courses/{doc_id}", headers=headers(a_tok), timeout=30)
        assert r_ok.status_code == 200, r_ok.text

        # Teacher (no org) tries to fetch the Cognify doc directly via id → must be 403
        r_forbid = requests.get(f"{API}/premade-courses/{doc_id}", headers=headers(t_tok), timeout=30)
        assert r_forbid.status_code == 403, f"expected 403 cross-org GET, got {r_forbid.status_code} {r_forbid.text[:200]}"

        r_view_forbid = requests.get(f"{API}/premade-courses/{doc_id}/view", headers=headers(t_tok), timeout=60)
        assert r_view_forbid.status_code == 403, f"/view bypass attempted; got {r_view_forbid.status_code}"


# ---------- PPTX SLIDES_JSON FALLBACK ----------
class TestPptxSlidesJsonFallback:
    @classmethod
    def setup_class(cls):
        cls.tok, cls.user = login(ORG_ADMIN)
        cls.uploaded_id = None

    def test_upload_pptx_and_view_with_libreoffice(self):
        """Sanity: with LibreOffice available, /view returns application/pdf."""
        pptx_bytes = make_sample_pptx_bytes()
        files = {
            "file": ("sample_iter40.pptx", pptx_bytes,
                     "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
        }
        data = {"title": "Iter40 PPTX Test", "description": "fallback test", "category": "lecture"}
        up = requests.post(f"{API}/premade-courses/upload",
                           headers=headers(self.tok), data=data, files=files, timeout=120)
        assert up.status_code == 200, up.text
        self.__class__.uploaded_id = up.json()["document"]["id"]
        # purge any cached PDF for a clean test
        cached = f"/app/generated_pdf_cache/{self.__class__.uploaded_id}.pdf"
        if os.path.exists(cached):
            os.remove(cached)

        r = requests.get(f"{API}/premade-courses/{self.__class__.uploaded_id}/view",
                         headers=headers(self.tok), timeout=120)
        assert r.status_code == 200, r.text
        assert "application/pdf" in r.headers.get("content-type", ""), \
            f"with LibreOffice we expect application/pdf, got {r.headers.get('content-type')}"

    def test_view_returns_slides_json_when_libreoffice_missing(self):
        """Rename soffice → trigger python-pptx fallback → expect JSON with slides[]."""
        assert self.__class__.uploaded_id, "previous test should have uploaded the doc"
        # invalidate cache
        cached = f"/app/generated_pdf_cache/{self.__class__.uploaded_id}.pdf"
        if os.path.exists(cached):
            os.remove(cached)

        soffice_src = "/usr/bin/soffice"
        soffice_bak = "/usr/bin/soffice.bak"
        libre_src = "/usr/bin/libreoffice"
        libre_bak = "/usr/bin/libreoffice.bak"
        renamed_soffice = False
        renamed_libre = False
        try:
            if os.path.exists(soffice_src):
                shutil.move(soffice_src, soffice_bak)
                renamed_soffice = True
            if os.path.exists(libre_src):
                shutil.move(libre_src, libre_bak)
                renamed_libre = True
            r = requests.get(f"{API}/premade-courses/{self.__class__.uploaded_id}/view",
                             headers=headers(self.tok), timeout=120)
            assert r.status_code == 200, f"status {r.status_code} body={r.text[:400]}"
            ct = r.headers.get("content-type", "")
            assert "application/json" in ct, f"expected JSON fallback, got {ct} body={r.text[:200]}"
            body = r.json()
            assert body["type"] == "slides_json"
            assert isinstance(body["slides"], list) and len(body["slides"]) >= 1
            slide0 = body["slides"][0]
            assert "title" in slide0 and "bullets" in slide0 and "images" in slide0
            assert body["total_slides"] == len(body["slides"])
        finally:
            if renamed_soffice and os.path.exists(soffice_bak):
                shutil.move(soffice_bak, soffice_src)
            if renamed_libre and os.path.exists(libre_bak):
                shutil.move(libre_bak, libre_src)

    def test_cleanup_uploaded_doc(self):
        if self.__class__.uploaded_id:
            requests.delete(f"{API}/premade-courses/{self.__class__.uploaded_id}",
                            headers=headers(self.tok), timeout=30)


# ---------- BUDGET-FRIENDLY ERRORS ----------
class TestBudgetFriendlyErrors:
    def test_generate_slides_returns_503_with_friendly_message(self):
        tok, _ = login(ORG_ADMIN)
        # topic is a query parameter (FastAPI default since not Body-wrapped)
        params = {"topic": "Photosynthesis basics", "slide_count": 2}
        r = requests.post(f"{API}/content/generate-slides", headers=headers(tok), params=params, timeout=180)
        # Either 503 friendly message (budget exhausted) OR 200 if budget is somehow available.
        if r.status_code == 503:
            detail = r.json().get("detail", "")
            assert "Emergent LLM Key budget exceeded" in detail, \
                f"Expected friendly budget message, got: {detail}"
            assert "Universal Key" in detail, f"Expected actionable Universal Key hint, got: {detail}"
        else:
            assert r.status_code in (200, 201), f"unexpected status {r.status_code}: {r.text[:300]}"

    def test_generate_video_records_friendly_error(self):
        tok, _ = login(ORG_ADMIN)
        params = {
            "topic": "Intro to algebra",
            "duration": 8,
        }
        r = requests.post(f"{API}/content/generate-video", headers=headers(tok), params=params, timeout=60)
        if r.status_code != 200:
            pytest.skip(f"generate-video did not accept request: {r.status_code} {r.text[:200]}")
        video_id = r.json().get("video_id") or r.json().get("id")
        if not video_id:
            pytest.skip("No video_id returned, cannot poll status")
        # Poll for up to 60s
        deadline = time.time() + 90
        status = None
        body = {}
        while time.time() < deadline:
            time.sleep(3)
            sr = requests.get(f"{API}/content/video-status/{video_id}", headers=headers(tok), timeout=30)
            if sr.status_code != 200:
                continue
            body = sr.json()
            status = body.get("status")
            if status in ("failed", "completed", "error"):
                break
        if status not in ("failed", "error"):
            pytest.skip(f"Video did not fail in time — final status={status}; budget may not be exhausted.")
        err = (body.get("error") or "").lower()
        assert "emergent llm key budget exceeded" in err or "budget" in err, \
            f"Expected friendly budget message in error field, got: {body.get('error')}"
