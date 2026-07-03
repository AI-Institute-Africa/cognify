"""AI Research & News Digest scheduler.

Every 4 hours, fetch fresh AI-related news, research and product launches from
real-time RSS feeds of the world's leading AI publishers, deduplicate against
previously-sent URLs and email a curated briefing to BOTH the operations
recipient (dennis@rubiem.com) and the super-admin recipient
(takuechakanyuka@gmail.com).

Design choice: RSS gives us verifiably real URLs and headlines with no LLM
hallucination. GPT-5.2 is used only to enrich each item with a short
"why-it-matters" summary — never to invent headlines or URLs.
"""
from __future__ import annotations
import os
import re
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

import feedparser
import requests

from services.smtp_notifications import send_email, render_notification

logger = logging.getLogger(__name__)

DEFAULT_RECIPIENTS = ["dennis@rubiem.com", "takuechakanyuka@gmail.com"]

RECIPIENTS: list[str] = [
    r.strip() for r in os.environ.get(
        "RESEARCH_DIGEST_RECIPIENTS",
        ",".join(DEFAULT_RECIPIENTS)
    ).split(",") if r.strip()
]

INTERVAL_HOURS = int(os.environ.get("RESEARCH_DIGEST_INTERVAL_HOURS", "4"))
STATE_KEY = "research_digest_v3"
MAX_ITEMS_PER_DIGEST = 20
MAX_AGE_HOURS = 24

