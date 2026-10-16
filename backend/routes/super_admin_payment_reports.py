"""Super Admin Course Payment Configuration & Multi-Channel Payment Reports for Cognify.

Features:
- Configures course pricing, duration in months, and automatic minimum monthly payment calculation.
- Generates detailed financial reports clearly distinguishing Online Gateway vs External/Manual (EcoCash, Cash, Bank Transfer).
- Tracks learners enrolled but not assessment-eligible, overdue learners, and partial payments.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from services.payment_period_engine import calculate_minimum_monthly_payment, to_decimal

logger = logging.getLogger(__name__)


class CoursePaymentConfigBody(BaseModel):
    price: float = Field(..., ge=0, description="Total course cost")
    currency: str = "USD"
    duration_months: int = Field(..., ge=1, le=48, description="Course duration in months")
    payment_required: bool = True
    category: Optional[str] = None


def make_super_admin_reports_router(db, require_super_admin):
    router = APIRouter(prefix="/super-admin", tags=["Super Admin Payment Config & Reports"])

    @router.put("/courses/{course_id}/payment-config")
    async def configure_course_payment(
        course_id: str,
        body: CoursePaymentConfigBody,
        _=Depends(require_super_admin)
    ):
        """Configure course payment settings and calculate monthly minimum."""
        course = await db.courses.find_one({"id": course_id})
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        monthly_min = calculate_minimum_monthly_payment(body.price, body.duration_months)

        update_fields = {
            "price": float(body.price),
            "total_price": float(body.price),
            "currency": body.currency.upper(),
            "duration_months": body.duration_months,
            "duration_weeks": body.duration_months * 4,
            "payment_required": body.payment_required,
            "is_paid": body.payment_required and body.price > 0,
            "minimum_monthly_payment": monthly_min,
            "payment_formula": f"{body.price:.2f} / {body.duration_months} months = {monthly_min:.2f}/mo",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        if body.category:
            update_fields["category"] = body.category

        await db.courses.update_one({"id": course_id}, {"$set": update_fields})
        updated = await db.courses.find_one({"id": course_id}, {"_id": 0})
        return {
            "success": True,
            "course_id": course_id,
            "course": updated,
            "calculated_minimum_monthly": monthly_min
        }

    @router.get("/reports/payments")
    @router.get("/payments/multi-channel-report")
    async def get_payment_reports(
        organisation_id: Optional[str] = None,
        course_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        _=Depends(require_super_admin)
    ):
        """Comprehensive reporting distinguishing Online Gateway vs External/Manual."""
        query: Dict[str, Any] = {}
        if organisation_id:
            query["organization_id"] = organisation_id
        if course_id:
            query["course_id"] = course_id
        if from_date or to_date:
            df = {}
            if from_date: df["$gte"] = from_date
            if to_date: df["$lte"] = to_date
            query["created_at"] = df

        # Fetch payments from payment_records and payment_transactions
        payments = await db.payment_records.find(query, {"_id": 0}).to_list(1000)

        # Totals by Channel / Source
        online_total = 0.0
        online_count = 0
        external_total = 0.0
        external_count = 0
        ecocash_total = 0.0
        ecocash_count = 0
        cash_total = 0.0
        bank_transfer_total = 0.0

        for p in payments:
            amt = float(p.get("amount", 0.0))
            src = p.get("source", "")
            method = (p.get("method") or "").lower()

            if src == "online_gateway":
                online_total += amt
                online_count += 1
            else:
                external_total += amt
                external_count += 1
                if method == "ecocash":
                    ecocash_total += amt
                    ecocash_count += 1
                elif method == "cash":
                    cash_total += amt
                elif method == "bank_transfer":
                    bank_transfer_total += amt

        # Enrolments & Assessment eligibility breakdown
        enr_query: Dict[str, Any] = {}
        if organisation_id: enr_query["organization_id"] = organisation_id
        if course_id: enr_query["course_id"] = course_id

        enrollments = await db.enrollments.find(enr_query, {"_id": 0}).to_list(2000)
        total_enrolled = len(enrollments)
        assessment_eligible_count = 0
        locked_count = 0
        partially_paid_count = 0
        overdue_count = 0
        completed_count = 0
        unpaid_count = 0

        for e in enrollments:
            st = e.get("payment_status", "UNPAID")
            if e.get("assessment_eligible"):
                assessment_eligible_count += 1
            else:
                locked_count += 1

            if st == "CURRENT": pass
            elif st == "PARTIALLY_PAID": partially_paid_count += 1
            elif st == "OVERDUE": overdue_count += 1
            elif st == "COMPLETED": completed_count += 1
            elif st == "UNPAID": unpaid_count += 1

        return {
            "summary": {
                "total_revenue": online_total + external_total,
                "online_revenue": online_total,
                "online_count": online_count,
                "external_revenue": external_total,
                "external_count": external_count,
                "ecocash_revenue": ecocash_total,
                "ecocash_count": ecocash_count,
                "cash_revenue": cash_total,
                "bank_transfer_revenue": bank_transfer_total,
            },
            "enrolments": {
                "total_enrolled": total_enrolled,
                "assessment_eligible": assessment_eligible_count,
                "assessment_locked": locked_count,
                "status_breakdown": {
                    "completed": completed_count,
                    "partially_paid": partially_paid_count,
                    "overdue": overdue_count,
                    "unpaid": unpaid_count,
                }
            },
            "recent_payments": payments[:50]
        }

    return router
