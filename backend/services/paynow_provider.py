"""Paynow provider — uses the official `paynow` PyPI SDK for correctness.

Reference: https://developers.paynow.co.zw/docs/
"""
from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger(__name__)

STATUS_MAP = {
    "paid": "paid", "awaiting delivery": "paid", "delivered": "paid",
    "created": "pending", "sent": "pending", "pending": "pending",
    "cancelled": "cancelled", "user cancelled": "cancelled",
    "refunded": "refunded",
    "disputed": "pending",
    "failed": "failed", "denied": "failed",
    "insufficient balance": "failed", "invalid amount": "failed",
    "invalid otp": "failed", "otp timeout": "failed",
    "otp cancelled": "failed", "delivery failure": "failed",
}


class PaynowProvider:
    slug = "paynow"

    def __init__(self, integration_id: str, integration_key: str,
                 result_url: str, return_url: str, environment: str = "sandbox"):
        self.integration_id = (integration_id or "").strip()
        self.integration_key = (integration_key or "").strip()
        self.result_url = (result_url or "").strip()
        self.return_url = (return_url or "").strip()
        self.environment = environment

    def is_configured(self) -> tuple[bool, str]:
        if not self.integration_id:
            return False, "integration_id missing"
        if not self.integration_key:
            return False, "integration_key missing"
        if not self.result_url:
            return False, "result_url missing"
        if not self.return_url:
            return False, "return_url missing"
        return True, "ok"

    def _client(self):
        from paynow import Paynow
        return Paynow(self.integration_id, self.integration_key,
                       self.return_url, self.result_url)

    def initiate(self, *, reference: str, amount: float, email: str,
                 description: str, additional_info: str = "") -> dict:
        ok, why = self.is_configured()
        if not ok:
            return {"ok": False, "error": f"Paynow not configured: {why}"}
        try:
            paynow = self._client()
            payment = paynow.create_payment(reference, email or "customer@cognify.local")
            payment.add(description or "Cognify purchase", amount)
            response = paynow.send(payment)
            if response.success:
                return {
                    "ok": True,
                    "redirect_url": response.redirect_url,
                    "poll_url": response.poll_url,
                    "reference": reference,
                }
            # SDK bug: response.error stays as the class default when success=False.
            # Read the real error from response.data (Paynow returns 'error' field).
            data = getattr(response, "data", {}) or {}
            err_text = data.get("error") if isinstance(data, dict) else str(data)
            return {"ok": False,
                    "error": err_text or "Paynow rejected the initiation",
                    "raw": {"data": str(data)[:400]}}
        except Exception as e:
            logger.exception("Paynow initiate crashed")
            return {"ok": False, "error": f"Paynow SDK error: {str(e)[:200]}"}

    def check_status(self, poll_url: str) -> dict:
        try:
            paynow = self._client()
            status = paynow.check_transaction_status(poll_url)
            paynow_status = (status.status or "").lower()
            return {
                "ok": True,
                "paynow_status": paynow_status,
                "cognify_status": STATUS_MAP.get(paynow_status, "pending"),
                "amount": getattr(status, "amount", None),
                "paynow_reference": getattr(status, "paynow_reference", None),
                "reference": getattr(status, "reference", None),
            }
        except Exception as e:
            logger.exception("Paynow status crashed")
            return {"ok": False, "error": str(e)[:200]}

    def parse_callback(self, form_data: dict) -> dict:
        """The SDK doesn't expose hash validation for arbitrary payload directly;
        do it manually per Paynow docs (SHA512 of concatenated values + key)."""
        import hashlib
        incoming = form_data.get("hash") or form_data.get("Hash") or ""
        values = "".join(str(v) for k, v in form_data.items() if k.lower() != "hash")
        expected = hashlib.sha512((values + self.integration_key).encode("utf-8")).hexdigest().upper()
        if incoming.upper() != expected:
            return {"ok": False, "error": "Invalid hash", "raw": form_data}
        paynow_status = (form_data.get("status") or "").lower()
        return {
            "ok": True,
            "paynow_status": paynow_status,
            "cognify_status": STATUS_MAP.get(paynow_status, "pending"),
            "reference": form_data.get("reference"),
            "paynow_reference": form_data.get("paynowreference"),
            "amount": form_data.get("amount"),
            "poll_url": form_data.get("pollurl"),
            "raw": form_data,
        }

    def refund(self, paynow_reference: str, amount: float, reason: str = "") -> dict:
        return {
            "ok": False, "manual_required": True,
            "message": ("Paynow does not expose a merchant-side refund API. "
                        "Please issue the refund from the Paynow dashboard at "
                        "https://www.paynow.co.zw"),
            "paynow_reference": paynow_reference, "amount": amount, "reason": reason,
        }
