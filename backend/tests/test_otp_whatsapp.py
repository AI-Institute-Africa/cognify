"""Unit tests for services/otp_service.py — BRD FR-07 (expiry), FR-08 (rate
limiting), FR-09 (not verified until validated), FR-10 (resend), and the masked
phone display required by section 11.

Pure in-process tests against the fake_db fixture; send_otp's dispatch call is
monkeypatched since no Twilio credentials exist in a test environment.
"""
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import services.otp_service as otp_service
from services.otp_service import send_otp, verify_otp, mask_phone, MAX_VERIFY_ATTEMPTS


async def _fake_whatsapp(phone_number, message):
    return {"success": True, "message_id": "SMfake", "status": "queued"}


async def _fake_sms(phone_number, message):
    return {"success": True, "message_id": "SMfake", "status": "queued"}


def _patch_dispatch(monkeypatch):
    import services.notification_service as notification_service
    monkeypatch.setattr(notification_service, "send_whatsapp", _fake_whatsapp)
    monkeypatch.setattr(notification_service, "send_sms", _fake_sms)


async def test_send_otp_then_verify_succeeds(fake_db, monkeypatch):
    _patch_dispatch(monkeypatch)
    send_result = await send_otp(fake_db, phone_number="+263771234567", purpose="registration")
    assert send_result["success"] is True

    record = await fake_db.phone_otp_verifications.find_one({"phone_number": "+263771234567"})
    # The plaintext code is never persisted (BRD section 8: handle OTP data securely).
    assert "otp_hash" in record and "code" not in record

    # Recover the plaintext code the only way a test can: via the hash, by brute
    # forcing isn't feasible, so instead verify the negative-then-positive path
    # using the service's own hash function with a known code via monkeypatch.
    import services.otp_service as mod
    monkeypatch.setattr(mod, "_generate_code", lambda: "123456")
    send_result2 = await send_otp(fake_db, phone_number="+263779999999", purpose="registration")
    assert send_result2["success"] is True

    verify_result = await verify_otp(fake_db, phone_number="+263779999999", code="123456", purpose="registration")
    assert verify_result["success"] is True

    record2 = await fake_db.phone_otp_verifications.find_one({"phone_number": "+263779999999"})
    assert record2["status"] == "verified"
    assert record2["verified_at"] is not None


async def test_verify_otp_rejects_wrong_code(fake_db, monkeypatch):
    _patch_dispatch(monkeypatch)
    monkeypatch.setattr(otp_service, "_generate_code", lambda: "111111")
    await send_otp(fake_db, phone_number="+263770000001", purpose="registration")

    result = await verify_otp(fake_db, phone_number="+263770000001", code="000000", purpose="registration")
    assert result["success"] is False
    assert "incorrect" in result["error"].lower()


async def test_verify_otp_rejects_expired_code(fake_db, monkeypatch):
    _patch_dispatch(monkeypatch)
    monkeypatch.setattr(otp_service, "_generate_code", lambda: "222222")
    await send_otp(fake_db, phone_number="+263770000002", purpose="registration")

    # Force the stored record to already be expired.
    record = await fake_db.phone_otp_verifications.find_one({"phone_number": "+263770000002"})
    await fake_db.phone_otp_verifications.update_one(
        {"id": record["id"]},
        {"$set": {"expires_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()}},
    )

    result = await verify_otp(fake_db, phone_number="+263770000002", code="222222", purpose="registration")
    assert result["success"] is False
    assert "expired" in result["error"].lower()


async def test_verify_otp_locks_out_after_max_attempts(fake_db, monkeypatch):
    _patch_dispatch(monkeypatch)
    monkeypatch.setattr(otp_service, "_generate_code", lambda: "333333")
    await send_otp(fake_db, phone_number="+263770000003", purpose="registration")

    for _ in range(MAX_VERIFY_ATTEMPTS):
        await verify_otp(fake_db, phone_number="+263770000003", code="000000", purpose="registration")

    result = await verify_otp(fake_db, phone_number="+263770000003", code="333333", purpose="registration")
    assert result["success"] is False
    assert "too many attempts" in result["error"].lower()


async def test_resend_is_rate_limited(fake_db, monkeypatch):
    _patch_dispatch(monkeypatch)
    first = await send_otp(fake_db, phone_number="+263770000004", purpose="registration")
    assert first["success"] is True

    second = await send_otp(fake_db, phone_number="+263770000004", purpose="registration")
    assert second["success"] is False
    assert "wait" in second["error"].lower()


def test_mask_phone_hides_middle_digits():
    masked = mask_phone("+263771234567")
    assert masked.startswith("+26")
    assert masked.endswith("67")
    assert "*" in masked
    assert "1234" not in masked
