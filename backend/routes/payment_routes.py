"""All payment-management routes for the Super Admin Payment platform.

Mounted under /api/super-admin/payments and /api/payments by server.py.
"""
from __future__ import annotations
import os, uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field
from services.payment_platform import PaymentPlatform

# These helpers are imported lazily from server.py via dependency injection setup
# We expose `make_router(db, require_super_admin, get_current_user)` so server.py wires it up.


class ProviderConfigPatch(BaseModel):
    enabled: Optional[bool] = None
    environment: Optional[str] = None
    integration_id: Optional[str] = None
    integration_key: Optional[str] = None
    result_url: Optional[str] = None
    return_url: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_email: Optional[str] = None
    default_currency: Optional[str] = None
    webhook_secret: Optional[str] = None
    connection_timeout: Optional[int] = None
    retry_attempts: Optional[int] = None
    enable_logging: Optional[bool] = None
    enable_email_notifications: Optional[bool] = None
    enable_sms_notifications: Optional[bool] = None
    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    encryption_key: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    publishable_key: Optional[str] = None


class ProductIn(BaseModel):
    title: str
    description: str = ""
    category: str = "general"
    price: float
    currency: str = "USD"
    tax_rate: float = 0
    discount: float = 0
    billing_type: str = "one_time"  # one_time | subscription
    billing_interval: Optional[str] = None  # monthly | quarterly | biannual | annual | lifetime
    sku: Optional[str] = None
    image_url: Optional[str] = None
    access_duration_days: Optional[int] = None
    download_limit: Optional[int] = None
    visibility: str = "public"  # public | private | unlisted
    status: str = "active"


class SettingsPatch(BaseModel):
    default_currency: Optional[str] = None
    supported_currencies: Optional[list[str]] = None
    invoice_prefix: Optional[str] = None
    receipt_prefix: Optional[str] = None
    reference_prefix: Optional[str] = None
    payment_timeout_seconds: Optional[int] = None
    max_retry: Optional[int] = None
    auto_generate_invoice: Optional[bool] = None
    auto_generate_receipt: Optional[bool] = None
    auto_activate_subscription: Optional[bool] = None
    auto_unlock_content: Optional[bool] = None
    auto_send_email: Optional[bool] = None
    auto_verify_payment: Optional[bool] = None
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    admin_notifications: Optional[bool] = None
    service_unavailable_message: Optional[str] = None
    fail_open: Optional[bool] = None


