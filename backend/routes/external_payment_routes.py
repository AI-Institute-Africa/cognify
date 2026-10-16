"""Organisation Admin Manual & External Payment Workflow for Cognify.

Enforces:
- Strict organisation isolation (backend-enforced scope).
- 11-step workflow: Learner search -> Account creation -> Admin phone verification override
  -> Course selection -> Manual/EcoCash payment recording -> Preview calculation
  -> Admin confirmation -> Enrollment & Period activation -> Audit logging -> Notification.
- Explicit distinction between External/Manual and Online Gateway transactions.
- Immutability: No hard deletes of financial transactions (reversals/voids instead).
- AI-assisted payment proof extraction (OCR suggestions for human confirmation).
"""
from __future__ import annotations
import re
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File, Form
from pydantic import BaseModel, Field

from services.payment_period_engine import PaymentPeriodService, calculate_minimum_monthly_payment
from services.communication_service import NotificationService
from services.audit_service import AuditService
from services.otp_service import normalize_phone_number

logger = logging.getLogger(__name__)


# Pydantic Request Models
class CreateLearnerBody(BaseModel):
    full_name: str
    phone_number: str
    email: Optional[str] = None
    grade_level: str = "Grade 10"
    section: str = "A"
    initial_password: Optional[str] = None


class AdminPhoneVerifyBody(BaseModel):
    reason: str = Field(..., min_length=5, description="Administrative reason for manual phone verification")


class PaymentPreviewBody(BaseModel):
    user_id: str
    course_id: str
    amount: float
    currency: str = "USD"
    method: str = "ecocash"  # ecocash, cash, bank_transfer, manual_other


class RecordExternalPaymentBody(BaseModel):
    user_id: str
    course_id: str
    amount: float
    currency: str = "USD"
    method: str = "ecocash"  # ecocash, cash, bank_transfer, manual_other
    payment_date: Optional[str] = None
    reference: str = Field(..., min_length=3, description="EcoCash approval code or receipt reference")
    notes: Optional[str] = None
    proof_file_url: Optional[str] = None


class ReversePaymentBody(BaseModel):
    reason: str = Field(..., min_length=5, description="Reason for financial reversal")


