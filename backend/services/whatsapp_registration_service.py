"""WhatsApp-based Registration Architecture & Webhook Handler for Cognify.

Enables prospective learners to register directly via WhatsApp:
1. User initiates conversation via WhatsApp.
2. System tracks conversational state machine in `db.whatsapp_registration_sessions`.
3. Collects required registration details: Full Name, Password.
4. Auto-verifies the phone number based on WhatsApp authentication.
5. Checks uniqueness (prevents duplicate verified accounts).
6. Creates Cognify account and StudentProfile.
7. Dispatches welcome message and login redirect link.
8. Idempotent processing using message SID / payload hashes.
"""
from __future__ import annotations
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import bcrypt

from services.otp_service import normalize_phone_number
from services.communication_service import NotificationService

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


class WhatsAppRegistrationService:
    def __init__(self, db):
        self.db = db
        self.notification_service = NotificationService(db)

    async def handle_incoming_message(
        self,
        from_phone: str,
        body_text: str,
        message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process incoming WhatsApp message through the registration state machine.
        
        Returns response dict containing `reply_text` and session metadata.
        """
        # Idempotency check on message_id
        if message_id:
            already_processed = await self.db.whatsapp_inbound_messages.find_one({"message_id": message_id})
            if already_processed:
                return {"reply_text": None, "duplicate": True}
            await self.db.whatsapp_inbound_messages.insert_one({
                "message_id": message_id,
                "from_phone": from_phone,
                "created_at": datetime.now(timezone.utc).isoformat()
            })

        norm_phone = normalize_phone_number(from_phone)
        text = body_text.strip()

        # Check if active verified account already exists for this phone
        existing_user = await self.db.users.find_one({
            "phone_number": norm_phone,
            "is_active": {"$ne": False}
        }, {"_id": 0, "id": 1, "full_name": 1, "phone_verified": 1})

        if existing_user and existing_user.get("phone_verified"):
            reply = (
                f"Hello {existing_user.get('full_name', '')}! You already have an active Cognify account "
                f"associated with {norm_phone}.\n\n"
                f"You can log in to your account at: http://localhost:3000/login\n"
                f"If you need to reset your password, visit: http://localhost:3000/forgot-password"
            )
            return {"reply_text": reply, "status": "already_registered"}

        # Fetch or initialize session
        session = await self.db.whatsapp_registration_sessions.find_one({
            "phone_number": norm_phone,
            "status": "in_progress"
        })

        now = datetime.now(timezone.utc).isoformat()

        if not session:
            # Start new registration session
            new_session = {
                "id": str(uuid.uuid4()),
                "phone_number": norm_phone,
                "step": "AWAITING_NAME",
                "collected_data": {},
                "status": "in_progress",
                "created_at": now,
                "updated_at": now
            }
            await self.db.whatsapp_registration_sessions.insert_one(new_session)
            reply = (
                "👋 Welcome to *COGNIFY*!\n"
                "“The Global Nervous System for Knowledge”\n"
                "“Transforming minds. Empowering Nations.”\n\n"
                "Let's get your learner account created in a few seconds.\n"
                "Please reply with your *Full Name*:"
            )
            return {"reply_text": reply, "step": "AWAITING_NAME"}

        current_step = session.get("step")

        if current_step == "AWAITING_NAME":
            if len(text) < 2:
                return {
                    "reply_text": "Please enter a valid full name (at least 2 letters):",
                    "step": "AWAITING_NAME"
                }

            await self.db.whatsapp_registration_sessions.update_one(
                {"id": session["id"]},
                {"$set": {
                    "step": "AWAITING_PASSWORD",
                    "collected_data.full_name": text,
                    "updated_at": now
                }}
            )
            reply = (
                f"Nice to meet you, *{text}*!\n\n"
                "Now, please create a secure *password* for your account (minimum 6 characters):"
            )
            return {"reply_text": reply, "step": "AWAITING_PASSWORD"}

        elif current_step == "AWAITING_PASSWORD":
            if len(text) < 6:
                return {
                    "reply_text": "Password must be at least 6 characters long. Please enter a stronger password:",
                    "step": "AWAITING_PASSWORD"
                }

            full_name = session.get("collected_data", {}).get("full_name", "Student")
            password = text

            # Create User Account
            user_id = str(uuid.uuid4())
            user_doc = {
                "id": user_id,
                "email": None,  # Optional for phone registration
                "phone_number": norm_phone,
                "phone_verified": True,  # Verified via WhatsApp origin
                "phone_verified_at": now,
                "preferred_contact_method": "whatsapp",
                "full_name": full_name,
                "role": "student",
                "password_hash": hash_password(password),
                "is_active": True,
                "registration_source": "whatsapp",
                "created_at": now,
                "updated_at": now
            }

            await self.db.users.insert_one(user_doc)

            # Create Student Profile
            student_profile = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "student_id": f"STU{user_id[:8].upper()}",
                "grade_level": "Grade 10",
                "section": "A",
                "phone": norm_phone,
                "enrolled_courses": [],
                "created_at": now
            }
            await self.db.student_profiles.insert_one(student_profile)

            # Mark session completed
            await self.db.whatsapp_registration_sessions.update_one(
                {"id": session["id"]},
                {"$set": {
                    "status": "completed",
                    "step": "COMPLETED",
                    "user_id": user_id,
                    "updated_at": now
                }}
            )

            reply = (
                f"🎉 Congratulations, *{full_name}*!\n"
                "Your Cognify account has been successfully created!\n\n"
                f"📱 *Phone:* {norm_phone}\n"
                "🎓 *Role:* Student\n\n"
                "You can now log in at: http://localhost:3000/login\n"
                "Explore courses, chat with your AI Personal Mentor, and start learning today!"
            )
            return {"reply_text": reply, "status": "completed", "user_id": user_id}

        return {"reply_text": "Please reply to continue your registration.", "step": current_step}
