"""Iteration 48 backend tests — Orphan detection lifecycle for public content.

Verifies:
  * GET /api/super-admin/public-content/orphans returns healthy/orphaned counts
  * Simulated orphan (disk file removed + storage_path unset) is detected
  * Download endpoint returns HTTP 410 with friendly message AND sets file_lost=True
  * POST /orphans/mark is idempotent and toggles file_lost correctly
  * Public listing hides file_lost docs
  * Restoring the file on disk + mark => file_lost cleared (restored>=1)
  * DELETE /orphans/{id} refuses when file is still reachable
  * Regression: healthy download, video, research-digest run-now
"""
import os
import shutil
import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://knowledge-sync-9.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

SUPER_EMAIL = "takuechakanyuka@gmail.com"
SUPER_PASS = "SuperAdmin@2026!"

ORPHAN_DOC_ID = "6a207bae-1b06-4857-87c8-94d9aeb5d28f"
ORPHAN_DOC_PATH = f"/app/uploaded_public_docs/{ORPHAN_DOC_ID}.pptx"
ORPHAN_BACKUP = f"/tmp/{ORPHAN_DOC_ID}.pptx.bak"
VIDEO_ID = "03c0b8aa-f1d8-4e75-ab64-77bd702f0ad4"

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")


@pytest.fixture(scope="module")
def db():
    client = MongoClient(MONGO_URL)
    return client[DB_NAME]


@pytest.fixture(scope="module")
def super_token():
    r = requests.post(f"{API}/auth/login", json={"email": SUPER_EMAIL, "password": SUPER_PASS}, timeout=30)
    assert r.status_code == 200, f"Super admin login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token")
    assert tok
    return tok


@pytest.fixture(scope="module")
def sa_headers(super_token):
    return {"Authorization": f"Bearer {super_token}"}


@pytest.fixture(scope="module", autouse=True)
def restore_state(sa_headers, db):
    """After the whole module runs, restore disk + DB to healthy state."""
    yield
    try:
        if os.path.exists(ORPHAN_BACKUP) and not os.path.exists(ORPHAN_DOC_PATH):
            shutil.move(ORPHAN_BACKUP, ORPHAN_DOC_PATH)
    except Exception:
        pass
    # Restore file_path in DB if unset
    try:
        db.public_content.update_one(
            {"id": ORPHAN_DOC_ID},
            {"$set": {"file_path": ORPHAN_DOC_PATH}, "$unset": {"file_lost": "", "file_lost_at": ""}},
        )
    except Exception:
        pass
    # Run mark endpoint to reconcile
    try:
        requests.post(f"{API}/super-admin/public-content/orphans/mark", headers=sa_headers, timeout=30)
    except Exception:
        pass


def _get_orphans(sa_headers):
    r = requests.get(f"{API}/super-admin/public-content/orphans", headers=sa_headers, timeout=60)
    assert r.status_code == 200, r.text
    return r.json()


# ============================================================
# 1. Baseline: all healthy on preview
# ============================================================
class TestBaselineOrphans:
    def test_orphans_endpoint_baseline_all_healthy(self, sa_headers):
        data = _get_orphans(sa_headers)
        assert "total_documents" in data
        assert "healthy" in data
        assert "orphaned" in data
        assert "orphans" in data
        assert isinstance(data["orphans"], list)
        print(f"Baseline: total={data['total_documents']} healthy={data['healthy']} orphaned={data['orphaned']}")
        # Preview should ideally have 0 orphans at start
        assert data["orphaned"] == 0, f"Expected 0 orphans at baseline, got {data['orphaned']}: {data['orphans']}"
        assert data["healthy"] >= 1


# ============================================================
# 2. Regression tests (do these BEFORE mutating disk state)
# ============================================================
class TestRegressionHealthy:
    def test_healthy_download_200(self):
        r = requests.get(f"{API}/public/content/{ORPHAN_DOC_ID}/download", timeout=60, allow_redirects=False)
        assert r.status_code == 200, f"Healthy download failed: {r.status_code} {r.text[:200]}"
        assert len(r.content) > 100
        assert "attachment" in r.headers.get("Content-Disposition", "").lower()

    def test_healthy_video_200(self):
        # Video endpoint requires auth per spec? Test says regression /api/public/{doc}/video/{vid}
        r = requests.get(f"{API}/public/{ORPHAN_DOC_ID}/video/{VIDEO_ID}", timeout=60, allow_redirects=False)
        # Accept 200 (with body) or 206 range
        assert r.status_code in (200, 206), f"Video failed: {r.status_code} {r.text[:200]}"
        ct = r.headers.get("Content-Type", "")
        assert "video/mp4" in ct or "mp4" in ct, f"Unexpected content-type: {ct}"

    def test_research_digest_run_now(self, sa_headers):
        r = requests.post(f"{API}/super-admin/research-digest/run-now", headers=sa_headers, timeout=120)
        assert r.status_code == 200, f"digest run-now failed: {r.status_code} {r.text[:300]}"
        data = r.json()
        recips = data.get("recipients") or []
        assert "dennis@rubiem.com" in recips
        assert "takuechakanyuka@gmail.com" in recips


