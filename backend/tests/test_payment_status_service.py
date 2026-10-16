"""Unit tests for services/payment_status_service.py — BRD CR 2026-10, FR-18 to
FR-20, section 5.5 (payment status), section 6.4 (partial-payment scenario).

Pure in-process tests against the in-memory fake_db fixture (see conftest.py) —
no live MongoDB or running server required, unlike the rest of backend/tests/.
"""
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.payment_status_service import (
    calculate_minimum_monthly_payment,
    get_payment_status,
    is_assessment_eligible,
    amount_required_to_restore_access,
    get_or_create_enrollment,
    record_payment,
)


# ---- FR-19/BR-02: minimum monthly payment, using the BRD section 5.4 worked examples ----

def test_minimum_payment_ai_fundamentals():
    course = {"id": "c1", "price": 120, "duration_months": 3}
    assert calculate_minimum_monthly_payment(course) == 40.0


def test_minimum_payment_machine_learning():
    course = {"id": "c2", "price": 240, "duration_months": 6}
    assert calculate_minimum_monthly_payment(course) == 40.0


def test_minimum_payment_ai_diploma():
    course = {"id": "c3", "price": 600, "duration_months": 12}
    assert calculate_minimum_monthly_payment(course) == 50.0


def test_minimum_payment_falls_back_to_duration_weeks_when_months_missing():
    course = {"id": "c4", "price": 100, "duration_weeks": 4}  # ~1 month
    assert calculate_minimum_monthly_payment(course) == 100.0


def test_minimum_payment_free_course_is_zero():
    course = {"id": "c5", "price": 0, "duration_months": 3}
    assert calculate_minimum_monthly_payment(course) == 0.0


# ---- section 5.5: payment status derivation ----

def test_status_unpaid_with_no_payment():
    enrollment = {"current_paid_until": None, "current_period_paid_amount": 0}
    assert get_payment_status(enrollment) == "unpaid"


def test_status_partially_paid():
    enrollment = {"current_paid_until": None, "current_period_paid_amount": 30}
    assert get_payment_status(enrollment) == "partially_paid"


def test_status_current_when_paid_until_in_future():
    future = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    enrollment = {"current_paid_until": future, "current_period_paid_amount": 0}
    assert get_payment_status(enrollment) == "current"


def test_status_overdue_when_paid_until_well_in_past():
    past = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    enrollment = {"current_paid_until": past, "current_period_paid_amount": 0}
    assert get_payment_status(enrollment) == "overdue"


def test_status_payment_due_in_short_grace_window():
    just_lapsed = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    enrollment = {"current_paid_until": just_lapsed, "current_period_paid_amount": 0}
    assert get_payment_status(enrollment) == "payment_due"


# ---- FR-20/FR-21/BR-04/BR-05: assessment eligibility ----

def test_assessment_blocked_when_unpaid():
    assert is_assessment_eligible({"payment_status": "unpaid"}) is False


def test_assessment_blocked_when_partially_paid():
    assert is_assessment_eligible({"payment_status": "partially_paid"}) is False


def test_assessment_allowed_when_current():
    assert is_assessment_eligible({"payment_status": "current"}) is True


def test_assessment_allowed_when_completed():
    assert is_assessment_eligible({"payment_status": "completed"}) is True


# ---- FR-26: amount required to restore access ----

def test_amount_required_reflects_partial_payment():
    course = {"price": 300, "duration_months": 6}  # minimum = $50
    enrollment = {"current_period_paid_amount": 30}
    assert amount_required_to_restore_access(course, enrollment) == 20.0


# ---- section 6.4 Important Partial-Payment Scenario, end to end against fake_db ----

async def test_partial_then_qualifying_payment_activates_access(fake_db):
    course = {"id": "course-1", "price": 300, "duration_months": 6}  # minimum = $50

    # Step 1: learner (or admin on their behalf) pays $30 — below the $50 minimum.
    result = await record_payment(
        fake_db, course=course, user_id="u1", amount=30, method="ecocash",
        source="manual", created_by="admin-1",
    )
    assert result["enrollment"]["payment_status"] == "partially_paid"
    assert is_assessment_eligible(result["enrollment"]) is False

    # Step 2: a further $20 brings the period total to $50 — now qualifying.
    result2 = await record_payment(
        fake_db, course=course, user_id="u1", amount=20, method="ecocash",
        source="manual", created_by="admin-1",
    )
    assert result2["enrollment"]["payment_status"] == "current"
    assert is_assessment_eligible(result2["enrollment"]) is True
    assert result2["enrollment"]["current_paid_until"] is not None

    # BR-07: both payments were recorded as given, not silently altered/merged.
    payments = await fake_db.manual_payments.find({"user_id": "u1"}).to_list()
    assert sorted(p["amount"] for p in payments) == [20, 30]


async def test_single_qualifying_payment_activates_access_immediately(fake_db):
    course = {"id": "course-2", "price": 120, "duration_months": 3}  # minimum = $40

    result = await record_payment(
        fake_db, course=course, user_id="u2", amount=40, method="other_manual",
        source="manual", created_by="admin-1", reference="REF123",
    )
    assert result["enrollment"]["payment_status"] == "current"
    assert result["minimum_monthly_payment"] == 40.0
    assert is_assessment_eligible(result["enrollment"]) is True


async def test_get_or_create_enrollment_is_idempotent(fake_db):
    e1 = await get_or_create_enrollment(fake_db, user_id="u3", course_id="course-3")
    e2 = await get_or_create_enrollment(fake_db, user_id="u3", course_id="course-3")
    assert e1["id"] == e2["id"]
    assert await fake_db.enrollments.count_documents({"user_id": "u3"}) == 1
