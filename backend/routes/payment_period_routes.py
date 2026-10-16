"""Learner Payment Status, Payment Periods, and History API for Cognify.

Exposes:
- GET /api/payment-status/{identifier}: Authoritative status for course or enrollment
- POST /api/payments/pay-period: Make online/direct payment for course period
- GET /api/payments/history/me: Full payment history with online vs external separation
"""
from __future__ import annotations
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from services.payment_period_engine import PaymentPeriodService, calculate_minimum_monthly_payment, to_decimal
from services.communication_service import NotificationService
from services.audit_service import AuditService

logger = logging.getLogger(__name__)


class PayPeriodBody(BaseModel):
    course_id: str
    amount: float
    method: str = "ecocash"  # ecocash, paynow, innbucks, mastercard, visa
    currency: str = "USD"
    phone_number: Optional[str] = None
    notes: Optional[str] = None


def make_payment_period_router(db, get_current_user):
    router = APIRouter(tags=["Payment Status & Periods"])
    period_svc = PaymentPeriodService(db)
    notification_svc = NotificationService(db)
    audit_svc = AuditService(db)

    @router.get("/courses/{course_id}/payment-breakdown")
    async def get_course_payment_breakdown_endpoint(course_id: str, current_user: dict = Depends(get_current_user)):
        """Calculate mandatory minimum monthly payment and breakdown for a course."""
        course = await db.courses.find_one({"id": course_id}, {"_id": 0})
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        total_price = float(to_decimal(course.get("price") or course.get("total_price", 0.0)))
        duration_months = int(course.get("duration_months") or max(1, int(course.get("duration_weeks", 4) / 4)))
        currency = course.get("currency", "USD")
        is_paid = course.get("is_paid", total_price > 0)
        payment_required = course.get("payment_required", is_paid and total_price > 0)

        min_monthly = calculate_minimum_monthly_payment(total_price, duration_months) if payment_required else 0.0

        return {
            "course_id": course_id,
            "course_name": course.get("name") or course.get("title"),
            "total_price": total_price,
            "currency": currency,
            "duration_months": duration_months,
            "minimum_monthly_payment": min_monthly,
            "is_paid": is_paid,
            "payment_required": payment_required,
            "formula": "TOTAL COURSE COST / DURATION IN MONTHS",
            "message": f"Mandatory minimum monthly payment is ${min_monthly:.2f} {currency}/month over {duration_months} month{'s' if duration_months > 1 else ''}." if min_monthly > 0 else "Free course. No payment required."
        }

    @router.get("/payment-status/{identifier}")
    async def get_payment_status(identifier: str, current_user: dict = Depends(get_current_user)):
        """Authoritative payment status by course_id or enrollment_id for current learner."""
        user_id = current_user["id"]

        # Check if identifier is enrollment_id
        enrollment = await db.enrollments.find_one({
            "$or": [{"id": identifier}, {"enrollment_id": identifier}]
        }, {"_id": 0})

        # If not, check if identifier is course_id
        if not enrollment:
            course = await db.courses.find_one({"id": identifier}, {"_id": 0})
            if not course:
                raise HTTPException(status_code=404, detail="Course or enrollment not found")

            enrollment = await db.enrollments.find_one({
                "$or": [
                    {"user_id": user_id, "course_id": identifier},
                    {"student_id": user_id, "course_id": identifier}
                ]
            }, {"_id": 0})

            if not enrollment:
                # Check student_profiles
                profile = await db.student_profiles.find_one({"user_id": user_id}, {"_id": 0})
                if profile and identifier in profile.get("enrolled_courses", []):
                    enrollment = {
                        "id": f"enr_{user_id}_{identifier}",
                        "user_id": user_id,
                        "course_id": identifier,
                        "organization_id": current_user.get("organization_id"),
                        "status": "active",
                        "enrolled_at": datetime.now(timezone.utc).isoformat()
                    }
                    await db.enrollments.update_one(
                        {"id": enrollment["id"]},
                        {"$setOnInsert": dict(enrollment)},
                        upsert=True
                    )

        if not enrollment:
            course = await db.courses.find_one({"id": identifier}, {"_id": 0})
            total_price = course.get("price") if course else 0.0
            duration_months = course.get("duration_months", 3) if course else 3
            return {
                "enrolled": False,
                "course_price": total_price,
                "currency": course.get("currency", "USD") if course else "USD",
                "duration_months": duration_months,
                "minimum_monthly_payment": calculate_minimum_monthly_payment(total_price, duration_months),
                "payment_status": "UNENROLLED",
                "assessment_eligible": False,
                "general_learning_allowed": False,
                "message": "Not enrolled in this course."
            }

        enr_id = enrollment.get("id") or enrollment.get("enrollment_id")
        status_data = await period_svc.recalculate_payment_status(enr_id)
        return status_data

    @router.post("/payments/pay-period")
    async def pay_period(body: PayPeriodBody, req: Request, current_user: dict = Depends(get_current_user)):
        """Record an online/learner-initiated payment towards course payment requirement."""
        user_id = current_user["id"]
        course_id = body.course_id

        course = await db.courses.find_one({"id": course_id}, {"_id": 0})
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        if body.amount <= 0:
            raise HTTPException(status_code=400, detail="Payment amount must be greater than zero")

        # Find or create enrollment
        enrollment = await db.enrollments.find_one({
            "$or": [
                {"user_id": user_id, "course_id": course_id},
                {"student_id": user_id, "course_id": course_id}
            ]
        }, {"_id": 0})

        now_iso = datetime.now(timezone.utc).isoformat()
        if not enrollment:
            enrollment_id = f"enr_{user_id}_{course_id}"
            enrollment = {
                "id": enrollment_id,
                "user_id": user_id,
                "student_id": user_id,
                "course_id": course_id,
                "organization_id": current_user.get("organization_id"),
                "status": "active",
                "enrolled_at": now_iso
            }
            await db.enrollments.insert_one(dict(enrollment))
            await db.student_profiles.update_one(
                {"user_id": user_id},
                {"$addToSet": {"enrolled_courses": course_id}},
                upsert=True
            )
            await db.courses.update_one(
                {"id": course_id},
                {"$addToSet": {"enrolled_students": user_id}}
            )

        enr_id = enrollment.get("id") or enrollment.get("enrollment_id")

        # Create Payment Record (Categorized as online gateway or learner mobile transaction)
        payment_id = str(uuid.uuid4())
        ref = f"COG-{uuid.uuid4().hex[:8].upper()}"

        payment_doc = {
            "id": payment_id,
            "user_id": user_id,
            "course_id": course_id,
            "enrollment_id": enr_id,
            "organization_id": current_user.get("organization_id"),
            "amount": float(body.amount),
            "currency": body.currency,
            "method": body.method.lower(),
            "source": "online_gateway" if body.method.lower() in ["stripe", "paynow", "card"] else "mobile_payment",
            "status": "completed",
            "payment_date": now_iso,
            "reference": ref,
            "phone_number": body.phone_number or current_user.get("phone_number"),
            "created_by": user_id,
            "notes": body.notes,
            "created_at": now_iso
        }

        await db.payment_records.insert_one(payment_doc)
        # Also sync to payment_transactions for Super Admin console
        await db.payment_transactions.insert_one(dict(payment_doc))

        # Recalculate status
        updated_status = await period_svc.recalculate_payment_status(enr_id)

        # Audit log
        await audit_svc.log(
            actor_id=user_id,
            action="payment.learner_pay",
            entity="payment",
            entity_id=payment_id,
            organisation_id=current_user.get("organization_id"),
            new_value={"amount": body.amount, "method": body.method, "status": "completed"},
            ip_address=req.client.host if req.client else None
        )

        # Notify learner
        if updated_status["assessment_eligible"]:
            event = "assessment_restored"
        elif updated_status["payment_status"] == "PARTIALLY_PAID":
            event = "partial_payment"
        else:
            event = "payment_confirmation"

        await notification_svc.notify_user(
            recipient_phone=payment_doc.get("phone_number"),
            recipient_email=current_user.get("email"),
            event=event,
            user_id=user_id,
            amount=body.amount,
            remaining=updated_status.get("amount_remaining", 0.0),
            course_name=course.get("name") or course.get("title")
        )

        return {
            "success": True,
            "payment_id": payment_id,
            "reference": ref,
            "amount": body.amount,
            "status": "completed",
            "payment_status": updated_status["payment_status"],
            "assessment_eligible": updated_status["assessment_eligible"],
            "amount_remaining": updated_status["amount_remaining"],
            "message": updated_status["message"]
        }

    @router.get("/payments/history/me")
    async def get_my_payment_history(current_user: dict = Depends(get_current_user)):
        """All payments made by or for current learner with source & method distinction."""
        user_id = current_user["id"]
        cursor = db.payment_records.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("created_at", -1)
        records = await cursor.to_list(200)

        # Enrich with course titles
        for r in records:
            if "course_title" not in r and r.get("course_id"):
                c = await db.courses.find_one({"id": r["course_id"]}, {"_id": 0, "name": 1, "title": 1})
                if c:
                    r["course_title"] = c.get("name") or c.get("title")

        return {"payments": records}

    return router
