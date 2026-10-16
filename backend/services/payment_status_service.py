"""Single authoritative payment-status / minimum-payment engine — BRD CR 2026-10,
section 5.4 (FR-18 to FR-20), section 5.5 (payment status), section 6.4 (partial
payment), BR-01 to BR-05.

Per section 17 Implementation Notes ("use a single authoritative payment-status
service for frontend and backend decisions... avoid duplicating minimum-payment
calculations"), every place that needs to know a course's minimum payment, an
enrollment's status, or whether a learner can open an assignment/exam must go
through this module rather than re-deriving it locally.

Dates are stored as ISO-8601 strings, matching the rest of backend/server.py's
persistence convention.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

PERIOD_DAYS = 30  # "one month of payment eligibility" (BR-03) approximated as 30 days


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(value) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def calculate_minimum_monthly_payment(course: dict) -> float:
    """BR-02: Minimum Monthly Payment = Total Course Cost / Course Duration in Months.
    FR-19: calculated automatically; never hardcode this elsewhere."""
    price = float(course.get("price") or 0)
    duration_months = course.get("duration_months")
    if not duration_months:
        # Fall back to duration_weeks (existing field) when a course hasn't been
        # given an explicit duration_months yet, per BR-01's "must have ... duration".
        weeks = course.get("duration_weeks") or 4
        duration_months = max(1, round(weeks / 4.345))
    duration_months = max(1, int(duration_months))
    if price <= 0:
        return 0.0
    return round(price / duration_months, 2)


def get_payment_status(enrollment: dict) -> str:
    """Section 5.5 status table, derived from the enrollment's current period."""
    current_paid_until = _parse(enrollment.get("current_paid_until"))
    period_paid = float(enrollment.get("current_period_paid_amount") or 0)
    now = _now()

    if current_paid_until and current_paid_until >= now:
        return "current"
    if current_paid_until and current_paid_until < now:
        # Was current, period lapsed without renewal.
        grace_end = current_paid_until + timedelta(days=3)
        return "payment_due" if now <= grace_end else "overdue"
    if period_paid > 0:
        return "partially_paid"
    return "unpaid"


def is_assessment_eligible(enrollment: dict) -> bool:
    """FR-20/FR-21/BR-04/BR-05: only 'current' or 'completed' unlock assignments/exams.
    Everything else (unpaid, partially paid, payment due, overdue) is blocked, but the
    learner keeps general access per section 5.6 — this function governs assessment
    access only, never login or course-browsing."""
    status = enrollment.get("payment_status") or get_payment_status(enrollment)
    return status in ("current", "completed")


def amount_required_to_restore_access(course: dict, enrollment: dict) -> float:
    """Drives the FR-26 blocked-access message ('states the amount required to
    restore access')."""
    minimum = calculate_minimum_monthly_payment(course)
    paid = float(enrollment.get("current_period_paid_amount") or 0)
    remaining = round(minimum - paid, 2)
    return max(0.0, remaining)


async def get_or_create_enrollment(
    db,
    *,
    user_id: str,
    course_id: str,
    organization_id: Optional[str] = None,
    source: str = "online",
    created_by: Optional[str] = None,
) -> dict:
    enrollment = await db.enrollments.find_one(
        {"user_id": user_id, "course_id": course_id}, {"_id": 0}
    )
    if enrollment:
        return enrollment
    now = _now()
    enrollment = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "course_id": course_id,
        "organization_id": organization_id,
        "status": "active",
        "enrolled_at": now.isoformat(),
        "payment_status": "unpaid",
        "current_paid_until": None,
        "current_period_start": now.isoformat(),
        "current_period_paid_amount": 0.0,
        "source": source,
        "created_by": created_by,
    }
    await db.enrollments.insert_one(enrollment)
    return enrollment


