"""Course and academic models"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid
from .enums import AttendanceStatus, FeeStatus

class Course(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    name: str
    description: str
    teacher_id: Optional[str] = None
    organization_id: Optional[str] = None
    grade_level: str
    credits: int = 3
    schedule: Optional[dict] = None
    syllabus: Optional[str] = None
    syllabus_upload_id: Optional[str] = None
    concepts: List[str] = []
    enrolled_students: List[str] = []
    max_students: int = 30
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CourseCreate(BaseModel):
    code: str
    name: str
    description: str
    teacher_id: Optional[str] = None
    grade_level: str
    credits: int = 3
    max_students: int = 30

class Attendance(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    course_id: str
    date: str
    status: AttendanceStatus
    remarks: Optional[str] = None
    marked_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AttendanceCreate(BaseModel):
    student_id: str
    course_id: str
    date: str
    status: AttendanceStatus
    remarks: Optional[str] = None

class Grade(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    course_id: str
    assessment_type: str
    assessment_name: str
    score: float
    max_score: float = 100
    weight: float = 1.0
    remarks: Optional[str] = None
    graded_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GradeCreate(BaseModel):
    student_id: str
    course_id: str
    assessment_type: str
    assessment_name: str
    score: float
    max_score: float = 100
    weight: float = 1.0
    remarks: Optional[str] = None

class Fee(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    fee_type: str
    description: str
    amount: float
    paid_amount: float = 0
    due_date: str
    status: FeeStatus = FeeStatus.PENDING
    payment_history: List[dict] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FeeCreate(BaseModel):
    student_id: str
    fee_type: str
    description: str
    amount: float
    due_date: str

class Achievement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    title: str
    description: str
    category: str
    date_awarded: str
    awarded_by: str
    badge_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AchievementCreate(BaseModel):
    student_id: str
    title: str
    description: str
    category: str
    date_awarded: str
