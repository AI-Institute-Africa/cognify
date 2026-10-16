"""Unit tests for services/audit_service.py — BRD section 8/9 (unified audit log)
and AC-13 ("All manual payment and enrolment actions appear in the audit log").
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.audit_service import log_action, list_actions


async def test_log_action_writes_canonical_and_legacy_fields(fake_db):
    entry = await log_action(
        fake_db,
        actor_id="admin-1",
        action="record_manual_payment",
        entity="payment",
        entity_id="pay-1",
        organisation_id="org-1",
        new_value={"amount": 50, "method": "ecocash"},
        reason="EcoCash top-up",
    )
    assert entry["actor_id"] == "admin-1"
    assert entry["entity"] == "payment"
    # Legacy field names kept for the existing super-admin payment-audit dashboard.
    assert entry["target_type"] == "payment"
    assert entry["target_id"] == "pay-1"
    assert entry["metadata"] == {"amount": 50, "method": "ecocash"}

    stored = await fake_db.audit_logs.find_one({"id": entry["id"]})
    assert stored is not None


async def test_list_actions_filters_by_entity_and_org(fake_db):
    await log_action(fake_db, actor_id="a1", action="record_manual_payment", entity="payment", organisation_id="org-1")
    await log_action(fake_db, actor_id="a1", action="create_learner", entity="user", organisation_id="org-1")
    await log_action(fake_db, actor_id="a2", action="record_manual_payment", entity="payment", organisation_id="org-2")

    org1_payments = await list_actions(fake_db, entity="payment", organisation_id="org-1")
    assert len(org1_payments) == 1
    assert org1_payments[0]["action"] == "record_manual_payment"

    all_org1 = await list_actions(fake_db, organisation_id="org-1")
    assert len(all_org1) == 2