async def record_payment(
    db,
    *,
    course: dict,
    user_id: str,
    amount: float,
    method: str,
    source: str,
    created_by: str,
    organization_id: Optional[str] = None,
    reference: Optional[str] = None,
    notes: Optional[str] = None,
    verified_by: Optional[str] = None,
    payment_date: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> dict:
    """Central write path for BOTH online-gateway and offline/manual payments
    (BRD section 6, FR-13). Records the payment as given (BR-07: "must not be
    silently altered") and only advances current_paid_until once the accumulated
    payment for the current period reaches the calculated minimum (section 6.4
    partial-payment scenario).

    Idempotency: when `idempotency_key` (or, as a fallback, `reference` scoped
    to learner+course) matches an existing non-voided payment, the existing
    payment/enrollment is returned with ``duplicate: True`` and no new record
    is written — safe to retry POSTs on network failure.
    Overpayment credit: any amount above the minimum is carried forward as
    `current_period_paid_amount` for the next period instead of being dropped,
    and whole extra months extend `current_paid_until` accordingly.
    """
    course_id = course["id"]
    if idempotency_key:
        existing = await db.manual_payments.find_one(
            {"idempotency_key": idempotency_key, "status": {"$ne": "voided"}}, {"_id": 0}
        )
        if existing:
            enrollment = await db.enrollments.find_one(
                {"id": existing.get("enrollment_id")}, {"_id": 0}
            ) or await get_or_create_enrollment(
                db, user_id=user_id, course_id=course_id,
                organization_id=organization_id, source=source, created_by=created_by,
            )
            return {
                "enrollment": enrollment,
                "payment": existing,
                "minimum_monthly_payment": calculate_minimum_monthly_payment(course),
                "duplicate": True,
            }
    if reference:
        existing_ref = await db.manual_payments.find_one(
            {
                "user_id": user_id, "course_id": course_id,
                "reference": reference, "status": {"$ne": "voided"},
            },
            {"_id": 0},
        )
        if existing_ref:
            enrollment = await db.enrollments.find_one(
                {"id": existing_ref.get("enrollment_id")}, {"_id": 0}
            ) or await get_or_create_enrollment(
                db, user_id=user_id, course_id=course_id,
                organization_id=organization_id, source=source, created_by=created_by,
            )
            return {
                "enrollment": enrollment,
                "payment": existing_ref,
                "minimum_monthly_payment": calculate_minimum_monthly_payment(course),
                "duplicate": True,
            }
    enrollment = await get_or_create_enrollment(
        db,
        user_id=user_id,
        course_id=course_id,
        organization_id=organization_id,
        source=source,
        created_by=created_by,
    )

    payment_record = {
        "id": str(uuid.uuid4()),
        "enrollment_id": enrollment["id"],
        "user_id": user_id,
        "course_id": course_id,
        "organization_id": organization_id,
        "amount": round(float(amount), 2),
        "currency": "USD",
        "method": method,
        "source": source,
        "status": "completed",
        "payment_date": payment_date or _now().isoformat(),
        "reference": reference,
        "idempotency_key": idempotency_key,
        "notes": notes,
        "created_by": created_by,
        "verified_by": verified_by,
        "created_at": _now().isoformat(),
        "voided_at": None,
        "voided_by": None,
        "void_reason": None,
    }
    await db.manual_payments.insert_one(dict(payment_record))

    minimum = calculate_minimum_monthly_payment(course)
    period_paid = float(enrollment.get("current_period_paid_amount") or 0) + float(amount)

    update: dict = {"current_period_paid_amount": round(period_paid, 2)}

    if minimum <= 0 or period_paid >= minimum:
        # Qualifying payment (BR-03): activates eligibility from whichever is
        # later — now, or the tail of the still-current period. Whole extra
        # months in an overpayment each extend a further PERIOD_DAYS, and any
        # leftover credit carries into the next period (never silently dropped).
        current_paid_until = _parse(enrollment.get("current_paid_until"))
        base = current_paid_until if (current_paid_until and current_paid_until > _now()) else _now()
        if minimum <= 0:
            periods = 1
            leftover = 0.0
        else:
            periods = max(1, int(period_paid // minimum))
            leftover = round(period_paid - periods * minimum, 2)
        new_paid_until = base + timedelta(days=PERIOD_DAYS * periods)
        update["current_paid_until"] = new_paid_until.isoformat()
        update["current_period_start"] = _now().isoformat()
        update["current_period_paid_amount"] = leftover
        update["payment_status"] = "current"
    else:
        update["payment_status"] = "partially_paid"

    await db.enrollments.update_one({"id": enrollment["id"]}, {"$set": update})
    enrollment.update(update)

    # Keep the legacy gate fields in sync too, since existing content/assignment
    # gates were reading these directly before an Enrollment record ever existed.
    if enrollment["payment_status"] in ("current", "completed"):
        await db.student_profiles.update_one(
            {"user_id": user_id}, {"$addToSet": {"enrolled_courses": course_id}}, upsert=True
        )
        await db.courses.update_one(
            {"id": course_id}, {"$addToSet": {"enrolled_students": user_id}}
        )

    return {"enrollment": enrollment, "payment": payment_record, "minimum_monthly_payment": minimum}


def assert_assessment_access(course: dict, enrollment: dict) -> dict:
    """Shared gate for every assignment/exam read AND write path (FR-20/FR-21,
    BR-04/BR-05, AC-08/AC-09). Returns ``{"allowed": True}`` for free courses
    and current/completed enrollments, else ``{"allowed": False,
    "amount_required": x}`` so callers return a consistent 403."""
    if not course or not course.get("is_paid", False):
        return {"allowed": True, "amount_required": 0.0}
    if is_assessment_eligible(enrollment):
        return {"allowed": True, "amount_required": 0.0}
    return {
        "allowed": False,
        "amount_required": amount_required_to_restore_access(course, enrollment),
        "payment_status": enrollment.get("payment_status") or get_payment_status(enrollment),
    }


async def recompute_enrollment_after_void(db, *, user_id: str, course: dict) -> dict:
    """Rebuild an enrollment from all non-voided payments (called after a void
    so eligibility is revoked when the remaining total no longer qualifies).
    Replays payments oldest-first through the same minimum/period math as
    record_payment, preserving overpayment credit."""
    course_id = course["id"]
    enrollment = await get_or_create_enrollment(db, user_id=user_id, course_id=course_id)
    payments = await db.manual_payments.find(
        {"user_id": user_id, "course_id": course_id, "status": {"$ne": "voided"}}
    ).to_list(length=10000)
    payments.sort(key=lambda p: p.get("created_at") or p.get("payment_date") or "")

    minimum = calculate_minimum_monthly_payment(course)
    now = _now()
    paid_until = None
    period_paid = 0.0
    period_start = enrollment.get("current_period_start") or enrollment.get("enrolled_at")
    status = "unpaid"

    for p in payments:
        try:
            amt = float(p.get("amount") or 0)
        except (TypeError, ValueError):
            continue
        if amt <= 0:
            continue
        period_paid += amt
        if minimum <= 0 or period_paid >= minimum:
            base = paid_until if (paid_until and paid_until > now) else now
            if minimum <= 0:
                periods = 1
                period_paid = 0.0
            else:
                periods = max(1, int(period_paid // minimum))
                period_paid = round(period_paid - periods * minimum, 2)
            paid_until = base + timedelta(days=PERIOD_DAYS * periods)
            period_start = now.isoformat()
            status = "current"
        else:
            status = "partially_paid"

    if paid_until is not None and paid_until < now - timedelta(days=3):
        status = "overdue"
    elif paid_until is not None and paid_until < now:
        status = "payment_due" if period_paid <= 0 else status
    if paid_until is None and period_paid <= 0:
        status = "unpaid"

    update = {
        "current_paid_until": paid_until.isoformat() if paid_until else None,
        "current_period_start": period_start,
        "current_period_paid_amount": round(period_paid, 2),
        "payment_status": status,
    }
    await db.enrollments.update_one({"id": enrollment["id"]}, {"$set": update})
    enrollment.update(update)
    return enrollment
