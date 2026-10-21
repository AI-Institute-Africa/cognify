"""WhatsApp Admin API Routes for Cognify."""
from __future__ import annotations
import os
import uuid
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


class WhatsAppEnrollRequest(BaseModel):
    phone_number: str
    name: Optional[str] = None


class WhatsAppTTSRequest(BaseModel):
    text: str
    lang: Optional[str] = "en"


class WhatsAppTranscribeRequest(BaseModel):
    audio_base64: str
    lang: Optional[str] = "en"


def normalize_spoken_digits(text: str) -> str:
    """Converts spoken numbers and phone digits into clean numeric format."""
    import re
    word_to_digit = {
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
        "o": "0", "oh": "0", "plus": "+"
    }
    tokens = text.lower().split()
    converted = []
    for t in tokens:
        clean_t = re.sub(r"[^a-z0-9+]", "", t)
        if clean_t in word_to_digit:
            converted.append(word_to_digit[clean_t])
        else:
            converted.append(t)
    res = " ".join(converted)
    res = re.sub(r"(?<=\d)\s+(?=\d)", "", res)
    res = re.sub(r"\+\s+", "+", res)
    return res


def make_whatsapp_admin_router(db):
    router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Admin"])
    svc = WhatsAppService(db)

    # ── WhatsApp Audio Transcription (STT) ──────────────────────────────────
    @router.post("/transcribe-audio")
    async def whatsapp_transcribe_audio(req: WhatsAppTranscribeRequest):
        """Transcribes incoming WhatsApp voice notes/audio to text using speech recognition."""
        try:
            import imageio_ffmpeg
            import subprocess
            import speech_recognition as sr
            import tempfile
            import base64
            import os

            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            raw_bytes = base64.b64decode(req.audio_base64)

            with tempfile.TemporaryDirectory() as td:
                in_file = os.path.join(td, "input.audio")
                wav_file = os.path.join(td, "output.wav")
                with open(in_file, "wb") as f:
                    f.write(raw_bytes)

                # Convert to 16kHz mono WAV for SpeechRecognition
                subprocess.run(
                    [ffmpeg, "-y", "-i", in_file, "-ar", "16000", "-ac", "1", wav_file],
                    capture_output=True,
                    check=True
                )

                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_file) as source:
                    audio_data = recognizer.record(source)
                    text = ""
                    for dialect in [req.lang or "en-US", "en-GB", "en"]:
                        try:
                            text = recognizer.recognize_google(audio_data, language=dialect)
                            if text:
                                break
                        except Exception:
                            continue

                if not text:
                    return {"ok": False, "text": "", "error": "Could not understand audio"}

                normalized = normalize_spoken_digits(text)
                return {"ok": True, "raw_text": text, "text": normalized}
        except Exception as e:
            logger.error(f"WhatsApp audio transcription failed: {e}")
            return {"ok": False, "error": str(e), "text": ""}

    # ── WhatsApp Voice Note Generator (TTS) ─────────────────────────────────
    @router.post("/generate-voice")
    async def whatsapp_generate_voice(req: WhatsAppTTSRequest):
        """Generates a WhatsApp-compatible Opus OGG voice note from text."""
        try:
            from gtts import gTTS
            import imageio_ffmpeg
            import subprocess
            import tempfile
            import base64
            import os

            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            tts_lang = req.lang if req.lang in ["en", "sn", "nd"] else "en"
            try:
                tts = gTTS(text=req.text, lang=tts_lang, tld="co.uk")
            except Exception:
                tts = gTTS(text=req.text, lang="en", tld="co.uk")

            with tempfile.TemporaryDirectory() as td:
                mp3_path = os.path.join(td, "voice.mp3")
                ogg_path = os.path.join(td, "voice.ogg")
                tts.save(mp3_path)

                # Convert to WhatsApp-native Opus OGG format
                subprocess.run(
                    [ffmpeg, "-y", "-i", mp3_path, "-c:a", "libopus", "-b:a", "32k", "-vn", ogg_path],
                    capture_output=True,
                    check=True
                )

                with open(ogg_path, "rb") as f:
                    ogg_bytes = f.read()

                b64_audio = base64.b64encode(ogg_bytes).decode("ascii")
                return {
                    "ok": True,
                    "audio_base64": b64_audio,
                    "mimetype": "audio/ogg; codecs=opus"
                }
        except Exception as e:
            logger.error(f"WhatsApp voice generation failed: {e}")
            return {"ok": False, "error": str(e)}

    # ── WhatsApp Instant Account Creation & OTP ─────────────────────────────
    @router.post("/direct-enroll")
    async def whatsapp_direct_enroll(req: WhatsAppEnrollRequest):
        """Creates or retrieves a Cognify account directly from WhatsApp,

        generates a WhatsApp OTP, and dispatches it directly to the user.
        """
        try:
            from services.otp_service import OTPService, normalize_phone_number
            from services.communication_service import NotificationService
        except ImportError:
            from backend.services.otp_service import OTPService, normalize_phone_number
            from backend.services.communication_service import NotificationService

        try:
            norm_phone = normalize_phone_number(req.phone_number)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        now_iso = datetime.now(timezone.utc).isoformat()
        user = await db.users.find_one({"phone_number": norm_phone})

        is_new_user = False
        if not user:
            is_new_user = True
            user_id = str(uuid.uuid4())
            display_name = req.name or f"Learner {norm_phone[-4:]}"
            user_doc = {
                "id": user_id,
                "email": f"wa_{norm_phone.replace('+', '')}@cognify.edu",
                "full_name": display_name,
                "role": "student",
                "phone_number": norm_phone,
                "phone_verified": True,
                "preferred_contact_method": "whatsapp",
                "is_active": True,
                "profile_completed": False,
                "created_via": "whatsapp_direct_enroll",
                "created_at": now_iso,
                "updated_at": now_iso
            }
            await db.users.insert_one(user_doc)

            # Insert default student profile
            await db.student_profiles.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "grade": "Unassigned",
                "section": "A",
                "phone": norm_phone,
                "organization_id": None,
                "enrolled_courses": [],
                "created_at": now_iso
            })
        else:
            user_id = user["id"]
            display_name = user.get("full_name") or f"Learner {norm_phone[-4:]}"

        # Generate OTP
        otp_service = OTPService(db)
        try:
            code, meta = await otp_service.generate_and_store_otp(norm_phone, purpose="login")
        except HTTPException as e:
            if e.status_code == 429:
                return {
                    "ok": True,
                    "already_sent": True,
                    "is_new_user": is_new_user,
                    "phone": norm_phone,
                    "message": "OTP was already generated recently. Please use the code already received."
                }
            raise e

        # Dispatch OTP via WhatsApp microservice
        login_url = "http://localhost:3000/login"
        wa_otp_msg = (
            f"🔐 *Your Cognify Verification Code*: *{code}*\n\n"
            f"👋 Hello {display_name}!\n"
            f"{'🎉 Your Cognify account has been created!' if is_new_user else 'Welcome back to Cognify!'}\n\n"
            f"Use your phone number: *{norm_phone}* and OTP code: *{code}* to log in.\n\n"
            f"🚀 Login: {login_url}\n"
            f"After login, you can immediately explore courses and complete your profile!"
        )

        send_res = await svc.send_message(norm_phone, wa_otp_msg)

        return {
            "ok": True,
            "is_new_user": is_new_user,
            "phone": norm_phone,
            "code": code,
            "dispatched": send_res.get("ok", False)
        }

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