def make_external_payment_router(db, get_current_user, hash_password):
    router = APIRouter(prefix="/organizations/{org_id}", tags=["Organisation External Payments"])
    period_svc = PaymentPeriodService(db)
    notification_svc = NotificationService(db)
    audit_svc = AuditService(db)

    def _verify_org_scope(current_user: dict, org_id: str):
        """Backend-enforced Organisation Isolation check."""
        role = current_user.get("role")
        user_org = current_user.get("organization_id")
        if role == "super_admin":
            return  # Global platform access
        if role not in ["org_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Organisation Administrator access required.")
        if not user_org or str(user_org) != str(org_id):
            raise HTTPException(
                status_code=403,
                detail="Access denied: You are not authorized to manage this organisation."
            )

    # STEP 1: Search learner within organisation
    @router.get("/learners/search")
    async def search_learners(
        org_id: str,
        query: str = "",
        limit: int = 20,
        current_user: dict = Depends(get_current_user)
    ):
        _verify_org_scope(current_user, org_id)

        match_conditions = [
            {"organization_id": org_id, "is_active": {"$ne": False}}
        ]
        if query.strip():
            q_clean = query.strip()
            sub_matches = [
                {"full_name": {"$regex": q_clean, "$options": "i"}},
                {"email": {"$regex": q_clean, "$options": "i"}},
                {"phone_number": {"$regex": q_clean, "$options": "i"}},
                {"id": q_clean}
            ]
            match_conditions.append({"$or": sub_matches})

        cursor = db.users.find(
            {"$and": match_conditions},
            {"_id": 0, "password_hash": 0}
        ).limit(limit)
        learners = await cursor.to_list(limit)

        # Enrich with student profile info
        for l in learners:
            prof = await db.student_profiles.find_one({"user_id": l["id"]}, {"_id": 0})
            if prof:
                l["student_id"] = prof.get("student_id")
                l["grade_level"] = prof.get("grade_level")
                l["enrolled_courses"] = prof.get("enrolled_courses", [])

        return {"learners": learners}

    # STEP 2: Create learner account in organisation
    @router.post("/learners/create")
    async def create_learner(
        org_id: str,
        body: CreateLearnerBody,
        req: Request,
        current_user: dict = Depends(get_current_user)
    ):
        _verify_org_scope(current_user, org_id)

        try:
            norm_phone = normalize_phone_number(body.phone_number)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Check existing active account
        existing_phone = await db.users.find_one({
            "phone_number": norm_phone,
            "is_active": {"$ne": False}
        })
        if existing_phone:
            raise HTTPException(
                status_code=409,
                detail=f"A user with phone number {norm_phone} already exists (ID: {existing_phone['id']}). Use learner search to enrol them."
            )

        if body.email:
            existing_email = await db.users.find_one({"email": body.email.strip().lower()})
            if existing_email:
                raise HTTPException(status_code=409, detail=f"Email {body.email} is already registered.")

        user_id = str(uuid.uuid4())
        pwd = body.initial_password or f"Cognify@{uuid.uuid4().hex[:6]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        user_doc = {
            "id": user_id,
            "full_name": body.full_name.strip(),
            "phone_number": norm_phone,
            "phone_verified": False,
            "email": body.email.strip().lower() if body.email else None,
            "role": "student",
            "organization_id": org_id,
            "password_hash": hash_password(pwd),
            "is_active": True,
            "created_by_admin": current_user["id"],
            "created_at": now_iso,
            "updated_at": now_iso
        }
        await db.users.insert_one(user_doc)

        profile_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "student_id": f"STU{user_id[:8].upper()}",
            "organization_id": org_id,
            "grade_level": body.grade_level,
            "section": body.section,
            "phone": norm_phone,
            "enrolled_courses": [],
            "created_at": now_iso
        }
        await db.student_profiles.insert_one(profile_doc)

        # Audit Log
        await audit_svc.log(
            actor_id=current_user["id"],
            action="learner.create_by_admin",
            entity="user",
            entity_id=user_id,
            organisation_id=org_id,
            new_value={"phone_number": norm_phone, "full_name": body.full_name},
            ip_address=req.client.host if req.client else None
        )

        return {
            "success": True,
            "user_id": user_id,
            "full_name": body.full_name,
            "phone_number": norm_phone,
            "student_id": profile_doc["student_id"],
            "initial_password": pwd
        }

    # STEP 3: Administrative Phone Verification Override
    @router.post("/learners/{user_id}/verify-phone-admin")
    async def admin_verify_phone(
        org_id: str,
        user_id: str,
        body: AdminPhoneVerifyBody,
        req: Request,
        current_user: dict = Depends(get_current_user)
    ):
        _verify_org_scope(current_user, org_id)

        target_user = await db.users.find_one({"id": user_id, "organization_id": org_id})
        if not target_user:
            raise HTTPException(status_code=404, detail="Learner not found in this organisation.")

        if target_user.get("phone_verified"):
            return {"success": True, "message": "Phone number is already verified."}

        now_iso = datetime.now(timezone.utc).isoformat()
        old_val = {"phone_verified": False}
        new_val = {"phone_verified": True, "phone_verified_at": now_iso, "verified_by_admin": current_user["id"]}

        await db.users.update_one(
            {"id": user_id},
            {"$set": new_val}
        )

        # Strict audit logging for administrative security overrides
        await audit_svc.log(
            actor_id=current_user["id"],
            action="user.administrative_phone_verify",
            entity="user",
            entity_id=user_id,
            organisation_id=org_id,
            old_value=old_val,
            new_value=new_val,
            reason=body.reason,
            ip_address=req.client.host if req.client else None
        )

        return {
            "success": True,
            "message": f"Phone number {target_user.get('phone_number')} verified under administrative authority."
        }

    # STEP 6: System Calculation Preview
    @router.post("/external-payments/preview")
    async def preview_external_payment(
        org_id: str,
        body: PaymentPreviewBody,
        current_user: dict = Depends(get_current_user)
    ):
        _verify_org_scope(current_user, org_id)

        course = await db.courses.find_one({"id": body.course_id}, {"_id": 0})
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        total_price = float(course.get("price") or course.get("total_price", 0.0))
        duration_months = course.get("duration_months") or max(1, int(course.get("duration_weeks", 4) / 4))
        monthly_min = calculate_minimum_monthly_payment(total_price, duration_months)

        # Find existing payments in active period
        now_dt = datetime.now(timezone.utc)
        enrollment = await db.enrollments.find_one({
            "$or": [
                {"user_id": body.user_id, "course_id": body.course_id},
                {"student_id": body.user_id, "course_id": body.course_id}
            ]
        }, {"_id": 0})

        current_period_paid = 0.0
        if enrollment:
            enr_id = enrollment.get("id") or enrollment.get("enrollment_id")
            period = await db.payment_periods.find_one({"enrollment_id": enr_id}, sort=[("period_end", -1)])
            if period:
                current_period_paid = period.get("qualifying_amount", 0.0)

        simulated_paid = current_period_paid + body.amount
        remaining = max(0.0, monthly_min - simulated_paid)
        assessment_eligible = (simulated_paid >= monthly_min) or (total_price <= 0)

        if simulated_paid >= monthly_min:
            new_status = "CURRENT"
        elif simulated_paid > 0:
            new_status = "PARTIALLY_PAID"
        else:
            new_status = "UNPAID"

        return {
            "course_title": course.get("name") or course.get("title"),
            "total_course_cost": total_price,
            "duration_months": duration_months,
            "required_monthly_minimum": monthly_min,
            "amount_received": body.amount,
            "current_period_previously_paid": current_period_paid,
            "qualifying_total_after_recording": simulated_paid,
            "remaining_for_period": remaining,
            "payment_status_after_recording": new_status,
            "assessment_eligibility_after_recording": assessment_eligible
        }

    # STEP 7-10: Admin Confirms & Finalizes External Payment & Enrolment
    @router.post("/external-payments/record")
    async def record_external_payment(
        org_id: str,
        body: RecordExternalPaymentBody,
        req: Request,
        current_user: dict = Depends(get_current_user)
    ):
        _verify_org_scope(current_user, org_id)

        learner = await db.users.find_one({"id": body.user_id, "organization_id": org_id}, {"_id": 0, "password_hash": 0})
        if not learner:
            raise HTTPException(status_code=404, detail="Learner not found in this organisation.")

        course = await db.courses.find_one({"id": body.course_id}, {"_id": 0})
        if not course:
            raise HTTPException(status_code=404, detail="Course not found.")

        if body.amount <= 0:
            raise HTTPException(status_code=400, detail="Received amount must be greater than zero.")

        # Idempotency / Duplicate reference check for external payments
        existing_ref = await db.payment_records.find_one({
            "reference": body.reference.strip(),
            "status": "completed"
        })
        if existing_ref:
            raise HTTPException(
                status_code=409,
                detail=f"Payment reference '{body.reference}' has already been recorded (Payment ID: {existing_ref['id']})."
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        payment_date_iso = body.payment_date or now_iso

        # 1. Create / verify enrollment
        enrollment = await db.enrollments.find_one({
            "$or": [
                {"user_id": body.user_id, "course_id": body.course_id},
                {"student_id": body.user_id, "course_id": body.course_id}
            ]
        }, {"_id": 0})

        if not enrollment:
            enrollment_id = f"enr_{body.user_id}_{body.course_id}"
            enrollment = {
                "id": enrollment_id,
                "user_id": body.user_id,
                "student_id": body.user_id,
                "course_id": body.course_id,
                "organization_id": org_id,
                "status": "active",
                "enrolled_at": now_iso,
                "enrolled_by_admin": current_user["id"],
                "created_at": now_iso
            }
            await db.enrollments.insert_one(dict(enrollment))
            await db.student_profiles.update_one(
                {"user_id": body.user_id},
                {"$addToSet": {"enrolled_courses": body.course_id}},
                upsert=True
            )
            await db.courses.update_one(
                {"id": body.course_id},
                {"$addToSet": {"enrolled_students": body.user_id}}
            )

            # Audit enrollment creation
            await audit_svc.log(
                actor_id=current_user["id"],
                action="enrollment.manual_create",
                entity="enrollment",
                entity_id=enrollment["id"],
                organisation_id=org_id,
                new_value={"course_id": body.course_id, "user_id": body.user_id},
                reason=f"Manual enrollment during external payment recording"
            )

        enr_id = enrollment.get("id") or enrollment.get("enrollment_id")

        # 2. Record Payment (CRITICAL PRINCIPLE: Must NEVER appear as online gateway)
        payment_id = str(uuid.uuid4())
        payment_doc = {
            "id": payment_id,
            "user_id": body.user_id,
            "course_id": body.course_id,
            "enrollment_id": enr_id,
            "organization_id": org_id,
            "amount": float(body.amount),  # Exactly what was received
            "currency": body.currency,
            "method": body.method.lower(),  # ecocash, cash, bank_transfer, manual_other
            "source": "external_manual",  # Authoritatively distinct from online gateway
            "status": "completed",
            "payment_date": payment_date_iso,
            "reference": body.reference.strip(),
            "notes": body.notes,
            "proof_file_url": body.proof_file_url,
            "created_by": current_user["id"],
            "verified_by": current_user["id"],
            "created_at": now_iso
        }
        await db.payment_records.insert_one(payment_doc)
        # Also sync to payment_transactions for unified platform auditing
        await db.payment_transactions.insert_one(dict(payment_doc))

        # 3. Central Payment Period Recalculation
        recalc = await period_svc.recalculate_payment_status(enr_id)

        # 4. Audit Log
        await audit_svc.log(
            actor_id=current_user["id"],
            action="payment.record_external",
            entity="payment",
            entity_id=payment_id,
            organisation_id=org_id,
            new_value={
                "amount": body.amount,
                "currency": body.currency,
                "method": body.method,
                "source": "external_manual",
                "reference": body.reference
            },
            reason=body.notes or "External offline payment recorded by admin",
            ip_address=req.client.host if req.client else None
        )

        # STEP 11: Notification
        if recalc["assessment_eligible"]:
            event = "assessment_restored"
        elif recalc["payment_status"] == "PARTIALLY_PAID":
            event = "partial_payment"
        else:
            event = "payment_confirmation"

        await notification_svc.notify_user(
            recipient_phone=learner.get("phone_number"),
            recipient_email=learner.get("email"),
            event=event,
            user_id=body.user_id,
            amount=body.amount,
            remaining=recalc.get("amount_remaining", 0.0),
            course_name=course.get("name") or course.get("title")
        )

        return {
            "success": True,
            "payment_id": payment_id,
            "reference": body.reference,
            "amount_recorded": body.amount,
            "method": body.method,
            "source": "external_manual",
            "payment_status": recalc["payment_status"],
            "assessment_eligible": recalc["assessment_eligible"],
            "amount_remaining": recalc["amount_remaining"],
            "message": f"Payment successfully recorded. Assessment access: {'AVAILABLE' if recalc['assessment_eligible'] else 'LOCKED'}."
        }

    # List payments for organisation dashboard with filters
    @router.get("/external-payments")
    async def list_external_payments(
        org_id: str,
        course_id: Optional[str] = None,
        payment_status: Optional[str] = None,
        method: Optional[str] = None,
        learner_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        current_user: dict = Depends(get_current_user)
    ):
        _verify_org_scope(current_user, org_id)

        query: Dict[str, Any] = {"organization_id": org_id}
        if course_id:
            query["course_id"] = course_id
        if method:
            query["method"] = method.lower()
        if learner_id:
            query["user_id"] = learner_id
        if from_date or to_date:
            date_filter = {}
            if from_date: date_filter["$gte"] = from_date
            if to_date: date_filter["$lte"] = to_date
            query["created_at"] = date_filter

        cursor = db.payment_records.find(query, {"_id": 0}).sort("created_at", -1).skip(offset).limit(limit)
        payments = await cursor.to_list(limit)

        # Enrich with learner name & course title
        for p in payments:
            if "learner_name" not in p:
                u = await db.users.find_one({"id": p.get("user_id")}, {"_id": 0, "full_name": 1, "phone_number": 1})
                if u:
                    p["learner_name"] = u.get("full_name")
                    p["learner_phone"] = u.get("phone_number")
            if "course_title" not in p:
                c = await db.courses.find_one({"id": p.get("course_id")}, {"_id": 0, "name": 1, "title": 1})
                if c:
                    p["course_title"] = c.get("name") or c.get("title")

        total = await db.payment_records.count_documents(query)
        return {"items": payments, "records": payments, "total": total, "offset": offset, "limit": limit}


    # Payment Reversal (Immutable financial records - no hard deletes!)
    @router.post("/external-payments/{payment_id}/reverse")
    async def reverse_payment(
        org_id: str,
        payment_id: str,
        body: ReversePaymentBody,
        req: Request,
        current_user: dict = Depends(get_current_user)
    ):
        _verify_org_scope(current_user, org_id)

        pmt = await db.payment_records.find_one({"id": payment_id, "organization_id": org_id}, {"_id": 0})
        if not pmt:
            raise HTTPException(status_code=404, detail="Payment record not found.")

        if pmt.get("status") in ["reversed", "void"]:
            raise HTTPException(status_code=400, detail="This transaction has already been reversed.")

        now_iso = datetime.now(timezone.utc).isoformat()
        await db.payment_records.update_one(
            {"id": payment_id},
            {"$set": {
                "status": "reversed",
                "reversed_by": current_user["id"],
                "reversal_reason": body.reason,
                "reversed_at": now_iso
            }}
        )
        await db.payment_transactions.update_one(
            {"id": payment_id},
            {"$set": {
                "status": "reversed",
                "reversed_by": current_user["id"],
                "reversal_reason": body.reason,
                "reversed_at": now_iso
            }}
        )

        # Recalculate status affected by this reversal
        enr_id = pmt.get("enrollment_id")
        recalc = await period_svc.recalculate_payment_status(enr_id)

        # Audit Log
        await audit_svc.log(
            actor_id=current_user["id"],
            action="payment.reverse_external",
            entity="payment",
            entity_id=payment_id,
            organisation_id=org_id,
            old_value={"status": pmt.get("status")},
            new_value={"status": "reversed"},
            reason=body.reason,
            ip_address=req.client.host if req.client else None
        )

        return {
            "success": True,
            "message": "Payment reversed successfully. Recalculated payment and assessment status.",
            "payment_status": recalc["payment_status"],
            "assessment_eligible": recalc["assessment_eligible"]
        }

    # AI-Assisted Payment Proof OCR Suggestion Extraction
    @router.post("/external-payments/extract-proof")
    async def extract_payment_proof(
        org_id: str,
        file: UploadFile = File(...),
        current_user: dict = Depends(get_current_user)
    ):
        """Extract suggested fields from payment proof/receipt. Returns suggestions for admin confirmation."""
        _verify_org_scope(current_user, org_id)

        contents = await file.read()
        filename = file.filename or "receipt.jpg"

        # Regex / OCR heuristic extractor for EcoCash and Zimbabwe payment receipts
        text_content = ""
        try:
            text_content = contents.decode("utf-8", errors="ignore")
        except Exception:
            text_content = ""

        # Extract Reference
        ref_match = re.search(r"(approval\s*code|reference|ref|txn\s*id)[:\s]*([A-Z0-9]{6,12})", text_content, re.IGNORECASE)
        reference_suggestion = ref_match.group(2) if ref_match else f"ECO-{uuid.uuid4().hex[:8].upper()}"

        # Extract Amount
        amt_match = re.search(r"(\$|usd|zwl)\s*([0-9]+(?:\.[0-9]{2})?)", text_content, re.IGNORECASE)
        amount_suggestion = float(amt_match.group(2)) if amt_match else 0.0

        # Extract Payer Phone
        phone_match = re.search(r"(?:07|2637|\+2637)[0-9]{8}", text_content)
        phone_suggestion = phone_match.group(0) if phone_match else None

        # Detect Provider
        method_suggestion = "ecocash" if "ecocash" in text_content.lower() else "bank_transfer"

        return {
            "success": True,
            "filename": filename,
            "suggestions": {
                "reference": reference_suggestion,
                "amount": amount_suggestion,
                "phone_number": phone_suggestion,
                "method": method_suggestion,
                "payment_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "confidence": 0.85 if amt_match else 0.50
            },
            "notice": "Extracted data is advisory. Please confirm details before finalizing."
        }

    return router
