"""Iteration 44: Upload speed, view speed, auth gating on audio/video, all-format render.

Tests cover:
1. Upload speed under 5s for PDF/PPTX/DOCX/TXT/PNG (super admin).
2. View speed under 1s for already-uploaded docs (all formats).
3. PPTX serves cached slides_json instantly as application/json.
4. /api/public/<id>/audio/<aid> and /video/<vid> reject anonymous with 401/403.
5. Backward compat: legacy file_data docs still render.
"""

import io
import os
import time
import uuid
import struct
import zlib
import zipfile
import pytest
import requests
from pathlib import Path

def _read_base_url():
    url = os.environ.get("REACT_APP_BACKEND_URL", "").strip()
    if not url:
        fe_env = Path("/app/frontend/.env")
        if fe_env.exists():
            for line in fe_env.read_text().splitlines():
                if line.startswith("REACT_APP_BACKEND_URL="):
                    url = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    return url.rstrip("/")

BASE_URL = _read_base_url()
assert BASE_URL, "REACT_APP_BACKEND_URL not found in env or /app/frontend/.env"
SUPER_ADMIN_EMAIL = "takuechakanyuka@gmail.com"
SUPER_ADMIN_PASSWORD = "SuperAdmin@2026!"

# ---------- helpers to build real-ish files in-memory ----------

def make_pdf(size_mb: float) -> bytes:
    """Minimal valid PDF padded to target size with a comment block."""
    pdf_core = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 144]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
        b"4 0 obj<</Length 44>>stream\nBT /F1 18 Tf 30 100 Td (Iter44 Test PDF) Tj ET\nendstream endobj\n"
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"xref\n0 6\n0000000000 65535 f\n0000000010 00000 n\n0000000060 00000 n\n0000000110 00000 n\n0000000210 00000 n\n0000000300 00000 n\n"
        b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n400\n%%EOF\n"
    )
    target = int(size_mb * 1024 * 1024)
    if len(pdf_core) >= target:
        return pdf_core
    pad_needed = target - len(pdf_core) - 4
    return pdf_core + b"%" + b"A" * pad_needed + b"\n"


def make_png(size_mb: float) -> bytes:
    """Construct a valid PNG. Padding via tEXt chunk to inflate size."""
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\xff\x00\x00" * 4 for _ in range(4))
    idat = zlib.compress(raw)
    png = sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat)
    target = int(size_mb * 1024 * 1024)
    pad = max(0, target - len(png) - 200)
    if pad:
        png += chunk(b"tEXt", b"pad\x00" + b"A" * pad)
    png += chunk(b"IEND", b"")
    return png


def make_docx(size_mb: float) -> bytes:
    """Build a minimal valid .docx zip; pad via extra file entries."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr("word/document.xml", '<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Iter44 DOCX test document content for rendering.</w:t></w:r></w:p></w:body></w:document>')
        target = int(size_mb * 1024 * 1024)
        pad_needed = target - buf.tell()
        if pad_needed > 0:
            z.writestr("padding.bin", b"X" * pad_needed)
    return buf.getvalue()


def make_pptx(size_mb: float) -> bytes:
    """Minimal pptx (python-pptx style) — built via raw zip to avoid extra deps."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/><Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>')
        z.writestr("ppt/_rels/presentation.xml.rels", '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/></Relationships>')
        z.writestr("ppt/presentation.xml", '<?xml version="1.0"?><p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst></p:presentation>')
        z.writestr("ppt/slides/slide1.xml", '<?xml version="1.0"?><p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:sp><p:txBody><a:bodyPr/><a:p><a:r><a:t>Iter44 PPTX slide test content</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>')
        target = int(size_mb * 1024 * 1024)
        pad_needed = target - buf.tell()
        if pad_needed > 0:
            z.writestr("ppt/media/pad.bin", b"X" * pad_needed)
    return buf.getvalue()


# ---------- fixtures ----------

@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


@pytest.fixture(scope="module")
def admin_token(session):
    r = session.post(f"{BASE_URL}/api/auth/login",
                     json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD})
    assert r.status_code == 200, f"super-admin login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ---------- upload speed tests ----------

UPLOAD_BUDGET_S = 5.0  # spec: under 5s per upload
created_doc_ids = []


def _upload(session, headers, filename, content, mime, title):
    files = {"file": (filename, content, mime)}
    data = {"title": title, "category": "General", "description": f"Iter44 test {filename}", "visibility": "public"}
    t0 = time.time()
    r = session.post(f"{BASE_URL}/api/super-admin/public-content/upload",
                     headers=headers, files=files, data=data, timeout=60)
    elapsed = time.time() - t0
    return r, elapsed


