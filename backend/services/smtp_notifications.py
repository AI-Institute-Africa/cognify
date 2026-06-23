"""Notification service.
Prefers Resend HTTP API (port 443) for delivery — falls back to Gmail SMTP if Resend
isn't configured or fails. The Resend path works inside Kubernetes preview pods where
outbound SMTP port 587 is blocked.
"""
import os
import smtplib
import asyncio
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

logger = logging.getLogger(__name__)

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", SMTP_USER)
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "True").lower() in ("1", "true", "yes")

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_SENDER = os.environ.get("SENDER_EMAIL") or SMTP_FROM_EMAIL or "onboarding@resend.dev"

_resend = None
if RESEND_API_KEY and not RESEND_API_KEY.startswith("re_test_"):
    try:
        import resend as _resend_lib
        _resend_lib.api_key = RESEND_API_KEY
        _resend = _resend_lib
        logger.info("smtp_notifications: Resend HTTP API ready (sender=%s)", RESEND_SENDER)
    except Exception as e:
        logger.warning("Resend client init failed, will fall back to SMTP: %s", e)


def _send_via_resend_sync(to_email: str, subject: str, html_body: str) -> bool:
    if not _resend:
        return False
    try:
        params = {
            "from": RESEND_SENDER,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        }
        resp = _resend.Emails.send(params)
        ok = bool(resp and (resp.get("id") if isinstance(resp, dict) else True))
        if not ok:
            logger.warning("Resend returned no id for %s: %r", to_email, resp)
        return ok
    except Exception as e:
        logger.error("Resend send to %s failed: %s", to_email, e)
        return False


def _send_email_sync(to_email: str, subject: str, html_body: str, plain_body: Optional[str] = None) -> bool:
    """Synchronous SMTP send. Returns True on success."""
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP not configured; skipping email to %s", to_email)
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM_EMAIL
        msg["To"] = to_email
        if plain_body:
            msg.attach(MIMEText(plain_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            if SMTP_USE_TLS:
                server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM_EMAIL, [to_email], msg.as_string())
        return True
    except Exception as e:
        logger.error("SMTP send to %s failed: %s", to_email, e)
        return False


async def send_email(to_email: str, subject: str, html_body: str, plain_body: Optional[str] = None) -> bool:
    """Async send — Resend (HTTPS) first, SMTP fallback. Returns True on success."""
    # Prefer Resend (HTTP API, never blocked by container egress rules)
    if _resend:
        ok = await asyncio.to_thread(_send_via_resend_sync, to_email, subject, html_body)
        if ok:
            return True
    # Fallback to SMTP
    return await asyncio.to_thread(_send_email_sync, to_email, subject, html_body, plain_body)


async def broadcast_to_org(db, organization_id: Optional[str], subject: str, html_body: str,
                            plain_body: Optional[str] = None,
                            exclude_user_id: Optional[str] = None,
                            role_filter: Optional[List[str]] = None) -> dict:
    """Send notification emails to all active users in an organization.

    Args:
        db: motor database handle
        organization_id: target org (None => skip — refuse to broadcast across orgs)
        subject, html_body, plain_body: email content
        exclude_user_id: skip this user (e.g., the actor)
        role_filter: only send to users with these roles (e.g., ["student", "teacher"])

    Returns dict with `sent`, `failed`, `total` counts.
    """
    if not organization_id:
        return {"sent": 0, "failed": 0, "total": 0, "skipped": "no organization_id"}

    query = {"organization_id": organization_id, "is_active": {"$ne": False}}
    if role_filter:
        query["role"] = {"$in": role_filter}
    if exclude_user_id:
        query["id"] = {"$ne": exclude_user_id}

    users = await db.users.find(query, {"_id": 0, "email": 1, "full_name": 1}).to_list(length=5000)
    if not users:
        return {"sent": 0, "failed": 0, "total": 0}

    sent = 0
    failed = 0
    for u in users:
        email = (u.get("email") or "").strip()
        if not email or "@" not in email:
            failed += 1
            continue
        # Personalize greeting in HTML body
        personalized_html = html_body.replace("{{name}}", u.get("full_name", "there"))
        ok = await send_email(email, subject, personalized_html, plain_body)
        if ok:
            sent += 1
        else:
            failed += 1
    return {"sent": sent, "failed": failed, "total": len(users)}


def render_notification(title: str, message: str, action_label: Optional[str] = None,
                         action_url: Optional[str] = None) -> str:
    """Render a consistent HTML email template."""
    action_html = ""
    if action_label and action_url:
        action_html = f"""
        <p style="text-align:center;margin:32px 0;">
          <a href="{action_url}"
             style="background:#7c3aed;color:#fff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:600;display:inline-block;">
            {action_label}
          </a>
        </p>
        """
    return f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family:Inter,Arial,sans-serif;background:#0f0f10;color:#e4e4e7;margin:0;padding:0;">
      <div style="max-width:600px;margin:0 auto;padding:32px;background:#18181b;border-radius:12px;">
        <h1 style="color:#fff;font-size:22px;margin:0 0 16px;">Cognify</h1>
        <h2 style="color:#a78bfa;font-size:18px;margin:0 0 16px;">{title}</h2>
        <p style="color:#d4d4d8;line-height:1.6;">Hi {{{{name}}}},</p>
        <div style="color:#a1a1aa;line-height:1.6;">{message}</div>
        {action_html}
        <hr style="border:0;border-top:1px solid #3f3f46;margin:32px 0;" />
        <p style="font-size:12px;color:#71717a;">
          You're receiving this because you're a member of your organization on Cognify.
        </p>
      </div>
    </body>
    </html>
    """



async def send_notification_email(recipients: List[str], subject: str, title: str, message: str,
                                   action_label: Optional[str] = None, action_url: Optional[str] = None,
                                   frontend_base_url: Optional[str] = None) -> dict:
    """High-level helper used by feature code: builds the HTML, fans out to recipients.

    Returns {sent, failed, total}.
    """
    if not recipients:
        return {"sent": 0, "failed": 0, "total": 0}
    # If action_url is a relative path, prefix with the frontend host so links work in email clients
    full_action_url = action_url
    if action_url and action_url.startswith("/"):
        base = frontend_base_url or os.environ.get("PUBLIC_FRONTEND_URL") or os.environ.get("REACT_APP_BACKEND_URL", "")
        if base:
            full_action_url = base.rstrip("/") + action_url
    html_body = render_notification(title=title, message=message,
                                    action_label=action_label, action_url=full_action_url)

    # Parallel fan-out — cap concurrency at 10 to be polite to the provider
    sem = asyncio.Semaphore(10)

    async def _one(email: str) -> bool:
        email = (email or "").strip()
        if not email or "@" not in email:
            return False
        async with sem:
            return await send_email(email, subject, html_body.replace("{{name}}", "there"))

    results = await asyncio.gather(*[_one(e) for e in recipients], return_exceptions=True)
    sent = sum(1 for r in results if r is True)
    failed = len(results) - sent
    logger.info("notification: sent=%d failed=%d total=%d subject=%r", sent, failed, len(recipients), subject)
    return {"sent": sent, "failed": failed, "total": len(recipients)}