# Live RSS feeds — real URLs from primary AI-industry sources
FEEDS: list[dict] = [
    # AI lab announcements
    {"url": "https://openai.com/blog/rss.xml", "source": "OpenAI Blog", "cat": "product"},
    {"url": "https://www.anthropic.com/news/rss.xml", "source": "Anthropic", "cat": "product"},
    {"url": "https://deepmind.google/blog/rss.xml", "source": "Google DeepMind", "cat": "research"},
    {"url": "https://ai.googleblog.com/atom.xml", "source": "Google AI Blog", "cat": "research"},
    {"url": "https://research.google/blog/rss", "source": "Google Research", "cat": "research"},
    {"url": "https://blogs.microsoft.com/ai/feed/", "source": "Microsoft AI", "cat": "product"},
    {"url": "https://research.facebook.com/feed/", "source": "Meta AI Research", "cat": "research"},
    {"url": "https://huggingface.co/blog/feed.xml", "source": "Hugging Face", "cat": "research"},

    # Academic / preprint
    {"url": "http://export.arxiv.org/rss/cs.AI", "source": "arXiv cs.AI", "cat": "research"},
    {"url": "http://export.arxiv.org/rss/cs.LG", "source": "arXiv cs.LG", "cat": "research"},
    {"url": "http://export.arxiv.org/rss/cs.CL", "source": "arXiv cs.CL", "cat": "research"},

    # Tech press (AI-focused)
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/", "source": "TechCrunch AI", "cat": "product"},
    {"url": "https://www.technologyreview.com/topic/artificial-intelligence/feed", "source": "MIT Tech Review", "cat": "applied"},
    {"url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "source": "The Verge AI", "cat": "product"},
    {"url": "https://www.wired.com/feed/tag/ai/latest/rss", "source": "Wired AI", "cat": "applied"},
    {"url": "https://venturebeat.com/category/ai/feed/", "source": "VentureBeat AI", "cat": "product"},

    # General press via Google News RSS (filtered to AI)
    {"url": "https://news.google.com/rss/search?q=artificial+intelligence+when:1d&hl=en-US&gl=US&ceid=US:en",
     "source": "Google News · AI", "cat": "applied"},
    {"url": "https://news.google.com/rss/search?q=%22OpenAI%22+OR+%22Anthropic%22+OR+%22Google+DeepMind%22+when:1d&hl=en-US&gl=US&ceid=US:en",
     "source": "Google News · Labs", "cat": "product"},
    {"url": "https://news.google.com/rss/search?q=AI+regulation+OR+%22AI+Act%22+when:1d&hl=en-US&gl=US&ceid=US:en",
     "source": "Google News · Policy", "cat": "policy"},
    {"url": "https://news.google.com/rss/search?q=%22AI+funding%22+OR+%22AI+startup%22+when:1d&hl=en-US&gl=US&ceid=US:en",
     "source": "Google News · Funding", "cat": "funding"},
    {"url": "https://news.google.com/rss/search?q=%22Africa%22+AI+OR+%22Zimbabwe%22+AI+when:2d&hl=en-US&gl=US&ceid=US:en",
     "source": "Google News · Africa AI", "cat": "africa"},
]

AI_KEYWORDS = re.compile(
    r"\b(ai|artificial intelligence|machine learning|deep learning|neural network|"
    r"llm|gpt|chatgpt|claude|gemini|copilot|openai|anthropic|deepmind|hugging face|"
    r"transformer|diffusion|generative|foundation model|agents?|rag|"
    r"reinforcement learning|nlp|computer vision)\b",
    re.IGNORECASE,
)


def _clean_text(html_or_text: str) -> str:
    if not html_or_text:
        return ""
    s = re.sub(r"<[^>]+>", " ", html_or_text)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _parse_feed(feed_def: dict) -> list[dict]:
    """Fetch one RSS feed and return normalised items."""
    try:
        # feedparser handles conditional GET etc., but let's fetch with requests
        # for a stable timeout across all feeds.
        headers = {"User-Agent": "Cognify-Research-Digest/1.0 (+https://cognify.aiinstituteafrica.com)"}
        r = requests.get(feed_def["url"], headers=headers, timeout=15)
        parsed = feedparser.parse(r.content)
    except Exception as e:
        logger.warning("Feed fetch failed for %s: %s", feed_def["source"], e)
        return []

    items = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=MAX_AGE_HOURS)
    for entry in parsed.entries[:15]:
        title = _clean_text(entry.get("title", ""))
        link = entry.get("link", "").strip()
        if not title or not link:
            continue
        summary = _clean_text(entry.get("summary", "") or entry.get("description", ""))[:600]
        # Try to parse date
        pub = entry.get("published") or entry.get("updated") or ""
        try:
            pub_dt = parsedate_to_datetime(pub) if pub else None
        except Exception:
            pub_dt = None
        if pub_dt and pub_dt.tzinfo is None:
            pub_dt = pub_dt.replace(tzinfo=timezone.utc)
        # Skip anything older than MAX_AGE_HOURS (for Google News feeds already scoped by when:1d)
        if pub_dt and pub_dt < cutoff:
            continue
        # For general-news feeds, keep only clearly-AI items
        if feed_def.get("filter_ai") is None and feed_def["source"].startswith("Google News"):
            haystack = f"{title} {summary}"
            if not AI_KEYWORDS.search(haystack):
                continue
        items.append({
            "title": title,
            "url": link,
            "source": feed_def["source"],
            "category": feed_def["cat"],
            "summary": summary,
            "date": (pub_dt.strftime("%Y-%m-%d %H:%M UTC")
                     if pub_dt else datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        })
    return items


async def _fetch_all_feeds() -> list[dict]:
    """Fetch all feeds in parallel using thread pool (requests is sync)."""
    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(None, _parse_feed, f) for f in FEEDS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_items: list[dict] = []
    for r in results:
        if isinstance(r, list):
            all_items.extend(r)
    # Deduplicate by URL (some Google News URLs redirect the same story from different sources)
    seen_urls = set()
    dedup = []
    for it in all_items:
        u = it["url"]
        if u in seen_urls:
            continue
        seen_urls.add(u)
        dedup.append(it)
    # Sort: dedup by url, prefer primary-source feeds over Google News aggregations
    priority = {"OpenAI Blog": 1, "Anthropic": 1, "Google DeepMind": 1,
                "Google AI Blog": 1, "Google Research": 1, "Microsoft AI": 1,
                "Meta AI Research": 1, "Hugging Face": 1,
                "arXiv cs.AI": 2, "arXiv cs.LG": 2, "arXiv cs.CL": 2,
                "TechCrunch AI": 3, "MIT Tech Review": 3, "The Verge AI": 3,
                "Wired AI": 3, "VentureBeat AI": 3}
    dedup.sort(key=lambda x: priority.get(x["source"], 9))
    return dedup


async def _enrich_with_llm(items: list[dict]) -> list[dict]:
    """Ask GPT-5.2 for a 1-sentence 'why this matters' impact statement per item.
    Non-blocking — if the LLM fails or budget is exhausted, items still go out
    without the impact field.
    """
    if not items:
        return items
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        return items
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        # Batch enrich — one call, all items at once
        titles = "\n".join(
            f"{i + 1}. {it['title']} — {it['source']}" for i, it in enumerate(items[:MAX_ITEMS_PER_DIGEST])
        )
        chat = LlmChat(
            api_key=api_key,
            session_id=f"digest-enrich-{datetime.now(timezone.utc).strftime('%Y%m%d%H')}",
            system_message=(
                "For each numbered AI news headline, return ONE short 'why-this-matters' "
                "sentence (max 25 words) explaining the strategic significance for "
                "practitioners and decision-makers. Return the numbered list, one line per "
                "item, format: '<number>. <sentence>'. No preamble, no markdown."
            ),
        )
        chat.with_model("openai", "gpt-5.2")
        resp = await chat.send_message(UserMessage(text=titles))
        text = resp.text if hasattr(resp, "text") else str(resp)
        # Parse "1. text\n2. text\n..."
        for line in text.strip().splitlines():
            m = re.match(r"^\s*(\d+)\.\s*(.+?)\s*$", line)
            if not m:
                continue
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(items):
                items[idx]["impact"] = m.group(2)[:400]
    except Exception as e:
        logger.warning("LLM enrichment skipped: %s", e)
    return items


async def _filter_new(db, items: list[dict]) -> list[dict]:
    """Remove items whose URL was already sent in a prior digest."""
    if not items:
        return []
    urls = [i["url"] for i in items]
    seen = set()
    async for row in db.research_digest_sent.find(
            {"url": {"$in": urls}}, {"_id": 0, "url": 1}):
        seen.add(row["url"])
    return [i for i in items if i["url"] not in seen]


async def _record_sent(db, items: list[dict]):
    if not items:
        return
    now = datetime.now(timezone.utc).isoformat()
    docs = [{"url": i["url"], "title": i.get("title", "")[:280],
             "source": i.get("source", ""), "sent_at": now} for i in items]
    try:
        await db.research_digest_sent.insert_many(docs, ordered=False)
    except Exception:
        pass


CATEGORY_ICON = {
    "research": "🔬", "product": "🚀", "policy": "📜",
    "funding": "💰", "africa": "🌍", "applied": "⚙️",
}


def _format_html(items: list[dict], subject: str) -> str:
    if not items:
        body = "<p style='color:#71717a;'>No new AI publications in the last 4 hours.</p>"
    else:
        lines = []
        for it in items[:MAX_ITEMS_PER_DIGEST]:
            icon = CATEGORY_ICON.get((it.get("category") or "").lower(), "🧠")
            summary = it.get("summary") or ""
            impact = it.get("impact") or ""
            impact_html = (f"<div style='margin-top:6px;color:#a78bfa;font-size:12px;'>"
                           f"<strong>Why it matters:</strong> {impact}</div>") if impact else ""
            lines.append(
                "<li style='margin-bottom:16px;padding:14px;border:1px solid #27272a;"
                "border-radius:10px;background:#0b0b0f;list-style:none;'>"
                f"<div style='font-size:12px;color:#71717a;margin-bottom:6px;'>"
                f"{icon} {it.get('source','')} · {it.get('date','')} · {it.get('category','').upper()}</div>"
                f"<div style='font-size:16px;font-weight:600;color:#e4e4e7;margin-bottom:8px;line-height:1.3;'>"
                f"{it.get('title','(untitled)')}</div>"
                f"<div style='font-size:13px;color:#a1a1aa;line-height:1.5;'>{summary}</div>"
                f"{impact_html}"
                f"<div style='margin-top:10px;'>"
                f"<a href='{it['url']}' style='color:#7c3aed;font-size:13px;text-decoration:none;font-weight:600;'>"
                f"Read the full story →</a></div>"
                "</li>"
            )
        body = f"<ul style='padding:0;margin:0;list-style:none;'>{''.join(lines)}</ul>"

    intro = (
        "<p style='color:#a1a1aa;font-size:14px;line-height:1.5;'>"
        f"Curated by the <strong>Cognify Live Research Engine</strong>. "
        f"Delivered every {INTERVAL_HOURS} hours. "
        f"<br/>Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · "
        f"{len(items)} item(s) after deduplication."
        "</p>"
    )
    return render_notification(
        title=subject,
        message=intro + body,
        action_label="Open Cognify",
        action_url=(os.environ.get("PUBLIC_FRONTEND_URL", "").rstrip("/") + "/research") or None,
    )


async def _run_once(db) -> dict:
    all_items = await _fetch_all_feeds()
    new_items = await _filter_new(db, all_items)
    if not new_items:
        logger.info("AI research digest: no new items this cycle (fetched=%d)", len(all_items))
        await db.scheduler_state.update_one(
            {"_id": STATE_KEY},
            {"$set": {"last_run_at": datetime.now(timezone.utc).isoformat(),
                      "last_items_fetched": len(all_items),
                      "last_items_sent": 0}},
            upsert=True)
        return {"sent": 0, "fetched": len(all_items), "new": 0}

    # Cap and enrich
    new_items = new_items[:MAX_ITEMS_PER_DIGEST]
    await _enrich_with_llm(new_items)

    subject = (
        f"[Cognify AI Briefing] {len(new_items)} new AI stor"
        f"{'y' if len(new_items) == 1 else 'ies'} — "
        f"{datetime.now(timezone.utc).strftime('%b %d, %H:%M UTC')}"
    )
    html = _format_html(new_items, subject)

    sent_count = 0
    for recipient in RECIPIENTS:
        try:
            ok = await send_email(recipient, subject, html)
            if ok:
                sent_count += 1
                logger.info("AI research digest sent to %s (%d items)", recipient, len(new_items))
            else:
                logger.warning("AI research digest send to %s returned False", recipient)
        except Exception as e:
            logger.exception("AI research digest send to %s crashed: %s", recipient, e)

    await _record_sent(db, new_items)
    await db.scheduler_state.update_one(
        {"_id": STATE_KEY},
        {"$set": {"last_run_at": datetime.now(timezone.utc).isoformat(),
                  "last_items_fetched": len(all_items),
                  "last_items_sent": len(new_items),
                  "recipients": RECIPIENTS,
                  "sent_count": sent_count}},
        upsert=True)
    return {"sent": sent_count, "items": len(new_items),
            "fetched": len(all_items), "new": len(new_items),
            "recipients": RECIPIENTS}


async def start(db):
    """Forever-loop scheduler running every `INTERVAL_HOURS` hours."""
    logger.info(
        "AI research digest scheduler starting — recipients=%s, interval=%dh, feeds=%d",
        RECIPIENTS, INTERVAL_HOURS, len(FEEDS),
    )
    await asyncio.sleep(30)  # avoid firing during hot-reload chaos
    while True:
        try:
            result = await _run_once(db)
            logger.info("AI research digest tick: %s", result)
        except Exception as e:
            logger.exception("AI research digest tick failed: %s", e)
        await asyncio.sleep(INTERVAL_HOURS * 3600)


async def run_now(db) -> dict:
    """Manual trigger used by /api/super-admin/research-digest/run-now."""
    return await _run_once(db)
