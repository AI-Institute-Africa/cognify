"""Background scheduler that emails fresh research publications to a digest
recipient every 4 hours when new content is available, plus a guaranteed daily
summary at 09:00 UTC.

Run as `asyncio.create_task(start(db))` from server.py startup.
"""
from __future__ import annotations
import os, asyncio, logging
from datetime import datetime, timezone, timedelta
from services.smtp_notifications import send_notification_email, render_notification

logger = logging.getLogger(__name__)

RECIPIENT = os.environ.get("RESEARCH_DIGEST_EMAIL", "dennis@rubiem.com")
INTERVAL_HOURS = 4
STATE_KEY = "research_digest"


async def _collect_new_items(db, since_iso: str) -> list[dict]:
    """Pick up live-research items added since the last digest.
    Looks at the cached_research_articles collection populated by /api/research/search,
    plus public_content additions.
    """
    items: list[dict] = []
    try:
        async for d in db.cached_research_articles.find(
                {"created_at": {"$gte": since_iso}}, {"_id": 0}).sort("created_at", -1).limit(50):
            items.append({"kind": "research", "title": d.get("title"),
                          "url": d.get("url"), "summary": d.get("summary", "")[:300],
                          "source": d.get("source"), "created_at": d.get("created_at")})
    except Exception:
        pass
    try:
        async for d in db.public_content.find(
                {"created_at": {"$gte": since_iso}, "is_active": {"$ne": False}},
                {"_id": 0}).sort("created_at", -1).limit(50):
            items.append({"kind": "public", "title": d.get("title"),
                          "url": f"/public/{d.get('id')}",
                          "summary": (d.get("description") or "")[:300],
                          "source": "Cognify Public Library",
                          "created_at": d.get("created_at")})
    except Exception:
        pass
    return items


def _format_digest_html(items: list[dict], is_daily_summary: bool = False) -> str:
    title = "Daily Research Summary" if is_daily_summary else f"New publications — {len(items)} item(s)"
    lines = []
    for it in items[:40]:
        url = it.get("url") or "#"
        if url.startswith("/"):
            base = os.environ.get("PUBLIC_FRONTEND_URL", "")
            url = (base.rstrip("/") + url) if base else url
        kind_label = "📚 " if it.get("kind") == "public" else "🔬 "
        lines.append(
            f"<li style='margin-bottom:14px;'>"
            f"<strong>{kind_label}{it.get('title','(untitled)')}</strong><br/>"
            f"<span style='color:#71717a;font-size:12px;'>{it.get('source','')}</span><br/>"
            f"<span style='color:#52525b;font-size:13px;'>{(it.get('summary') or '')[:240]}</span><br/>"
            f"<a href='{url}' style='color:#7c3aed;font-size:13px;'>Read more →</a>"
            f"</li>")
    if not lines:
        body = "<p style='color:#71717a;'>No new publications in this period.</p>"
    else:
        body = f"<ul style='padding-left:18px;'>{''.join(lines)}</ul>"
    return render_notification(
        title=title,
        message=f"<div>{body}</div>",
        action_label="Open Cognify Research",
        action_url=(os.environ.get("PUBLIC_FRONTEND_URL", "") + "/research") or None,
    )


async def _run_once(db, *, is_daily_summary: bool = False) -> dict:
    state = await db.scheduler_state.find_one({"_id": STATE_KEY}) or {}
    last_run = state.get("last_run_at") or (datetime.now(timezone.utc) - timedelta(hours=INTERVAL_HOURS)).isoformat()
    items = await _collect_new_items(db, last_run)
    if not items and not is_daily_summary:
        logger.info("research_digest: no new items, skipping email")
        await db.scheduler_state.update_one(
            {"_id": STATE_KEY},
            {"$set": {"last_run_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True)
        return {"sent": 0, "items": 0, "reason": "no_new_items"}
    html = _format_digest_html(items, is_daily_summary)
    subject = ("[Cognify] Daily research summary" if is_daily_summary
               else f"[Cognify] New publications ({len(items)})")
    res = await send_notification_email(
        recipients=[RECIPIENT],
        subject=subject,
        title=subject,
        message="See latest entries below.",
        frontend_base_url=os.environ.get("PUBLIC_FRONTEND_URL"))
    # Override with our richer html body — re-send with proper html
    from services.smtp_notifications import send_email
    await send_email(RECIPIENT, subject, html)
    await db.scheduler_state.update_one(
        {"_id": STATE_KEY},
        {"$set": {"last_run_at": datetime.now(timezone.utc).isoformat(),
                  "last_items_sent": len(items), "is_daily": is_daily_summary}},
        upsert=True)
    return {"sent": res.get("sent", 0), "items": len(items)}


async def start(db):
    """Forever-loop scheduler. 4-hour cycle + daily summary at 09:00 UTC."""
    logger.info("research_digest: scheduler starting (recipient=%s, every %dh)", RECIPIENT, INTERVAL_HOURS)
    last_daily_date = None
    while True:
        try:
            now = datetime.now(timezone.utc)
            # Daily summary at 09:00 UTC once per day
            send_daily = (now.hour == 9 and last_daily_date != now.date())
            if send_daily:
                await _run_once(db, is_daily_summary=True)
                last_daily_date = now.date()
            await _run_once(db, is_daily_summary=False)
        except Exception as e:
            logger.exception("research_digest tick failed: %s", e)
        await asyncio.sleep(INTERVAL_HOURS * 3600)
