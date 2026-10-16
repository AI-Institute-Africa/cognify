"""WhatsApp Webhook Route for Cognify.

Handles incoming WhatsApp registration and conversational messages from:
- Twilio WhatsApp webhook (x-www-form-urlencoded)
- Meta WhatsApp Cloud API / Generic JSON webhooks
"""
from __future__ import annotations
import logging
from typing import Optional
from fastapi import APIRouter, Request, Response
from services.whatsapp_registration_service import WhatsAppRegistrationService

logger = logging.getLogger(__name__)


def make_whatsapp_webhook_router(db):
    router = APIRouter(prefix="/webhooks/whatsapp", tags=["WhatsApp Webhook"])
    service = WhatsAppRegistrationService(db)

    @router.post("")
    async def receive_whatsapp_webhook(request: Request):
        """Incoming WhatsApp message handler."""
        content_type = request.headers.get("content-type", "")

        from_phone = ""
        body_text = ""
        message_id = None

        if "application/x-www-form-urlencoded" in content_type:
            form_data = await request.form()
            from_raw = form_data.get("From", "")
            # Twilio format: 'whatsapp:+263771234567'
            from_phone = from_raw.replace("whatsapp:", "").strip()
            body_text = form_data.get("Body", "").strip()
            message_id = form_data.get("MessageSid")
        else:
            try:
                json_data = await request.json()
                from_phone = json_data.get("from") or json_data.get("sender", "")
                body_text = json_data.get("body") or json_data.get("text") or json_data.get("message", "")
                message_id = json_data.get("message_id") or json_data.get("id")
            except Exception:
                pass

        if not from_phone or not body_text:
            return {"status": "ignored", "reason": "Missing sender or body"}

        result = await service.handle_incoming_message(
            from_phone=from_phone,
            body_text=body_text,
            message_id=message_id
        )

        reply = result.get("reply_text")

        # If Twilio request, respond with TwiML MessagingResponse
        if "application/x-www-form-urlencoded" in content_type and reply:
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{reply}</Message>
</Response>"""
            return Response(content=twiml, media_type="application/xml")

        return {"status": "ok", "reply": reply, "session": result}

    return router
