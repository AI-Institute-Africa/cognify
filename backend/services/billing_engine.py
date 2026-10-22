"""Cognify Billing Engine — server-side authoritative price calculation.

For a checkout request the frontend passes { product_id | course_id | plan_id, coupon_code? }.
The backend:
  1. Loads the product from the database (never trusts the frontend price)
  2. Applies coupon (if valid)
  3. Applies tax
  4. Creates an invoice + transaction row
Returns the authoritative amount, currency and a Cognify reference for Paynow initiation.
"""
from __future__ import annotations
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _next_ref(prefix: str, sequence: int) -> str:
    year = datetime.now(timezone.utc).year
    return f"{prefix}-{year}-{sequence:06d}"


async def _next_sequence(db, key: str) -> int:
    r = await db.counters.find_one_and_update(
        {"_id": key}, {"$inc": {"seq": 1}}, upsert=True, return_document=True)
    return int(r["seq"]) if r else 1


async def resolve_product(db, *, product_id: Optional[str] = None,
                           course_id: Optional[str] = None,
                           plan_id: Optional[str] = None) -> dict:
    """Return { kind, product_dict, price, currency, name } from an authoritative source."""
    if product_id:
        p = await db.payment_products.find_one({"id": product_id, "deleted_at": None}, {"_id": 0})
        if not p:
            raise ValueError("Product not found")
        return {"kind": "product", "product": p,
                "price": float(p.get("price", 0)),
                "currency": p.get("currency", "USD"),
                "name": p.get("title") or p.get("name") or "Cognify Product"}
    if course_id:
        c = await db.courses.find_one({"id": course_id}, {"_id": 0})
        if not c:
            raise ValueError("Course not found")
        return {"kind": "course", "product": c,
                "price": float(c.get("price", 0)),
                "currency": c.get("currency", "USD"),
                "name": c.get("title") or c.get("name") or "Course"}
    if plan_id:
        pl = await db.payment_pricing_plans.find_one({"id": plan_id, "deleted_at": None}, {"_id": 0})
        if not pl:
            raise ValueError("Pricing plan not found")
        return {"kind": "subscription_plan", "product": pl,
                "price": float(pl.get("price", 0)),
                "currency": pl.get("currency", "USD"),
                "name": pl.get("name") or "Subscription"}
    raise ValueError("Must supply product_id, course_id or plan_id")


async def apply_coupon(db, *, code: str, base_amount: float, currency: str,
                        user_id: str) -> dict:
    """Return { valid, discount_amount, coupon_id, message }."""
    if not code:
        return {"valid": False, "discount_amount": 0.0, "message": "no coupon"}
    coupon = await db.payment_coupons.find_one(
        {"code": code.upper(), "deleted_at": None, "enabled": True}, {"_id": 0})
    if not coupon:
        return {"valid": False, "discount_amount": 0.0, "message": "coupon not found"}
    # Expiry
    expires = coupon.get("expires_at")
    if expires and expires < _now_iso():
        return {"valid": False, "discount_amount": 0.0, "message": "coupon expired"}
    # Currency
    if coupon.get("currency") and coupon["currency"] != currency:
        return {"valid": False, "discount_amount": 0.0, "message": "coupon currency mismatch"}
    # Discount
    discount = 0.0
    if coupon.get("discount_type") == "percentage":
        discount = base_amount * float(coupon.get("value", 0)) / 100.0
    else:
        discount = float(coupon.get("value", 0))
    discount = round(min(discount, base_amount), 2)
    return {"valid": True, "discount_amount": discount,
            "coupon_id": coupon.get("id"), "message": "applied"}


async def apply_tax(db, *, base_amount: float, currency: str,
                     country: Optional[str] = None) -> dict:
    """Look up a matching tax rule; returns tax amount + rate."""
    query = {"deleted_at": None, "enabled": True, "currency": currency}
    if country:
        query["country"] = country
    tax_rule = await db.payment_taxes.find_one(query, {"_id": 0})
    if not tax_rule:
        return {"tax_rate": 0.0, "tax_amount": 0.0}
    rate = float(tax_rule.get("rate", 0))
    return {"tax_rate": rate, "tax_amount": round(base_amount * rate / 100.0, 2),
            "tax_id": tax_rule.get("id"), "tax_name": tax_rule.get("name")}


