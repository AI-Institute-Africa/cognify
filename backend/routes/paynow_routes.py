"""Paynow payment routes — customer-facing endpoints."""
from __future__ import annotations
import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Form, Body
from pydantic import BaseModel

from services.billing_engine import (
    create_invoice_and_transaction, mark_paid, mark_failed, revenue_snapshot
)
from services.entitlement_engine import (
    check_course_access, user_ai_usage_summary
)

logger = logging.getLogger(__name__)


class CheckoutRequest(BaseModel):
    product_id: Optional[str] = None
    course_id: Optional[str] = None
    plan_id: Optional[str] = None
    coupon_code: Optional[str] = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fernet(payment_platform):
    return payment_platform


def make_router(db, get_current_user, payment_platform):
    """payment_platform: instance exposing decrypt_secret(str) for Fernet-encrypted keys."""
    r = APIRouter(prefix="/api/checkout")

    # ---------------------------------------------------------- provider loader
    async def _load_paynow():
        from services.paynow_provider import PaynowProvider
        p = await db.payment_providers.find_one(
            {"slug": "paynow", "deleted_at": None}, {"_id": 0})
        if not p:
            return None, "Paynow provider not configured"
        # Decrypt the integration key
        try:
            key = payment_platform.decrypt_secret(p.get("integration_key", ""))
        except Exception:
            key = ""
        webhook_secret = ""
        if p.get("webhook_secret"):
            try:
                webhook_secret = payment_platform.decrypt_secret(p["webhook_secret"])
            except Exception:
                pass
        # Fall back to environment for URLs (production stability)
        backend_base = os.environ.get("PUBLIC_BACKEND_URL") or ""
        frontend_base = os.environ.get("PUBLIC_FRONTEND_URL") or ""
        default_result = f"{backend_base.rstrip('/')}/api/payments/paynow/result" if backend_base else p.get("result_url")
        default_return = f"{frontend_base.rstrip('/')}/payment/paynow/return" if frontend_base else p.get("return_url")
        prov = PaynowProvider(
            integration_id=p.get("integration_id", ""),
            integration_key=key,
            result_url=p.get("result_url") or default_result or "",
            return_url=p.get("return_url") or default_return or "",
            environment=p.get("environment", "sandbox"),
        )
        return prov, None

    # ---------------------------------------------------------- 1) initiate
    @r.post("/paynow/initiate")
    async def paynow_initiate(payload: CheckoutRequest,
                               current_user: dict = Depends(get_current_user)):
        """Server-side authoritative checkout — creates invoice + transaction,
        initiates Paynow, returns the redirect URL for the customer."""
        try:
            billing = await create_invoice_and_transaction(
                db, user=current_user,
                product_id=payload.product_id, course_id=payload.course_id,
                plan_id=payload.plan_id, coupon_code=payload.coupon_code,
                provider_slug="paynow")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Free tier — no Paynow needed
        if billing["amount"] <= 0:
            await mark_paid(db, transaction_id=billing["transaction"]["id"],
                             paynow_reference="FREE-0", poll_url=None)
            return {"free": True, "transaction_id": billing["transaction"]["id"],
                    "cognify_reference": billing["cognify_reference"]}

        prov, err = await _load_paynow()
        if err or not prov:
            await mark_failed(db, transaction_id=billing["transaction"]["id"],
                                reason=err or "Paynow unavailable")
            raise HTTPException(status_code=503,
                                 detail="Payment service unavailable. Please try again shortly.")
        ok, why = prov.is_configured()
        if not ok:
            await mark_failed(db, transaction_id=billing["transaction"]["id"],
                                reason=f"Paynow config: {why}")
            raise HTTPException(status_code=503,
                                 detail=f"Payment service is being configured ({why}). Try again shortly.")

        res = await asyncio.to_thread(
            prov.initiate,
            reference=billing["cognify_reference"],
            amount=billing["amount"],
            email=current_user.get("email") or "",
            description=f"Cognify: {billing['invoice']['product_name']}",
            additional_info=billing["invoice"]["product_name"],
        )
        if not res["ok"]:
            err_msg = str(res.get("error") or "Paynow rejected initiation")[:400]
            await mark_failed(db, transaction_id=billing["transaction"]["id"],
                                reason=err_msg)
            await db.payment_logs.insert_one({
                "event": "PAYNOW_REJECTED",
                "transaction_id": billing["transaction"]["id"],
                "reason": err_msg,
                "at": _now_iso(),
            })
            raise HTTPException(status_code=502, detail=err_msg)

        await db.payment_transactions.update_one(
            {"id": billing["transaction"]["id"]},
            {"$set": {"status": "pending",
                      "poll_url": res.get("poll_url"),
                      "redirect_url": res.get("redirect_url")}})
        await db.payment_logs.insert_one({
            "event": "PAYNOW_REDIRECT_CREATED",
            "transaction_id": billing["transaction"]["id"],
            "at": _now_iso(),
        })
        return {
            "redirect_url": res["redirect_url"],
            "poll_url": res["poll_url"],
            "cognify_reference": billing["cognify_reference"],
            "transaction_id": billing["transaction"]["id"],
            "amount": billing["amount"],
            "currency": billing["currency"],
        }

    # ---------------------------------------------------------- 2) callback (webhook)
    # NOTE: legacy endpoint at /api/payments/paynow/result is superseded — Paynow should
    # POST to /api/checkout/paynow/result. Legacy path still exists in server.py.
    @r.post("/paynow/result")
    async def paynow_result(request: Request):
        """Paynow POSTs application/x-www-form-urlencoded here.
        MUST be idempotent — Paynow retries frequently."""
        prov, err = await _load_paynow()
        if err or not prov:
            logger.warning(f"paynow_result: provider unavailable ({err})")
            return "Error"
        form = await request.form()
        form_data = {k: (v[0] if isinstance(v, list) else str(v)) for k, v in form.items()}
        await db.payment_webhook_events.insert_one({
            "provider": "paynow", "at": _now_iso(),
            "payload": {k: ("*****" if k.lower() == "hash" else v) for k, v in form_data.items()},
        })
        parsed = prov.parse_callback(form_data)
        if not parsed["ok"]:
            await db.payment_logs.insert_one({
                "event": "SIGNATURE_INVALID",
                "at": _now_iso(),
                "reason": parsed.get("error"),
            })
            return "Ok"  # Never leak reason to caller
        cognify_ref = parsed["reference"]
        cognify_status = parsed["cognify_status"]
        tx = await db.payment_transactions.find_one(
            {"reference": cognify_ref, "deleted_at": None}, {"_id": 0})
        if not tx:
            logger.warning(f"paynow_result: unknown reference {cognify_ref}")
            return "Ok"
        # Amount validation (paynow returns strings)
        try:
            paynow_amount = float(parsed.get("amount") or 0)
            if abs(paynow_amount - float(tx["amount"])) > 0.01:
                await db.payment_logs.insert_one({
                    "event": "AMOUNT_MISMATCH",
                    "transaction_id": tx["id"], "at": _now_iso(),
                    "expected": tx["amount"], "actual": paynow_amount,
                })
                await mark_failed(db, transaction_id=tx["id"],
                                    reason=f"Amount mismatch: expected {tx['amount']} got {paynow_amount}",
                                    paynow_reference=parsed.get("paynow_reference"))
                return "Ok"
        except Exception:
            pass
        if cognify_status == "paid":
            first = await mark_paid(
                db, transaction_id=tx["id"],
                paynow_reference=parsed.get("paynow_reference"),
                poll_url=parsed.get("poll_url"))
            logger.info(f"paynow_result: transaction {tx['reference']} PAID (first={first})")
        elif cognify_status in ("failed", "cancelled"):
            await mark_failed(db, transaction_id=tx["id"],
                                reason=parsed.get("paynow_status", "unknown"),
                                paynow_reference=parsed.get("paynow_reference"))
        else:
            # Still pending — record but don't finalise
            await db.payment_transactions.update_one(
                {"id": tx["id"], "status": {"$in": ["initiated", "pending"]}},
                {"$set": {"provider_reference": parsed.get("paynow_reference"),
                          "poll_url": parsed.get("poll_url")}})
        return "Ok"

    # ---------------------------------------------------------- 3) reconcile / status
    @r.get("/paynow/status/{reference}")
    async def paynow_status(reference: str,
                             current_user: dict = Depends(get_current_user)):
        """Server-side reconciliation — poll Paynow directly if we're still pending.
        Only the owner (or admin) can query."""
        tx = await db.payment_transactions.find_one({"reference": reference}, {"_id": 0})
        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found")
        if tx["user_id"] != current_user["id"] and current_user.get("role") not in ("admin", "super_admin"):
            raise HTTPException(status_code=403, detail="Not your transaction")
        if tx["status"] in ("paid", "failed", "cancelled", "refunded"):
            return {"status": tx["status"], "transaction": tx}
        # Ask Paynow for real status
        prov, err = await _load_paynow()
        if err or not prov or not tx.get("poll_url"):
            return {"status": tx["status"], "transaction": tx}
        s = await asyncio.to_thread(prov.check_status, tx["poll_url"])
        if s.get("ok") and s["cognify_status"] == "paid":
            await mark_paid(db, transaction_id=tx["id"],
                             paynow_reference=s.get("paynow_reference"),
                             poll_url=tx.get("poll_url"))
            tx = await db.payment_transactions.find_one({"id": tx["id"]}, {"_id": 0})
        elif s.get("ok") and s["cognify_status"] in ("failed", "cancelled"):
            await mark_failed(db, transaction_id=tx["id"], reason=s.get("paynow_status", ""))
            tx = await db.payment_transactions.find_one({"id": tx["id"]}, {"_id": 0})
        return {"status": tx["status"], "transaction": tx}

    # ---------------------------------------------------------- 4) my invoices
    @r.get("/me/invoices")
    async def my_invoices(current_user: dict = Depends(get_current_user)):
        rows = await db.payment_invoices.find(
            {"user_id": current_user["id"], "deleted_at": None},
            {"_id": 0}).sort("created_at", -1).to_list(200)
        return {"invoices": rows}

    @r.get("/me/receipts")
    async def my_receipts(current_user: dict = Depends(get_current_user)):
        rows = await db.payment_receipts.find(
            {"user_id": current_user["id"], "deleted_at": None},
            {"_id": 0}).sort("issued_at", -1).to_list(200)
        return {"receipts": rows}

    @r.get("/me/subscriptions")
    async def my_subs(current_user: dict = Depends(get_current_user)):
        rows = await db.payment_subscriptions.find(
            {"user_id": current_user["id"], "deleted_at": None},
            {"_id": 0}).sort("created_at", -1).to_list(50)
        return {"subscriptions": rows}

    @r.get("/me/entitlements")
    async def my_ents(current_user: dict = Depends(get_current_user)):
        rows = await db.entitlements.find(
            {"user_id": current_user["id"], "status": "active"},
            {"_id": 0}).to_list(500)
        return {"entitlements": rows}

    @r.get("/me/ai-usage")
    async def my_ai_usage(current_user: dict = Depends(get_current_user)):
        return await user_ai_usage_summary(db, user_id=current_user["id"])

    # ---------------------------------------------------------- 5) course access check
    @r.get("/access/course/{course_id}")
    async def can_access_course(course_id: str,
                                 current_user: dict = Depends(get_current_user)):
        return await check_course_access(db, user=current_user, course_id=course_id)

    return r
