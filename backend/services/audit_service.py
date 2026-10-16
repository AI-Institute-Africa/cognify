"""Unified audit log — BRD CR 2026-10, section 8/9 (Security & Audit Requirements, Data Model).

Single collection (`audit_logs`) for every admin/financial/account mutation: manual
payments, manual enrolment, phone verification, role changes. Replaces the
payments-only `payment_audit_logs` collection written by
services.payment_platform.PaymentPlatformService.audit(), which now delegates here.

Each document carries both the canonical BRD field names (entity/entity_id/old_value/
new_value/timestamp) and the legacy payment-dashboard field names (target_type/
target_id/metadata/created_at) so the existing super-admin payment audit view keeps
working unmodified against the unified collection.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional


async def log_action(
    db,
    *,
    actor_id: str,
    action: str,
    entity: str,
    entity_id: Optional[str] = None,
    organisation_id: Optional[str] = None,
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
    reason: Optional[str] = None,
) -> dict:
    """Write one audit entry. Call this for every manual payment, enrolment,
    phone-verification, or role/permission change — never skip it for a mutation
    a Super Admin or Organisation Admin performs on someone else's behalf."""
    now = datetime.now(timezone.utc)
    entry = {
        "id": str(uuid.uuid4()),
        "actor_id": actor_id,
        "organisation_id": organisation_id,
        "action": action,
        "entity": entity,
        "entity_id": entity_id,
        "old_value": old_value,
        "new_value": new_value,
        "reason": reason,
        "timestamp": now.isoformat(),
        # Legacy-compatible aliases for the existing payment audit dashboard
        # (backend/routes/payment_routes.py GET /super-admin/.../audit-logs).
        "target_type": entity,
        "target_id": entity_id,
        "metadata": new_value or {},
        "created_at": now.isoformat(),
    }
    await db.audit_logs.insert_one(entry)
    return entry


async def list_actions(
    db,
    *,
    entity: Optional[str] = None,
    organisation_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    limit: int = 200,
) -> list:
    query: dict = {}
    if entity:
        query["entity"] = entity
    if organisation_id:
        query["organisation_id"] = organisation_id
    if actor_id:
        query["actor_id"] = actor_id
    cursor = db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit)
    return await cursor.to_list(length=limit)