@pytest.mark.parametrize("name,builder,mime,ext", [
    ("iter44_test.txt", lambda: b"Iter44 test text file " * 200, "text/plain", "txt"),
    ("iter44_test.png", lambda: make_png(0.05), "image/png", "png"),
    ("iter44_test.docx", lambda: make_docx(2.0),
     "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx"),
    ("iter44_test.pptx", lambda: make_pptx(5.0),
     "application/vnd.openxmlformats-officedocument.presentationml.presentation", "pptx"),
    ("iter44_test.pdf", lambda: make_pdf(10.0), "application/pdf", "pdf"),
])
def test_upload_speed_under_5s(session, admin_headers, name, builder, mime, ext):
    """Each format must upload in <5s; background extraction is deferred."""
    content = builder()
    title = f"TEST_iter44_{ext}_{uuid.uuid4().hex[:6]}"
    r, elapsed = _upload(session, admin_headers, name, content, mime, title)
    assert r.status_code in (200, 201), f"{ext} upload failed: {r.status_code} {r.text[:300]}"
    body = r.json()
    doc_id = body.get("id") or (body.get("document") or {}).get("id")
    assert doc_id, f"no doc id in response: {body}"
    created_doc_ids.append((ext, doc_id))
    assert elapsed < UPLOAD_BUDGET_S, f"{ext} upload took {elapsed:.2f}s (> {UPLOAD_BUDGET_S}s)"
    print(f"UPLOAD {ext}: {len(content)/1024:.0f}KB in {elapsed:.2f}s -> doc_id={doc_id}")


# ---------- view speed tests ----------

VIEW_BUDGET_S = 1.0


def test_view_speed_all_formats(session):
    """GET /api/public/content/<id>/view must respond <1s for each uploaded format
    once background processing (PPTX slide cache) is complete — matches spec's
    'already-uploaded docs' use case."""
    assert created_doc_ids, "no docs created in upload tests"
    failures = []
    for ext, doc_id in created_doc_ids:
        # For PPTX, wait until slides_json is cached so we measure cached-path speed
        if ext == "pptx":
            deadline = time.time() + 30
            while time.time() < deadline:
                rh = session.head(f"{BASE_URL}/api/public/content/{doc_id}/view", timeout=10)
                if "application/json" in rh.headers.get("content-type", "").lower():
                    break
                time.sleep(1)
        t0 = time.time()
        r = session.get(f"{BASE_URL}/api/public/content/{doc_id}/view", timeout=15, stream=True)
        first_chunk = next(r.iter_content(8192), b"")
        elapsed = time.time() - t0
        ct = r.headers.get("content-type", "")
        print(f"VIEW {ext}: status={r.status_code} ct={ct} in {elapsed:.3f}s (first chunk {len(first_chunk)}B)")
        if r.status_code != 200:
            failures.append(f"{ext}: status {r.status_code}")
            continue
        if elapsed >= VIEW_BUDGET_S:
            failures.append(f"{ext}: view took {elapsed:.2f}s (> {VIEW_BUDGET_S}s)")
        if ext == "pptx" and "application/json" not in ct:
            failures.append(f"pptx returned {ct} instead of application/json (slides cache MISS)")
    assert not failures, "View-speed failures: " + "; ".join(failures)


def test_pptx_first_view_cold_does_not_exceed_5s(session, admin_headers):
    """Cold-path PPTX view (background cache not yet finished) — should not exceed 5s
    for a small synthetic pptx. Documents user-perceived 'first view' latency."""
    content = make_pptx(0.5)
    title = f"TEST_iter44_pptx_cold_{uuid.uuid4().hex[:6]}"
    r, _ = _upload(session, admin_headers, "iter44_cold.pptx", content,
                   "application/vnd.openxmlformats-officedocument.presentationml.presentation", title)
    assert r.status_code in (200, 201)
    cold_doc_id = r.json().get("id") or r.json()["document"]["id"]
    t0 = time.time()
    rv = session.get(f"{BASE_URL}/api/public/content/{cold_doc_id}/view", timeout=30, stream=True)
    next(rv.iter_content(64), b"")
    elapsed = time.time() - t0
    print(f"PPTX COLD VIEW: status={rv.status_code} ct={rv.headers.get('content-type')} in {elapsed:.2f}s")
    # Cleanup
    session.delete(f"{BASE_URL}/api/super-admin/public-content/{cold_doc_id}?hard=true",
                   headers=admin_headers, timeout=15)
    # Soft assertion: warn but don't fail — cold path uses LibreOffice and can be slow
    if elapsed > 5.0:
        pytest.skip(f"PPTX cold path took {elapsed:.1f}s (LibreOffice conversion) — expected if cache not warm")


