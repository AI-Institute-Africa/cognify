"""Shared authentication utilities"""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt

from database import db
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS

security = HTTPBearer()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user_id: str, role: str, org_id: str = None) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "org_id": org_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def serialize_doc(doc: dict) -> dict:
    if doc and 'created_at' in doc and isinstance(doc['created_at'], datetime):
        doc['created_at'] = doc['created_at'].isoformat()
    if doc and 'graded_at' in doc and isinstance(doc['graded_at'], datetime):
        doc['graded_at'] = doc['graded_at'].isoformat()
    if doc and 'last_reviewed' in doc and isinstance(doc['last_reviewed'], datetime):
        doc['last_reviewed'] = doc['last_reviewed'].isoformat()
    if doc and 'next_review' in doc and isinstance(doc['next_review'], datetime):
        doc['next_review'] = doc['next_review'].isoformat()
    return doc


async def check_staff_permission(user: dict, permission: str) -> bool:
    """Check if a teacher has the required staff permission. Org admins and admins always pass."""
    if user.get('role') in ['org_admin', 'admin']:
        return True
    if user.get('role') != 'teacher':
        return False
    org_id = user.get('org_id') or user.get('organization_id')
    if not org_id:
        return False
    rights_doc = await db.staff_rights.find_one(
        {"user_id": user.get('id'), "org_id": org_id},
        {"_id": 0}
    )
    if not rights_doc:
        return True  # No rights record = default allow for teachers
    return rights_doc.get(permission, False)
