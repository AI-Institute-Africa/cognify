"""Emergent Object Storage helper.

Persistent replacement for /app/uploaded_public_docs and /app/generated_video_public.
Use put_object / get_object / stream_object from anywhere in the codebase.

All paths are prefixed with COGNIFY/ to isolate this app.
"""
from __future__ import annotations
import os
import logging
import requests
from typing import Iterator

logger = logging.getLogger(__name__)

STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
APP_NAME = os.environ.get("OBJSTORE_APP_NAME", "cognify")

_storage_key: str | None = None


def init_storage(force: bool = False) -> str | None:
    """Initialise a session-scoped storage_key. Safe to call multiple times."""
    global _storage_key
    if _storage_key and not force:
        return _storage_key
    if not EMERGENT_KEY:
        logger.warning("EMERGENT_LLM_KEY not set — object storage disabled")
        return None
    try:
        resp = requests.post(f"{STORAGE_URL}/init",
                              json={"emergent_key": EMERGENT_KEY}, timeout=30)
        resp.raise_for_status()
        _storage_key = resp.json().get("storage_key")
        logger.info("Object storage initialised")
        return _storage_key
    except Exception as e:
        logger.error("Object storage init failed: %s", e)
        return None


def _key() -> str | None:
    return _storage_key or init_storage()


def put_object(path: str, data: bytes, content_type: str) -> dict | None:
    """Upload bytes. Returns {"path","size","etag"} or None on failure."""
    k = _key()
    if not k:
        return None
    try:
        resp = requests.put(f"{STORAGE_URL}/objects/{path}",
                            headers={"X-Storage-Key": k, "Content-Type": content_type},
                            data=data, timeout=180)
        if resp.status_code == 403:
            init_storage(force=True)
            k = _key()
            resp = requests.put(f"{STORAGE_URL}/objects/{path}",
                                headers={"X-Storage-Key": k, "Content-Type": content_type},
                                data=data, timeout=180)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("put_object(%s) failed: %s", path, e)
        return None


def put_file(path: str, local_path: str, content_type: str) -> dict | None:
    """Upload a file from local disk without loading it fully in memory."""
    k = _key()
    if not k:
        return None
    try:
        with open(local_path, "rb") as f:
            resp = requests.put(f"{STORAGE_URL}/objects/{path}",
                                headers={"X-Storage-Key": k, "Content-Type": content_type},
                                data=f, timeout=600)
            if resp.status_code == 403:
                init_storage(force=True)
                f.seek(0)
                resp = requests.put(f"{STORAGE_URL}/objects/{path}",
                                    headers={"X-Storage-Key": _key(), "Content-Type": content_type},
                                    data=f, timeout=600)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("put_file(%s) failed: %s", path, e)
        return None


def get_object(path: str) -> tuple[bytes, str] | None:
    """Download entire object. Returns (bytes, content_type) or None."""
    k = _key()
    if not k:
        return None
    try:
        resp = requests.get(f"{STORAGE_URL}/objects/{path}",
                            headers={"X-Storage-Key": k}, timeout=120)
        if resp.status_code == 403:
            init_storage(force=True)
            resp = requests.get(f"{STORAGE_URL}/objects/{path}",
                                headers={"X-Storage-Key": _key()}, timeout=120)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.content, resp.headers.get("Content-Type", "application/octet-stream")
    except Exception as e:
        logger.error("get_object(%s) failed: %s", path, e)
        return None


def stream_object(path: str, chunk_size: int = 1024 * 256) -> Iterator[bytes] | None:
    """Return a generator that streams the object bytes. Preserves memory."""
    k = _key()
    if not k:
        return None
    try:
        r = requests.get(f"{STORAGE_URL}/objects/{path}",
                        headers={"X-Storage-Key": k}, stream=True, timeout=180)
        if r.status_code == 403:
            init_storage(force=True)
            r = requests.get(f"{STORAGE_URL}/objects/{path}",
                            headers={"X-Storage-Key": _key()}, stream=True, timeout=180)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        content_type = r.headers.get("Content-Type", "application/octet-stream")

        def _gen():
            try:
                for c in r.iter_content(chunk_size=chunk_size):
                    if c:
                        yield c
            finally:
                r.close()
        return _gen(), content_type
    except Exception as e:
        logger.error("stream_object(%s) failed: %s", path, e)
        return None


def make_path(kind: str, doc_id: str, ext: str) -> str:
    """Uniform path builder: cognify/{kind}/{doc_id}.{ext}."""
    ext = (ext or "bin").lower().lstrip(".")
    return f"{APP_NAME}/{kind}/{doc_id}.{ext}"
