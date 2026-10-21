"""SMS Administration & Control Engine Routes for Cognify.

Provides:
- SMS Gateway status, provider details, and balance/credit estimates
- Quick SMS dispatcher (single & batch) via configured provider (SMSPoP)
- SMS notification history & delivery logs
- Templates & trigger configurations for automated alerts (OTP, enrolments, fees, attendance)
"""
from __future__ import annotations
import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

try:
    from auth_utils import get_current_user
except ImportError:
    from backend.auth_utils import get_current_user

try:
    from services.communication_service import NotificationService, SMSPoPProvider
except ImportError:
    from backend.services.communication_service import NotificationService, SMSPoPProvider

logger = logging.getLogger(__name__)


class SendSMSRequest(BaseModel):
    to: str = Field(..., description="Recipient phone number (e.g. +263786434988 or 0786434988)")
    message: str = Field(..., max_length=640, description="SMS content")
    sender_id: Optional[str] = "SMSPoP"


class BroadcastSMSRequest(BaseModel):
    recipients: List[str] = Field(..., min_items=1)
    message: str = Field(..., max_length=640)
    sender_id: Optional[str] = "SMSPoP"


class UpdateSMSConfig(BaseModel):
    sender_id: Optional[str] = None
    enabled: Optional[bool] = True


def make_sms_admin_router(db):
    router = APIRouter(prefix="/api/sms", tags=["SMS Control Engine"])
    sms_provider = SMSPoPProvider()
    notification_service = NotificationService(db)

    def require_admin(user=Depends(get_current_user)):
        if user.get("role") not in ("super_admin", "admin"):
            raise HTTPException(status_code=403, detail="Admin or Super Admin privileges required")
        return user

    @router.get("/status")
    async def get_sms_status(user=Depends(require_admin)):
        """Fetch live status of the SMS gateway & SMSPoP integration."""
        api_key = os.environ.get("SMSPOP_API_KEY") or os.environ.get("SMS_API_KEY", "")
        sender_id = os.environ.get("SMSPOP_SENDER_ID") or os.environ.get("SMS_SENDER_ID", "SMSPoP")
        base_url = os.environ.get("SMSPOP_BASE_URL", "https://smspop.co.zw/api")

        is_configured = bool(api_key and len(api_key) > 10)

        # Count total sent SMS logs in local database
        total_logs = 0
        delivered_logs = 0
        failed_logs = 0
        recent_campaigns = []

        try:
            total_logs = await db.notification_logs.count_documents({"channel": "sms"})
            delivered_logs = await db.notification_logs.count_documents({"channel": "sms", "status": "delivered"})
            failed_logs = await db.notification_logs.count_documents({"channel": "sms", "status": "failed"})
        except Exception:
            pass

        # Try to retrieve recent campaigns from SMSPoP
        credits_remaining = None
        if is_configured:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=8.0, verify=False) as client:
                    resp = await client.get(
                        f"{base_url.rstrip('/')}/campaigns",
                        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
                    )
                    if resp.status_code == 200:
                        c_data = resp.json().get("data", {})
                        recent_campaigns = c_data.get("campaigns", [])[:10]
            except Exception as e:
                logger.warning(f"Failed to fetch SMSPoP campaigns: {e}")

        return {
            "status": "connected" if is_configured else "unconfigured",
            "provider": "smspop",
            "provider_name": "SMSPoP Zimbabwe",
            "sender_id": sender_id,
            "base_url": base_url,
            "api_key_masked": f"{api_key[:6]}...{api_key[-4:]}" if is_configured else None,
            "stats": {
                "total_dispatched": total_logs,
                "delivered": delivered_logs,
                "failed": failed_logs,
            },
            "recent_campaigns": recent_campaigns
        }

    @router.post("/send")
    async def send_single_sms(req: SendSMSRequest, user=Depends(require_admin)):
        """Send a single live SMS via the SMS gateway."""
        result = await sms_provider.send_sms(req.to, req.message)

        # Log into notification_logs
        try:
            log_entry = {
                "id": str(uuid.uuid4()),
                "user_id": user.get("id"),
                "recipient": req.to,
                "channel": "sms",
                "event": "manual_admin_sms",
                "message": req.message,
                "provider_reference": result.get("provider_id"),
                "status": "delivered" if result.get("success") else "failed",
                "error_info": result.get("error"),
                "sent_at": datetime.now(timezone.utc).isoformat()
            }
            await db.notification_logs.insert_one(log_entry)
        except Exception as e:
            logger.error(f"Failed to persist admin SMS log: {e}")

        if not result.get("success"):
            raise HTTPException(status_code=502, detail=result.get("error", "SMS dispatch failed"))

        return {
            "success": True,
            "message": "SMS dispatched successfully",
            "provider_id": result.get("provider_id"),
            "credits_remaining": result.get("credits_remaining")
        }

    @router.post("/broadcast")
    async def broadcast_sms(req: BroadcastSMSRequest, user=Depends(require_admin)):
        """Send bulk/broadcast SMS to multiple contacts."""
        results = []
        sent_count = 0
        failed_count = 0

        for phone in req.recipients:
            res = await sms_provider.send_sms(phone, req.message)
            if res.get("success"):
                sent_count += 1
            else:
                failed_count += 1
            results.append({"phone": phone, "result": res})

        return {
            "total": len(req.recipients),
            "sent": sent_count,
            "failed": failed_count,
            "results": results
        }

    @router.get("/logs")
    async def get_sms_logs(
        limit: int = Query(50, ge=1, le=200),
        status: Optional[str] = None,
        user=Depends(require_admin)
    ):
        """Fetch delivery logs for all SMS notifications sent through the platform."""
        query: Dict[str, Any] = {"channel": "sms"}
        if status:
            query["status"] = status

        logs = []
        try:
            cursor = db.notification_logs.find(query, {"_id": 0}).sort("sent_at", -1).limit(limit)
            logs = await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error fetching SMS logs: {e}")

        return {"logs": logs, "count": len(logs)}

    @router.get("/templates")
    async def get_sms_templates(user=Depends(require_admin)):
        """Predefined event triggers and notification templates."""
        return {
            "templates": [
                {
                    "event": "registration_otp",
                    "label": "Registration & Login OTP",
                    "template": "Your Cognify verification code is {code}."
                },
                {
                    "event": "phone_verified",
                    "label": "Phone Verified Welcome",
                    "template": "Your phone number has been successfully verified on Cognify. Welcome aboard!"
                },
                {
                    "event": "course_enrolment",
                    "label": "Course Enrolment Alert",
                    "template": "You have been enrolled in {course_name} on Cognify."
                },
                {
                    "event": "payment_confirmation",
                    "label": "Payment Received Confirmation",
                    "template": "Your Cognify payment of ${amount} has been received."
                },
                {
                    "event": "payment_due",
                    "label": "Payment Due Reminder",
                    "template": "Your Cognify course payment of ${amount} is due for {course_name}."
                },
                {
                    "event": "assessment_restored",
                    "label": "Assessment Unlocked Notification",
                    "template": "Your payment requirement has been met. Your Cognify assessment access is now available."
                }
            ]
        }

    return router
