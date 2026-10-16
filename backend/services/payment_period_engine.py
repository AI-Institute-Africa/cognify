"""Payment Period Engine and Central Payment Status Service for Cognify.

Provides:
- Precise Decimal-based calculation of minimum monthly payments.
- Management of payment periods (period start, end, required, qualifying).
- Authoritative calculation of payment status:
  UNPAID, PARTIALLY_PAID, CURRENT, PAYMENT_DUE, OVERDUE, COMPLETED.
- Financial record recording & cumulative qualifying amount aggregation.
- Separation of general learning access from assessment access.
"""
from __future__ import annotations
import uuid
import logging
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


def to_decimal(val: Any) -> Decimal:
    """Safely convert numeric or string to Decimal."""
    if val is None:
        return Decimal("0.00")
    if isinstance(val, (int, float, str)):
        return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if isinstance(val, Decimal):
        return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return Decimal("0.00")


def calculate_minimum_monthly_payment(total_course_cost: Any, duration_months: int) -> float:
    """Calculate minimum monthly payment with precise decimal rounding.
    
    Formula: TOTAL COURSE COST / COURSE DURATION IN MONTHS
    Rounded to 2 decimal places with ROUND_HALF_UP.
    """
    if not duration_months or duration_months <= 0:
        return float(to_decimal(total_course_cost))
    
    cost_dec = to_decimal(total_course_cost)
    if cost_dec <= Decimal("0.00"):
        return 0.0
    
    dur_dec = Decimal(str(duration_months))
    monthly = (cost_dec / dur_dec).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return float(monthly)


