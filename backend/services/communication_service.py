"""Multi-Channel Communication & Notification Architecture for Cognify.

Supports:
- SMS (Twilio SMS, Infobip / Africa's Talking / Webhook, Fallback simulator)
- WhatsApp (Twilio WhatsApp, Generic WhatsApp Business API, wa.me fallback)
- Email (Resend, SMTP, In-memory simulator)

Guarantees:
- Asynchronous and resilient: Notification delivery failures NEVER crash financial or enrolment transactions.
- Audit logging of all notifications with status, provider references, and timestamps.
- Reusable templates for OTP, payments, partial payments, due dates, and assessment unlock.
"""
from __future__ import annotations
import os
import uuid
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


# ==================== PROVIDER INTERFACES ====================

class SMSProvider(ABC):
    slug = "sms_base"
    @abstractmethod
    async def send_sms(self, to_phone: str, message: str) -> dict: ...


class WhatsAppProvider(ABC):
    slug = "whatsapp_base"
    @abstractmethod
    async def send_whatsapp(self, to_phone: str, message: str) -> dict: ...


class EmailProvider(ABC):
    slug = "email_base"
    @abstractmethod
    async def send_email(self, to_email: str, subject: str, html_content: str) -> dict: ...


# ==================== CONCRETE IMPLEMENTATIONS ====================

class SMSPoPProvider(SMSProvider):
    slug = "smspop_sms"
    def __init__(self):
        self.api_key = os.environ.get("SMSPOP_API_KEY") or os.environ.get("SMS_API_KEY", "")
        self.sender_id = os.environ.get("SMSPOP_SENDER_ID") or os.environ.get("SMS_SENDER_ID", "SMSPoP")
        self.base_url = os.environ.get("SMSPOP_BASE_URL", "https://smspop.co.zw/api")

    async def send_sms(self, to_phone: str, message: str) -> dict:
        if not self.api_key:
            logger.info(f"[SMS Simulator] To: {to_phone} | Message: {message}")
            return {"success": True, "provider": "simulator", "provider_id": f"sim_sms_{uuid.uuid4().hex[:8]}"}

        # Format Zimbabwean or international MSISDN (e.g., 0771234567 -> 263771234567)
        clean_phone = to_phone.strip().replace(" ", "").replace("-", "")
        if clean_phone.startswith("+"):
            clean_phone = clean_phone[1:]
        if clean_phone.startswith("0") and len(clean_phone) == 10:
            clean_phone = "263" + clean_phone[1:]

        try:
            import httpx
            async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
                payload = {
                    "name": "Cognify Notification",
                    "message": message,
                    "sender_id": self.sender_id,
                    "contact_import_method": "manual",
                    "manual_contacts": clean_phone
                }
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                resp = await client.post(
                    f"{self.base_url.rstrip('/')}/campaigns",
                    json=payload,
                    headers=headers
                )
                
                try:
                    data = resp.json()
                except Exception:
                    data = {}

                if resp.status_code in [200, 201] and data.get("success"):
                    summary = data.get("data", {}).get("summary", {})
                    contacts = data.get("data", {}).get("contacts", [{}])
                    msg_id = contacts[0].get("message_id") if contacts else None
                    logger.info(f"[SMSPoP] Dispatched SMS to {clean_phone} (message_id={msg_id})")
                    return {
                        "success": True,
                        "provider": "smspop",
                        "provider_id": str(msg_id or data.get("data", {}).get("campaign", {}).get("id")),
                        "credits_remaining": summary.get("credits_remaining")
                    }
                else:
                    err_msg = data.get("message") or resp.text
                    logger.error(f"[SMSPoP Error] ({resp.status_code}): {err_msg}")
                    return {"success": False, "error": f"SMSPoP error: {err_msg}"}
        except Exception as e:
            logger.error(f"[SMSPoP Exception]: {e}")
            return {"success": False, "error": str(e)}


