"""Secure OTP and Phone Number Verification Service for Cognify.

Features:
- Phone number normalization (Zimbabwe +263 and international E.164).
- Cryptographically secure 6-digit OTP generation.
- One-way hashing (SHA-256) of OTP values at rest.
- Configurable expiration, max verification attempts, and resend cooldown.
- Hourly rate-limiting per phone number.
- Single-use invalidation upon verification to prevent replay.
- Purpose tracking: registration, phone_change, account_recovery, sensitive_action.
"""
from __future__ import annotations
import os
import re
import uuid
import secrets
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Configurable settings
OTP_EXPIRY_MINUTES = int(os.environ.get("OTP_EXPIRY_MINUTES", 10))
OTP_MAX_ATTEMPTS = int(os.environ.get("OTP_MAX_ATTEMPTS", 5))
OTP_RESEND_COOLDOWN_SECONDS = int(os.environ.get("OTP_RESEND_COOLDOWN_SECONDS", 60))
OTP_MAX_REQUESTS_PER_HOUR = int(os.environ.get("OTP_MAX_REQUESTS_PER_HOUR", 5))


def normalize_phone_number(raw_phone: str) -> str:
    """Normalize phone number to international E.164 format.
    
    Defaults local Zimbabwe formats:
    - 0771234567 -> +263771234567
    - 263771234567 -> +263771234567
    - +263771234567 -> +263771234567
    """
    if not raw_phone:
        raise ValueError("Phone number is required")
    
    cleaned = re.sub(r"[\s\-\(\)]", "", str(raw_phone).strip())
    
    # If starts with +, ensure digits only after
    if cleaned.startswith("+"):
        digits = cleaned[1:]
        if not digits.isdigit() or len(digits) < 7 or len(digits) > 15:
            raise ValueError(f"Invalid international phone number: {raw_phone}")
        return f"+{digits}"
    
    # Handle local 0-prefixed numbers (Zimbabwe default)
    if cleaned.startswith("0") and len(cleaned) in [10, 11]:
        return f"+263{cleaned[1:]}"
    
    # Handle Zimbabwe without +
    if cleaned.startswith("263") and len(cleaned) in [12, 13]:
        return f"+{cleaned}"
    
    # Standard digits
    if cleaned.isdigit() and 7 <= len(cleaned) <= 15:
        # Default to +263 if 9 digits (e.g. 771234567)
        if len(cleaned) == 9:
            return f"+263{cleaned}"
        return f"+{cleaned}"
    
    raise ValueError(f"Invalid phone number format: {raw_phone}. Please provide valid phone number (e.g. +263771234567)")


def hash_otp(phone: str, otp_code: str) -> str:
    """SHA-256 hash of (phone + salt + code)."""
    salt = os.environ.get("JWT_SECRET", "cognify_salt_2026")
    return hashlib.sha256(f"{phone}:{otp_code}:{salt}".encode()).hexdigest()


