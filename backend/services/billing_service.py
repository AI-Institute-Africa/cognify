"""
Cognify AI Billing Integration Service
Connects Cognify Learning Platform with the Cognify AI Billing System.
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

BILLING_URL = os.environ.get("COGNIFY_BILLING_URL", "http://127.0.0.1:8001").rstrip("/")
INTEGRATION_KEY = os.environ.get(
    "COGNIFY_COURSE_PAYMENT_INTEGRATION_KEY",
    "MN9pnmF7iuSeoNunEVjbEll1Z7xRcHRxsp_YCbcX1rhJ_GwusrGHr8C7scgg_INW"
)


class BillingService:
    """Manages integration with the Cognify AI Billing System."""

    def __init__(self, db=None):
        self.db = db
        self.base_url = BILLING_URL
        self.integration_key = INTEGRATION_KEY

    def _admin_headers(self) -> Dict[str, str]:
        return {
            "X-Cognify-Integration-Key": self.integration_key,
            "Content-Type": "application/json",
        }

    def _user_headers(self, token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def sync_user(
        self,
        cognify_user_id: str,
        user_email: str,
        phone_verified: bool = False
    ) -> Dict[str, Any]:
        """
        Synchronize a user account with the billing system.
        Grants the lifetime free onboarding allowance and returns a user-scoped billing access token.
        """
        if not user_email:
            logger.warning(f"Cannot sync user {cognify_user_id} without email")
            return {}

        payload = {
            "cognify_user_id": str(cognify_user_id),
            "user_email": user_email.strip().lower(),
            "phone_verified": bool(phone_verified),
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{self.base_url}/integrations/cognify/users",
                    json=payload,
                    headers=self._admin_headers(),
                )
                if res.status_code >= 400:
                    logger.error(f"Billing user sync failed ({res.status_code}): {res.text}")
                    return {}

                data = res.json()
                billing_token = data.get("billing_access_token")
                billing_user_id = data.get("user_id")
                signup_credit = data.get("signup_credit_balance_minor", 0)

                # Save on the user's record in MongoDB if db reference exists
                if self.db is not None and billing_token:
                    await self.db.users.update_one(
                        {"id": cognify_user_id},
                        {
                            "$set": {
                                "billing_access_token": billing_token,
                                "billing_user_id": billing_user_id,
                                "signup_credit_balance_minor": signup_credit,
                                "billing_synced_at": datetime.now(timezone.utc).isoformat(),
                            }
                        }
                    )
                return data
        except Exception as e:
            logger.exception(f"Error syncing user {cognify_user_id} with billing API: {e}")
            return {}

    async def get_or_create_billing_token(self, user: Dict[str, Any]) -> Optional[str]:
        """
        Retrieve existing billing_access_token or automatically sync user to generate one.
        """
        if user.get("billing_access_token"):
            return user["billing_access_token"]

        sync_res = await self.sync_user(
            cognify_user_id=user["id"],
            user_email=user.get("email") or f"user_{user['id']}@cognify.africa",
            phone_verified=bool(user.get("phone_verified") or user.get("phone_number")),
        )
        return sync_res.get("billing_access_token")

    async def sync_course_payment(
        self,
        payment_id: str,
        enrollment_id: str,
        course_id: str,
        course_name: str,
        user_email: str,
        plan_code: str = "diploma-individual",
        course_price_minor: int = 4999,
        paid_total_minor: int = 4999,
        currency: str = "USD",
        course_end: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Notify billing system of a verified course payment/enrollment.
        Reserves capacity from Central Token Bank and funds the student's course wallet.
        """
        if course_end is None:
            # Default to 12 months access from now
            from datetime import timedelta
            end_dt = datetime.now(timezone.utc) + timedelta(days=365)
            course_end_str = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        elif hasattr(course_end, "strftime"):
            course_end_str = course_end.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            course_end_str = str(course_end)

        payload = {
            "payment_id": str(payment_id),
            "enrollment_id": str(enrollment_id),
            "course_id": str(course_id),
            "course_name": str(course_name or "Course"),
            "user_email": str(user_email).strip().lower(),
            "plan_code": plan_code or "diploma-individual",
            "course_price_minor": max(1, int(course_price_minor)),
            "paid_total_minor": max(1, int(paid_total_minor)),
            "currency": currency.upper() if currency else "USD",
            "course_end": course_end_str,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{self.base_url}/integrations/cognify/course-payments",
                    json=payload,
                    headers=self._admin_headers(),
                )
                if res.status_code >= 400:
                    logger.error(f"Billing course payment sync failed ({res.status_code}): {res.text}")
                    return {"status_code": res.status_code, "error": res.text}
                return res.json()
        except Exception as e:
            logger.exception(f"Error syncing course payment {payment_id}: {e}")
            return {"error": str(e)}

    async def sync_course_completion(
        self,
        enrollment_id: str,
        user_email: str,
        completion_event_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Notify billing system of course graduation or completion.
        Recycles unconsumed course tokens back into the Central Token Bank. Idempotent.
        """
        event_id = completion_event_id or f"compl-{enrollment_id}-{str(uuid.uuid4())[:8]}"
        payload = {
            "enrollment_id": str(enrollment_id),
            "user_email": str(user_email).strip().lower(),
            "completion_event_id": event_id,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{self.base_url}/integrations/cognify/course-completion",
                    json=payload,
                    headers=self._admin_headers(),
                )
                if res.status_code >= 400:
                    logger.error(f"Billing course completion sync failed ({res.status_code}): {res.text}")
                    return {"status_code": res.status_code, "error": res.text}
                return res.json()
        except Exception as e:
            logger.exception(f"Error syncing course completion for enrollment {enrollment_id}: {e}")
            return {"error": str(e)}

    async def estimate_usage(
        self,
        billing_access_token: str,
        resource: str,
        model: str,
        quantity: int = 1,
        input_units: int = 0,
        output_units: int = 0,
        quality: str = "standard",
    ) -> Dict[str, Any]:
        """
        Preflight cost estimation request before invoking AI providers.
        Throws HTTP 402 with appropriate top-up message if allowance is exhausted.
        Ensures text and audio are not blocked by media allowance exhaustion.
        """
        payload = {
            "resource": resource,
            "model": model,
            "quantity": quantity,
            "input_units": input_units,
            "output_units": output_units,
            "quality": quality,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{self.base_url}/usage/estimate",
                    json=payload,
                    headers=self._user_headers(billing_access_token),
                )
        except Exception as e:
            logger.warning(f"Billing estimate request network error: {e}")
            # If billing service is temporarily unreachable, do not hard-crash
            return {"quote_id": None, "affordable": True}

        # Handle 402 Payment Required or 429 Quota Exceeded
        if res.status_code in (402, 429):
            self._raise_topup_error(resource)

        if res.status_code >= 400:
            logger.error(f"Billing estimate returned {res.status_code}: {res.text}")
            # Check if 403 phone verification
            if res.status_code == 403:
                raise HTTPException(
                    status_code=403,
                    detail="Phone verification is required before using free AI credits."
                )
            raise HTTPException(status_code=res.status_code, detail=res.text)

        data = res.json()
        if not data.get("affordable", True):
            self._raise_topup_error(resource)

        return data

    def _raise_topup_error(self, resource: str):
        """Raise HTTP 402 with the exact requirement-specified top-up message."""
        if resource in ("image", "slides"):
            msg = (
                "Your free image and slide generation allowance has been used. "
                "Top up your AI tokens to continue learning using image and slide generation."
            )
        elif resource == "video":
            msg = (
                "You have used your free 12-second video generation allowance. "
                "Top up your AI tokens to continue learning with AI-generated videos."
            )
        else:
            msg = "Allocated credits are depleted; purchase a credit pack or upgrade your account to continue"

        raise HTTPException(status_code=402, detail=msg)

    async def settle_usage(
        self,
        billing_access_token: str,
        quote_id: Optional[str],
        resource: str,
        model: str,
        quantity: int = 1,
        input_units: int = 0,
        output_units: int = 0,
        quality: str = "standard",
        service: str = "ai_generation",
    ) -> Dict[str, Any]:
        """
        Settle actual AI generation usage against student's wallet via POST /gateway/route.
        """
        if not quote_id:
            logger.info("Skipping usage settlement: no quote_id")
            return {}

        payload = {
            "service": service,
            "quote_id": quote_id,
            "usage": {
                "resource": resource,
                "model": model,
                "quantity": quantity,
                "input_units": input_units,
                "output_units": output_units,
                "quality": quality,
                "idempotency_key": str(uuid.uuid4()),
            },
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{self.base_url}/gateway/route",
                    json=payload,
                    headers=self._user_headers(billing_access_token),
                )
                if res.status_code >= 400:
                    logger.warning(f"Billing settlement returned {res.status_code}: {res.text}")
                    return {"error": res.text, "status_code": res.status_code}
                return res.json()
        except Exception as e:
            logger.exception(f"Error settling billing usage for quote {quote_id}: {e}")
            return {"error": str(e)}

    async def get_entitlements(self, billing_access_token: str) -> Dict[str, Any]:
        """
        Fetch learner's live entitlement summary from GET /entitlements/me.
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(
                    f"{self.base_url}/entitlements/me",
                    headers=self._user_headers(billing_access_token),
                )
                if res.status_code >= 400:
                    logger.error(f"Entitlements fetch failed ({res.status_code}): {res.text}")
                    return {}
                return res.json()
        except Exception as e:
            logger.exception(f"Error fetching entitlements: {e}")
            return {}