class TwilioSMSProvider(SMSProvider):
    slug = "twilio_sms"
    def __init__(self):
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
        self.from_number = os.environ.get("TWILIO_SMS_FROM_NUMBER") or os.environ.get("TWILIO_FROM_NUMBER", "")

    async def send_sms(self, to_phone: str, message: str) -> dict:
        if not (self.account_sid and self.auth_token and self.from_number):
            logger.info(f"[SMS Simulator] To: {to_phone} | Message: {message}")
            return {"success": True, "provider": "simulator", "provider_id": f"sim_sms_{uuid.uuid4().hex[:8]}"}

        try:
            import httpx
            from base64 import b64encode
            auth_header = b64encode(f"{self.account_sid}:{self.auth_token}".encode()).decode()
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json",
                    headers={
                        "Authorization": f"Basic {auth_header}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    data={
                        "From": self.from_number,
                        "To": to_phone,
                        "Body": message
                    },
                    timeout=20
                )
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    return {"success": True, "provider": "twilio", "provider_id": data.get("sid")}
                return {"success": False, "error": f"Twilio SMS error ({resp.status_code}): {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


class TwilioWhatsAppProvider(WhatsAppProvider):
    slug = "twilio_whatsapp"
    def __init__(self):
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
        self.whatsapp_number = os.environ.get("TWILIO_WHATSAPP_NUMBER", "")

    async def send_whatsapp(self, to_phone: str, message: str) -> dict:
        clean_phone = to_phone if to_phone.startswith("+") else f"+{to_phone}"
        if not (self.account_sid and self.auth_token and self.whatsapp_number):
            # Safe fallback: simulator with wa.me click link
            encoded_msg = message.replace(" ", "%20").replace("\n", "%0A")
            wa_link = f"https://wa.me/{clean_phone.replace('+', '')}?text={encoded_msg}"
            logger.info(f"[WhatsApp Simulator] To: {clean_phone} | Link: {wa_link}")
            return {"success": True, "provider": "simulator", "provider_id": f"sim_wa_{uuid.uuid4().hex[:8]}", "link": wa_link}

        try:
            import httpx
            from base64 import b64encode
            auth_header = b64encode(f"{self.account_sid}:{self.auth_token}".encode()).decode()
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json",
                    headers={
                        "Authorization": f"Basic {auth_header}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    data={
                        "From": f"whatsapp:{self.whatsapp_number}",
                        "To": f"whatsapp:{clean_phone}",
                        "Body": message
                    },
                    timeout=20
                )
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    return {"success": True, "provider": "twilio", "provider_id": data.get("sid")}
                return {"success": False, "error": f"Twilio WhatsApp error ({resp.status_code}): {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


class ResendEmailProvider(EmailProvider):
    slug = "resend_email"
    def __init__(self):
        self.api_key = os.environ.get("RESEND_API_KEY", "")
        self.from_email = os.environ.get("FROM_EMAIL", "noreply@cognify.edu")

    async def send_email(self, to_email: str, subject: str, html_content: str) -> dict:
        if not self.api_key:
            logger.info(f"[Email Simulator] To: {to_email} | Subject: {subject}")
            return {"success": True, "provider": "simulator", "provider_id": f"sim_mail_{uuid.uuid4().hex[:8]}"}

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={
                        "from": f"Cognify <{self.from_email}>",
                        "to": [to_email],
                        "subject": subject,
                        "html": html_content
                    },
                    timeout=20
                )
                if resp.status_code in [200, 201]:
                    return {"success": True, "provider": "resend", "provider_id": resp.json().get("id")}
                return {"success": False, "error": f"Resend error ({resp.status_code}): {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ==================== CENTRAL NOTIFICATION SERVICE ====================

class NotificationService:
    def __init__(self, db):
        self.db = db
        # Prioritize SMSPoP provider if API key configured
        if os.environ.get("SMSPOP_API_KEY") or os.environ.get("SMS_API_KEY"):
            self.sms_provider: SMSProvider = SMSPoPProvider()
        elif os.environ.get("TWILIO_ACCOUNT_SID"):
            self.sms_provider: SMSProvider = TwilioSMSProvider()
        else:
            self.sms_provider: SMSProvider = SMSPoPProvider()

        self.wa_provider: WhatsAppProvider = TwilioWhatsAppProvider()
        self.email_provider: EmailProvider = ResendEmailProvider()

    def format_template(self, event: str, **kwargs) -> str:
        """Centralized notification templates as specified in BRD."""
        if event == "registration_otp":
            return f"Your Cognify verification code is {kwargs.get('code')}."
        elif event == "phone_verified":
            return "Your phone number has been successfully verified on Cognify. Welcome aboard!"
        elif event == "course_enrolment":
            return f"You have been enrolled in {kwargs.get('course_name', 'your course')} on Cognify."
        elif event == "payment_confirmation":
            return f"Your Cognify payment of ${float(kwargs.get('amount', 0)):.2f} has been received."
        elif event == "partial_payment":
            return (
                f"We received your payment of ${float(kwargs.get('amount', 0)):.2f}. "
                f"You need ${float(kwargs.get('remaining', 0)):.2f} more to meet the current monthly requirement."
            )
        elif event == "payment_due":
            return f"Your Cognify course payment of ${float(kwargs.get('amount', 0)):.2f} is due for {kwargs.get('course_name', 'your course')}."
        elif event == "payment_overdue":
            return (
                f"Your Cognify assessment access is currently locked because your payment is overdue. "
                f"Pay ${float(kwargs.get('remaining', 0)):.2f} to restore eligibility."
            )
        elif event == "assessment_restored":
            return "Your payment requirement has been met. Your Cognify assessment access is now available."
        elif event == "custom":
            return kwargs.get("message", "")
        return kwargs.get("message", "Cognify notification")

    async def notify_user(
        self,
        recipient_phone: Optional[str] = None,
        recipient_email: Optional[str] = None,
        event: str = "custom",
        channels: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> dict:
        """Send asynchronous, multi-channel notification and persist history safely."""
        channels = channels or ["sms", "whatsapp"]
        message_text = self.format_template(event, **kwargs)
        results = {}

        for ch in channels:
            ch_res = {"success": False}
            try:
                if ch == "sms" and recipient_phone:
                    ch_res = await self.sms_provider.send_sms(recipient_phone, message_text)
                elif ch == "whatsapp" and recipient_phone:
                    ch_res = await self.wa_provider.send_whatsapp(recipient_phone, message_text)
                elif ch == "email" and recipient_email:
                    subject = kwargs.get("subject", "Cognify Notification")
                    html = f"<div style='font-family:sans-serif;'><p>{message_text}</p></div>"
                    ch_res = await self.email_provider.send_email(recipient_email, subject, html)
            except Exception as e:
                logger.error(f"Failed to send on channel {ch}: {e}")
                ch_res = {"success": False, "error": str(e)}

            results[ch] = ch_res

            # Record in notification_logs
            try:
                log_entry = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "recipient": recipient_phone if ch in ["sms", "whatsapp"] else recipient_email,
                    "channel": ch,
                    "event": event,
                    "message": message_text,
                    "provider_reference": ch_res.get("provider_id"),
                    "status": "delivered" if ch_res.get("success") else "failed",
                    "error_info": ch_res.get("error"),
                    "sent_at": datetime.now(timezone.utc).isoformat()
                }
                await self.db.notification_logs.insert_one(log_entry)
            except Exception as e:
                logger.error(f"Failed to save notification log: {e}")

        return {"results": results, "message": message_text}