class OTPService:
    def __init__(self, db):
        self.db = db

    async def generate_and_store_otp(
        self,
        phone_number: str,
        purpose: str = "registration"
    ) -> Tuple[str, dict]:
        """Generate a random 6-digit OTP, enforce rate-limits and cooldowns, and save hashed record.
        
        Returns: (plain_otp_code, otp_record_metadata)
        Note: plain_otp_code is returned ONLY to be dispatched via SMS/WhatsApp provider.
        """
        norm_phone = normalize_phone_number(phone_number)
        now = datetime.now(timezone.utc)

        # 1. Check Hourly Rate Limit
        one_hour_ago = now - timedelta(hours=1)
        recent_count = await self.db.otp_verifications.count_documents({
            "phone_number": norm_phone,
            "created_at": {"$gte": one_hour_ago.isoformat()}
        })
        if recent_count >= OTP_MAX_REQUESTS_PER_HOUR:
            raise HTTPException(
                status_code=429,
                detail=f"Too many verification requests. Please wait before requesting another code."
            )

        # 2. Check Resend Cooldown
        latest_otp = await self.db.otp_verifications.find_one(
            {"phone_number": norm_phone, "status": "pending"},
            sort=[("created_at", -1)]
        )
        if latest_otp and latest_otp.get("resend_available_at"):
            try:
                cooldown_until = datetime.fromisoformat(latest_otp["resend_available_at"])
                if cooldown_until.tzinfo is None:
                    cooldown_until = cooldown_until.replace(tzinfo=timezone.utc)
                if now < cooldown_until:
                    seconds_left = int((cooldown_until - now).total_seconds())
                    raise HTTPException(
                        status_code=429,
                        detail=f"Please wait {seconds_left} seconds before requesting a new code."
                    )
            except HTTPException:
                raise
            except Exception:
                pass

        # Invalidate any previously pending OTP for this phone & purpose
        await self.db.otp_verifications.update_many(
            {"phone_number": norm_phone, "purpose": purpose, "status": "pending"},
            {"$set": {"status": "superseded", "invalidated_at": now.isoformat()}}
        )

        # Generate 6-digit code
        code = f"{secrets.randbelow(900000) + 100000}"
        code_hash = hash_otp(norm_phone, code)

        expires_at = now + timedelta(minutes=OTP_EXPIRY_MINUTES)
        resend_available_at = now + timedelta(seconds=OTP_RESEND_COOLDOWN_SECONDS)

        record_id = str(uuid.uuid4())
        record = {
            "id": record_id,
            "phone_number": norm_phone,
            "otp_hash": code_hash,
            "purpose": purpose,
            "attempts": 0,
            "max_attempts": OTP_MAX_ATTEMPTS,
            "status": "pending",
            "expires_at": expires_at.isoformat(),
            "resend_available_at": resend_available_at.isoformat(),
            "created_at": now.isoformat()
        }

        await self.db.otp_verifications.insert_one(record)

        meta = {
            "record_id": record_id,
            "phone_number": norm_phone,
            "expires_in_seconds": OTP_EXPIRY_MINUTES * 60,
            "resend_in_seconds": OTP_RESEND_COOLDOWN_SECONDS,
            "purpose": purpose
        }
        return code, meta

    async def verify_otp(
        self,
        phone_number: str,
        otp_code: str,
        purpose: str = "registration"
    ) -> bool:
        """Verify the user's OTP code securely.
        
        Enforces:
        - Expiration
        - Max attempt lockout
        - Correct code matching
        - Single-use invalidation
        """
        norm_phone = normalize_phone_number(phone_number)
        now = datetime.now(timezone.utc)

        otp_doc = await self.db.otp_verifications.find_one(
            {"phone_number": norm_phone, "purpose": purpose, "status": "pending"},
            sort=[("created_at", -1)]
        )

        if not otp_doc:
            raise HTTPException(
                status_code=400,
                detail="No pending verification request found for this phone number. Please request a new code."
            )

        # Check expiration
        expires_at = datetime.fromisoformat(otp_doc["expires_at"])
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if now > expires_at:
            await self.db.otp_verifications.update_one(
                {"id": otp_doc["id"]},
                {"$set": {"status": "expired", "updated_at": now.isoformat()}}
            )
            raise HTTPException(
                status_code=400,
                detail="Verification code has expired. Please request a new code."
            )

        # Check attempt count
        current_attempts = otp_doc.get("attempts", 0) + 1
        if current_attempts > otp_doc.get("max_attempts", OTP_MAX_ATTEMPTS):
            await self.db.otp_verifications.update_one(
                {"id": otp_doc["id"]},
                {"$set": {"status": "failed", "attempts": current_attempts, "updated_at": now.isoformat()}}
            )
            raise HTTPException(
                status_code=400,
                detail="Maximum verification attempts exceeded. Please request a new code."
            )

        expected_hash = hash_otp(norm_phone, str(otp_code).strip())
        if secrets.compare_digest(otp_doc["otp_hash"], expected_hash):
            # Success: invalidate OTP immediately to prevent reuse
            await self.db.otp_verifications.update_one(
                {"id": otp_doc["id"]},
                {"$set": {
                    "status": "verified",
                    "attempts": current_attempts,
                    "verified_at": now.isoformat(),
                    "updated_at": now.isoformat()
                }}
            )
            return True
        else:
            # Increment attempts
            await self.db.otp_verifications.update_one(
                {"id": otp_doc["id"]},
                {"$set": {"attempts": current_attempts, "updated_at": now.isoformat()}}
            )
            attempts_left = max(0, otp_doc.get("max_attempts", OTP_MAX_ATTEMPTS) - current_attempts)
            raise HTTPException(
                status_code=400,
                detail=f"Invalid verification code. {attempts_left} attempt(s) remaining."
            )
