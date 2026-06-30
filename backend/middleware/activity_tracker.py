"""Activity tracking middleware.

For each request:
  - If authenticated, bumps user.last_seen_at and user.total_active_seconds (only
    counting time when the gap between requests is < 5 min — anything bigger is
    treated as "idle" and not added to the active-time counter).
  - If anonymous and hitting a public path (/, /public, /api/public/*), inserts a
    lightweight row into the anonymous_visits collection (IP + UA + referrer).
"""
from __future__ import annotations
import os
from datetime import datetime, timezone
from starlette.middleware.base import BaseHTTPMiddleware
import jwt as _jwt
import uuid

JWT_SECRET = os.environ.get("JWT_SECRET") or os.environ.get("SECRET_KEY", "cognify-secret")
JWT_ALG = "HS256"
ACTIVE_GAP_SECONDS = 300  # 5 min — bigger gap counts as "new session"


def install(app, db):
    async def get_uid(req) -> str | None:
        auth = req.headers.get("Authorization", "")
        if not auth.lower().startswith("bearer "):
            return None
        try:
            data = _jwt.decode(auth.split(" ", 1)[1], JWT_SECRET, algorithms=[JWT_ALG])
            return data.get("sub") or data.get("user_id") or data.get("id")
        except Exception:
            return None

    class _Activity(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            try:
                now = datetime.now(timezone.utc)
                now_iso = now.isoformat()
                uid = await get_uid(request)
                if uid:
                    last = await db.users.find_one({"id": uid}, {"_id": 0, "last_seen_at": 1, "total_active_seconds": 1})
                    inc = 0
                    if last and last.get("last_seen_at"):
                        try:
                            prev = datetime.fromisoformat(last["last_seen_at"])
                            gap = (now - prev).total_seconds()
                            if 0 <= gap <= ACTIVE_GAP_SECONDS:
                                inc = int(gap)
                        except Exception:
                            inc = 0
                    update = {"$set": {"last_seen_at": now_iso}}
                    if inc:
                        update["$inc"] = {"total_active_seconds": inc}
                    referrer = request.headers.get("referer") or request.headers.get("referrer")
                    if referrer and "cognify" not in referrer.lower() and "aiinstituteafrica" not in referrer.lower() and "emergentagent" not in referrer.lower():
                        update["$set"]["last_referrer"] = referrer[:512]
                    await db.users.update_one({"id": uid}, update)
                else:
                    # Anonymous visit — only record public paths
                    path = request.url.path or ""
                    if path == "/" or path.startswith("/public") or path.startswith("/api/public"):
                        ip = (request.client.host if request.client else None) or "?"
                        await db.anonymous_visits.insert_one({
                            "id": str(uuid.uuid4()),
                            "ip": ip,
                            "path": path,
                            "method": request.method,
                            "ua": (request.headers.get("user-agent") or "")[:300],
                            "referrer": (request.headers.get("referer") or "")[:512],
                            "created_at": now_iso,
                        })
            except Exception:
                pass
            return response

    app.add_middleware(_Activity)
