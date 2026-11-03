"""
Billing API Routes for Cognify Learning Platform
Exposes entitlements, course completion, and billing integration endpoints.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

try:
    from auth_utils import get_current_user
except ImportError:
    from backend.auth_utils import get_current_user

try:
    from services.billing_service import BillingService
except ImportError:
    from backend.services.billing_service import BillingService

logger = logging.getLogger(__name__)


def make_billing_router(db):
    router = APIRouter(tags=["Billing & Entitlements"])
    billing_svc = BillingService(db)

    @router.get("/api/entitlements/me")
    @router.get("/entitlements/me")
    @router.get("/api/billing/entitlements")
    async def get_my_entitlements(current_user: dict = Depends(get_current_user)):
        """
        Fetch the current student's live balance, free allowances, and active course allocations.
        """
        user_id = current_user["id"]
        # Fetch fresh user record from DB
        user_doc = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
        if not user_doc:
            user_doc = current_user

        token = await billing_svc.get_or_create_billing_token(user_doc)
        if not token:
            raise HTTPException(status_code=502, detail="Failed to initialize billing account")

        entitlements = await billing_svc.get_entitlements(token)
        return {
            **entitlements,
            "billing_access_token": token,
            "user_id": user_id,
        }

    @router.post("/api/courses/{course_id}/complete")
    @router.post("/courses/{course_id}/complete")
    async def complete_course(
        course_id: str,
        student_id: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """
        Mark a course completed for a student and trigger token recycling
        back to the Central Token Bank for any unconsumed tokens.
        """
        target_student_id = student_id or current_user["id"]
        # If completing on behalf of someone else, require teacher or admin
        if target_student_id != current_user["id"] and current_user.get("role") not in ["teacher", "admin", "super_admin", "org_admin"]:
            raise HTTPException(status_code=403, detail="Permission denied")

        student = await db.users.find_one({"id": target_student_id}, {"_id": 0, "password_hash": 0})
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        course = await db.courses.find_one({"id": course_id}, {"_id": 0})
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        # Find or create enrollment
        enrollment = await db.enrollments.find_one({
            "$or": [
                {"user_id": target_student_id, "course_id": course_id},
                {"student_id": target_student_id, "course_id": course_id},
            ]
        }, {"_id": 0})

        enrollment_id = enrollment.get("id") or enrollment.get("enrollment_id") if enrollment else f"enr-{target_student_id[:8]}-{course_id[:8]}"

        # Mark enrollment completed in MongoDB
        now_iso = datetime.now(timezone.utc).isoformat()
        await db.enrollments.update_many(
            {
                "$or": [
                    {"user_id": target_student_id, "course_id": course_id},
                    {"student_id": target_student_id, "course_id": course_id},
                ]
            },
            {"$set": {"status": "completed", "completed_at": now_iso}}
        )

        # Update student profile
        await db.student_profiles.update_one(
            {"user_id": target_student_id},
            {"$addToSet": {"completed_courses": course_id}},
            upsert=True
        )

        # Notify billing system to recycle unconsumed tokens back to Central Token Bank
        user_email = student.get("email") or f"user_{target_student_id}@cognify.africa"
        completion_event_id = f"compl-{enrollment_id}-{int(datetime.now(timezone.utc).timestamp())}"

        recycle_res = await billing_svc.sync_course_completion(
            enrollment_id=enrollment_id,
            user_email=user_email,
            completion_event_id=completion_event_id,
        )

        return {
            "message": "Course marked completed successfully",
            "course_id": course_id,
            "enrollment_id": enrollment_id,
            "completion_event_id": completion_event_id,
            "tokens_recycled_minor": recycle_res.get("released_minor", 0),
            "billing_result": recycle_res,
        }

    return router
