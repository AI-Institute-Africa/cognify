"""Organization Public Join Link.

Feature: allow any organization to share a public URL (e.g. /join/<org-slug>)
where anonymous visitors can sign up and be auto-attached to that org as
members. Signups enter a "pending" state and must be approved by the org admin
before they gain course access.

Endpoints:
    Public (no auth):
      GET  /api/public/org/{slug}                       — landing page data
      POST /api/public/org/{slug}/signup                — apply to join
    Org Admin:
      GET  /api/org-admin/join-settings                 — read link config
      PUT  /api/org-admin/join-settings                 — update link config
      GET  /api/org-admin/pending-members               — pending signup list
      POST /api/org-admin/pending-members/{uid}/approve — approve one
      POST /api/org-admin/pending-members/{uid}/reject  — reject one
      GET  /api/org-admin/members                       — all approved members
"""
from __future__ import annotations
import re
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, EmailStr, Field

logger = logging.getLogger(__name__)


class JoinSettings(BaseModel):
    enabled: bool = True
    require_approval: bool = True
    allowed_domains: list[str] = Field(default_factory=list)


class OrgJoinSignup(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None


def _slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", (name or "").lower()).strip("-")
    return s or "org"


def _domain(email: str) -> str:
    return email.split("@", 1)[-1].strip().lower() if "@" in email else ""


def make_router(db, require_org_admin, get_current_user, hash_password_fn,
                create_token_fn, verify_password_fn):
    """Return a single APIRouter mounting all join-related endpoints under /api."""
    router = APIRouter(prefix="/api")

    # ------------------------------------------------------------------ helpers
    async def _get_org_by_slug(slug: str) -> dict:
        # Match either the persisted slug field or a slugified `name`
        slug_lc = slug.lower()
        orgs = db.organizations
        org = await orgs.find_one({"join_slug": slug_lc}, {"_id": 0})
        if not org:
            org = await orgs.find_one({"slug": slug_lc}, {"_id": 0})
        if not org:
            # Fallback: derive from name (older orgs don't have join_slug)
            async for o in orgs.find({}, {"_id": 0}):
                if _slugify(o.get("name", "")) == slug_lc:
                    org = o
                    break
        return org

    async def _ensure_join_slug(org: dict) -> str:
        if org.get("join_slug"):
            return org["join_slug"]
        base = _slugify(org.get("name") or "org")
        candidate = base
        n = 1
        while await db.organizations.find_one({"join_slug": candidate}):
            n += 1
            candidate = f"{base}-{n}"
        await db.organizations.update_one({"id": org["id"]}, {"$set": {"join_slug": candidate}})
        return candidate

    # ---------------------------------------------------------------- public UI
    @router.get("/public/org/{slug}")
    async def public_org_landing(slug: str):
        """Landing-page data for /join/<slug>. Includes the org's public courses."""
        org = await _get_org_by_slug(slug)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        # Guard: org must have opted in (default enabled=True for backfill)
        js = (org.get("join_settings") or {})
        if not js.get("enabled", True):
            raise HTTPException(status_code=403, detail="Public join link is disabled for this organization")

        # List public courses within this org (visibility == 'public' OR is_public == True)
        courses_cursor = db.courses.find(
            {"organization_id": org["id"],
             "$or": [{"visibility": "public"}, {"is_public": True}]},
            {"_id": 0, "id": 1, "title": 1, "description": 1, "cover_image": 1,
             "subject": 1, "grade_level": 1, "duration_hours": 1,
             "is_free": 1, "price": 1, "currency": 1})
        courses = await courses_cursor.to_list(length=200)

        member_count = await db.users.count_documents(
            {"organization_id": org["id"], "member_status": {"$ne": "pending"}})

        return {
            "org": {
                "id": org["id"],
                "name": org.get("name"),
                "description": org.get("description") or org.get("about"),
                "logo_url": org.get("logo_url"),
                "website": org.get("website"),
                "country": org.get("country"),
                "org_type": org.get("org_type"),
            },
            "public_courses": courses,
            "member_count": member_count,
            "join_slug": await _ensure_join_slug(org),
            "require_approval": js.get("require_approval", True),
        }

    @router.post("/public/org/{slug}/signup")
    async def public_org_signup(slug: str, payload: OrgJoinSignup):
        """Anonymous visitor signs up under an org. Enters pending status by default."""
        org = await _get_org_by_slug(slug)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        js = (org.get("join_settings") or {})
        if not js.get("enabled", True):
            raise HTTPException(status_code=403, detail="Public join link is disabled for this organization")

        # Domain allow-list check
        allowed = js.get("allowed_domains") or []
        if allowed:
            if _domain(payload.email) not in [d.lower().lstrip("@") for d in allowed]:
                raise HTTPException(
                    status_code=400,
                    detail=f"This organization only accepts sign-ups from: {', '.join(allowed)}")

        # Idempotency: reject if email already registered
        existing = await db.users.find_one({"email": payload.email.lower()}, {"_id": 0, "id": 1, "organization_id": 1})
        if existing:
            raise HTTPException(status_code=400, detail="An account with this email already exists. Please log in.")

        # Password strength (basic)
        if len(payload.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

        require_approval = js.get("require_approval", True)
        member_status = "pending" if require_approval else "active"

        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        user_doc = {
            "id": user_id,
            "email": payload.email.lower(),
            "full_name": payload.full_name.strip(),
            "phone": payload.phone,
            "role": "student",
            "organization_id": org["id"],
            "member_status": member_status,
            "joined_via": "public_link",
            "joined_slug": slug.lower(),
            "password_hash": hash_password_fn(payload.password),
            "created_at": now,
            "email_verified": False,
        }
        await db.users.insert_one(user_doc)

        # Notify org admin (best-effort)
        try:
            from services.smtp_notifications import send_email, render_notification
            org_admin = await db.users.find_one(
                {"organization_id": org["id"], "role": {"$in": ["org_admin", "admin"]}},
                {"_id": 0, "email": 1, "full_name": 1})
            if org_admin and org_admin.get("email"):
                subject = f"New member signup — {payload.full_name} wants to join {org.get('name')}"
                body = render_notification(
                    title=subject,
                    message=(
                        f"<p><strong>{payload.full_name}</strong> ({payload.email}) has "
                        f"requested to join <strong>{org.get('name')}</strong> via your "
                        f"public join link.</p>"
                        f"<p>Approve or reject them from the Members panel.</p>"
                    ),
                    action_label="Review Pending Members" if require_approval else "View Members",
                )
                import os
                frontend = (os.environ.get("PUBLIC_FRONTEND_URL") or "").rstrip("/")
                # send_email is async and returns bool
                await send_email(org_admin["email"], subject, body)
        except Exception as e:
            logger.warning(f"member signup notification failed: {e}")

        if require_approval:
            return {
                "status": "pending",
                "message": ("Your application has been received. "
                            "You will receive an email once the organization admin approves you."),
                "user_id": user_id,
            }
        # Auto-approved → issue token immediately
        token = create_token_fn(user_id, "student")
        return {
            "status": "active",
            "message": "Welcome — your account is ready.",
            "user_id": user_id,
            "access_token": token,
            "user": {"id": user_id, "email": payload.email.lower(),
                     "full_name": payload.full_name, "role": "student",
                     "organization_id": org["id"]},
        }

    # --------------------------------------------------------------- admin side
    async def _get_admin_org(current_user: dict) -> dict:
        org_id = current_user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No organization on this account")
        org = await db.organizations.find_one({"id": org_id}, {"_id": 0})
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        return org

    @router.get("/org-admin/join-settings")
    async def get_join_settings(current_user: dict = Depends(require_org_admin)):
        org = await _get_admin_org(current_user)
        slug = await _ensure_join_slug(org)
        js = org.get("join_settings") or {}
        return {
            "join_slug": slug,
            "enabled": js.get("enabled", True),
            "require_approval": js.get("require_approval", True),
            "allowed_domains": js.get("allowed_domains", []),
        }

    @router.put("/org-admin/join-settings")
    async def update_join_settings(patch: JoinSettings,
                                    current_user: dict = Depends(require_org_admin)):
        org = await _get_admin_org(current_user)
        await _ensure_join_slug(org)
        clean_domains = [d.strip().lower().lstrip("@")
                         for d in (patch.allowed_domains or []) if d.strip()]
        await db.organizations.update_one(
            {"id": org["id"]},
            {"$set": {"join_settings": {
                "enabled": bool(patch.enabled),
                "require_approval": bool(patch.require_approval),
                "allowed_domains": clean_domains,
            }}})
        return await get_join_settings(current_user)

    @router.get("/org-admin/pending-members")
    async def list_pending_members(current_user: dict = Depends(require_org_admin)):
        org = await _get_admin_org(current_user)
        cursor = db.users.find(
            {"organization_id": org["id"], "member_status": "pending"},
            {"_id": 0, "id": 1, "email": 1, "full_name": 1, "phone": 1,
             "created_at": 1, "joined_via": 1, "joined_slug": 1})
        pending = await cursor.to_list(length=500)
        return {"pending": pending, "count": len(pending)}

    @router.get("/org-admin/members")
    async def list_members(current_user: dict = Depends(require_org_admin)):
        org = await _get_admin_org(current_user)
        cursor = db.users.find(
            {"organization_id": org["id"],
             "$or": [{"member_status": "active"},
                     {"member_status": {"$exists": False}}]},
            {"_id": 0, "id": 1, "email": 1, "full_name": 1, "role": 1,
             "member_status": 1, "created_at": 1, "last_seen_at": 1, "joined_via": 1})
        members = await cursor.to_list(length=2000)
        return {"members": members, "count": len(members)}

    @router.post("/org-admin/pending-members/{user_id}/approve")
    async def approve_member(user_id: str,
                              current_user: dict = Depends(require_org_admin)):
        org = await _get_admin_org(current_user)
        user = await db.users.find_one(
            {"id": user_id, "organization_id": org["id"], "member_status": "pending"},
            {"_id": 0, "email": 1, "full_name": 1})
        if not user:
            raise HTTPException(status_code=404, detail="Pending member not found")
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"member_status": "active",
                      "approved_at": datetime.now(timezone.utc).isoformat(),
                      "approved_by": current_user.get("id")}})
        # Notify user
        try:
            from services.smtp_notifications import send_email, render_notification
            subject = f"You've been approved — welcome to {org.get('name')}"
            body = render_notification(
                title=f"Welcome to {org.get('name')}",
                message=(
                    f"<p>Hi {user.get('full_name')},</p>"
                    f"<p>Your application to join <strong>{org.get('name')}</strong> "
                    f"has been approved. You now have full access to the "
                    f"organization's courses and resources.</p>"
                ),
                action_label="Log in and start learning",
            )
            await send_email(user["email"], subject, body)
        except Exception as e:
            logger.warning(f"approval notification failed: {e}")
        return {"status": "approved", "user_id": user_id}

    @router.post("/org-admin/pending-members/{user_id}/reject")
    async def reject_member(user_id: str,
                             reason: Optional[str] = Body(None, embed=True),
                             current_user: dict = Depends(require_org_admin)):
        org = await _get_admin_org(current_user)
        user = await db.users.find_one(
            {"id": user_id, "organization_id": org["id"], "member_status": "pending"},
            {"_id": 0, "email": 1, "full_name": 1})
        if not user:
            raise HTTPException(status_code=404, detail="Pending member not found")
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"member_status": "rejected",
                      "rejected_at": datetime.now(timezone.utc).isoformat(),
                      "rejected_by": current_user.get("id"),
                      "rejection_reason": reason}})
        try:
            from services.smtp_notifications import send_email, render_notification
            subject = f"Your application to {org.get('name')} was not accepted"
            body = render_notification(
                title="Application update",
                message=(
                    f"<p>Hi {user.get('full_name')},</p>"
                    f"<p>Your application to join <strong>{org.get('name')}</strong> "
                    f"was not accepted at this time."
                    + (f"</p><p><em>Reason:</em> {reason}</p>" if reason else "</p>")
                    + "<p>You may contact the organization directly if you have questions.</p>"
                ),
            )
            await send_email(user["email"], subject, body)
        except Exception as e:
            logger.warning(f"rejection notification failed: {e}")
        return {"status": "rejected", "user_id": user_id}

    return router
