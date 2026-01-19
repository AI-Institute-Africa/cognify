"""Enumeration types for the application"""
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"
    ORG_ADMIN = "org_admin"

class OrgType(str, Enum):
    SCHOOL = "school"
    UNIVERSITY = "university"
    GOVERNMENT = "government"
    INSTITUTION = "institution"
    CORPORATE = "corporate"

class OrgStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

class FeeStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    PARTIAL = "partial"

class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"

class ContentType(str, Enum):
    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"

class ConceptStatus(str, Enum):
    NOT_STARTED = "not_started"
    LEARNING = "learning"
    MASTERED = "mastered"
    NEEDS_REVIEW = "needs_review"
