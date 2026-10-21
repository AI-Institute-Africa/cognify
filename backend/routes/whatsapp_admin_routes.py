"""WhatsApp Admin API Routes for Cognify."""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
try:
    from auth_utils import get_current_user
except ImportError:
    from backend.auth_utils import get_current_user
try:
    from services.whatsapp_service import WhatsAppService
except ImportError:
    from backend.services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)


class ConnectRequest(BaseModel):
    method: str = "qr"  # "qr" or "pairing"
    phone_number: Optional[str] = None


class SendMessageRequest(BaseModel):
    to: str
    message: str


class PauseRequest(BaseModel):
    hours: int


class RecipientModel(BaseModel):
    name: str
    phone: str
    alerts: List[str] = ["morning", "evening", "weekly", "registration", "corporate"]


def make_whatsapp_admin_router(db):
    router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Admin"])
    svc = WhatsAppService(db)

    def require_super_admin(user=Depends(get_current_user)):
        if user.get("role") not in ("super_admin", "admin"):
            raise HTTPException(status_code=403, detail="Super admin required")
        return user

    @router.get("/status")
    async def get_status(user=Depends(require_super_admin)):
        return await svc.get_status()

    @router.post("/connect")
    async def connect(req: ConnectRequest, user=Depends(require_super_admin)):
        return await svc.connect(req.method, req.phone_number)

    @router.post("/disconnect")
    async def disconnect(user=Depends(require_super_admin)):
        return await svc.disconnect()

    @router.post("/send")
    async def send_message(req: SendMessageRequest, user=Depends(require_super_admin)):
        return await svc.send_message(req.to, req.message)

    @router.get("/messages")
    async def get_messages(user=Depends(require_super_admin)):
        return await svc.get_messages()

    @router.get("/settings")
    async def get_settings(user=Depends(require_super_admin)):
        return await svc.get_settings()

    @router.post("/settings/toggle-ai")
    async def toggle_ai(user=Depends(require_super_admin)):
        return await svc.toggle_ai()

    @router.post("/settings/pause")
    async def pause_ai(req: PauseRequest, user=Depends(require_super_admin)):
        return await svc.pause_ai(req.hours)

    @router.get("/community")
    async def get_community_url():
        """Public endpoint — returns community group URL."""
        url = await svc.get_community_url()
        return {"url": url}

    # ── Report Recipients ──────────────────────────────────────────────────
    @router.get("/recipients")
    async def get_recipients(user=Depends(require_super_admin)):
        col = db["whatsapp_report_recipients"]
        recipients = await col.find({}, {"_id": 0}).to_list(length=100)
        return {"recipients": recipients}

    @router.post("/recipients")
    async def add_recipient(rec: RecipientModel, user=Depends(require_super_admin)):
        col = db["whatsapp_report_recipients"]
        doc = rec.dict()
        doc["created_at"] = datetime.now(timezone.utc).isoformat()
        await col.update_one({"phone": rec.phone}, {"$set": doc}, upsert=True)
        return {"ok": True}

    @router.delete("/recipients/{phone}")
    async def delete_recipient(phone: str, user=Depends(require_super_admin)):
        col = db["whatsapp_report_recipients"]
        await col.delete_one({"phone": phone})
        return {"ok": True}

    # ── Executive Reports (called by Node.js service) ──────────────────────
    @router.get("/report/{report_type}")
    async def get_report(report_type: str):
        """Called by the WhatsApp Node.js service to get report content."""
        col = db["whatsapp_report_recipients"]
        recipients_docs = await col.find({
            "alerts": {"$in": [report_type]}
        }, {"_id": 0}).to_list(length=50)
        phones = [r["phone"] for r in recipients_docs]

        now = datetime.now(timezone.utc)
        
        if report_type == "morning":
            users_col = db["users"]
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            new_students = await users_col.count_documents({
                "created_at": {"$gte": today_start.isoformat()}
            })
            total_students = await users_col.count_documents({"role": "student"})
            courses_col = db["courses"]
            total_courses = await courses_col.count_documents({})

            message = (
                f"🌅 *Cognify Morning Briefing*\n"
                f"📅 {now.strftime('%A, %d %B %Y')}\n\n"
                f"📊 *Today's Overview:*\n"
                f"• New Learners Today: *{new_students}*\n"
                f"• Total Active Learners: *{total_students}*\n"
                f"• Total Courses: *{total_courses}*\n\n"
                f"🚀 Have a productive day!\n"
                f"_Powered by Cognify AI Platform_"
            )

        elif report_type == "evening":
            payments_col = db.get_collection("payments") if hasattr(db, "get_collection") else db["payments"]
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_payments = await payments_col.count_documents({
                "created_at": {"$gte": today_start.isoformat()},
                "status": "completed"
            })
            message = (
                f"🌙 *Cognify Evening Reconciliation*\n"
                f"📅 {now.strftime('%d %B %Y, %H:%M')}\n\n"
                f"💰 *Today's Payments:*\n"
                f"• Completed Transactions: *{today_payments}*\n\n"
                f"✅ All systems operational.\n"
                f"_Cognify Finance Desk_"
            )

        elif report_type == "weekly":
            users_col = db["users"]
            total_students = await users_col.count_documents({"role": "student"})
            courses_col = db["courses"]
            total_courses = await courses_col.count_documents({})
            message = (
                f"📊 *Cognify Weekly Report*\n"
                f"Week of {now.strftime('%d %B %Y')}\n\n"
                f"🎓 *Platform Summary:*\n"
                f"• Total Learners: *{total_students}*\n"
                f"• Active Courses: *{total_courses}*\n\n"
                f"📈 Keep growing with Cognify!\n"
                f"_Cognify Leadership Desk_"
            )
        else:
            message = f"📢 Cognify Alert — {report_type} — {now.strftime('%d %B %Y %H:%M')}"

        return {"message": message, "recipients": phones, "type": report_type}

    return router