class PaymentPeriodService:
    def __init__(self, db):
        self.db = db

    async def get_or_create_active_period(self, enrollment: dict, course: dict) -> dict:
        """Find the active payment period for an enrollment or create the initial one."""
        enrollment_id = enrollment.get("id") or enrollment.get("enrollment_id")
        user_id = enrollment.get("user_id") or enrollment.get("student_id")
        course_id = course.get("id")

        now = datetime.now(timezone.utc)

        # Check existing active period
        period = await self.db.payment_periods.find_one({
            "enrollment_id": enrollment_id,
            "period_start": {"$lte": now.isoformat()},
            "period_end": {"$gte": now.isoformat()},
        }, {"_id": 0})

        if period:
            return period

        # Check most recent period
        latest_period = await self.db.payment_periods.find_one({
            "enrollment_id": enrollment_id
        }, {"_id": 0}, sort=[("period_end", -1)])

        total_price = course.get("price") or course.get("total_price", 0.0)
        duration_months = course.get("duration_months") or max(1, int(course.get("duration_weeks", 4) / 4))
        monthly_min = calculate_minimum_monthly_payment(total_price, duration_months)

        if not latest_period:
            # First period starts at enrollment creation time or now
            enrolled_at_str = enrollment.get("enrolled_at") or enrollment.get("created_at")
            if enrolled_at_str:
                try:
                    start_dt = datetime.fromisoformat(enrolled_at_str)
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=timezone.utc)
                except Exception:
                    start_dt = now
            else:
                start_dt = now

            period_number = 1
        else:
            try:
                prev_end = datetime.fromisoformat(latest_period["period_end"])
                if prev_end.tzinfo is None:
                    prev_end = prev_end.replace(tzinfo=timezone.utc)
                start_dt = prev_end
            except Exception:
                start_dt = now
            period_number = latest_period.get("period_number", 1) + 1

        end_dt = start_dt + timedelta(days=30)

        new_period = {
            "id": str(uuid.uuid4()),
            "enrollment_id": enrollment_id,
            "user_id": user_id,
            "course_id": course_id,
            "organization_id": enrollment.get("organization_id") or course.get("organization_id"),
            "period_number": period_number,
            "period_start": start_dt.isoformat(),
            "period_end": end_dt.isoformat(),
            "required_amount": monthly_min,
            "qualifying_amount": 0.0,
            "currency": course.get("currency", "USD"),
            "status": "UNPAID",
            "payment_ids": [],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        await self.db.payment_periods.insert_one(dict(new_period))
        new_period.pop("_id", None)
        return new_period

    async def recalculate_payment_status(self, enrollment_id: str) -> dict:
        """Central, authoritative calculation of payment status and assessment eligibility.
        
        Evaluates:
        - Total course cost vs cumulative total payments across all periods
        - Current period required vs cumulative qualifying payments in current period
        - Returns full status breakdown.
        """
        enrollment = await self.db.enrollments.find_one({"$or": [{"id": enrollment_id}, {"enrollment_id": enrollment_id}]}, {"_id": 0})
        if not enrollment:
            # Check if enrolled directly in student profile
            raise ValueError(f"Enrollment {enrollment_id} not found")

        course_id = enrollment.get("course_id")
        course = await self.db.courses.find_one({"id": course_id}, {"_id": 0})
        if not course:
            raise ValueError(f"Course {course_id} not found")

        total_price = float(to_decimal(course.get("price") or course.get("total_price", 0.0)))
        currency = course.get("currency", "USD")
        duration_months = course.get("duration_months") or max(1, int(course.get("duration_weeks", 4) / 4))
        is_paid = course.get("is_paid", total_price > 0)
        payment_required = course.get("payment_required", is_paid and total_price > 0)

        # Free courses are always completed & eligible
        if not payment_required or total_price <= 0:
            return {
                "enrolled": True,
                "course_price": 0.0,
                "currency": currency,
                "duration_months": duration_months,
                "minimum_monthly_payment": 0.0,
                "total_paid_all_time": 0.0,
                "current_period_start": None,
                "current_period_end": None,
                "amount_paid_current_period": 0.0,
                "amount_required_current_period": 0.0,
                "amount_remaining": 0.0,
                "payment_status": "COMPLETED",
                "general_learning_allowed": True,
                "assessment_eligible": True,
                "message": "Free course. Full access granted."
            }

        monthly_min = calculate_minimum_monthly_payment(total_price, duration_months)

        # Get all valid payments for this enrollment / user + course
        user_id = enrollment.get("user_id") or enrollment.get("student_id")
        payments_cursor = self.db.payment_records.find({
            "$or": [
                {"enrollment_id": enrollment.get("id")},
                {"enrollment_id": enrollment.get("enrollment_id")},
                {"$and": [{"user_id": user_id}, {"course_id": course_id}]}
            ],
            "status": {"$in": ["completed", "paid", "succeeded"]}
        }, {"_id": 0})
        payments = await payments_cursor.to_list(1000)

        # Total paid all time
        total_paid_dec = Decimal("0.00")
        for p in payments:
            total_paid_dec += to_decimal(p.get("amount", 0))

        total_paid_float = float(total_paid_dec)
        total_price_dec = to_decimal(total_price)

        # Check if entire course is fully settled
        if total_paid_dec >= total_price_dec and total_price_dec > Decimal("0.00"):
            # Fully settled course
            await self.db.enrollments.update_one(
                {"$or": [{"id": enrollment_id}, {"enrollment_id": enrollment_id}]},
                {"$set": {
                    "payment_status": "COMPLETED",
                    "assessment_eligible": True,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            return {
                "enrolled": True,
                "course_price": total_price,
                "currency": currency,
                "duration_months": duration_months,
                "minimum_monthly_payment": monthly_min,
                "total_paid_all_time": total_paid_float,
                "current_period_start": None,
                "current_period_end": None,
                "amount_paid_current_period": monthly_min,
                "amount_required_current_period": monthly_min,
                "amount_remaining": 0.0,
                "payment_status": "COMPLETED",
                "general_learning_allowed": True,
                "assessment_eligible": True,
                "message": "Course fee completely settled. Assessment access is fully unlocked."
            }

        # Active period calculation
        active_period = await self.get_or_create_active_period(enrollment, course)
        period_start_str = active_period.get("period_start")
        period_end_str = active_period.get("period_end")

        # Sum qualifying payments that fell into this period
        period_paid_dec = Decimal("0.00")
        period_payment_ids = []
        for p in payments:
            p_date_str = p.get("payment_date") or p.get("created_at")
            if p_date_str:
                if period_start_str <= p_date_str <= period_end_str:
                    period_paid_dec += to_decimal(p.get("amount", 0))
                    period_payment_ids.append(p.get("id"))
            else:
                period_paid_dec += to_decimal(p.get("amount", 0))
                period_payment_ids.append(p.get("id"))

        required_monthly_dec = to_decimal(monthly_min)
        remaining_dec = max(Decimal("0.00"), required_monthly_dec - period_paid_dec)

        now = datetime.now(timezone.utc)
        period_end_dt = datetime.fromisoformat(period_end_str)
        if period_end_dt.tzinfo is None:
            period_end_dt = period_end_dt.replace(tzinfo=timezone.utc)

        is_past_due = now > period_end_dt
        is_near_due = (period_end_dt - now).days <= 5

        # Determine authoritative payment status
        if period_paid_dec >= required_monthly_dec:
            status = "CURRENT"
            assessment_eligible = True
            msg = "Monthly payment requirement met. Assessment access is available."
        elif period_paid_dec > Decimal("0.00"):
            status = "OVERDUE" if is_past_due else "PARTIALLY_PAID"
            assessment_eligible = False
            msg = f"Assessment access is currently locked because your required monthly payment is not up to date. You need ${float(remaining_dec):.2f} more to restore access."
        else:
            status = "OVERDUE" if is_past_due else ("PAYMENT_DUE" if is_near_due else "UNPAID")
            assessment_eligible = False
            msg = f"Assessment access is currently locked. Pay ${float(required_monthly_dec):.2f} to unlock assessments."

        # Sync period in database
        await self.db.payment_periods.update_one(
            {"id": active_period["id"]},
            {"$set": {
                "qualifying_amount": float(period_paid_dec),
                "required_amount": float(required_monthly_dec),
                "status": status,
                "payment_ids": period_payment_ids,
                "updated_at": now.isoformat()
            }}
        )

        # Sync enrollment in database
        await self.db.enrollments.update_one(
            {"$or": [{"id": enrollment_id}, {"enrollment_id": enrollment_id}]},
            {"$set": {
                "payment_status": status,
                "assessment_eligible": assessment_eligible,
                "updated_at": now.isoformat()
            }}
        )

        return {
            "enrolled": True,
            "course_price": total_price,
            "currency": currency,
            "duration_months": duration_months,
            "minimum_monthly_payment": monthly_min,
            "total_paid_all_time": total_paid_float,
            "current_period_start": period_start_str,
            "current_period_end": period_end_str,
            "amount_paid_current_period": float(period_paid_dec),
            "amount_required_current_period": float(required_monthly_dec),
            "amount_remaining": float(remaining_dec),
            "payment_status": status,
            "general_learning_allowed": True,  # Overdue never disables entire learning access
            "assessment_eligible": assessment_eligible,
            "message": msg
        }
