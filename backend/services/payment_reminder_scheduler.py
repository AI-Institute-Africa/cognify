"""Payment due/overdue reminder scheduler — BRD FR-14.

Forever-loop background task, following the same pattern as
services.research_digest.start(), rather than adding a new scheduler dependency
(APScheduler/Celery) that nothing else in this codebase uses.
"""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

INTERVAL_HOURS = 24


async def _run_once(db):
    from services.payment_status_service import get_payment_status, amount_required_to_restore_access
    from services.notification_service import send_notification

    enrollments = await db.enrollments.find(
        {"status": "active"}, {"_id": 0}
    ).to_list(length=10000)

    sent = 0
    for enrollment in enrollments:
        status = get_payment_status(enrollment)
        if status not in ("payment_due", "overdue"):
            continue
        course = await db.courses.find_one({"id": enrollment["course_id"]}, {"_id": 0})
        if not course:
            continue
        amount_due = amount_required_to_restore_access(course, enrollment)
        await send_notification(
            user_id=enrollment["user_id"],
            notification_type="payment_reminder",
            channels=["email", "whatsapp", "sms"],
            template_type="payment_overdue" if status == "overdue" else "payment_due",
            template_data={"course_name": course.get("name", ""), "amount_due": amount_due},
            db=db,
        )
        sent += 1

    await db.scheduler_state.update_one(
        {"_id": "payment_reminders"},
        {"$set": {"last_run_at": datetime.now(timezone.utc).isoformat(), "last_sent": sent}},
        upsert=True,
    )
    return sent


async def start(db):
    """Forever-loop scheduler, one pass every INTERVAL_HOURS."""
    logger.info("payment_reminder_scheduler: starting (every %dh)", INTERVAL_HOURS)
    while True:
        try:
            sent = await _run_once(db)
            logger.info("payment_reminder_scheduler: sent %d reminder(s)", sent)
        except Exception as e:
            logger.exception("payment_reminder_scheduler tick failed: %s", e)
        await asyncio.sleep(INTERVAL_HOURS * 3600)
