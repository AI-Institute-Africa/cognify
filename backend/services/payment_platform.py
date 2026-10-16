"""Provider-independent Payment Platform v2 — Super Admin Payment Management.

All NEW business logic uses this module. The legacy payment_service.py with its
hardcoded course package pricing remains untouched and will be replaced once the
admin migrates products into this system.

Credentials are encrypted at rest via Fernet (PAYMENT_ENCRYPTION_KEY env var).
"""
from __future__ import annotations
import os, uuid, logging, hmac, hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

_KEY = os.environ.get("PAYMENT_ENCRYPTION_KEY", "")
if not _KEY:
    raise RuntimeError("PAYMENT_ENCRYPTION_KEY missing in backend/.env")
_FERNET = Fernet(_KEY.encode())


def encrypt_str(v: str) -> str:
    return "" if not v else _FERNET.encrypt(v.encode()).decode()

def decrypt_str(v: str) -> str:
    if not v:
        return ""
    try: return _FERNET.decrypt(v.encode()).decode()
    except Exception: return ""

def mask_secret(v: str, show: int = 4) -> str:
    if not v: return ""
    if len(v) <= show * 2: return "•" * len(v)
    return v[:show] + "•" * (len(v) - show * 2) + v[-show:]


class PaymentProvider(ABC):
    slug = "abstract"; display_name = "Abstract"
    def __init__(self, config: dict): self.config = config or {}
    @property
    def enabled(self) -> bool: return bool(self.config.get("enabled")) and self.has_credentials()
    @property
    def environment(self) -> str: return (self.config.get("environment") or "sandbox").lower()
    @abstractmethod
    def has_credentials(self) -> bool: ...
    @abstractmethod
    async def test_connection(self) -> dict: ...
    @abstractmethod
    async def create_payment(self, **kw) -> dict: ...
    @abstractmethod
    async def verify_payment(self, **kw) -> dict: ...
    @abstractmethod
    async def refund_payment(self, **kw) -> dict: ...
    @abstractmethod
    async def cancel_payment(self, **kw) -> dict: ...
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        secret = self.config.get("webhook_secret_plain") or ""
        if not secret: return False
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature or "")


class PaynowProvider(PaymentProvider):
    slug = "paynow"; display_name = "Paynow"
    def has_credentials(self): return bool(self.config.get("integration_id_plain") and self.config.get("integration_key_plain"))
    async def test_connection(self):
        if not self.has_credentials():
            return {"ok": False, "message": "Missing Integration ID/Key", "latency_ms": 0}
        return {"ok": True, "environment": self.environment, "latency_ms": 0,
                "message": f"Credentials present ({self.environment}). Live verification on first transaction."}
    async def create_payment(self, **kw):
        if not self.enabled:
            return {"ok": False, "error": "Paynow disabled or missing credentials"}
        return {"ok": False, "error": "Paynow awaiting merchant activation",
                "redirect_url": None, "poll_url": None, "transaction_id": None, "raw": {}}
    async def verify_payment(self, **kw): return {"ok": False, "status": "unavailable"}
    async def refund_payment(self, **kw): return {"ok": False, "error": "Paynow refunds pending activation"}
    async def cancel_payment(self, **kw): return {"ok": False, "error": "Paynow cancel pending activation"}


class StubProvider(PaymentProvider):
    def __init__(self, slug, display_name, config):
        super().__init__(config); self.slug = slug; self.display_name = display_name
    def has_credentials(self): return bool(self.config.get("api_key_plain") or self.config.get("client_secret_plain"))
    async def test_connection(self):
        return {"ok": self.has_credentials(), "latency_ms": 0,
                "message": f"{self.display_name} stub — SDK to be wired on activation."}
    async def create_payment(self, **kw): return {"ok": False, "error": f"{self.display_name} not yet integrated"}
    async def verify_payment(self, **kw): return {"ok": False, "status": "unavailable"}
    async def refund_payment(self, **kw): return {"ok": False, "error": "not yet"}
    async def cancel_payment(self, **kw): return {"ok": False, "error": "not yet"}


