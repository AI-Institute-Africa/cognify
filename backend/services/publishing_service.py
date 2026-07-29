"""Weekly-rotating publishing service for AI research articles.

Every generated news article is:
  1) persisted to `published_articles` (source of truth)
  2) marked with the destination (ISO-week-based rotation)
  3) POSTed to the destination's optional webhook (if configured)

The active destination flips each ISO week (odd weeks → destination index 0,
even weeks → index 1) so nothing is hard-coded. Admins can enable/disable
rotation, add destinations, reorder, or override the current week manually.

Public endpoint: GET /api/public/news serves the articles for the current
active destination whose scope == 'internal' (so cognify.aiinstituteafrica.com/news
renders on THIS codebase). External destinations receive the payload via webhook.
"""
from __future__ import annotations
import os
import uuid
import hashlib
import logging
import asyncio
from datetime import datetime, timezone, date
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Default destinations bootstrapped on first use — matches the user's spec.
DEFAULT_DESTINATIONS = [
    {
        "name": "Cognify News",
        "site_url": "https://cognify.aiinstituteafrica.com/news",
        "scope": "internal",           # rendered on this app's /news page
        "webhook_url": None,
        "webhook_secret": None,
        "order": 0,
        "enabled": True,
    },
    {
        "name": "AI Institute Africa · Local Articles",
        "site_url": "https://aiinstituteafrica.com/local_articles",
        "scope": "external",           # POSTed to webhook_url
        "webhook_url": None,           # admin configures on target site
        "webhook_secret": None,
        "order": 1,
        "enabled": True,
    },
]

SETTINGS_KEY = "publishing_settings"


def _iso_week_index(d: date | None = None) -> int:
    d = d or datetime.now(timezone.utc).date()
    return d.isocalendar()[1]  # 1..53


def _article_slug(title: str) -> str:
    import re
    s = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")
    return s[:80] or "article"


