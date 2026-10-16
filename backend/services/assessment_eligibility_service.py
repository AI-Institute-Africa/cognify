"""Assessment Eligibility Service for Cognify.

Centralized authorization function for all assignment and examination APIs.
Evaluates:
- Authenticated user
- Active course enrolment
- Organisation-level scope matching
- Central payment-status verification (CURRENT, COMPLETED, or free course)
- Academic eligibility
"""
from __future__ import annotations
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException
from services.payment_period_engine import PaymentPeriodService

logger = logging.getLogger(__name__)


async def check_assessment_eligibility(
    db,
    user: dict,
    course_id: str,
    enrollment: Optional[dict] = None
) -> dict:
    """Evaluate whether user can view or submit assignments/examinations.
    
    Returns dict:
    {
        "eligible": bool,
        "role_bypass": bool,
        "payment_status": str,
        "amount_remaining": float,
        "message": str
    }
    Raises HTTPException(403) with descriptive details if ineligible.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    role = user.get("role", "")
    user_id = user.get("id")

    # Staff roles have administrative preview access
    if role in ["admin", "super_admin"]:
        return {
            "eligible": True,
            "role_bypass": True,
            "payment_status": "CURRENT",
            "amount_remaining": 0.0,
            "message": "Administrative access granted"
        }

    # Fetch course
    course = await db.courses.find_one({"id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Teachers assigned to this course or in the course's org have access
    if role == "teacher":
        if course.get("teacher_id") == user_id or (course.get("organization_id") and course.get("organization_id") == user.get("organization_id")):
            return {
                "eligible": True,
                "role_bypass": True,
                "payment_status": "CURRENT",
                "amount_remaining": 0.0,
                "message": "Instructor access granted"
            }

    # Check organisation isolation
    course_org = course.get("organization_id")
    user_org = user.get("organization_id")
    if course_org and user_org and course_org != user_org and role != "super_admin":
        raise HTTPException(
            status_code=403,
            detail="You do not belong to the organisation providing this course."
        )

    # Find enrollment
    if not enrollment:
        enrollment = await db.enrollments.find_one({
            "$or": [
                {"user_id": user_id, "course_id": course_id},
                {"student_id": user_id, "course_id": course_id}
            ]
        }, {"_id": 0})

    # If no record in db.enrollments, check student profile
    if not enrollment:
        profile = await db.student_profiles.find_one({"user_id": user_id}, {"_id": 0})
        if profile and course_id in profile.get("enrolled_courses", []):
            enrollment = {
                "id": f"enr_{user_id}_{course_id}",
                "user_id": user_id,
                "course_id": course_id,
                "organization_id": user.get("organization_id"),
                "status": "active",
                "enrolled_at": profile.get("created_at")
            }
            # Persist into enrollments collection for consistent tracking
            await db.enrollments.update_one(
                {"id": enrollment["id"]},
                {"$setOnInsert": dict(enrollment)},
                upsert=True
            )

    if not enrollment:
        raise HTTPException(
            status_code=403,
            detail="You are not enrolled in this course."
        )

    # Check if course is free
    total_price = course.get("price") or course.get("total_price", 0.0)
    is_paid = course.get("is_paid", total_price > 0)
    payment_required = course.get("payment_required", is_paid and total_price > 0)

    if not payment_required or total_price <= 0:
        return {
            "eligible": True,
            "role_bypass": False,
            "payment_status": "COMPLETED",
            "amount_remaining": 0.0,
            "message": "Free course: assessment access granted"
        }

    # Authoritative calculation via PaymentPeriodService
    svc = PaymentPeriodService(db)
    enr_id = enrollment.get("id") or enrollment.get("enrollment_id")
    calc = await svc.recalculate_payment_status(enr_id)

    if not calc["assessment_eligible"]:
        remaining = calc["amount_remaining"]
        err_msg = (
            f"Assessment access is currently locked because your required monthly payment "
            f"is not up to date. You need ${remaining:.2f} more to restore access."
        )
        raise HTTPException(
            status_code=403,
            detail={
                "code": "ASSESSMENT_PAYMENT_RESTRICTION",
                "assessment_eligible": False,
                "message": err_msg,
                "amount_remaining": remaining,

                "required_amount": calc["amount_required_current_period"],
                "payment_status": calc["payment_status"],
                "course_id": course_id,
                "enrollment_id": enr_id
            }
        )

    return {
        "eligible": True,
        "role_bypass": False,
        "payment_status": calc["payment_status"],
        "amount_remaining": 0.0,
        "message": "Payment status qualifying: assessment access unlocked"
    }
