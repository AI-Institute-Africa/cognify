"""Entitlement Engine — central authority for 'can this user access X'.

Grants and checks entitlements across:
  - courses (paid one-time purchase, subscription-included, institution seat)
  - ai_features (metered / plan_included / paid_per_use)
  - add_ons

Collections used:
  - entitlements     : who has access to what and until when
  - ai_usage         : per-request metering log
  - subscriptions    : active subscription rows
  - courses / users / organizations : lookups
"""
from __future__ import annotations
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Feature slugs — used across the app for gating
FEATURE_COURSE_ACCESS = "COURSE_ACCESS"
FEATURE_AI_COURSE_GENERATOR = "AI_COURSE_GENERATOR"
FEATURE_AI_QUIZ_GENERATOR = "AI_QUIZ_GENERATOR"
FEATURE_AI_ASSESSMENT_GENERATOR = "AI_ASSESSMENT_GENERATOR"
FEATURE_AI_VIDEO = "AI_VIDEO"
FEATURE_AI_AUDIO = "AI_AUDIO"
FEATURE_AI_TUTOR = "AI_TUTOR"
FEATURE_AI_MENTOR = "AI_MENTOR"
FEATURE_AI_RESEARCH = "AI_RESEARCH"
FEATURE_AI_TRANSLATION = "AI_TRANSLATION"
FEATURE_AI_AVATAR = "AI_AVATAR"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def grant_entitlement(db, *, user_id: str, resource_kind: str, resource_id: str,
                             source: str, source_id: Optional[str] = None,
                             expires_at: Optional[str] = None,
                             organization_id: Optional[str] = None,
                             metadata: Optional[dict] = None) -> dict:
    """Idempotent — one row per (user, resource_kind, resource_id, source_id).
    resource_kind: 'course' | 'ai_feature' | 'subscription_plan' | 'add_on'
    source: 'purchase' | 'subscription' | 'institution' | 'trial' | 'admin_comp' | 'free'"""
    filter_ = {
        "user_id": user_id,
        "resource_kind": resource_kind,
        "resource_id": resource_id,
        "source_id": source_id,
    }
    doc = {
        **filter_,
        "source": source,
        "organization_id": organization_id,
        "granted_at": _now_iso(),
        "expires_at": expires_at,
        "status": "active",
        "metadata": metadata or {},
    }
    await db.entitlements.update_one(filter_, {"$set": doc,
                                                "$setOnInsert": {"id": str(uuid.uuid4())}},
                                      upsert=True)
    row = await db.entitlements.find_one(filter_, {"_id": 0})
    logger.info(f"grant_entitlement {resource_kind}={resource_id} to user={user_id} via {source}")
    return row


async def revoke_entitlement(db, *, user_id: str, resource_kind: str,
                              resource_id: str, source_id: Optional[str] = None):
    filter_ = {"user_id": user_id, "resource_kind": resource_kind,
               "resource_id": resource_id}
    if source_id:
        filter_["source_id"] = source_id
    await db.entitlements.update_many(filter_, {"$set": {
        "status": "revoked", "revoked_at": _now_iso()}})


async def check_course_access(db, *, user: dict, course_id: str) -> dict:
    """Central 'can this user open this course' check.
    Returns { allowed: bool, reason: str, entitlement: dict|None }"""
    if not user or not user.get("id"):
        return {"allowed": False, "reason": "unauthenticated"}

    # Super admin or admin override
    if user.get("role") in ("super_admin", "admin"):
        return {"allowed": True, "reason": "admin_override"}

    course = await db.courses.find_one({"id": course_id}, {"_id": 0})
    if not course:
        return {"allowed": False, "reason": "course_not_found"}

    # Course creator/teacher
    if course.get("created_by") == user["id"] or course.get("teacher_id") == user["id"]:
        return {"allowed": True, "reason": "author"}

    price = float(course.get("price") or 0)
    is_free = price <= 0 or course.get("is_free") or course.get("fee_type") == "free"
    if is_free:
        # Auto-grant free entitlement for tracking
        await grant_entitlement(
            db, user_id=user["id"], resource_kind="course",
            resource_id=course_id, source="free")
        return {"allowed": True, "reason": "free_course"}

    # Direct purchase entitlement
    now = _now_iso()
    ent = await db.entitlements.find_one({
        "user_id": user["id"],
        "resource_kind": "course",
        "resource_id": course_id,
        "status": "active",
        "$or": [{"expires_at": None}, {"expires_at": {"$gt": now}}],
    }, {"_id": 0})
    if ent:
        return {"allowed": True, "reason": "direct_entitlement", "entitlement": ent}

    # Active subscription that includes this course
    subs = await db.payment_subscriptions.find({
        "user_id": user["id"], "status": {"$in": ["active", "trialing"]},
        "current_period_end": {"$gt": now},
    }, {"_id": 0, "plan_id": 1, "included_course_ids": 1}).to_list(20)
    for s in subs:
        if course_id in (s.get("included_course_ids") or []):
            return {"allowed": True, "reason": "subscription", "subscription_id": s.get("id")}

    # Institution seat
    org_id = user.get("organization_id")
    if org_id:
        seat = await db.entitlements.find_one({
            "organization_id": org_id, "resource_kind": "course",
            "resource_id": course_id, "status": "active"}, {"_id": 0})
        if seat:
            return {"allowed": True, "reason": "institution_seat"}

    return {"allowed": False, "reason": "no_entitlement",
            "price": price, "currency": course.get("currency", "USD")}


