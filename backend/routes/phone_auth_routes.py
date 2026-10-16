"""Phone Authentication & OTP Verification Routes for Cognify.

Provides:
- Phone number registration alongside preserved email registration
- Secure OTP request, generation, rate limiting, and verification
- Phone-based login with password or OTP
- Phone addition & verification for existing users (backward compatibility)
- Duplicate phone registration prevention
"""
from __future__ import annotations
import os
import uuid
import logging

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from services.otp_service import OTPService, normalize_phone_number
from services.communication_service import NotificationService
from services.audit_service import AuditService

logger = logging.getLogger(__name__)


class RequestOTPBody(BaseModel):
    phone_number: str
    channel: Optional[str] = "sms"
    purpose: str = "registration"


class VerifyOTPBody(BaseModel):
    phone_number: str
    otp_code: str
    purpose: str = "registration"


class PhoneRegisterBody(BaseModel):
    phone_number: str
    otp_code: str
    password: str
    full_name: str
    email: Optional[str] = None
    role: str = "student"
    organization_id: Optional[str] = None
    preferred_contact_method: str = "sms"  # sms, whatsapp, email


class PhoneLoginBody(BaseModel):
    phone_number: Optional[str] = None
    identifier: Optional[str] = None
    password: Optional[str] = None
    otp_code: Optional[str] = None