class PaymentPlatform:
    """Service facade. Single entry-point used everywhere in Cognify."""

    SECRET_FIELDS = {"integration_key", "api_key", "secret_key", "encryption_key",
                     "client_secret", "publishable_key", "webhook_secret"}

    DEFAULT_SETTINGS = {
        "default_currency": "USD",
        "supported_currencies": ["USD", "ZWL", "ZAR", "GBP", "EUR"],
        "invoice_prefix": "INV-", "receipt_prefix": "RCT-", "reference_prefix": "CGN-",
        "payment_timeout_seconds": 1800, "max_retry": 3,
        "auto_generate_invoice": True, "auto_generate_receipt": True,
        "auto_activate_subscription": True, "auto_unlock_content": True,
        "auto_send_email": True, "auto_verify_payment": True,
        "email_notifications": True, "sms_notifications": False, "admin_notifications": True,
        "service_unavailable_message": "Payment service is temporarily unavailable. You can still access this feature — billing will be activated soon.",
        "fail_open": True,
    }

    def __init__(self, db): self.db = db

    async def settings(self) -> dict:
        doc = await self.db.payment_settings.find_one({"_id": "global"})
        if not doc:
            await self.db.payment_settings.insert_one({"_id": "global", **self.DEFAULT_SETTINGS,
                "updated_at": datetime.now(timezone.utc).isoformat()})
            return dict(self.DEFAULT_SETTINGS)
        doc.pop("_id", None)
        return {**self.DEFAULT_SETTINGS, **doc}

    async def update_settings(self, patch: dict) -> dict:
        patch = {k: v for k, v in patch.items() if k in self.DEFAULT_SETTINGS}
        patch["updated_at"] = datetime.now(timezone.utc).isoformat()
        await self.db.payment_settings.update_one({"_id": "global"}, {"$set": patch}, upsert=True)
        return await self.settings()

    async def list_providers(self) -> list[dict]:
        docs = await self.db.payment_providers.find({"deleted_at": None}, {"_id": 0}).to_list(50)
        if not docs:
            await self._seed_providers()
            docs = await self.db.payment_providers.find({"deleted_at": None}, {"_id": 0}).to_list(50)
        return [self._mask(d) for d in docs]

    async def _seed_providers(self):
        now = datetime.now(timezone.utc).isoformat()
        seed = [
            {"slug": "paynow", "display_name": "Paynow", "is_primary": True, "enabled": False,
             "environment": "sandbox", "integration_id": "", "integration_key": "",
             "webhook_secret": "", "result_url": "", "return_url": "",
             "merchant_email": "", "merchant_name": "Cognify", "default_currency": "USD"},
            {"slug": "stripe", "display_name": "Stripe", "enabled": False, "environment": "sandbox",
             "api_key": "", "publishable_key": "", "webhook_secret": ""},
            {"slug": "flutterwave", "display_name": "Flutterwave", "enabled": False,
             "environment": "sandbox", "api_key": "", "secret_key": "", "webhook_secret": ""},
            {"slug": "pesepay", "display_name": "Pesepay", "enabled": False,
             "environment": "sandbox", "api_key": "", "encryption_key": ""},
            {"slug": "paypal", "display_name": "PayPal", "enabled": False, "environment": "sandbox",
             "client_id": "", "client_secret": ""},
        ]
        for p in seed:
            p.update({"id": str(uuid.uuid4()), "created_at": now, "updated_at": now,
                      "deleted_at": None, "last_health_check": None,
                      "health_status": "untested", "webhook_status": "inactive", "api_version": "v1"})
        await self.db.payment_providers.insert_many(seed)

    def _mask(self, doc: dict) -> dict:
        for k in list(doc.keys()):
            if k.endswith("_plain"):
                doc.pop(k, None)
        for k in self.SECRET_FIELDS:
            if doc.get(k):
                plain = decrypt_str(doc[k])
                doc[k + "_preview"] = mask_secret(plain) if plain else "•••"
                doc[k] = "[ENCRYPTED]"
        return doc

    async def configure_provider(self, slug: str, patch: dict) -> dict:
        existing = await self.db.payment_providers.find_one({"slug": slug, "deleted_at": None})
        if not existing: raise ValueError(f"Provider {slug} not found")
        update = {}
        for k, v in patch.items():
            if k in {"slug", "id", "_id", "created_at", "deleted_at"}: continue
            if k in self.SECRET_FIELDS:
                if v:  # only update when non-empty (preserve existing)
                    update[k] = encrypt_str(str(v))
            else:
                update[k] = v
        update["updated_at"] = datetime.now(timezone.utc).isoformat()
        await self.db.payment_providers.update_one({"slug": slug}, {"$set": update})
        out = await self.db.payment_providers.find_one({"slug": slug}, {"_id": 0})
        return self._mask(out)

    async def get_provider_with_secrets(self, slug: str):
        doc = await self.db.payment_providers.find_one({"slug": slug, "deleted_at": None})
        if not doc: return None
        cfg = dict(doc)
        for k in self.SECRET_FIELDS:
            if cfg.get(k): cfg[k + "_plain"] = decrypt_str(cfg[k])
        cfg["integration_id_plain"] = cfg.get("integration_id", "")
        if slug == "paynow": return PaynowProvider(cfg)
        return StubProvider(slug, doc.get("display_name", slug.title()), cfg)

    async def active_provider(self):
        for slug in ("paynow", "stripe", "flutterwave", "pesepay", "paypal"):
            p = await self.get_provider_with_secrets(slug)
            if p and p.enabled: return p
        return None

    async def audit(self, *, actor_id, action, target_type, target_id=None, metadata=None):
        from services.audit_service import log_action
        await log_action(
            self.db,
            actor_id=actor_id,
            action=action,
            entity=target_type,
            entity_id=target_id,
            new_value=metadata or {},
        )

    async def log_event(self, *, level, provider, event, message, payload=None):
        await self.db.payment_logs.insert_one({
            "id": str(uuid.uuid4()), "level": level, "provider": provider,
            "event": event, "message": message, "payload": payload or {},
            "created_at": datetime.now(timezone.utc).isoformat()})

    async def create_payment(self, *, user_id, product_id, amount, currency,
                              description, customer_email, return_url, result_url,
                              metadata=None) -> dict:
        s = await self.settings()
        prov = await self.active_provider()
        if not prov:
            return {"ok": True, "fail_open": True,
                    "message": s.get("service_unavailable_message"),
                    "transaction_id": None, "redirect_url": None}
        ref = f"{s['reference_prefix']}{uuid.uuid4().hex[:10].upper()}"
        tx_id = str(uuid.uuid4())
        await self.db.payment_transactions.insert_one({
            "id": tx_id, "reference": ref, "user_id": user_id, "product_id": product_id,
            "amount": amount, "currency": currency, "description": description,
            "provider": prov.slug, "status": "initiated", "customer_email": customer_email,
            "metadata": metadata or {}, "deleted_at": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()})
        resp = await prov.create_payment(amount=amount, currency=currency, reference=ref,
            description=description, customer_email=customer_email,
            return_url=return_url, result_url=result_url, metadata=metadata)
        await self.db.payment_transactions.update_one({"id": tx_id},
            {"$set": {"provider_transaction_id": resp.get("transaction_id"),
                      "redirect_url": resp.get("redirect_url"),
                      "poll_url": resp.get("poll_url"),
                      "status": "pending" if resp.get("ok") else "failed",
                      "provider_raw": resp.get("raw") or {},
                      "updated_at": datetime.now(timezone.utc).isoformat()}})
        await self.log_event(level="info" if resp.get("ok") else "error",
            provider=prov.slug, event="create",
            message=resp.get("error") or "ok",
            payload={"tx_id": tx_id, "amount": amount, "currency": currency})
        return {**resp, "transaction_id": tx_id, "reference": ref}

    async def verify_payment(self, *, transaction_id) -> dict:
        tx = await self.db.payment_transactions.find_one({"id": transaction_id})
        if not tx: return {"ok": False, "status": "not_found"}
        prov = await self.get_provider_with_secrets(tx["provider"])
        if not prov: return {"ok": False, "status": "no_provider"}
        resp = await prov.verify_payment(transaction_id=tx.get("provider_transaction_id"),
                                          poll_url=tx.get("poll_url"))
        await self.db.payment_transactions.update_one({"id": transaction_id},
            {"$set": {"status": resp.get("status", tx["status"]),
                      "updated_at": datetime.now(timezone.utc).isoformat()}})
        return resp

    async def refund_payment(self, *, transaction_id, amount=None, reason=None):
        tx = await self.db.payment_transactions.find_one({"id": transaction_id})
        if not tx: return {"ok": False, "error": "Transaction not found"}
        prov = await self.get_provider_with_secrets(tx["provider"])
        if not prov: return {"ok": False, "error": "Provider unavailable"}
        resp = await prov.refund_payment(transaction_id=tx.get("provider_transaction_id"),
                                          amount=amount, reason=reason)
        if resp.get("ok"):
            await self.db.payment_refunds.insert_one({
                "id": str(uuid.uuid4()), "transaction_id": transaction_id,
                "amount": amount or tx["amount"], "reason": reason, "status": "completed",
                "deleted_at": None,
                "created_at": datetime.now(timezone.utc).isoformat()})
            await self.db.payment_transactions.update_one({"id": transaction_id},
                {"$set": {"status": "refunded",
                          "updated_at": datetime.now(timezone.utc).isoformat()}})
        return resp

    async def cancel_payment(self, *, transaction_id):
        tx = await self.db.payment_transactions.find_one({"id": transaction_id})
        if not tx: return {"ok": False, "error": "Transaction not found"}
        prov = await self.get_provider_with_secrets(tx["provider"])
        if not prov: return {"ok": False, "error": "Provider unavailable"}
        resp = await prov.cancel_payment(transaction_id=tx.get("provider_transaction_id"))
        if resp.get("ok"):
            await self.db.payment_transactions.update_one({"id": transaction_id},
                {"$set": {"status": "cancelled",
                          "updated_at": datetime.now(timezone.utc).isoformat()}})
        return resp