# ============================================================
# 3. Orphan simulation lifecycle
# ============================================================
class TestOrphanLifecycle:
    def test_01_simulate_orphan(self, db, sa_headers):
        # Backup and remove disk file
        assert os.path.exists(ORPHAN_DOC_PATH), f"Cannot simulate orphan: {ORPHAN_DOC_PATH} missing"
        shutil.copy2(ORPHAN_DOC_PATH, ORPHAN_BACKUP)
        os.remove(ORPHAN_DOC_PATH)
        # Unset storage_path AND file_data so it truly looks orphaned
        r = db.public_content.update_one(
            {"id": ORPHAN_DOC_ID},
            {"$unset": {"storage_path": "", "file_data": ""}},
        )
        assert r.matched_count == 1

        data = _get_orphans(sa_headers)
        ids = [o["id"] for o in data["orphans"]]
        assert ORPHAN_DOC_ID in ids, f"Expected orphan not detected. orphans={ids}"
        assert data["orphaned"] >= 1
        print(f"After simulate: healthy={data['healthy']} orphaned={data['orphaned']}")

    def test_02_download_returns_410_and_marks_lost(self, db):
        r = requests.get(f"{API}/public/content/{ORPHAN_DOC_ID}/download", timeout=30, allow_redirects=False)
        assert r.status_code == 410, f"Expected 410, got {r.status_code}: {r.text[:200]}"
        detail = r.json().get("detail", "")
        assert "archived" in detail.lower()
        assert "administrator" in detail.lower() or "re-upload" in detail.lower()
        # Verify file_lost was set
        doc = db.public_content.find_one({"id": ORPHAN_DOC_ID}, {"file_lost": 1, "file_lost_at": 1})
        assert doc.get("file_lost") is True, f"file_lost not set on doc: {doc}"
        assert doc.get("file_lost_at")

    def test_03_public_listing_hides_lost(self):
        r = requests.get(f"{API}/public/content", timeout=30)
        assert r.status_code == 200
        data = r.json()
        ids = [d.get("id") for d in data.get("documents", [])]
        assert ORPHAN_DOC_ID not in ids, "file_lost doc still appearing in public listing"

    def test_04_mark_endpoint_idempotent(self, db, sa_headers):
        # Clear file_lost first so mark has work to do
        db.public_content.update_one({"id": ORPHAN_DOC_ID}, {"$unset": {"file_lost": "", "file_lost_at": ""}})
        r = requests.post(f"{API}/super-admin/public-content/orphans/mark", headers=sa_headers, timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("marked_lost", 0) >= 1, f"Expected marked_lost>=1, got {data}"
        # Second call — should be 0
        r2 = requests.post(f"{API}/super-admin/public-content/orphans/mark", headers=sa_headers, timeout=60)
        assert r2.status_code == 200
        data2 = r2.json()
        assert data2.get("marked_lost", 0) == 0, f"Expected marked_lost=0 second call, got {data2}"

    def test_05_delete_refuses_when_reachable(self, db, sa_headers):
        # Temporarily put a dummy file back on disk with matching file_path
        db.public_content.update_one({"id": ORPHAN_DOC_ID}, {"$set": {"file_path": ORPHAN_DOC_PATH}})
        # Restore actual file so it's reachable
        shutil.copy2(ORPHAN_BACKUP, ORPHAN_DOC_PATH)
        r = requests.delete(f"{API}/super-admin/public-content/orphans/{ORPHAN_DOC_ID}", headers=sa_headers, timeout=30)
        assert r.status_code == 400, f"Expected 400 refusal, got {r.status_code}: {r.text}"
        # Now remove again for restore test
        os.remove(ORPHAN_DOC_PATH)

    def test_06_restore_file_and_mark_clears_flag(self, db, sa_headers):
        # Restore physical file to disk
        shutil.copy2(ORPHAN_BACKUP, ORPHAN_DOC_PATH)
        # Ensure file_path is set
        db.public_content.update_one({"id": ORPHAN_DOC_ID}, {"$set": {"file_path": ORPHAN_DOC_PATH}})
        r = requests.post(f"{API}/super-admin/public-content/orphans/mark", headers=sa_headers, timeout=60)
        assert r.status_code == 200
        data = r.json()
        assert data.get("marked_lost", 0) == 0, f"Expected marked_lost=0 after restore, got {data}"
        assert data.get("restored", 0) >= 1, f"Expected restored>=1, got {data}"
        # Confirm doc back in public listing
        r2 = requests.get(f"{API}/public/content", timeout=30)
        ids = [d.get("id") for d in r2.json().get("documents", [])]
        assert ORPHAN_DOC_ID in ids, "Restored doc not in public listing"
        # Confirm orphans endpoint clean
        data3 = _get_orphans(sa_headers)
        assert data3["orphaned"] == 0
