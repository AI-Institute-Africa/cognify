"""Organization models"""
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid
from .enums import OrgType, OrgStatus

class Organization(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    org_type: OrgType
    country: str
    address: str
    phone: str
    email: EmailStr
    website: Optional[str] = None
    logo_url: Optional[str] = None
    registration_number: Optional[str] = None
    verification_docs: List[str] = []
    status: OrgStatus = OrgStatus.PENDING
    admin_user_id: Optional[str] = None
    participant_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OrganizationCreate(BaseModel):
    name: str
    org_type: OrgType
    country: str
    address: str
    phone: str
    email: EmailStr
    website: Optional[str] = None
    registration_number: Optional[str] = None
    admin_name: str
    admin_email: EmailStr
    admin_password: str
