"""WhatsApp Admin API Routes for Cognify."""
from __future__ import annotations
import asyncio
import os
import ipaddress
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
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


class WhatsAppQuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1500)
    language: str = "en"


class WhatsAppLearningRequest(BaseModel):
    sender_jid: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    phone_number: Optional[str] = None


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
            from gtts.lang import tts_langs
            import imageio_ffmpeg
            import subprocess
            import tempfile
            import base64
            import os

            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            tts_lang = req.lang or "en"
            if tts_lang not in tts_langs():
                return {"ok": False, "error": f"Cognify voice generation does not support language code '{tts_lang}'"}
            tts = gTTS(text=req.text, lang=tts_lang, tld="co.uk")

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

    @router.post("/answer")
    async def whatsapp_answer(req: WhatsAppQuestionRequest, request: Request):
        """Answer WhatsApp questions using Cognify information and the public course catalogue."""
        client_host = request.client.host if request.client else ""
        try:
            is_local_request = ipaddress.ip_address(client_host).is_loopback
        except ValueError:
            is_local_request = False
        if not is_local_request:
            raise HTTPException(status_code=403, detail="This endpoint is for the local WhatsApp service")

        course_filter = {
            "is_active": True,
            "$or": [
                {"organization_id": None},
                {"organization_id": {"$exists": False}},
                {"is_public": True},
                {"visibility": "public"},
            ],
        }
        course_projection = {
            "_id": 0,
            "name": 1,
            "title": 1,
            "description": 1,
            "subject": 1,
            "grade_level": 1,
            "duration_hours": 1,
            "duration_weeks": 1,
            "duration_months": 1,
            "is_free": 1,
            "price": 1,
            "currency": 1,
            "credits": 1,
        }
        courses = []
        try:
            courses = await asyncio.wait_for(
                db.courses.find(course_filter, course_projection).limit(30).to_list(length=30),
                timeout=2.5,
            )
        except Exception as e:
            logger.warning("WhatsApp answer catalogue unavailable: %s", e)

        language = req.language if req.language in {"en", "sn", "nd"} else "en"
        has_model_endpoint = bool(
            (os.environ.get("EMERGENT_API_BASE") and os.environ.get("EMERGENT_LLM_KEY"))
            or (os.environ.get("OPENAI_API_KEY") and not os.environ["OPENAI_API_KEY"].startswith("sk-dummy"))
        )
        if not has_model_endpoint:
            question = req.question.strip().lower()
            pricing_terms = ("fee", "fees", "price", "cost", "payment", "pay", "invoice", "tuition")
            course_terms = ("course", "catalog", "programme", "program", "study", "learn")
            if any(term in question for term in course_terms) and not any(term in question for term in pricing_terms):
                if courses:
                    course_lines = []
                    seen_courses = set()
                    for course in courses[:12]:
                        title = course.get("title") or course.get("name") or "Course"
                        if title.strip().casefold() in seen_courses:
                            continue
                        seen_courses.add(title.strip().casefold())
                        details = [course.get("subject"), course.get("grade_level")]
                        details = [detail for detail in details if detail]
                        line = f"- {title}"
                        if details:
                            line += f" ({', '.join(details)})"
                        if course.get("is_free"):
                            line += " - Free"
                        elif course.get("price") is not None and course.get("price") > 0:
                            line += f" — {course.get('currency') or 'USD'} {course['price']}"
                        course_lines.append(line)
                    reply = "Here are courses currently listed in Cognify:\n" + "\n".join(course_lines)
                else:
                    reply = "I can't retrieve the live course catalogue right now. Sign in to Cognify and open Course Catalogue to see current courses and details."
            elif any(term in question for term in ("enroll", "enrol", "register", "registration", "join")):
                reply = "To start enrollment, reply ENROLL here. I can guide you through account setup and send a sign-in verification code to this WhatsApp number."
            elif any(term in question for term in ("fee", "fees", "price", "cost", "payment", "pay", "invoice", "tuition")):
                priced_courses = [
                    course for course in courses
                    if course.get("is_free") or (course.get("price") is not None and course.get("price") > 0)
                ]
                if priced_courses:
                    price_lines = []
                    seen_courses = set()
                    for course in priced_courses[:12]:
                        title = course.get("title") or course.get("name") or "Course"
                        if title.strip().casefold() in seen_courses:
                            continue
                        seen_courses.add(title.strip().casefold())
                        if course.get("is_free"):
                            price_lines.append(f"- {title}: Free")
                        else:
                            price_lines.append(
                                f"- {title}: {course.get('currency') or 'USD'} {course['price']}"
                            )
                    pricing_details = "\n".join(price_lines)
                else:
                    pricing_details = "Current course prices aren't available in the catalogue data I can access. Check the course page in Cognify for its current price."
                reply = (
                    f"{pricing_details}\n\n"
                    "You can pay through Cognify's Paynow page: https://www.paynow.co.zw/aiia. "
                    "For a payment or invoice status, sign in and check Fees & Payments."
                )
            elif any(term in question for term in ("otp", "login", "log in", "password", "account", "verification")):
                reply = "For account access, open Cognify and use the phone sign-in/verification flow. If you started WhatsApp enrollment, the verification code is sent in a separate message. Never share your code with anyone."
            elif any(term in question for term in ("certificate", "certification", "credential")):
                reply = "Cognify provides course learning and certificate features. Available credentials depend on the course and your completion status; check the course page and your Certificates area for details."
            elif any(term in question for term in ("support", "contact", "help", "number", "whatsapp")):
                reply = "Cognify WhatsApp support is available on this number: +263790499962. You can also email support@cognify.com. For account-specific help, please sign in first."
            else:
                reply = "I can help with Cognify courses, enrollment, account access, fees and payments, certificates, and support. Ask me about one of those, or sign in to Cognify for account-specific information."
            return {"ok": True, "reply": reply}

        try:
            from services.ai_provider import ai_provider
        except ImportError:
            from backend.services.ai_provider import ai_provider

        system_prompt = (
            "You are Cognify's WhatsApp information assistant. Answer questions about Cognify, "
            "its learning platform, courses, enrollment, student accounts, payments, certificates, "
            "and support. Use only the current course catalogue supplied with the question and "
            "information explicitly supported by the question or Cognify context. Do not invent "
            "course availability, prices, accreditation, deadlines, policies, or account/payment "
            "status. If information is missing, say so briefly and direct the user to sign in to "
            "Cognify or contact support. Do not expose another learner's data. For unrelated "
            "questions, politely say you can help with Cognify services. Keep replies concise and "
            f"answer in language code {language}."
        )
        question = (
            f"Question: {req.question.strip()}\n\n"
            "Current public course catalogue (JSON):\n"
            f"{json.dumps(courses, ensure_ascii=False, default=str)}"
        )
        try:
            reply = await ai_provider.chat_completion(
                [{"role": "user", "content": question}],
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=600,
            )
            return {"ok": True, "reply": reply}
        except Exception as e:
            logger.exception("WhatsApp Cognify question answering failed")
            raise HTTPException(status_code=503, detail="Cognify answers are temporarily unavailable") from e

    @router.post("/learning")
    async def whatsapp_learning(req: WhatsAppLearningRequest, request: Request):
        """List, enroll in, and access stored Cognify course content from WhatsApp."""
        client_host = request.client.host if request.client else ""
        try:
            is_local_request = ipaddress.ip_address(client_host).is_loopback
        except ValueError:
            is_local_request = False
        if not is_local_request:
            raise HTTPException(status_code=403, detail="This endpoint is for the local WhatsApp service")

        import re
        sender_jid = req.sender_jid.strip()
        command = req.message.strip()
        lowered = command.casefold()
        session_col = db.whatsapp_learning_sessions
        session = await session_col.find_one({"sender_jid": sender_jid}, {"_id": 0}) or {}
        language = session.get("language", "en")

        from services.otp_service import normalize_phone_number
        phone_number = None
        try:
            if req.phone_number:
                phone_number = normalize_phone_number(req.phone_number)
        except ValueError:
            phone_number = None
        if phone_number:
            await session_col.update_one(
                {"sender_jid": sender_jid},
                {"$set": {"sender_jid": sender_jid, "phone_number": phone_number}},
                upsert=True,
            )
        else:
            phone_number = session.get("phone_number")
        user = await db.users.find_one({"phone_number": phone_number}, {"_id": 0}) if phone_number else None

        lang_match = re.fullmatch(r"(?:lang|language)\s+([a-zA-Z-]{2,20})", command, re.IGNORECASE)
        if lang_match:
            requested_language = lang_match.group(1).lower()
            try:
                from services.multilingual import SUPPORTED_LANGUAGES
            except ImportError:
                from backend.services.multilingual import SUPPORTED_LANGUAGES
            language = requested_language if requested_language in SUPPORTED_LANGUAGES else next(
                (code for code, details in SUPPORTED_LANGUAGES.items()
                 if requested_language in {details["name"].lower(), details["native"].lower()}),
                None,
            )
            if not language:
                supported = ", ".join(SUPPORTED_LANGUAGES.keys())
                return {"reply": f"That language isn't in Cognify's supported list. Use one of these codes: {supported}. Example: LANG sn."}
            await session_col.update_one(
                {"sender_jid": sender_jid},
                {"$set": {"sender_jid": sender_jid, "language": language, **({"phone_number": phone_number} if phone_number else {})}},
                upsert=True,
            )
            return {"reply": f"Language preference saved as {language}. Send COURSES to browse Cognify's catalogue."}

        org_id = user.get("organization_id") if user else None
        course_filter = {
            "is_active": True,
            "$or": ([{"organization_id": org_id}] if org_id else []) + [
                {"organization_id": None},
                {"organization_id": {"$exists": False}},
                {"is_public": True},
                {"visibility": "public"},
            ],
        }
        courses = await db.courses.find(course_filter, {"_id": 0}).limit(100).to_list(length=100)
        unique_courses = []
        seen_courses = set()
        for course in courses:
            title = (course.get("title") or course.get("name") or "").strip().casefold()
            code = (course.get("code") or "").strip().casefold()
            org = course.get("organization_id") or course.get("org_id") or ""
            identity = (title, code, org)
            if title and identity not in seen_courses:
                seen_courses.add(identity)
                unique_courses.append(course)
        courses = unique_courses

        if lowered in {"help", "menu", "start", "learning"}:
            return {"reply": "Cognify WhatsApp learning commands:\nCOURSES - list available courses\nENROLL COURSE <number> - enroll in a course\nLEARN <number> - select an enrolled course\nTEXT / AUDIO / SLIDES / VIDEO - choose a lesson mode\nNEXT - continue to the next lesson\nLANG <code> - set language, e.g. LANG sn or LANG fr"}

        course_list_request = lowered in {"courses", "course", "catalog", "catalogue", "programs", "programmes", "available courses"} or bool(
            re.search(r"\b(what|which|show|list|available)\b.*\b(courses?|catalogue|catalog|programmes?|programs?)\b", lowered)
        )
        if course_list_request:
            if not courses:
                return {"reply": "There are no active public courses in Cognify's catalogue right now."}
            lines = ["*Active Cognify courses:*\n"]
            for index, course in enumerate(courses, 1):
                title = course.get("title") or course.get("name") or course.get("code") or f"Course {index}"
                description = (course.get("description") or "").strip()
                price = float(course.get("price") or course.get("total_price") or 0)
                is_free = course.get("is_free", price == 0)
                fee = "Free" if is_free else f"{course.get('currency') or 'USD'} {price:g}"
                lines.append(f"{index}. *{title}* - {fee}")
                if description:
                    lines.append(f"   {description[:180]}")
            lines.append("\nReply *ENROLL COURSE <number>* to enroll in a free course, or *LEARN <number>* to open a course you already have access to.")
            return {"reply": "\n".join(lines)}

        enroll_match = re.fullmatch(r"enroll\s+course\s+(\d+)", command, re.IGNORECASE)
        learn_match = re.fullmatch(r"learn(?:\s+(\d+))?", command, re.IGNORECASE)
        mode_match = re.fullmatch(r"(?:mode\s+)?(text|audio|slides?|video)", command, re.IGNORECASE)
        next_match = lowered in {"next", "next lesson"}
        if not (enroll_match or learn_match or mode_match or next_match):
            if any(phrase in lowered for phrase in ("how do i enroll", "how can i enroll", "how to enroll", "how do i register")):
                return {"reply": "To study on Cognify WhatsApp: first send ENROLL <your mobile number> to set up/sign in. Then send COURSES, choose a course with ENROLL COURSE <number>, and use LEARN <number> to start after access is confirmed."}
            return {"reply": "I can help with Cognify courses and lessons. Send COURSES to browse, ENROLL COURSE <number> to enroll, LEARN <number> to open an enrolled course, or MODE TEXT/AUDIO/SLIDES/VIDEO."}

        if not user:
            return {"reply": "To enroll or open course lessons, first connect your Cognify account by replying *ENROLL <your mobile number>* (for example, ENROLL 0771234567). Then repeat your course command. You can browse COURSES without an account."}
        if user.get("role") != "student":
            return {"reply": "WhatsApp course learning is available for student accounts. Sign in to Cognify with a student account to continue."}

        profile = await db.student_profiles.find_one({"user_id": user["id"]}, {"_id": 0}) or {}
        enrolled_ids = set(profile.get("enrolled_courses", []))
        paid_enrollments = await db.enrollments.find(
            {"student_id": user["id"], "payment_status": "completed"}, {"_id": 0, "course_id": 1}
        ).to_list(length=200)
        enrolled_ids.update(item.get("course_id") for item in paid_enrollments if item.get("course_id"))

        if enroll_match:
            course_index = int(enroll_match.group(1))
            if course_index < 1 or course_index > len(courses):
                return {"reply": "That course number is not in the current Cognify catalogue. Send COURSES to see the available numbers."}
            course = courses[course_index - 1]
            course_id = course["id"]
            price = float(course.get("price") or course.get("total_price") or 0)
            is_free = course.get("is_free", price == 0)
            if not is_free and price > 0 and course_id not in enrolled_ids:
                payment = await db.payments.find_one(
                    {"user_id": user["id"], "course_id": course_id, "status": "paid"}, {"_id": 0, "id": 1}
                )
                if not payment:
                    return {"reply": f"*{course.get('title') or course.get('name')}* requires payment ({course.get('currency') or 'USD'} {price:g}). Use Cognify's payment page: https://www.paynow.co.zw/aiia. After payment is recorded, send ENROLL COURSE {course_index} again."}
            if course_id in enrolled_ids:
                return {"reply": f"You are already enrolled in *{course.get('title') or course.get('name')}*. Send LEARN {course_index} to begin."}
            await db.student_profiles.update_one(
                {"user_id": user["id"]},
                {"$setOnInsert": {"user_id": user["id"], "completed_courses": [], "quiz_scores": []},
                 "$addToSet": {"enrolled_courses": course_id}},
                upsert=True,
            )
            await db.courses.update_one({"id": course_id}, {"$addToSet": {"enrolled_students": user["id"]}})
            return {"reply": f"You are enrolled in *{course.get('title') or course.get('name')}*. Send LEARN {course_index} to open its lessons."}

        selected_course_id = session.get("course_id")
        if learn_match and learn_match.group(1):
            course_index = int(learn_match.group(1))
            if course_index < 1 or course_index > len(courses):
                return {"reply": "That course number is not in the current Cognify catalogue. Send COURSES to see the available numbers."}
            course = courses[course_index - 1]
            selected_course_id = course["id"]
            if selected_course_id not in enrolled_ids:
                return {"reply": f"Your account isn't enrolled in *{course.get('title') or course.get('name')}*. Send ENROLL COURSE {course_index} to check enrollment options."}
            await session_col.update_one(
                {"sender_jid": sender_jid},
                {"$set": {"sender_jid": sender_jid, "phone_number": phone_number, "course_id": selected_course_id, "lesson_index": 0}},
                upsert=True,
            )
        elif selected_course_id not in enrolled_ids:
            return {"reply": "Select a course you are enrolled in first. Send COURSES, then LEARN <number>."}

        course = next((item for item in courses if item.get("id") == selected_course_id), None)
        if not course:
            return {"reply": "That course is no longer in the active Cognify catalogue. Send COURSES to refresh your list."}

        course_price = float(course.get("price") or course.get("total_price") or 0)
        if not course.get("is_free", course_price == 0) and course_price > 0:
            payment = await db.payments.find_one(
                {"user_id": user["id"], "course_id": selected_course_id, "status": "paid"},
                {"_id": 0, "id": 1},
            )
            completed_enrollment = await db.enrollments.find_one(
                {"student_id": user["id"], "course_id": selected_course_id, "payment_status": "completed"},
                {"_id": 0, "id": 1},
            )
            if not payment and not completed_enrollment:
                return {"reply": f"Access to *{course.get('title') or course.get('name')}* is locked until Cognify records its payment. Use https://www.paynow.co.zw/aiia, then check Fees & Payments or contact support."}

        if mode_match:
            selected_mode = mode_match.group(1).lower().rstrip("s")
            if selected_mode == "slide":
                selected_mode = "slides"
            await session_col.update_one(
                {"sender_jid": sender_jid}, {"$set": {"mode": selected_mode}}, upsert=True
            )
            session["mode"] = selected_mode
        selected_mode = session.get("mode", "text")

        contents = await db.course_contents.find(
            {"course_id": selected_course_id}, {"_id": 0}
        ).to_list(length=200)
        lessons = await db.lessons.find(
            {"course_id": selected_course_id}, {"_id": 0}
        ).sort("order", 1).to_list(length=100)
        items_by_id = {}
        for index, item in enumerate(contents + lessons):
            item_id = item.get("id") or f"{item.get('title', 'item')}:{index}"
            if item_id in items_by_id:
                merged = {**items_by_id[item_id], **item}
                for text_key in ("text", "content", "content_text", "description"):
                    merged[text_key] = item.get(text_key) or items_by_id[item_id].get(text_key)
                items_by_id[item_id] = merged
            else:
                items_by_id[item_id] = item
        items = sorted(items_by_id.values(), key=lambda item: (item.get("order", 999), item.get("title", "")))
        if not items and course.get("lessons"):
            items = course["lessons"]

        def item_type(item):
            kind = str(item.get("type") or item.get("content_type") or "text").lower()
            url = str(item.get("url") or item.get("video_url") or item.get("audio_url") or "").lower()
            if "video" in kind or url.endswith((".mp4", ".mov", ".webm", ".avi")):
                return "video"
            if "audio" in kind or item.get("audio_url") or url.endswith((".mp3", ".wav", ".ogg", ".m4a")):
                return "audio"
            if any(token in kind for token in ("slide", "presentation", "document")) or url.endswith((".pdf", ".ppt", ".pptx")):
                return "slides"
            return "text"

        if selected_mode == "text":
            candidates = [item for item in items if item.get("text") or item.get("content") or item.get("content_text") or item.get("description")]
        else:
            candidates = [item for item in items if item_type(item) == selected_mode]
            if selected_mode == "audio" and not candidates:
                candidates = [item for item in items if item.get("text") or item.get("content") or item.get("content_text")]

        if not candidates:
            return {"reply": f"Cognify has no {selected_mode} lesson material uploaded for *{course.get('title') or course.get('name')}* yet. Try MODE TEXT or another available mode."}

        lesson_index = int(session.get("lesson_index", 0))
        if next_match:
            lesson_index += 1
            await session_col.update_one(
                {"sender_jid": sender_jid}, {"$set": {"lesson_index": lesson_index}}, upsert=True
            )
        if lesson_index >= len(candidates):
            return {"reply": "You've reached the end of the available Cognify material in this mode. Choose another mode or send LEARN <number> to restart a course."}

        item = candidates[lesson_index]
        title = item.get("title") or item.get("name") or f"Lesson {lesson_index + 1}"
        body = item.get("text") or item.get("content") or item.get("content_text") or item.get("description") or ""
        media_url = item.get("url") or item.get("video_url") or item.get("audio_url")
        media = None
        if selected_mode == "text" or (selected_mode == "audio" and not media_url):
            reply = f"*{course.get('title') or course.get('name')} - {title}*\n\n{body[:3500]}"
            if selected_mode == "audio":
                media = {"type": "tts", "text": body[:3500], "language": language}
        else:
            reply = f"*{course.get('title') or course.get('name')} - {title}*"
            if media_url:
                media = {
                    "type": selected_mode,
                    "url": media_url,
                    "mime_type": item.get("mime_type"),
                    "filename": item.get("original_filename") or item.get("filename") or f"{title}.{ 'mp4' if selected_mode == 'video' else 'pdf' }",
                    "caption": reply,
                }
            elif body:
                reply += f"\n\n{body[:3000]}"
        if lesson_index + 1 < len(candidates):
            reply += f"\n\nSend NEXT for item {lesson_index + 2} of {len(candidates)}."

        has_translation_model = bool(os.environ.get("EMERGENT_API_BASE") and os.environ.get("EMERGENT_LLM_KEY")) or bool(os.environ.get("OPENAI_API_KEY"))
        if language != "en":
            if has_translation_model:
                try:
                    from services.multilingual import translate_text
                except ImportError:
                    from backend.services.multilingual import translate_text
                translated, error = await translate_text(reply, language, "en")
                if translated and not error:
                    reply = translated
                    if media:
                        media["caption"] = translated
                        if media.get("type") == "tts":
                            media["text"] = translated
            else:
                reply += f"\n\nTranslation to {language} isn't configured in Cognify right now; the course material is shown in its original language."
                if media and media.get("type") == "tts":
                    media = None

        return {"reply": reply, "media": media}

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