def make_router(db, require_super_admin, get_current_user):
    """Build the routers. Returns a tuple (sa_router, customer_router, activity_router)."""
    sa = APIRouter(prefix="/super-admin/payments", tags=["payments-admin"])
    cust = APIRouter(prefix="/payments", tags=["payments-customer"])
    act = APIRouter(prefix="/super-admin/activity", tags=["activity"])
    ps = PaymentPlatform(db)

    # ----- Dashboard ------------------------------------------------------
    @sa.get("/dashboard")
    async def dashboard(_=Depends(require_super_admin)):
        now = datetime.now(timezone.utc)
        def iso(dt): return dt.isoformat()
        today_start = iso(datetime(now.year, now.month, now.day, tzinfo=timezone.utc))
        week_start = iso(now - timedelta(days=7))
        month_start = iso(now - timedelta(days=30))
        year_start = iso(now - timedelta(days=365))

        async def sum_paid(after):
            cursor = db.payment_transactions.aggregate([
                {"$match": {"status": {"$in": ["paid", "succeeded", "completed"]},
                            "created_at": {"$gte": after},
                            "deleted_at": None}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}])
            doc = await cursor.to_list(1)
            return (doc[0]["total"] if doc else 0), (doc[0]["count"] if doc else 0)

        today_rev, today_count = await sum_paid(today_start)
        week_rev, _ = await sum_paid(week_start)
        month_rev, _ = await sum_paid(month_start)
        year_rev, _ = await sum_paid(year_start)

        status_counts = {}
        async for d in db.payment_transactions.aggregate([
            {"$match": {"deleted_at": None}},
            {"$group": {"_id": "$status", "n": {"$sum": 1}}}]):
            status_counts[d["_id"]] = d["n"]

        active_subs = await db.payment_subscriptions.count_documents({"status": "active", "deleted_at": None})
        expired_subs = await db.payment_subscriptions.count_documents({"status": "expired", "deleted_at": None})

        recent_tx = await db.payment_transactions.find({"deleted_at": None}, {"_id": 0}).sort("created_at", -1).limit(8).to_list(8)
        recent_errs = await db.payment_logs.find({"level": "error"}, {"_id": 0}).sort("created_at", -1).limit(8).to_list(8)

        avg_tx = (today_rev / today_count) if today_count else 0
        return {
            "revenue": {"today": today_rev, "week": week_rev, "month": month_rev, "year": year_rev,
                        "growth_pct": 0, "avg_transaction": avg_tx},
            "transactions": {"total": sum(status_counts.values()),
                              "successful": status_counts.get("paid", 0) + status_counts.get("succeeded", 0),
                              "pending": status_counts.get("pending", 0),
                              "failed": status_counts.get("failed", 0),
                              "cancelled": status_counts.get("cancelled", 0),
                              "refunded": status_counts.get("refunded", 0)},
            "subscriptions": {"active": active_subs, "expired": expired_subs},
            "recent_transactions": recent_tx,
            "recent_errors": recent_errs,
            "top_products": [],
        }

    # ----- Providers ------------------------------------------------------
    @sa.get("/providers")
    async def list_providers(_=Depends(require_super_admin)):
        return {"providers": await ps.list_providers()}

    @sa.put("/providers/{slug}")
    async def configure_provider(slug: str, patch: ProviderConfigPatch,
                                  request: Request, user=Depends(require_super_admin)):
        try:
            out = await ps.configure_provider(slug, patch.dict(exclude_unset=True))
            await ps.audit(actor_id=user["id"], action="provider.configure",
                           target_type="provider", target_id=slug,
                           metadata={"ip": request.client.host if request.client else None})
            return out
        except ValueError as e:
            raise HTTPException(404, str(e))

    @sa.post("/providers/{slug}/test")
    async def test_provider(slug: str, user=Depends(require_super_admin)):
        prov = await ps.get_provider_with_secrets(slug)
        if not prov:
            raise HTTPException(404, "Provider not found")
        result = await prov.test_connection()
        await db.payment_providers.update_one({"slug": slug}, {"$set": {
            "last_health_check": datetime.now(timezone.utc).isoformat(),
            "health_status": "healthy" if result.get("ok") else "error"}})
        await ps.audit(actor_id=user["id"], action="provider.test",
                       target_type="provider", target_id=slug, metadata={"result": result})
        return result

    @sa.post("/providers/{slug}/enable")
    async def enable_provider(slug: str, user=Depends(require_super_admin)):
        await db.payment_providers.update_one({"slug": slug}, {"$set": {"enabled": True}})
        await ps.audit(actor_id=user["id"], action="provider.enable",
                       target_type="provider", target_id=slug)
        return {"ok": True}

    @sa.post("/providers/{slug}/disable")
    async def disable_provider(slug: str, user=Depends(require_super_admin)):
        await db.payment_providers.update_one({"slug": slug}, {"$set": {"enabled": False}})
        await ps.audit(actor_id=user["id"], action="provider.disable",
                       target_type="provider", target_id=slug)
        return {"ok": True}

    # ----- Products -------------------------------------------------------
    @sa.get("/products")
    async def list_products(_=Depends(require_super_admin)):
        docs = await db.payment_products.find({"deleted_at": None}, {"_id": 0}).sort("created_at", -1).to_list(500)
        return {"products": docs}

    @sa.post("/products")
    async def create_product(p: ProductIn, user=Depends(require_super_admin)):
        doc = {**p.dict(), "id": str(uuid.uuid4()),
               "created_at": datetime.now(timezone.utc).isoformat(),
               "updated_at": datetime.now(timezone.utc).isoformat(),
               "deleted_at": None, "created_by": user["id"]}
        await db.payment_products.insert_one(doc)
        doc.pop("_id", None)
        return doc

    @sa.put("/products/{pid}")
    async def update_product(pid: str, p: ProductIn, _=Depends(require_super_admin)):
        await db.payment_products.update_one({"id": pid}, {"$set": {
            **p.dict(exclude_unset=True),
            "updated_at": datetime.now(timezone.utc).isoformat()}})
        return await db.payment_products.find_one({"id": pid}, {"_id": 0})

    @sa.delete("/products/{pid}")
    async def delete_product(pid: str, _=Depends(require_super_admin)):
        await db.payment_products.update_one({"id": pid}, {"$set": {
            "deleted_at": datetime.now(timezone.utc).isoformat()}})
        return {"ok": True}

    # ----- Subscriptions --------------------------------------------------
    @sa.get("/subscriptions")
    async def list_subs(status: Optional[str] = None, _=Depends(require_super_admin)):
        q = {"deleted_at": None}
        if status: q["status"] = status
        return {"subscriptions": await db.payment_subscriptions.find(q, {"_id": 0}).sort("created_at", -1).limit(500).to_list(500)}

    @sa.post("/subscriptions/{sid}/{action}")
    async def sub_action(sid: str, action: str, user=Depends(require_super_admin)):
        if action not in {"pause", "resume", "cancel", "expire", "renew", "upgrade", "downgrade"}:
            raise HTTPException(400, "Unknown action")
        status_map = {"pause": "paused", "resume": "active", "cancel": "cancelled",
                      "expire": "expired", "renew": "active", "upgrade": "active", "downgrade": "active"}
        await db.payment_subscriptions.update_one({"id": sid}, {"$set": {
            "status": status_map[action],
            "updated_at": datetime.now(timezone.utc).isoformat()}})
        await ps.audit(actor_id=user["id"], action=f"subscription.{action}",
                       target_type="subscription", target_id=sid)
        return {"ok": True, "new_status": status_map[action]}

    # ----- Transactions / Invoices / Receipts / Refunds -------------------
    def _list_paged(collection):
        async def _h(status: Optional[str] = None, limit: int = 100,
                     offset: int = 0, _=Depends(require_super_admin)):
            q = {"deleted_at": None}
            if status: q["status"] = status
            cur = collection.find(q, {"_id": 0}).sort("created_at", -1).skip(offset).limit(min(limit, 500))
            items = await cur.to_list(limit)
            total = await collection.count_documents(q)
            return {"items": items, "total": total, "offset": offset, "limit": limit}
        return _h

    sa.add_api_route("/transactions", _list_paged(db.payment_transactions), methods=["GET"])
    sa.add_api_route("/invoices", _list_paged(db.payment_invoices), methods=["GET"])
    sa.add_api_route("/receipts", _list_paged(db.payment_receipts), methods=["GET"])
    sa.add_api_route("/refunds", _list_paged(db.payment_refunds), methods=["GET"])

    # ----- Logs (Payment, Webhook, Audit) ---------------------------------
    def _logs(coll):
        async def _h(limit: int = 200, level: Optional[str] = None,
                     _=Depends(require_super_admin)):
            q = {}
            if level: q["level"] = level
            return {"items": await coll.find(q, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)}
        return _h

    sa.add_api_route("/payment-logs", _logs(db.payment_logs), methods=["GET"])
    sa.add_api_route("/webhook-logs", _logs(db.payment_webhook_events), methods=["GET"])
    sa.add_api_route("/audit-logs", _logs(db.payment_audit_logs), methods=["GET"])

    # ----- Revenue Analytics ----------------------------------------------
    @sa.get("/revenue/timeseries")
    async def revenue_timeseries(days: int = 30, _=Depends(require_super_admin)):
        after = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        cursor = db.payment_transactions.aggregate([
            {"$match": {"status": {"$in": ["paid", "succeeded", "completed"]},
                        "created_at": {"$gte": after}, "deleted_at": None}},
            {"$group": {"_id": {"$substr": ["$created_at", 0, 10]},
                        "revenue": {"$sum": "$amount"}, "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}])
        return {"series": [{"date": d["_id"], "revenue": d["revenue"], "count": d["count"]} async for d in cursor]}

    # ----- Pricing Plans / Coupons / Taxes / Currencies -------------------
    def _crud(name: str, coll):
        @sa.get(f"/{name}")
        async def _list(_=Depends(require_super_admin)):
            return {"items": await coll.find({"deleted_at": None}, {"_id": 0}).sort("created_at", -1).to_list(500)}
        @sa.post(f"/{name}")
        async def _create(body: dict, _=Depends(require_super_admin)):
            doc = {**body, "id": str(uuid.uuid4()),
                   "created_at": datetime.now(timezone.utc).isoformat(),
                   "updated_at": datetime.now(timezone.utc).isoformat(),
                   "deleted_at": None}
            await coll.insert_one(doc); doc.pop("_id", None)
            return doc
        @sa.delete(f"/{name}/{{rid}}")
        async def _del(rid: str, _=Depends(require_super_admin)):
            await coll.update_one({"id": rid}, {"$set": {
                "deleted_at": datetime.now(timezone.utc).isoformat()}})
            return {"ok": True}
        return _list, _create, _del

    _crud("pricing-plans", db.payment_pricing_plans)
    _crud("coupons", db.payment_coupons)
    _crud("taxes", db.payment_taxes)
    _crud("currencies", db.payment_currencies)
    _crud("email-templates", db.payment_email_templates)

    # ----- Settings -------------------------------------------------------
    @sa.get("/settings")
    async def get_settings(_=Depends(require_super_admin)):
        return await ps.settings()

    @sa.put("/settings")
    async def put_settings(p: SettingsPatch, user=Depends(require_super_admin)):
        out = await ps.update_settings(p.dict(exclude_unset=True))
        await ps.audit(actor_id=user["id"], action="settings.update",
                       target_type="settings", metadata={})
        return out

    # ----- Webhook receiver (customer-facing) ----------------------------
    @cust.post("/webhook/{slug}")
    async def receive_webhook(slug: str, request: Request):
        payload = await request.body()
        signature = request.headers.get("X-Signature", "")
        prov = await ps.get_provider_with_secrets(slug)
        verified = bool(prov and prov.verify_webhook_signature(payload, signature))
        await db.payment_webhook_events.insert_one({
            "id": str(uuid.uuid4()), "provider": slug,
            "verified": verified, "signature": signature,
            "payload": payload.decode("utf-8", errors="replace")[:8000],
            "status": "received",
            "created_at": datetime.now(timezone.utc).isoformat()})
        if not verified:
            return {"ok": False, "verified": False}
        # TODO: parse payload, update transactions
        return {"ok": True}

    @sa.post("/webhook-events/{wid}/replay")
    async def replay_webhook(wid: str, _=Depends(require_super_admin)):
        await db.payment_webhook_events.update_one({"id": wid}, {"$set": {"status": "replayed",
            "replayed_at": datetime.now(timezone.utc).isoformat()}})
        return {"ok": True}

    # ----- Customer-side endpoints (used by app premium-feature pages) ---
    @cust.post("/checkout")
    async def checkout(body: dict, user=Depends(get_current_user)):
        for k in ("product_id", "return_url", "result_url"):
            if not body.get(k):
                raise HTTPException(400, f"Missing {k}")
        prod = await db.payment_products.find_one({"id": body["product_id"], "deleted_at": None})
        if not prod:
            raise HTTPException(404, "Product not found")
        return await ps.create_payment(
            user_id=user["id"], product_id=prod["id"],
            amount=prod["price"], currency=prod["currency"],
            description=prod["title"], customer_email=user["email"],
            return_url=body["return_url"], result_url=body["result_url"],
            metadata=body.get("metadata", {}))

    @cust.get("/transactions/{tx_id}")
    async def get_tx(tx_id: str, user=Depends(get_current_user)):
        tx = await db.payment_transactions.find_one({"id": tx_id}, {"_id": 0})
        if not tx or tx.get("user_id") != user["id"]:
            raise HTTPException(404, "Not found")
        return tx

    @cust.post("/transactions/{tx_id}/verify")
    async def verify(tx_id: str, user=Depends(get_current_user)):
        tx = await db.payment_transactions.find_one({"id": tx_id})
        if not tx or tx.get("user_id") != user["id"]:
            raise HTTPException(404, "Not found")
        return await ps.verify_payment(transaction_id=tx_id)

    @cust.get("/status")
    async def public_status():
        prov = await ps.active_provider()
        s = await ps.settings()
        return {
            "available": bool(prov),
            "provider": prov.slug if prov else None,
            "fail_open": s.get("fail_open", True),
            "message": s.get("service_unavailable_message") if not prov else None,
        }

    # ===================  ACTIVITY ANALYTICS  ==========================
    @act.get("/online")
    async def online_users(_=Depends(require_super_admin)):
        """Currently-online registered users (active in the last 5 minutes)."""
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        cur = db.users.find({"last_seen_at": {"$gte": cutoff}, "is_active": {"$ne": False}},
                            {"_id": 0, "id": 1, "email": 1, "full_name": 1, "role": 1,
                             "last_seen_at": 1, "total_active_seconds": 1, "last_referrer": 1})
        users = await cur.sort("last_seen_at", -1).limit(200).to_list(200)
        return {"users": users, "count": len(users)}

    @act.get("/external")
    async def external_visitors(_=Depends(require_super_admin)):
        """Anonymous visitors hitting /public or / (last 24h) + users who came in via external referrers."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        anon = await db.anonymous_visits.aggregate([
            {"$match": {"created_at": {"$gte": cutoff}}},
            {"$group": {"_id": {"ip": "$ip", "path": "$path"},
                        "hits": {"$sum": 1}, "last": {"$max": "$created_at"},
                        "referrer": {"$last": "$referrer"},
                        "ua": {"$last": "$ua"}}},
            {"$sort": {"last": -1}}, {"$limit": 200}]).to_list(200)
        ext_users = await db.users.find(
            {"last_referrer": {"$exists": True, "$ne": ""},
             "last_seen_at": {"$gte": cutoff}},
            {"_id": 0, "email": 1, "full_name": 1, "role": 1, "last_referrer": 1,
             "last_seen_at": 1}).sort("last_seen_at", -1).limit(200).to_list(200)
        return {"anonymous_visitors": anon, "external_referred_users": ext_users}

    @act.get("/usage")
    async def usage_hours(_=Depends(require_super_admin)):
        users = await db.users.find(
            {"is_active": {"$ne": False}},
            {"_id": 0, "id": 1, "email": 1, "full_name": 1, "role": 1,
             "last_seen_at": 1, "total_active_seconds": 1, "last_referrer": 1}
        ).sort("total_active_seconds", -1).limit(500).to_list(500)
        for u in users:
            secs = u.get("total_active_seconds", 0) or 0
            u["total_hours"] = round(secs / 3600.0, 2)
        return {"users": users}

    return sa, cust, act