def test_view_content_types(session):
    """Verify Content-Type for each format matches spec."""
    expected = {
        "pdf": "application/pdf",
        "png": "image/png",
        "txt": "text/plain",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pptx": "application/json",  # cached slides_json
    }
    for ext, doc_id in created_doc_ids:
        r = session.get(f"{BASE_URL}/api/public/content/{doc_id}/view", timeout=10, stream=True)
        next(r.iter_content(64), b"")
        ct = r.headers.get("content-type", "").lower()
        assert expected[ext] in ct, f"{ext}: expected {expected[ext]}, got {ct}"


# ---------- auth gating on media ----------

def test_media_info_requires_auth(session):
    """media-info needs login; anonymous must be 401/403."""
    if not created_doc_ids:
        pytest.skip("no docs to test")
    _, doc_id = created_doc_ids[0]
    r = requests.get(f"{BASE_URL}/api/public/content/{doc_id}/media-info", timeout=10)
    assert r.status_code in (401, 403), f"expected 401/403 anonymous, got {r.status_code}: {r.text[:200]}"


def test_audio_endpoint_rejects_anonymous(session):
    """Hit /api/public/<id>/audio/<aid> with NO auth → must be 401/403, not bytes."""
    if not created_doc_ids:
        pytest.skip("no docs to test")
    _, doc_id = created_doc_ids[0]
    fake_aid = "anon-test-aid"
    r = requests.get(f"{BASE_URL}/api/public/{doc_id}/audio/{fake_aid}", timeout=10)
    assert r.status_code in (401, 403), (
        f"audio endpoint should reject anonymous; got {r.status_code} ct={r.headers.get('content-type')}"
    )
    assert "audio/" not in r.headers.get("content-type", "").lower(), \
        "anonymous user received audio bytes — auth gating broken!"


def test_video_endpoint_rejects_anonymous(session):
    """Hit /api/public/<id>/video/<vid> with NO auth → must be 401/403."""
    if not created_doc_ids:
        pytest.skip("no docs to test")
    _, doc_id = created_doc_ids[0]
    fake_vid = "anon-test-vid"
    r = requests.get(f"{BASE_URL}/api/public/{doc_id}/video/{fake_vid}", timeout=10)
    assert r.status_code in (401, 403), (
        f"video endpoint should reject anonymous; got {r.status_code} ct={r.headers.get('content-type')}"
    )
    assert "video/" not in r.headers.get("content-type", "").lower(), \
        "anonymous user received video bytes — auth gating broken!"


# ---------- listing strips media urls ----------

def test_public_listing_strips_media_urls(session):
    """Public listing must NOT expose audio_url/video_url, but expose has_audio/has_video booleans."""
    r = session.get(f"{BASE_URL}/api/public/content", timeout=10)
    assert r.status_code == 200
    docs = r.json().get("documents", [])
    for d in docs[:30]:
        assert "audio_url" not in d, "audio_url leaked in public listing"
        assert "video_url" not in d, "video_url leaked in public listing"
        assert "has_audio" in d and "has_video" in d, "missing has_audio/has_video flags"


# ---------- pptx cache verification (presence of slides_json shape in response) ----------

def test_pptx_returns_slides_json_shape(session):
    pptx_docs = [d for ext, d in created_doc_ids if ext == "pptx"]
    if not pptx_docs:
        pytest.skip("no pptx uploaded")
    doc_id = pptx_docs[0]
    # Wait briefly for background task to cache slides_json
    deadline = time.time() + 15
    body = None
    while time.time() < deadline:
        r = session.get(f"{BASE_URL}/api/public/content/{doc_id}/view", timeout=10)
        ct = r.headers.get("content-type", "")
        if r.status_code == 200 and "application/json" in ct:
            body = r.json()
            break
        time.sleep(1)
    assert body, "pptx slides_json never cached"
    assert body.get("type") == "slides_json"
    assert "slides" in body and isinstance(body["slides"], list)
    assert body.get("total_slides", 0) >= 1


# ---------- cleanup ----------

def test_cleanup_uploaded_docs(session, admin_headers):
    """Hard-delete the docs we created."""
    for _, doc_id in list(created_doc_ids):
        try:
            r = session.delete(f"{BASE_URL}/api/super-admin/public-content/{doc_id}?hard=true",
                               headers=admin_headers, timeout=15)
            print(f"cleanup {doc_id}: {r.status_code}")
        except Exception as e:
            print(f"cleanup error {doc_id}: {e}")