async def ensure_defaults(db):
    """Bootstrap destinations + settings on first use. Idempotent."""
    for d in DEFAULT_DESTINATIONS:
        await db.publishing_destinations.update_one(
            {"site_url": d["site_url"]},
            {"$setOnInsert": {**d, "id": str(uuid.uuid4()),
                              "created_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )
    await db.scheduler_state.update_one(
        {"_id": SETTINGS_KEY},
        {"$setOnInsert": {
            "rotation_enabled": True,
            "manual_override_destination_id": None,
            "manual_override_week": None,   # ISO week integer when override applies
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )


async def list_destinations(db) -> list[dict]:
    await ensure_defaults(db)
    return await db.publishing_destinations.find(
        {}, {"_id": 0}).sort("order", 1).to_list(50)


async def get_settings(db) -> dict:
    await ensure_defaults(db)
    return await db.scheduler_state.find_one({"_id": SETTINGS_KEY}, {"_id": 0}) or {}


async def get_active_destination(db, week: int | None = None) -> Optional[dict]:
    """Return the currently-active destination based on ISO week rotation.
    Honours manual override if configured for the current week."""
    await ensure_defaults(db)
    week = week if week is not None else _iso_week_index()
    settings = await get_settings(db)

    # Manual override for THIS week wins
    override_id = settings.get("manual_override_destination_id")
    override_week = settings.get("manual_override_week")
    if override_id and override_week == week:
        dest = await db.publishing_destinations.find_one({"id": override_id, "enabled": True}, {"_id": 0})
        if dest:
            return dest

    if not settings.get("rotation_enabled", True):
        # Fixed-first destination when rotation disabled
        return await db.publishing_destinations.find_one(
            {"enabled": True}, {"_id": 0}, sort=[("order", 1)])

    dests = [d for d in await list_destinations(db) if d.get("enabled")]
    if not dests:
        return None
    idx = (week - 1) % len(dests)
    return dests[idx]


async def get_next_destination(db, week: int | None = None) -> Optional[dict]:
    week = (week if week is not None else _iso_week_index()) + 1
    return await get_active_destination(db, week=week)


async def _post_webhook(url: str, secret: str | None, payload: dict, retries: int = 3) -> tuple[bool, str]:
    """POST payload to external webhook with HMAC signature and retry."""
    headers = {"Content-Type": "application/json",
               "User-Agent": "Cognify-Publisher/1.0"}
    if secret:
        import hmac
        import json as _json
        body = _json.dumps(payload, separators=(",", ":")).encode()
        sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        headers["X-Cognify-Signature"] = f"sha256={sig}"
    last_err = ""
    for attempt in range(retries):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=20)
            if 200 <= r.status_code < 300:
                return True, f"HTTP {r.status_code}"
            last_err = f"HTTP {r.status_code}: {r.text[:200]}"
        except Exception as e:
            last_err = str(e)[:200]
        await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s backoff
    return False, last_err


async def publish_articles(db, items: list[dict]) -> dict:
    """Persist + publish a batch of items. Returns { active_destination, published, failed }."""
    if not items:
        return {"active_destination": None, "published": 0, "failed": 0, "articles": []}

    active = await get_active_destination(db)
    if not active:
        logger.warning("No enabled publishing destinations")
        return {"active_destination": None, "published": 0, "failed": len(items), "articles": []}

    week = _iso_week_index()
    published_at = datetime.now(timezone.utc).isoformat()
    published_ids = []
    fail_count = 0

    for it in items:
        article_id = str(uuid.uuid4())
        record = {
            "id": article_id,
            "title": it.get("title", ""),
            "slug": _article_slug(it.get("title", "") + "-" + article_id[:6]),
            "source_url": it.get("url"),
            "source": it.get("source", ""),
            "category": it.get("category", ""),
            "summary": it.get("summary", ""),
            "impact": it.get("impact", ""),
            "publication_date": it.get("date", ""),
            "destination_id": active["id"],
            "destination_name": active["name"],
            "destination_site_url": active["site_url"],
            "destination_scope": active["scope"],
            "published_week": week,
            "published_year": datetime.now(timezone.utc).year,
            "published_at": published_at,
            "publish_status": "published",
            "publish_attempts": 1,
            "webhook_error": None,
        }
        try:
            await db.published_articles.insert_one(record)
            # External destination → POST to its webhook (if configured)
            if active["scope"] == "external" and active.get("webhook_url"):
                payload = {
                    "id": article_id,
                    "title": record["title"],
                    "slug": record["slug"],
                    "source_url": record["source_url"],
                    "source": record["source"],
                    "category": record["category"],
                    "summary": record["summary"],
                    "impact": record["impact"],
                    "publication_date": record["publication_date"],
                    "published_at": published_at,
                }
                ok, err = await _post_webhook(active["webhook_url"],
                                               active.get("webhook_secret"), payload)
                await db.published_articles.update_one({"id": article_id}, {"$set": {
                    "publish_status": "published" if ok else "webhook_failed",
                    "webhook_error": None if ok else err,
                    "publish_attempts": 4 if not ok else 1,
                }})
                if not ok:
                    fail_count += 1
                    logger.warning(f"webhook publish failed for {article_id}: {err}")
            published_ids.append(article_id)
        except Exception as e:
            fail_count += 1
            logger.exception(f"publish article failed: {e}")
            try:
                await db.publishing_logs.insert_one({
                    "article_id": article_id,
                    "title": record["title"],
                    "destination_name": active["name"],
                    "error": str(e)[:400],
                    "at": published_at,
                })
            except Exception:
                pass

    # Aggregate log entry
    try:
        await db.publishing_logs.insert_one({
            "id": str(uuid.uuid4()),
            "batch_size": len(items),
            "destination_id": active["id"],
            "destination_name": active["name"],
            "destination_site_url": active["site_url"],
            "week": week,
            "published_at": published_at,
            "published_count": len(published_ids),
            "failed_count": fail_count,
        })
    except Exception:
        pass

    return {
        "active_destination": active,
        "published": len(published_ids),
        "failed": fail_count,
        "week": week,
        "articles": published_ids,
    }


def build_article_url(dest: dict, article_slug: str, article_id: str) -> str:
    """Compose the public URL where a published article can be viewed."""
    base = (dest.get("site_url") or "").rstrip("/")
    return f"{base}/{article_slug}-{article_id[:8]}"


async def publishing_stats(db) -> dict:
    """Summary for the admin dashboard: current active site, next site, history counts."""
    week = _iso_week_index()
    active = await get_active_destination(db, week=week)
    nxt = await get_next_destination(db, week=week)
    settings = await get_settings(db)
    total = await db.published_articles.count_documents({})
    this_week = await db.published_articles.count_documents({"published_week": week})
    return {
        "iso_week": week,
        "iso_year": datetime.now(timezone.utc).year,
        "rotation_enabled": settings.get("rotation_enabled", True),
        "manual_override": {
            "destination_id": settings.get("manual_override_destination_id"),
            "week": settings.get("manual_override_week"),
        },
        "active_destination": active,
        "next_destination": nxt,
        "total_published": total,
        "published_this_week": this_week,
    }