def make_phone_auth_router(db, get_current_user, hash_password, verify_password, create_token):
    router = APIRouter(prefix="/auth/phone", tags=["Phone Authentication"])
    otp_service = OTPService(db)
    notification_service = NotificationService(db)
    audit_service = AuditService(db)

    @router.post("/request-otp")
    async def request_otp(body: RequestOTPBody):
        """Generate and dispatch secure OTP to user's phone via SMS/WhatsApp."""
        try:
            norm_phone = normalize_phone_number(body.phone_number)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # If registration, check if active verified account already exists
        if body.purpose == "registration":
            existing = await db.users.find_one({
                "phone_number": norm_phone,
                "is_active": {"$ne": False},
                "phone_verified": True
            }, {"_id": 0, "id": 1})
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail="An account with this phone number already exists. Please log in or recover your account."
                )

        code, meta = await otp_service.generate_and_store_otp(norm_phone, purpose=body.purpose)

        # Dispatch via Notification Service (Prioritize SMS as requested)
        notify_res = await notification_service.notify_user(
            recipient_phone=norm_phone,
            event="registration_otp",
            channels=["sms", "whatsapp"],
            code=code
        )

        wa_link = None
        if isinstance(notify_res, dict) and notify_res.get("whatsapp") and notify_res["whatsapp"].get("link"):
            wa_link = notify_res["whatsapp"]["link"]

        return {
            "success": True,
            "message": f"Verification code sent to {norm_phone}",
            "expires_in_seconds": meta["expires_in_seconds"],
            "resend_in_seconds": meta["resend_in_seconds"],
            # Provide simulator code in dev/test when third-party provider not configured
            "dev_simulator_code": code if not os.environ.get("TWILIO_ACCOUNT_SID") else None,
            "whatsapp_link": wa_link
        }

    @router.post("/verify-otp")
    async def verify_otp_endpoint(body: VerifyOTPBody):
        """Verify OTP validity without registering."""
        try:
            norm_phone = normalize_phone_number(body.phone_number)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        verified = await otp_service.verify_otp(norm_phone, body.otp_code, purpose=body.purpose)
        return {"success": verified, "message": "Phone number verified successfully"}

    @router.post("/register")
    async def register_with_phone(body: PhoneRegisterBody, req: Request):
        """Create a new Cognify account using verified phone number."""
        try:
            norm_phone = normalize_phone_number(body.phone_number)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Check unique constraint on verified phone
        existing_phone = await db.users.find_one({
            "phone_number": norm_phone,
            "is_active": {"$ne": False},
            "phone_verified": True
        })
        if existing_phone:
            raise HTTPException(
                status_code=409,
                detail="An account with this phone number already exists. Please log in."
            )

        # If email was provided, check email uniqueness too
        if body.email:
            existing_email = await db.users.find_one({"email": body.email.strip().lower()})
            if existing_email:
                raise HTTPException(status_code=400, detail="Email is already registered to another account")

        # Verify OTP
        await otp_service.verify_otp(norm_phone, body.otp_code, purpose="registration")

        now_iso = datetime.now(timezone.utc).isoformat()
        user_id = str(uuid.uuid4())

        user_doc = {
            "id": user_id,
            "phone_number": norm_phone,
            "phone_verified": True,
            "phone_verified_at": now_iso,
            "preferred_contact_method": body.preferred_contact_method,
            "email": body.email.strip().lower() if body.email else None,
            "full_name": body.full_name.strip(),
            "role": body.role if body.role in ["student", "teacher", "parent"] else "student",
            "organization_id": body.organization_id,
            "password_hash": hash_password(body.password),
            "is_active": True,
            "registration_source": "phone_otp",
            "created_at": now_iso,
            "updated_at": now_iso
        }

        await db.users.insert_one(user_doc)

        # Create role profile
        if user_doc["role"] == "student":
            await db.student_profiles.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "student_id": f"STU{user_id[:8].upper()}",
                "grade_level": "Grade 10",
                "section": "A",
                "phone": norm_phone,
                "organization_id": body.organization_id,
                "enrolled_courses": [],
                "created_at": now_iso
            })
        elif user_doc["role"] == "teacher":
            await db.teacher_profiles.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "employee_id": f"TCH{user_id[:8].upper()}",
                "department": "General",
                "phone": norm_phone,
                "organization_id": body.organization_id,
                "assigned_courses": [],
                "created_at": now_iso
            })

        # Audit log
        await audit_service.log(
            actor_id=user_id,
            action="user.register_with_phone",
            entity="user",
            entity_id=user_id,
            organisation_id=body.organization_id,
            new_value={"phone_number": norm_phone, "full_name": body.full_name},
            ip_address=req.client.host if req.client else None
        )

        # Send welcome notification
        await notification_service.notify_user(
            recipient_phone=norm_phone,
            recipient_email=user_doc.get("email"),
            event="phone_verified",
            user_id=user_id
        )

        token = create_token(user_id, user_doc["role"], user_doc.get("organization_id"))
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "full_name": user_doc["full_name"],
                "phone_number": norm_phone,
                "phone_verified": True,
                "email": user_doc.get("email"),
                "role": user_doc["role"],
                "organization_id": user_doc.get("organization_id")
            }
        }

    @router.post("/login")
    async def login_with_phone(body: PhoneLoginBody):
        """Authenticate using phone number + password OR phone number + OTP code."""
        raw_identifier = body.phone_number or body.identifier
        if not raw_identifier:
            raise HTTPException(status_code=400, detail="Phone number or identifier is required")

        norm_phone = None
        try:
            norm_phone = normalize_phone_number(raw_identifier)
        except ValueError:
            pass

        query_conditions = []
        if norm_phone:
            query_conditions.append({"phone_number": norm_phone})
        clean_id = raw_identifier.strip().lower()
        query_conditions.append({"email": clean_id})
        query_conditions.append({"phone_number": raw_identifier.strip()})

        user = await db.users.find_one({"$or": query_conditions}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Account not found. Please check your credentials or register.")

        if user.get("is_active") is False:
            raise HTTPException(status_code=403, detail="Account has been deactivated. Please contact support.")

        target_phone = user.get("phone_number") or norm_phone

        # Authenticate via OTP or Password
        if body.otp_code:
            if not target_phone:
                raise HTTPException(status_code=400, detail="No phone number associated with this account for OTP verification.")
            # Verify OTP with pending record
            otp_doc = await db.otp_verifications.find_one(
                {"phone_number": target_phone, "status": "pending"},
                sort=[("created_at", -1)]
            )
            purpose = otp_doc.get("purpose", "login") if otp_doc else "login"
            await otp_service.verify_otp(target_phone, body.otp_code, purpose=purpose)
        elif body.password:
            if not verify_password(body.password, user.get("password_hash", "")):
                raise HTTPException(status_code=401, detail="Invalid phone number or password")
        else:
            raise HTTPException(status_code=400, detail="Please provide either password or 6-digit OTP code")

        token = create_token(user["id"], user["role"], user.get("organization_id"))
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "full_name": user["full_name"],
                "phone_number": user.get("phone_number"),
                "phone_verified": user.get("phone_verified", False),
                "email": user.get("email"),
                "role": user["role"],
                "organization_id": user.get("organization_id")
            }
        }

    @router.post("/link-phone")
    async def link_and_verify_phone_for_existing_user(
        body: VerifyOTPBody,
        current_user: dict = Depends(get_current_user)
    ):
        """Allows an existing email user to add and verify their phone number."""
        try:
            norm_phone = normalize_phone_number(body.phone_number)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Check if another user has this phone verified
        existing = await db.users.find_one({
            "phone_number": norm_phone,
            "id": {"$ne": current_user["id"]},
            "phone_verified": True
        })
        if existing:
            raise HTTPException(status_code=409, detail="This phone number is already verified on another account.")

        await otp_service.verify_otp(norm_phone, body.otp_code, purpose="phone_change")

        now_iso = datetime.now(timezone.utc).isoformat()
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": {
                "phone_number": norm_phone,
                "phone_verified": True,
                "phone_verified_at": now_iso,
                "updated_at": now_iso
            }}
        )

        return {"success": True, "message": f"Phone number {norm_phone} verified and linked to your account."}

    return router