async def check_ai_feature(db, *, user: dict, feature: str,
                             organization_id: Optional[str] = None) -> dict:
    """Verify a paid AI feature usage. Returns { allowed, reason, remaining, plan_id }."""
    if not user or not user.get("id"):
        return {"allowed": False, "reason": "unauthenticated"}
    if user.get("role") in ("super_admin", "admin"):
        return {"allowed": True, "reason": "admin_override", "remaining": None}

    # Read the platform feature policy (billing_type / limits)
    policy = await db.ai_feature_policies.find_one({"feature": feature}, {"_id": 0}) or {}
    billing_type = policy.get("billing_type", "FREE")

    if billing_type == "FREE":
        return {"allowed": True, "reason": "free_feature"}

    # Look for active subscription
    now = _now_iso()
    subs = await db.payment_subscriptions.find({
        "user_id": user["id"], "status": {"$in": ["active", "trialing"]},
        "current_period_end": {"$gt": now},
    }, {"_id": 0}).to_list(20)

    if billing_type in ("PLAN_INCLUDED", "SUBSCRIPTION_REQUIRED"):
        for s in subs:
            if feature in (s.get("included_features") or []):
                # Check per-period usage limit if set
                limit = (s.get("feature_limits") or {}).get(feature)
                if limit is None:
                    return {"allowed": True, "reason": "plan_included",
                            "subscription_id": s.get("id"), "remaining": None}
                used = await db.ai_usage.count_documents({
                    "user_id": user["id"], "feature": feature,
                    "subscription_id": s.get("id"),
                    "billing_period_start": s.get("current_period_start"),
                })
                if used < limit:
                    return {"allowed": True, "reason": "plan_included",
                            "subscription_id": s.get("id"),
                            "remaining": max(0, limit - used - 1),
                            "limit": limit}
                return {"allowed": False, "reason": "usage_limit_reached",
                        "limit": limit, "used": used}
        return {"allowed": False, "reason": "no_subscription",
                "message": "This AI feature requires an active subscription."}

    if billing_type == "METERED":
        credits = await _remaining_credits(db, user_id=user["id"])
        cost = int(policy.get("credit_cost", 1))
        if credits >= cost:
            return {"allowed": True, "reason": "metered",
                    "remaining": credits - cost}
        return {"allowed": False, "reason": "no_credits", "remaining": credits}

    if billing_type == "PAID_PER_USE":
        return {"allowed": False, "reason": "pay_per_use_required",
                "price": policy.get("price"), "currency": policy.get("currency", "USD"),
                "message": "This feature is pay-per-use. Please purchase before use."}

    return {"allowed": False, "reason": "unknown_billing_type"}


async def _remaining_credits(db, *, user_id: str) -> int:
    row = await db.ai_credit_wallets.find_one({"user_id": user_id}, {"_id": 0, "balance": 1})
    return int((row or {}).get("balance", 0))


async def record_ai_usage(db, *, user: dict, feature: str, model: str = "",
                           input_tokens: int = 0, output_tokens: int = 0,
                           estimated_cost: float = 0.0, success: bool = True,
                           subscription_id: Optional[str] = None,
                           metadata: Optional[dict] = None) -> str:
    """Log one AI operation for analytics + usage limits."""
    usage_id = str(uuid.uuid4())
    doc = {
        "id": usage_id,
        "user_id": user["id"],
        "organization_id": user.get("organization_id"),
        "feature": feature,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost": estimated_cost,
        "success": success,
        "subscription_id": subscription_id,
        "created_at": _now_iso(),
        "metadata": metadata or {},
    }
    if subscription_id:
        sub = await db.payment_subscriptions.find_one({"id": subscription_id},
                                                       {"_id": 0, "current_period_start": 1})
        if sub:
            doc["billing_period_start"] = sub.get("current_period_start")
    await db.ai_usage.insert_one(doc)
    # Deduct from credit wallet for METERED policies (best-effort)
    policy = await db.ai_feature_policies.find_one({"feature": feature}, {"_id": 0}) or {}
    if policy.get("billing_type") == "METERED":
        cost = int(policy.get("credit_cost", 1))
        await db.ai_credit_wallets.update_one(
            {"user_id": user["id"]},
            {"$inc": {"balance": -cost},
             "$setOnInsert": {"user_id": user["id"], "created_at": _now_iso()}},
            upsert=True)
    return usage_id


async def user_ai_usage_summary(db, *, user_id: str) -> dict:
    """User billing dashboard — AI usage snapshot for the current billing period."""
    wallet = await db.ai_credit_wallets.find_one({"user_id": user_id}, {"_id": 0}) or {}
    subs = await db.payment_subscriptions.find(
        {"user_id": user_id, "status": {"$in": ["active", "trialing"]}},
        {"_id": 0}).to_list(10)
    breakdown = []
    for s in subs:
        for feat in (s.get("included_features") or []):
            limit = (s.get("feature_limits") or {}).get(feat)
            used = await db.ai_usage.count_documents({
                "user_id": user_id, "feature": feat, "subscription_id": s.get("id"),
                "billing_period_start": s.get("current_period_start")})
            breakdown.append({"feature": feat, "used": used, "limit": limit,
                              "plan_id": s.get("plan_id"),
                              "period_end": s.get("current_period_end")})
    return {
        "credits_balance": int(wallet.get("balance", 0)),
        "subscriptions": [{"id": s.get("id"), "plan_id": s.get("plan_id"),
                           "status": s.get("status"),
                           "current_period_end": s.get("current_period_end")}
                          for s in subs],
        "features": breakdown,
    }
