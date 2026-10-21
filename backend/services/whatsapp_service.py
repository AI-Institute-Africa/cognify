"""Cognify WhatsApp Service — proxies to the Baileys Node.js microservice."""
from __future__ import annotations
import os
import logging
import httpx
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

WHATSAPP_SERVICE_URL = os.environ.get("WHATSAPP_SERVICE_URL", "http://localhost:3001")


class WhatsAppService:
    """Proxy client for the Cognify WhatsApp Node.js microservice."""

    def __init__(self, db=None):
        self.db = db
        self.base_url = WHATSAPP_SERVICE_URL

    async def _get(self, path: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10.0) as c:
                r = await c.get(f"{self.base_url}{path}")
                return r.json()
        except Exception as e:
            logger.warning(f"WhatsApp service GET {path} failed: {e}")
            return {}

    async def _post(self, path: str, data: dict = None) -> dict:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.post(f"{self.base_url}{path}", json=data or {})
                return r.json()
        except Exception as e:
            logger.warning(f"WhatsApp service POST {path} failed: {e}")
            return {"error": str(e)}

    async def get_status(self) -> dict:
        return await self._get("/status")

    async def connect(self, method: str = "qr", phone_number: str = None) -> dict:
        return await self._post("/connect", {"method": method, "phone_number": phone_number})

    async def disconnect(self) -> dict:
        return await self._post("/disconnect")

    async def send_message(self, to_phone: str, message: str) -> dict:
        return await self._post("/send", {"to": to_phone, "message": message})

    async def get_messages(self) -> dict:
        return await self._get("/messages")

    async def get_settings(self) -> dict:
        return await self._get("/settings")

    async def update_settings(self, settings: dict) -> dict:
        return await self._post("/settings", settings)

    async def toggle_ai(self) -> dict:
        return await self._post("/settings/toggle-ai")

    async def pause_ai(self, hours: int) -> dict:
        return await self._post("/settings/pause", {"hours": hours})

    async def get_community_url(self) -> str:
        r = await self._get("/community-url")
        return r.get("url", "")

    async def send_alert(self, to_phones: List[str], message: str):
        """Send an alert to multiple phone numbers."""
        results = []
        for phone in to_phones:
            r = await self.send_message(phone, message)
            results.append({"phone": phone, "result": r})
        return results
