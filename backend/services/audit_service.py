"""Audit Logging Service for Cognify.

Tracks all financial and administrative operations immutably.
Logs:
- Manual payments (EcoCash, Bank Transfer, Cash)
- Payment reversals / adjustments / voids
- Enrolments and manual enrolments
- Administrative phone verifications
- Assessment overrides
- Organisation permission changes
"""
from __future__ import annotations
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class AuditService:
    def __init__(self, db):
        self.db = db

    async def log(
        self,
        actor_id: str,
        action: str,
        entity: str,
        entity_id: str,
        organisation_id: Optional[str] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> dict:
        """Create an immutable audit log entry."""
        # Sanitize sensitive fields if present
        def sanitize(v):
            if not isinstance(v, dict):
                return v
            clean = dict(v)
            for k in ["password", "password_hash", "otp", "otp_hash", "token", "secret"]:
                if k in clean:
                    clean[k] = "[REDACTED]"
            return clean

        record = {
            "id": str(uuid.uuid4()),
            "actor_id": actor_id,
            "organisation_id": organisation_id,
            "action": action,
            "entity": entity,
            "entity_id": entity_id,
            "old_value": sanitize(old_value) if old_value else None,
            "new_value": sanitize(new_value) if new_value else None,
            "reason": reason,
            "ip_address": ip_address,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        try:
            await self.db.audit_logs.insert_one(dict(record))
            # Also sync into payment_audit_logs if financial
            if entity in ["payment", "enrollment", "financial_period"]:
                await self.db.payment_audit_logs.insert_one(dict(record))
        except Exception as e:
            logger.error(f"Audit log insertion failed: {e}")

        record.pop("_id", None)
        return record

    async def list_logs(
        self,
        organisation_id: Optional[str] = None,
        entity: Optional[str] = None,
        entity_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Query audit logs respecting organisation boundaries."""
        query = {}
        if organisation_id:
            query["organisation_id"] = organisation_id
        if entity:
            query["entity"] = entity
        if entity_id:
            query["entity_id"] = entity_id

        cursor = self.db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).skip(offset).limit(limit)
        return await cursor.to_list(limit)