async def create_invoice_and_transaction(db, *, user: dict,
                                          product_id: Optional[str] = None,
                                          course_id: Optional[str] = None,
                                          plan_id: Optional[str] = None,
                                          coupon_code: Optional[str] = None,
                                          provider_slug: str = "paynow") -> dict:
    """Full authoritative pricing + invoice + transaction creation.
    Returns { invoice, transaction, cognify_reference, amount, currency }."""
    prod = await resolve_product(db, product_id=product_id, course_id=course_id, plan_id=plan_id)
    base_amount = prod["price"]
    currency = prod["currency"]
    coupon_res = await apply_coupon(db, code=coupon_code or "", base_amount=base_amount,
                                     currency=currency, user_id=user["id"])
    after_coupon = round(base_amount - coupon_res["discount_amount"], 2)
    tax_res = await apply_tax(db, base_amount=after_coupon, currency=currency,
                               country=user.get("country"))
    final_amount = round(after_coupon + tax_res["tax_amount"], 2)

    # Generate refs
    invoice_seq = await _next_sequence(db, "invoice_seq")
    tx_seq = await _next_sequence(db, "transaction_seq")
    invoice_ref = _next_ref("COG-INV", invoice_seq)
    tx_ref = _next_ref("COG-TX", tx_seq)

    now = _now_iso()
    invoice = {
        "id": str(uuid.uuid4()),
        "reference": invoice_ref,
        "user_id": user["id"],
        "user_email": user.get("email"),
        "organization_id": user.get("organization_id"),
        "product_kind": prod["kind"],
        "product_id": prod["product"].get("id"),
        "product_name": prod["name"],
        "course_id": course_id,
        "plan_id": plan_id,
        "base_amount": base_amount,
        "coupon_id": coupon_res.get("coupon_id"),
        "coupon_code": coupon_code,
        "discount_amount": coupon_res["discount_amount"],
        "tax_id": tax_res.get("tax_id"),
        "tax_rate": tax_res["tax_rate"],
        "tax_amount": tax_res["tax_amount"],
        "amount": final_amount,
        "currency": currency,
        "status": "pending",
        "payment_url": "https://www.paynow.co.zw/aiia",
        "dedicated_bill_url": "https://www.paynow.co.zw/aiia",
        "created_at": now,
        "deleted_at": None,
    }
    transaction = {
        "id": str(uuid.uuid4()),
        "reference": tx_ref,
        "invoice_id": invoice["id"],
        "invoice_reference": invoice_ref,
        "user_id": user["id"],
        "product_kind": prod["kind"],
        "product_id": prod["product"].get("id"),
        "course_id": course_id,
        "plan_id": plan_id,
        "amount": final_amount,
        "currency": currency,
        "provider": provider_slug,
        "payment_url": "https://www.paynow.co.zw/aiia",
        "dedicated_bill_url": "https://www.paynow.co.zw/aiia",
        "provider_reference": None,
        "poll_url": None,
        "status": "initiated",
        "created_at": now,
        "paid_at": None,
        "deleted_at": None,
    }
    await db.payment_invoices.insert_one(invoice)
    await db.payment_transactions.insert_one(transaction)

    # Audit
    await db.payment_audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "actor_id": user["id"],
        "actor_role": user.get("role"),
        "action": "invoice_created",
        "resource": "invoice",
        "resource_id": invoice["id"],
        "amount": final_amount,
        "currency": currency,
        "at": now,
    })
    return {
        "invoice": {k: v for k, v in invoice.items() if k != "_id"},
        "transaction": {k: v for k, v in transaction.items() if k != "_id"},
        "cognify_reference": tx_ref,
        "amount": final_amount,
        "currency": currency,
    }


async def mark_paid(db, *, transaction_id: str, paynow_reference: str,
                      poll_url: Optional[str] = None) -> bool:
    """Idempotent transition: initiated/pending → paid. Returns True on first success."""
    now = _now_iso()
    r = await db.payment_transactions.update_one(
        {"id": transaction_id, "status": {"$in": ["initiated", "pending"]}},
        {"$set": {"status": "paid", "paid_at": now,
                  "provider_reference": paynow_reference,
                  "poll_url": poll_url}})
    if r.modified_count == 0:
        return False  # already processed
    tx = await db.payment_transactions.find_one({"id": transaction_id}, {"_id": 0})
    await db.payment_invoices.update_one(
        {"id": tx["invoice_id"]},
        {"$set": {"status": "paid", "paid_at": now,
                  "provider_reference": paynow_reference}})
    # Generate receipt
    receipt_seq = await _next_sequence(db, "receipt_seq")
    receipt_ref = _next_ref("COG-RCP", receipt_seq)
    await db.payment_receipts.insert_one({
        "id": str(uuid.uuid4()),
        "reference": receipt_ref,
        "invoice_id": tx["invoice_id"],
        "transaction_id": tx["id"],
        "user_id": tx["user_id"],
        "amount": tx["amount"],
        "currency": tx["currency"],
        "provider": tx["provider"],
        "provider_reference": paynow_reference,
        "issued_at": now,
        "deleted_at": None,
    })
    # Grant entitlement
    from services.entitlement_engine import grant_entitlement
    if tx.get("course_id"):
        await grant_entitlement(
            db, user_id=tx["user_id"], resource_kind="course",
            resource_id=tx["course_id"], source="purchase", source_id=tx["id"])
    if tx.get("plan_id"):
        await _activate_subscription(db, user_id=tx["user_id"],
                                      plan_id=tx["plan_id"], transaction_id=tx["id"])
    # Audit
    await db.payment_audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "actor_id": "system",
        "actor_role": "system",
        "action": "transaction_paid",
        "resource": "transaction",
        "resource_id": tx["id"],
        "amount": tx["amount"],
        "currency": tx["currency"],
        "at": now,
    })
    await db.payment_logs.insert_one({
        "id": str(uuid.uuid4()),
        "event": "PAYMENT_PAID",
        "transaction_id": tx["id"], "at": now,
    })
    return True


