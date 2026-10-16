"""Minimal phone/WhatsApp OTP verification engine — BRD CR 2026-10, section 6.5
(WhatsApp registration) and section 6.1 ("verify/update the learner's phone
number"). Modeled on the existing email-OTP pattern in backend/server.py's
"EMAIL VERIFICATION & AUTH ENHANCEMENTS" section, but for the phone/WhatsApp
channel, and covers FR-07 (expiry), FR-08 (rate limiting), FR-09 (phone not
verified until OTP validated), FR-10 (resend).

Full phone-only self-registration (FR-01 to FR-05) is explicitly out of scope —
this engine exists only to support WhatsApp registration and admin-assisted
phone verification.
"""
from __future__ import annotations
import hashlib
import random
import string
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 10
MAX_VERIFY_ATTEMPTS = 5
RESEND_COOLDOWN_SECONDS = 60


def _hash_code(code: str, phone_number: str) -> str:
    return hashlib.sha256(f"{phone_number}:{code}".encode()).hexdigest()


def _generate_code() -> str:
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def send_otp(
    db,
    *,
    phone_number: str,
    channel: str = "whatsapp",
    purpose: str = "registration",
    user_id: Optional[str] = None,
) -> dict:
    """FR-06/FR-08: generate + dispatch an OTP, rate-limited per phone+purpose."""
    last = await db.phone_otp_verifications.find_one(
        {"phone_number": phone_number, "purpose": purpose},
        sort=[("created_at", -1)],
    )
    if last:
        last_created = datetime.fromisoformat(last["created_at"])
        if (_now() - last_created).total_seconds() < RESEND_COOLDOWN_SECONDS:
            return {"success": False, "error": "Please wait before requesting another code"}

    code = _generate_code()
    record = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "phone_number": phone_number,
        "otp_hash": _hash_code(code, phone_number),
        "purpose": purpose,
        "channel": channel,
        "expires_at": (_now() + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat(),
        "attempts": 0,
        "verified_at": None,
        "status": "pending",
        "created_at": _now().isoformat(),
    }
    await db.phone_otp_verifications.insert_one(record)

    from services.notification_service import send_sms, send_whatsapp, get_whatsapp_message
    message = get_whatsapp_message("otp_verification", code=code, expires_minutes=OTP_EXPIRY_MINUTES)
    if channel == "sms":
        dispatch_result = await send_sms(phone_number, message)
    else:
        dispatch_result = await send_whatsapp(phone_number, message)

    return {
        "success": True,
        "expires_in_minutes": OTP_EXPIRY_MINUTES,
        "dispatch": dispatch_result,
    }


async def verify_otp(db, *, phone_number: str, code: str, purpose: str = "registration") -> dict:
    """FR-09: phone is not verified until this returns success=True."""
    record = await db.phone_otp_verifications.find_one(
        {"phone_number": phone_number, "purpose": purpose, "status": "pending"},
        sort=[("created_at", -1)],
    )
    if not record:
        return {"success": False, "error": "No pending verification for this phone number"}

    if record["attempts"] >= MAX_VERIFY_ATTEMPTS:
        return {"success": False, "error": "Too many attempts. Request a new code."}

    await db.phone_otp_verifications.update_one(
        {"id": record["id"]}, {"$inc": {"attempts": 1}}
    )

    if datetime.fromisoformat(record["expires_at"]) < _now():
        return {"success": False, "error": "Code expired. Request a new one."}

    if _hash_code(code, phone_number) != record["otp_hash"]:
        return {"success": False, "error": "Incorrect code"}

    await db.phone_otp_verifications.update_one(
        {"id": record["id"]},
        {"$set": {"status": "verified", "verified_at": _now().isoformat()}},
    )
    return {"success": True}


def mask_phone(phone_number: str) -> str:
    """BRD section 11: 'OTP screens shall clearly show the destination phone
    number in masked form'."""
    if not phone_number or len(phone_number) < 4:
        return "****"
    return f"{phone_number[:3]}{'*' * (len(phone_number) - 5)}{phone_number[-2:]}"