async def mark_failed(db, *, transaction_id: str, reason: str,
                        paynow_reference: Optional[str] = None) -> bool:
    now = _now_iso()
    reason_str = str(reason)[:400] if reason else ""
    r = await db.payment_transactions.update_one(
        {"id": transaction_id, "status": {"$in": ["initiated", "pending"]}},
        {"$set": {"status": "failed", "failure_reason": reason_str,
                  "provider_reference": paynow_reference}})
    if r.modified_count == 0:
        return False
    tx = await db.payment_transactions.find_one({"id": transaction_id}, {"_id": 0})
    await db.payment_invoices.update_one({"id": tx["invoice_id"]},
                                           {"$set": {"status": "failed"}})
    await db.payment_logs.insert_one({
        "id": str(uuid.uuid4()), "event": "PAYMENT_FAILED",
        "transaction_id": tx["id"], "at": now, "reason": reason_str,
    })
    return True


async def _activate_subscription(db, *, user_id: str, plan_id: str,
                                    transaction_id: str) -> str:
    """Create/refresh a subscription row after successful payment."""
    plan = await db.payment_pricing_plans.find_one({"id": plan_id, "deleted_at": None},
                                                     {"_id": 0}) or {}
    interval = (plan.get("billing_cycle") or "monthly").lower()
    now = datetime.now(timezone.utc)
    if interval == "annual" or interval == "yearly":
        end = now + timedelta(days=365)
    elif interval == "quarterly":
        end = now + timedelta(days=90)
    elif interval == "biannual":
        end = now + timedelta(days=182)
    elif interval == "lifetime":
        end = now + timedelta(days=365 * 100)
    else:  # monthly default
        end = now + timedelta(days=30)
    sub_id = str(uuid.uuid4())
    sub = {
        "id": sub_id,
        "user_id": user_id,
        "plan_id": plan_id,
        "plan_name": plan.get("name"),
        "status": "active",
        "billing_cycle": interval,
        "current_period_start": now.isoformat(),
        "current_period_end": end.isoformat(),
        "included_course_ids": plan.get("included_course_ids", []),
        "included_features": plan.get("included_features", []),
        "feature_limits": plan.get("feature_limits", {}),
        "activated_via_transaction": transaction_id,
        "created_at": now.isoformat(),
        "deleted_at": None,
    }
    await db.payment_subscriptions.insert_one(sub)
    # Grant per-course entitlements to make check_course_access fast-path work
    from services.entitlement_engine import grant_entitlement
    for cid in plan.get("included_course_ids", []):
        await grant_entitlement(
            db, user_id=user_id, resource_kind="course",
            resource_id=cid, source="subscription", source_id=sub_id,
            expires_at=end.isoformat())
    return sub_id


async def revenue_snapshot(db) -> dict:
    """Return today/week/month/year gross revenue + transaction counts."""
    from datetime import date
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    week_start = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0).isoformat()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

    async def _sum(since: str) -> float:
        pipeline = [
            {"$match": {"status": "paid", "paid_at": {"$gte": since}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
        ]
        r = await db.payment_transactions.aggregate(pipeline).to_list(1)
        return round(float(r[0]["total"]) if r else 0.0, 2)

    return {
        "today_revenue": await _sum(today),
        "week_revenue": await _sum(week_start),
        "month_revenue": await _sum(month_start),
        "year_revenue": await _sum(year_start),
        "counts": {
            "total": await db.payment_transactions.count_documents({}),
            "paid": await db.payment_transactions.count_documents({"status": "paid"}),
            "pending": await db.payment_transactions.count_documents({"status": {"$in": ["initiated", "pending"]}}),
            "failed": await db.payment_transactions.count_documents({"status": "failed"}),
            "cancelled": await db.payment_transactions.count_documents({"status": "cancelled"}),
            "refunded": await db.payment_transactions.count_documents({"status": "refunded"}),
        },
    }
