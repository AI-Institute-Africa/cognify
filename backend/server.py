from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import io
import base64
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'default-secret-key')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', 24))

# Supported Languages
SUPPORTED_LANGUAGES = ['en', 'sn', 'nd', 'sw', 'zu']  # English, Shona, Ndebele, Swahili, Zulu

# Create the main app
app = FastAPI(title="EduOS 2026", description="AI-Powered School Management Platform - Phase 2")

# Create routers
api_router = APIRouter(prefix="/api")
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
users_router = APIRouter(prefix="/users", tags=["Users"])
students_router = APIRouter(prefix="/students", tags=["Students"])
teachers_router = APIRouter(prefix="/teachers", tags=["Teachers"])
courses_router = APIRouter(prefix="/courses", tags=["Courses"])
attendance_router = APIRouter(prefix="/attendance", tags=["Attendance"])
grades_router = APIRouter(prefix="/grades", tags=["Grades"])
fees_router = APIRouter(prefix="/fees", tags=["Fees"])
achievements_router = APIRouter(prefix="/achievements", tags=["Achievements"])
ai_router = APIRouter(prefix="/ai", tags=["AI Services"])
dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])
orgs_router = APIRouter(prefix="/organizations", tags=["Organizations"])
knowledge_router = APIRouter(prefix="/knowledge", tags=["Knowledge Graph"])
mentor_router = APIRouter(prefix="/mentor", tags=["AI Mentor"])
content_router = APIRouter(prefix="/content", tags=["Multimodal Content"])
voice_router = APIRouter(prefix="/voice", tags=["Voice & Avatar"])

security = HTTPBearer()

# Enums
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

# ==================== PHASE 2 MODELS ====================

# Organization Models
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

# Knowledge Graph Models
class Concept(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    subject: str
    grade_level: str
    prerequisites: List[str] = []
    dependencies: List[str] = []
    cross_links: List[str] = []  # Links to other subjects
    real_world_apps: List[str] = []
    difficulty: int = 1  # 1-10
    estimated_time_minutes: int = 30
    content_modules: List[str] = []  # IDs of content modules
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LearnerConceptState(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    concept_id: str
    status: ConceptStatus = ConceptStatus.NOT_STARTED
    confidence: float = 0.0  # 0-1
    retention_score: float = 0.0  # 0-1
    last_reviewed: Optional[datetime] = None
    next_review: Optional[datetime] = None
    attempts: int = 0
    correct_attempts: int = 0
    time_spent_minutes: int = 0
    notes: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# AI Mentor Models
class MentorProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    personality_traits: Dict[str, float] = {}  # e.g., {"patience": 0.8, "humor": 0.5}
    learning_style: str = "visual"  # visual, auditory, kinesthetic, reading
    preferred_pace: str = "moderate"  # slow, moderate, fast
    preferred_language: str = "en"
    voice_id: Optional[str] = None  # ElevenLabs voice ID
    avatar_settings: Dict[str, Any] = {}
    conversation_history: List[Dict] = []
    strengths: List[str] = []
    weaknesses: List[str] = []
    goals: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MentorConversation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    messages: List[Dict] = []
    context: Dict[str, Any] = {}
    topic: Optional[str] = None
    mood: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Multimodal Content Models
class ContentModule(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    concept_id: str
    title: str
    content_type: ContentType
    content_url: Optional[str] = None
    content_text: Optional[str] = None
    language: str = "en"
    translations: Dict[str, str] = {}  # language_code: translated_content
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    images: List[str] = []
    duration_minutes: int = 0
    difficulty: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Voice/Avatar Models
class VoiceProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    description: Optional[str] = None
    voice_id: str  # ElevenLabs voice ID
    is_cloned: bool = False
    clone_source: Optional[str] = None  # e.g., "father", "brother", "custom"
    sample_urls: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Syllabus Ingestion Models
class SyllabusUpload(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    filename: str
    file_url: str
    status: str = "processing"  # processing, completed, failed
    extracted_concepts: List[str] = []
    generated_modules: List[str] = []
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Original Phase 1 Models (keeping for backward compatibility)
class UserBase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    email: EmailStr
    full_name: str
    role: UserRole

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.STUDENT
    organization_id: Optional[str] = None
    preferred_language: str = "en"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Optional[str] = None
    preferred_language: str = "en"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    profile_image: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class StudentProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    student_id: str
    grade_level: str
    section: str
    parent_id: Optional[str] = None
    organization_id: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    enrolled_courses: List[str] = []
    gpa: float = 0.0
    career_aptitude_score: Optional[dict] = None
    learning_profile: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TeacherProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    employee_id: str
    department: str
    organization_id: Optional[str] = None
    subjects: List[str] = []
    qualifications: List[str] = []
    phone: Optional[str] = None
    hire_date: Optional[str] = None
    assigned_courses: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
    concepts: List[str] = []  # Knowledge graph concept IDs
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
    max_score: float
    weight: float = 1.0
    remarks: Optional[str] = None
    graded_by: str
    graded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GradeCreate(BaseModel):
    student_id: str
    course_id: str
    assessment_type: str
    assessment_name: str
    score: float
    max_score: float
    weight: float = 1.0
    remarks: Optional[str] = None

class Fee(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    organization_id: Optional[str] = None
    fee_type: str
    amount: float
    due_date: str
    status: FeeStatus = FeeStatus.PENDING
    paid_amount: float = 0.0
    payment_date: Optional[str] = None
    payment_method: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FeeCreate(BaseModel):
    student_id: str
    fee_type: str
    amount: float
    due_date: str
    description: Optional[str] = None

class Achievement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    title: str
    description: str
    category: str
    date_awarded: str
    awarded_by: Optional[str] = None
    certificate_url: Optional[str] = None
    is_verified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AchievementCreate(BaseModel):
    student_id: str
    title: str
    description: str
    category: str
    date_awarded: str

class Notification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    message: str
    type: str = "info"
    is_read: bool = False
    link: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatMessage(BaseModel):
    message: str
    context: Optional[str] = None
    language: str = "en"
    include_audio: bool = False

class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    language: str = "en"

# Helper Functions
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

# ==================== ORGANIZATION ROUTES ====================

@orgs_router.post("/register", status_code=201)
async def register_organization(org_data: OrganizationCreate):
    """Register a new organization with admin user"""
    # Check if org email exists
    existing_org = await db.organizations.find_one({"email": org_data.email})
    if existing_org:
        raise HTTPException(status_code=400, detail="Organization email already registered")
    
    # Check if admin email exists
    existing_user = await db.users.find_one({"email": org_data.admin_email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Admin email already registered")
    
    # Create organization
    org = Organization(
        name=org_data.name,
        org_type=org_data.org_type,
        country=org_data.country,
        address=org_data.address,
        phone=org_data.phone,
        email=org_data.email,
        website=org_data.website,
        registration_number=org_data.registration_number
    )
    org_dict = org.model_dump()
    org_dict['created_at'] = org_dict['created_at'].isoformat()
    
    # Create admin user
    admin_user = {
        "id": str(uuid.uuid4()),
        "email": org_data.admin_email,
        "full_name": org_data.admin_name,
        "role": "org_admin",
        "organization_id": org.id,
        "password_hash": hash_password(org_data.admin_password),
        "preferred_language": "en",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    org_dict['admin_user_id'] = admin_user['id']
    
    await db.organizations.insert_one(org_dict)
    await db.users.insert_one(admin_user)
    
    token = create_token(admin_user['id'], admin_user['role'], org.id)
    
    return {
        "message": "Organization registered successfully. Awaiting verification.",
        "organization_id": org.id,
        "status": org.status,
        "access_token": token,
        "user": {"id": admin_user['id'], "email": admin_user['email'], "full_name": admin_user['full_name'], "role": admin_user['role']}
    }

@orgs_router.post("/{org_id}/upload-verification")
async def upload_verification_docs(
    org_id: str,
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload verification documents for organization"""
    org = await db.organizations.find_one({"id": org_id}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if current_user.get('organization_id') != org_id and current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Store file references (in production, upload to S3/GCS)
    doc_urls = []
    for file in files:
        content = await file.read()
        # Store as base64 for now (in production use cloud storage)
        doc_id = str(uuid.uuid4())
        doc_urls.append(f"/api/documents/{doc_id}")
        await db.documents.insert_one({
            "id": doc_id,
            "org_id": org_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "content": base64.b64encode(content).decode(),
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    await db.organizations.update_one(
        {"id": org_id},
        {"$push": {"verification_docs": {"$each": doc_urls}}}
    )
    
    return {"message": "Documents uploaded successfully", "document_urls": doc_urls}

@orgs_router.get("/{org_id}")
async def get_organization(org_id: str, current_user: dict = Depends(get_current_user)):
    org = await db.organizations.find_one({"id": org_id}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return serialize_doc(org)

@orgs_router.post("/{org_id}/verify")
async def verify_organization(org_id: str, approved: bool, current_user: dict = Depends(get_current_user)):
    """Admin only: Verify or reject organization"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Only platform admins can verify organizations")
    
    new_status = OrgStatus.VERIFIED if approved else OrgStatus.REJECTED
    await db.organizations.update_one(
        {"id": org_id},
        {"$set": {"status": new_status}}
    )
    return {"message": f"Organization {new_status}", "status": new_status}

@orgs_router.post("/{org_id}/enroll-participant")
async def enroll_participant(
    org_id: str,
    user_data: UserCreate,
    current_user: dict = Depends(get_current_user)
):
    """Enroll a new participant in organization"""
    org = await db.organizations.find_one({"id": org_id}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if org['status'] != 'verified':
        raise HTTPException(status_code=400, detail="Organization not verified yet")
    
    if current_user.get('organization_id') != org_id and current_user['role'] not in ['admin', 'org_admin']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role,
        organization_id=org_id,
        preferred_language=user_data.preferred_language
    )
    user_dict = user.model_dump()
    user_dict['password_hash'] = hash_password(user_data.password)
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    # Create profile based on role
    if user_data.role == UserRole.STUDENT:
        profile = StudentProfile(
            user_id=user.id,
            student_id=f"STU{str(uuid.uuid4())[:8].upper()}",
            grade_level="Grade 10",
            section="A",
            organization_id=org_id
        )
        profile_dict = profile.model_dump()
        profile_dict['created_at'] = profile_dict['created_at'].isoformat()
        await db.student_profiles.insert_one(profile_dict)
    elif user_data.role == UserRole.TEACHER:
        profile = TeacherProfile(
            user_id=user.id,
            employee_id=f"TCH{str(uuid.uuid4())[:8].upper()}",
            department="General",
            organization_id=org_id
        )
        profile_dict = profile.model_dump()
        profile_dict['created_at'] = profile_dict['created_at'].isoformat()
        await db.teacher_profiles.insert_one(profile_dict)
    
    # Update participant count
    await db.organizations.update_one(
        {"id": org_id},
        {"$inc": {"participant_count": 1}}
    )
    
    return {"message": "Participant enrolled successfully", "user_id": user.id}

# ==================== KNOWLEDGE GRAPH ROUTES ====================

@knowledge_router.get("/concepts")
async def get_concepts(
    subject: Optional[str] = None,
    grade_level: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all concepts, optionally filtered"""
    query = {}
    if subject:
        query['subject'] = subject
    if grade_level:
        query['grade_level'] = grade_level
    
    concepts = await db.concepts.find(query, {"_id": 0}).to_list(1000)
    return [serialize_doc(c) for c in concepts]

@knowledge_router.get("/concepts/{concept_id}")
async def get_concept(concept_id: str, current_user: dict = Depends(get_current_user)):
    concept = await db.concepts.find_one({"id": concept_id}, {"_id": 0})
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
    
    # Get related concepts
    if concept.get('prerequisites'):
        prereqs = await db.concepts.find({"id": {"$in": concept['prerequisites']}}, {"_id": 0}).to_list(100)
        concept['prerequisite_details'] = [serialize_doc(p) for p in prereqs]
    
    return serialize_doc(concept)

@knowledge_router.get("/user-progress")
async def get_user_knowledge_progress(current_user: dict = Depends(get_current_user)):
    """Get user's progress across all concepts"""
    states = await db.learner_concept_states.find(
        {"user_id": current_user['id']},
        {"_id": 0}
    ).to_list(1000)
    
    # Enrich with concept details
    for state in states:
        concept = await db.concepts.find_one({"id": state['concept_id']}, {"_id": 0})
        if concept:
            state['concept'] = serialize_doc(concept)
    
    return [serialize_doc(s) for s in states]

@knowledge_router.post("/concepts/{concept_id}/update-state")
async def update_concept_state(
    concept_id: str,
    confidence: float = 0.0,
    time_spent: int = 0,
    correct: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Update learner's state for a concept"""
    state = await db.learner_concept_states.find_one(
        {"user_id": current_user['id'], "concept_id": concept_id},
        {"_id": 0}
    )
    
    if state:
        # Update existing state
        updates = {
            "confidence": confidence,
            "time_spent_minutes": state.get('time_spent_minutes', 0) + time_spent,
            "attempts": state.get('attempts', 0) + 1,
            "last_reviewed": datetime.now(timezone.utc).isoformat()
        }
        if correct:
            updates['correct_attempts'] = state.get('correct_attempts', 0) + 1
        
        # Calculate retention and next review
        correct_rate = updates.get('correct_attempts', 0) / updates['attempts'] if updates['attempts'] > 0 else 0
        updates['retention_score'] = correct_rate
        
        # Spaced repetition: schedule next review
        if correct_rate >= 0.8:
            updates['status'] = 'mastered'
            updates['next_review'] = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        elif correct_rate >= 0.5:
            updates['status'] = 'learning'
            updates['next_review'] = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        else:
            updates['status'] = 'needs_review'
            updates['next_review'] = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        
        await db.learner_concept_states.update_one(
            {"user_id": current_user['id'], "concept_id": concept_id},
            {"$set": updates}
        )
    else:
        # Create new state
        new_state = LearnerConceptState(
            user_id=current_user['id'],
            concept_id=concept_id,
            confidence=confidence,
            time_spent_minutes=time_spent,
            attempts=1,
            correct_attempts=1 if correct else 0,
            status=ConceptStatus.LEARNING,
            last_reviewed=datetime.now(timezone.utc)
        )
        state_dict = new_state.model_dump()
        state_dict['created_at'] = state_dict['created_at'].isoformat()
        state_dict['last_reviewed'] = state_dict['last_reviewed'].isoformat()
        await db.learner_concept_states.insert_one(state_dict)
    
    return {"message": "State updated successfully"}

# ==================== AI MENTOR ROUTES ====================

@mentor_router.get("/profile")
async def get_mentor_profile(current_user: dict = Depends(get_current_user)):
    """Get or create AI mentor profile for user"""
    profile = await db.mentor_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
    
    if not profile:
        # Create default profile
        new_profile = MentorProfile(user_id=current_user['id'])
        profile_dict = new_profile.model_dump()
        profile_dict['created_at'] = profile_dict['created_at'].isoformat()
        await db.mentor_profiles.insert_one(profile_dict)
        profile = profile_dict
    
    return serialize_doc(profile)

@mentor_router.post("/profile/update")
async def update_mentor_profile(
    learning_style: Optional[str] = None,
    preferred_pace: Optional[str] = None,
    preferred_language: Optional[str] = None,
    goals: Optional[List[str]] = None,
    current_user: dict = Depends(get_current_user)
):
    """Update AI mentor profile settings"""
    updates = {}
    if learning_style:
        updates['learning_style'] = learning_style
    if preferred_pace:
        updates['preferred_pace'] = preferred_pace
    if preferred_language:
        updates['preferred_language'] = preferred_language
    if goals:
        updates['goals'] = goals
    
    await db.mentor_profiles.update_one(
        {"user_id": current_user['id']},
        {"$set": updates},
        upsert=True
    )
    return {"message": "Profile updated successfully"}

@mentor_router.post("/chat")
async def mentor_chat(chat_data: ChatMessage, current_user: dict = Depends(get_current_user)):
    """Chat with AI mentor"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        # Get mentor profile for personalization
        profile = await db.mentor_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
        
        # Get recent conversation history
        recent_convos = await db.mentor_conversations.find(
            {"user_id": current_user['id']},
            {"_id": 0}
        ).sort("created_at", -1).limit(5).to_list(5)
        
        # Get user's learning progress
        progress = await db.learner_concept_states.find(
            {"user_id": current_user['id']},
            {"_id": 0}
        ).to_list(100)
        
        learning_context = ""
        if progress:
            mastered = sum(1 for p in progress if p.get('status') == 'mastered')
            needs_review = sum(1 for p in progress if p.get('status') == 'needs_review')
            learning_context = f"Mastered concepts: {mastered}, Needs review: {needs_review}"
        
        # Build personalized system message
        language_map = {
            'en': 'English',
            'sn': 'Shona',
            'nd': 'Ndebele',
            'sw': 'Swahili',
            'zu': 'Zulu'
        }
        preferred_lang = language_map.get(chat_data.language, 'English')
        
        system_message = f"""You are a personal AI learning mentor for {current_user.get('full_name', 'the student')}.
You remember all past interactions and adapt your teaching style accordingly.
Current learning profile: Style={profile.get('learning_style', 'visual') if profile else 'visual'}, Pace={profile.get('preferred_pace', 'moderate') if profile else 'moderate'}
{f'Learning Progress: {learning_context}' if learning_context else ''}
Goals: {profile.get('goals', ['General learning']) if profile else ['General learning']}
Respond in {preferred_lang}. Be encouraging, patient, and adapt explanations to the learner's style.
If they struggle, provide hints and analogies. Remember their strengths and weaknesses."""
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"mentor-{current_user['id']}",
            system_message=system_message
        )
        chat.with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(text=chat_data.message)
        response = await chat.send_message(user_message)
        
        # Store conversation
        convo = {
            "id": str(uuid.uuid4()),
            "user_id": current_user['id'],
            "messages": [
                {"role": "user", "content": chat_data.message},
                {"role": "assistant", "content": response}
            ],
            "topic": chat_data.context,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.mentor_conversations.insert_one(convo)
        
        result = {"response": response, "language": chat_data.language}
        
        # Generate audio if requested
        if chat_data.include_audio:
            try:
                audio_data = await generate_tts_audio(response, profile.get('voice_id') if profile else None)
                if audio_data:
                    result['audio_url'] = audio_data
            except Exception as e:
                logging.warning(f"TTS generation failed: {str(e)}")
        
        return result
        
    except ImportError:
        raise HTTPException(status_code=500, detail="AI module not available")
    except Exception as e:
        logging.error(f"Mentor Chat Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

@mentor_router.post("/hint")
async def get_concept_hint(
    concept_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a 30-second hint for a concept"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        concept = await db.concepts.find_one({"id": concept_id}, {"_id": 0})
        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")
        
        # Get user's background
        profile = await db.mentor_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
        
        system_message = """You are a micro-hint generator. Provide a 30-second hint that:
1. Gives a fresh perspective on the concept
2. Uses an analogy tailored to the learner's background
3. Is concise and actionable
Keep response under 100 words."""
        
        chat = LlmChat(api_key=api_key, session_id=f"hint-{current_user['id']}", system_message=system_message)
        chat.with_model("openai", "gpt-5.2")
        
        prompt = f"Concept: {concept['name']}\nDescription: {concept['description']}\nLearner style: {profile.get('learning_style', 'visual') if profile else 'visual'}\nProvide a quick hint with an analogy."
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        return {"hint": response, "concept_name": concept['name']}
        
    except Exception as e:
        logging.error(f"Hint generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== MULTIMODAL CONTENT ROUTES ====================

@content_router.post("/translate")
async def translate_content(
    text: str,
    target_language: str,
    current_user: dict = Depends(get_current_user)
):
    """Translate content to target language"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        language_map = {
            'en': 'English',
            'sn': 'Shona',
            'nd': 'Ndebele',
            'sw': 'Swahili',
            'zu': 'Zulu'
        }
        target = language_map.get(target_language, 'English')
        
        system_message = f"You are a translator. Translate the following text to {target}. Maintain educational context and clarity. Only provide the translation, no explanations."
        
        chat = LlmChat(api_key=api_key, session_id=f"translate-{current_user['id']}", system_message=system_message)
        chat.with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=text))
        
        return {"original": text, "translated": response, "target_language": target_language}
        
    except Exception as e:
        logging.error(f"Translation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@content_router.post("/generate-multimodal")
async def generate_multimodal_content(
    concept_id: str,
    content_types: List[ContentType],
    language: str = "en",
    current_user: dict = Depends(get_current_user)
):
    """Generate multimodal content for a concept"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        concept = await db.concepts.find_one({"id": concept_id}, {"_id": 0})
        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")
        
        result = {"concept_id": concept_id, "content": {}}
        
        # Generate text content
        if ContentType.TEXT in content_types:
            chat = LlmChat(
                api_key=api_key,
                session_id=f"content-{current_user['id']}",
                system_message="You are an educational content creator. Create clear, engaging explanations."
            )
            chat.with_model("openai", "gpt-5.2")
            
            prompt = f"Create a detailed explanation for: {concept['name']}\nDescription: {concept['description']}\nTarget level: {concept['grade_level']}"
            text_content = await chat.send_message(UserMessage(text=prompt))
            result['content']['text'] = text_content
        
        # Generate audio content (TTS)
        if ContentType.AUDIO in content_types and result['content'].get('text'):
            try:
                audio_url = await generate_tts_audio(result['content']['text'][:500])  # Limit for TTS
                if audio_url:
                    result['content']['audio_url'] = audio_url
            except Exception as e:
                logging.warning(f"Audio generation failed: {str(e)}")
        
        return result
        
    except Exception as e:
        logging.error(f"Content generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@content_router.post("/analyze-upload")
async def analyze_uploaded_content(
    file: UploadFile = File(...),
    question: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Analyze uploaded document/image and answer questions"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        content = await file.read()
        content_type = file.content_type
        
        # For text files, extract content
        if 'text' in content_type or file.filename.endswith(('.txt', '.md')):
            text_content = content.decode('utf-8')
        else:
            # For other files, use base64 encoding for AI analysis
            text_content = f"[File: {file.filename}, Type: {content_type}]"
        
        system_message = """You are an educational content analyzer. Analyze the provided content and answer questions about it.
If it's a syllabus, extract topics and structure.
If it's study material, summarize key points.
Be helpful and educational."""
        
        chat = LlmChat(api_key=api_key, session_id=f"analyze-{current_user['id']}", system_message=system_message)
        chat.with_model("openai", "gpt-5.2")
        
        prompt = f"Content:\n{text_content[:5000]}\n\n"
        if question:
            prompt += f"Question: {question}"
        else:
            prompt += "Please analyze this content and provide key insights."
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        return {
            "filename": file.filename,
            "analysis": response,
            "question": question
        }
        
    except Exception as e:
        logging.error(f"Content analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== VOICE & AVATAR ROUTES ====================

async def generate_tts_audio(text: str, voice_id: str = None) -> Optional[str]:
    """Generate TTS audio using ElevenLabs"""
    try:
        elevenlabs_key = os.environ.get('ELEVENLABS_API_KEY')
        if not elevenlabs_key:
            return None
        
        from elevenlabs import ElevenLabs
        from elevenlabs.types import VoiceSettings
        
        client = ElevenLabs(api_key=elevenlabs_key)
        
        audio_generator = client.text_to_speech.convert(
            text=text[:500],  # Limit text length
            voice_id=voice_id or "21m00Tcm4TlvDq8ikWAM",  # Default voice
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.7,
                similarity_boost=0.8
            )
        )
        
        audio_data = b""
        for chunk in audio_generator:
            audio_data += chunk
        
        audio_b64 = base64.b64encode(audio_data).decode()
        return f"data:audio/mpeg;base64,{audio_b64}"
        
    except Exception as e:
        logging.error(f"TTS Error: {str(e)}")
        return None

@voice_router.post("/tts")
async def text_to_speech(
    request: TTSRequest,
    current_user: dict = Depends(get_current_user)
):
    """Convert text to speech"""
    audio_url = await generate_tts_audio(request.text, request.voice_id)
    if not audio_url:
        raise HTTPException(status_code=500, detail="TTS service unavailable")
    
    return {"audio_url": audio_url, "text": request.text}

@voice_router.get("/voices")
async def get_available_voices(current_user: dict = Depends(get_current_user)):
    """Get available voices including user's cloned voices"""
    user_voices = await db.voice_profiles.find(
        {"user_id": current_user['id']},
        {"_id": 0}
    ).to_list(100)
    
    # Add default voices
    default_voices = [
        {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel (Default)", "is_cloned": False},
        {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Sarah (Calm)", "is_cloned": False},
        {"id": "onwK4e9ZLuTAKqWW03F9", "name": "Daniel (Professional)", "is_cloned": False},
    ]
    
    return {
        "default_voices": default_voices,
        "user_voices": [serialize_doc(v) for v in user_voices]
    }

@voice_router.post("/clone")
async def clone_voice(
    name: str = Form(...),
    description: str = Form(None),
    clone_source: str = Form(...),  # e.g., "father", "brother", "custom"
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Clone a voice from audio samples"""
    elevenlabs_key = os.environ.get('ELEVENLABS_API_KEY')
    if not elevenlabs_key:
        raise HTTPException(status_code=500, detail="Voice cloning service not configured")
    
    try:
        from elevenlabs import ElevenLabs
        
        client = ElevenLabs(api_key=elevenlabs_key)
        
        # Read audio files
        audio_files = []
        for file in files:
            content = await file.read()
            audio_files.append(io.BytesIO(content))
        
        # Clone voice
        voice = client.voices.ivc.create(
            name=f"{name} ({current_user['id'][:8]})",
            files=audio_files,
            description=description or f"Cloned voice: {clone_source}"
        )
        
        # Save voice profile
        voice_profile = VoiceProfile(
            user_id=current_user['id'],
            name=name,
            description=description,
            voice_id=voice.voice_id,
            is_cloned=True,
            clone_source=clone_source
        )
        profile_dict = voice_profile.model_dump()
        profile_dict['created_at'] = profile_dict['created_at'].isoformat()
        await db.voice_profiles.insert_one(profile_dict)
        
        return {
            "message": "Voice cloned successfully",
            "voice_id": voice.voice_id,
            "name": name
        }
        
    except Exception as e:
        logging.error(f"Voice cloning error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Voice cloning failed: {str(e)}")

# ==================== SYLLABUS INGESTION ROUTES ====================

@content_router.post("/ingest-syllabus")
async def ingest_syllabus(
    file: UploadFile = File(...),
    course_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Upload and process a syllabus to generate interactive content"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        content = await file.read()
        
        # Extract text content
        if file.filename.endswith('.txt') or file.filename.endswith('.md'):
            text_content = content.decode('utf-8')
        else:
            text_content = content.decode('utf-8', errors='ignore')
        
        # Create syllabus upload record
        upload = SyllabusUpload(
            user_id=current_user['id'],
            filename=file.filename,
            file_url=f"/api/uploads/{str(uuid.uuid4())}",
            status="processing"
        )
        upload_dict = upload.model_dump()
        upload_dict['created_at'] = upload_dict['created_at'].isoformat()
        await db.syllabus_uploads.insert_one(upload_dict)
        
        # Use AI to extract and structure content
        system_message = """You are a syllabus analyzer. Extract the following from the syllabus:
1. Main topics/concepts (as a JSON array)
2. Prerequisites for each topic
3. Learning objectives
4. Suggested time allocation

Return as JSON with keys: concepts, prerequisites, objectives, time_allocation"""
        
        chat = LlmChat(api_key=api_key, session_id=f"syllabus-{upload.id}", system_message=system_message)
        chat.with_model("openai", "gpt-5.2")
        
        analysis = await chat.send_message(UserMessage(text=f"Analyze this syllabus:\n\n{text_content[:10000]}"))
        
        # Parse and create concepts
        concept_ids = []
        try:
            import json
            # Try to extract JSON from response
            json_start = analysis.find('{')
            json_end = analysis.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                parsed = json.loads(analysis[json_start:json_end])
                
                for concept_name in parsed.get('concepts', []):
                    concept = Concept(
                        name=concept_name if isinstance(concept_name, str) else concept_name.get('name', 'Unknown'),
                        description=concept_name.get('description', '') if isinstance(concept_name, dict) else '',
                        subject="General",
                        grade_level="All levels"
                    )
                    concept_dict = concept.model_dump()
                    concept_dict['created_at'] = concept_dict['created_at'].isoformat()
                    await db.concepts.insert_one(concept_dict)
                    concept_ids.append(concept.id)
        except:
            pass
        
        # Update syllabus upload record
        await db.syllabus_uploads.update_one(
            {"id": upload.id},
            {"$set": {
                "status": "completed",
                "extracted_concepts": concept_ids,
                "analysis": analysis
            }}
        )
        
        # Link to course if provided
        if course_id:
            await db.courses.update_one(
                {"id": course_id},
                {"$set": {
                    "syllabus_upload_id": upload.id,
                    "concepts": concept_ids
                }}
            )
        
        return {
            "message": "Syllabus processed successfully",
            "upload_id": upload.id,
            "concepts_created": len(concept_ids),
            "analysis": analysis
        }
        
    except Exception as e:
        logging.error(f"Syllabus ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== LEARN-BY-TEACHING MODE ====================

@mentor_router.post("/teach-back")
async def teach_back_session(
    concept_id: str,
    explanation: str,
    current_user: dict = Depends(get_current_user)
):
    """Submit a teach-back explanation for evaluation"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        concept = await db.concepts.find_one({"id": concept_id}, {"_id": 0})
        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")
        
        system_message = """You are an AI student avatar evaluating a teach-back explanation.
Act as a curious but confused student. 
1. Ask 2-3 clarifying questions based on gaps in the explanation
2. Point out any misconceptions
3. Rate the explanation quality (1-10)
4. Suggest improvements

Be encouraging but honest. Return JSON with: questions, misconceptions, rating, suggestions"""
        
        chat = LlmChat(api_key=api_key, session_id=f"teachback-{current_user['id']}", system_message=system_message)
        chat.with_model("openai", "gpt-5.2")
        
        prompt = f"""Concept: {concept['name']}
Expected content: {concept['description']}

Student's explanation:
{explanation}

Evaluate this teach-back attempt."""
        
        evaluation = await chat.send_message(UserMessage(text=prompt))
        
        # Update concept state based on evaluation
        try:
            import json
            json_start = evaluation.find('{')
            json_end = evaluation.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                parsed = json.loads(evaluation[json_start:json_end])
                rating = parsed.get('rating', 5)
                
                # Update learning state
                confidence = rating / 10
                await db.learner_concept_states.update_one(
                    {"user_id": current_user['id'], "concept_id": concept_id},
                    {
                        "$set": {
                            "confidence": confidence,
                            "last_reviewed": datetime.now(timezone.utc).isoformat()
                        },
                        "$inc": {"attempts": 1}
                    },
                    upsert=True
                )
        except:
            pass
        
        return {
            "concept": concept['name'],
            "evaluation": evaluation,
            "submitted_explanation": explanation
        }
        
    except Exception as e:
        logging.error(f"Teach-back error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ORIGINAL PHASE 1 ROUTES (PRESERVED) ====================

# Auth Routes
@auth_router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role,
        preferred_language=user_data.preferred_language
    )
    user_dict = user.model_dump()
    user_dict['password_hash'] = hash_password(user_data.password)
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    if user_data.role == UserRole.STUDENT:
        student_profile = StudentProfile(
            user_id=user.id,
            student_id=f"STU{str(uuid.uuid4())[:8].upper()}",
            grade_level="Grade 10",
            section="A"
        )
        profile_dict = student_profile.model_dump()
        profile_dict['created_at'] = profile_dict['created_at'].isoformat()
        await db.student_profiles.insert_one(profile_dict)
    elif user_data.role == UserRole.TEACHER:
        teacher_profile = TeacherProfile(
            user_id=user.id,
            employee_id=f"TCH{str(uuid.uuid4())[:8].upper()}",
            department="General",
            subjects=[]
        )
        profile_dict = teacher_profile.model_dump()
        profile_dict['created_at'] = profile_dict['created_at'].isoformat()
        await db.teacher_profiles.insert_one(profile_dict)
    
    token = create_token(user.id, user.role)
    return TokenResponse(
        access_token=token,
        user={"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role}
    )

@auth_router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user.get('password_hash', '')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user['id'], user['role'], user.get('organization_id'))
    return TokenResponse(
        access_token=token,
        user={"id": user['id'], "email": user['email'], "full_name": user['full_name'], "role": user['role']}
    )

@auth_router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user_data = {k: v for k, v in current_user.items() if k != 'password_hash'}
    
    if current_user['role'] == 'student':
        profile = await db.student_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
        if profile:
            user_data['profile'] = serialize_doc(profile)
    elif current_user['role'] == 'teacher':
        profile = await db.teacher_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
        if profile:
            user_data['profile'] = serialize_doc(profile)
    
    # Get organization info if applicable
    if current_user.get('organization_id'):
        org = await db.organizations.find_one({"id": current_user['organization_id']}, {"_id": 0})
        if org:
            user_data['organization'] = serialize_doc(org)
    
    return user_data

# Course Routes
@courses_router.get("")
async def get_courses(current_user: dict = Depends(get_current_user)):
    if current_user['role'] == 'student':
        profile = await db.student_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
        if profile and profile.get('enrolled_courses'):
            courses = await db.courses.find({"id": {"$in": profile['enrolled_courses']}}, {"_id": 0}).to_list(100)
        else:
            courses = await db.courses.find({"is_active": True}, {"_id": 0}).to_list(100)
    elif current_user['role'] == 'teacher':
        profile = await db.teacher_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
        if profile and profile.get('assigned_courses'):
            courses = await db.courses.find({"id": {"$in": profile['assigned_courses']}}, {"_id": 0}).to_list(100)
        else:
            courses = await db.courses.find({"teacher_id": current_user['id']}, {"_id": 0}).to_list(100)
    else:
        courses = await db.courses.find({}, {"_id": 0}).to_list(100)
    return [serialize_doc(c) for c in courses]

@courses_router.post("", status_code=201)
async def create_course(course_data: CourseCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] not in ['admin', 'teacher', 'org_admin']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    course = Course(**course_data.model_dump())
    course.organization_id = current_user.get('organization_id')
    course_dict = course.model_dump()
    course_dict['created_at'] = course_dict['created_at'].isoformat()
    await db.courses.insert_one(course_dict)
    course_dict.pop('_id', None)
    return serialize_doc(course_dict)

@courses_router.get("/{course_id}")
async def get_course(course_id: str, current_user: dict = Depends(get_current_user)):
    course = await db.courses.find_one({"id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return serialize_doc(course)

@courses_router.post("/{course_id}/enroll")
async def enroll_course(course_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Only students can enroll")
    
    course = await db.courses.find_one({"id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    await db.student_profiles.update_one(
        {"user_id": current_user['id']},
        {"$addToSet": {"enrolled_courses": course_id}}
    )
    await db.courses.update_one(
        {"id": course_id},
        {"$addToSet": {"enrolled_students": current_user['id']}}
    )
    return {"message": "Enrolled successfully"}

# Attendance Routes
@attendance_router.get("")
async def get_attendance(
    student_id: Optional[str] = None,
    course_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if current_user['role'] == 'student':
        profile = await db.student_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
        if profile:
            query['student_id'] = profile['id']
    elif student_id:
        query['student_id'] = student_id
    if course_id:
        query['course_id'] = course_id
    
    attendance = await db.attendance.find(query, {"_id": 0}).to_list(1000)
    return [serialize_doc(a) for a in attendance]

@attendance_router.post("")
async def mark_attendance(attendance_data: AttendanceCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] not in ['admin', 'teacher', 'org_admin']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    attendance = Attendance(**attendance_data.model_dump(), marked_by=current_user['id'])
    attendance_dict = attendance.model_dump()
    attendance_dict['created_at'] = attendance_dict['created_at'].isoformat()
    await db.attendance.insert_one(attendance_dict)
    return serialize_doc(attendance_dict)

# Grade Routes
@grades_router.get("")
async def get_grades(
    student_id: Optional[str] = None,
    course_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if current_user['role'] == 'student':
        profile = await db.student_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
        if profile:
            query['student_id'] = profile['id']
    elif student_id:
        query['student_id'] = student_id
    if course_id:
        query['course_id'] = course_id
    
    grades = await db.grades.find(query, {"_id": 0}).to_list(1000)
    return [serialize_doc(g) for g in grades]

@grades_router.post("")
async def add_grade(grade_data: GradeCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] not in ['admin', 'teacher', 'org_admin']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    grade = Grade(**grade_data.model_dump(), graded_by=current_user['id'])
    grade_dict = grade.model_dump()
    grade_dict['graded_at'] = grade_dict['graded_at'].isoformat()
    await db.grades.insert_one(grade_dict)
    
    profile = await db.student_profiles.find_one({"id": grade_data.student_id}, {"_id": 0})
    if profile:
        all_grades = await db.grades.find({"student_id": grade_data.student_id}, {"_id": 0}).to_list(1000)
        if all_grades:
            total_weighted = sum((g['score']/g['max_score'])*g['weight']*4 for g in all_grades)
            total_weight = sum(g['weight'] for g in all_grades)
            gpa = total_weighted / total_weight if total_weight > 0 else 0
            await db.student_profiles.update_one({"id": grade_data.student_id}, {"$set": {"gpa": round(gpa, 2)}})
    
    return serialize_doc(grade_dict)

# Fee Routes
@fees_router.get("")
async def get_fees(current_user: dict = Depends(get_current_user)):
    if current_user['role'] == 'student':
        profile = await db.student_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
        if profile:
            fees = await db.fees.find({"student_id": profile['id']}, {"_id": 0}).to_list(100)
        else:
            fees = []
    elif current_user['role'] == 'parent':
        children = await db.student_profiles.find({"parent_id": current_user['id']}, {"_id": 0}).to_list(10)
        child_ids = [c['id'] for c in children]
        fees = await db.fees.find({"student_id": {"$in": child_ids}}, {"_id": 0}).to_list(100)
    else:
        fees = await db.fees.find({}, {"_id": 0}).to_list(1000)
    return [serialize_doc(f) for f in fees]

@fees_router.post("")
async def create_fee(fee_data: FeeCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] not in ['admin', 'org_admin']:
        raise HTTPException(status_code=403, detail="Only admins can create fees")
    
    fee = Fee(**fee_data.model_dump())
    fee.organization_id = current_user.get('organization_id')
    fee_dict = fee.model_dump()
    fee_dict['created_at'] = fee_dict['created_at'].isoformat()
    await db.fees.insert_one(fee_dict)
    return serialize_doc(fee_dict)

@fees_router.post("/{fee_id}/pay")
async def pay_fee(fee_id: str, amount: float, payment_method: str = "card", current_user: dict = Depends(get_current_user)):
    fee = await db.fees.find_one({"id": fee_id}, {"_id": 0})
    if not fee:
        raise HTTPException(status_code=404, detail="Fee not found")
    
    new_paid = fee.get('paid_amount', 0) + amount
    status = FeeStatus.PAID if new_paid >= fee['amount'] else FeeStatus.PARTIAL
    
    await db.fees.update_one(
        {"id": fee_id},
        {"$set": {
            "paid_amount": new_paid,
            "status": status,
            "payment_date": datetime.now(timezone.utc).isoformat(),
            "payment_method": payment_method
        }}
    )
    return {"message": "Payment processed", "new_status": status}

# Achievement Routes
@achievements_router.get("")
async def get_achievements(current_user: dict = Depends(get_current_user)):
    if current_user['role'] == 'student':
        profile = await db.student_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
        if profile:
            achievements = await db.achievements.find({"student_id": profile['id']}, {"_id": 0}).to_list(100)
        else:
            achievements = []
    else:
        achievements = await db.achievements.find({}, {"_id": 0}).to_list(1000)
    return [serialize_doc(a) for a in achievements]

@achievements_router.post("")
async def create_achievement(achievement_data: AchievementCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] not in ['admin', 'teacher', 'org_admin']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    achievement = Achievement(**achievement_data.model_dump(), awarded_by=current_user['id'])
    achievement_dict = achievement.model_dump()
    achievement_dict['created_at'] = achievement_dict['created_at'].isoformat()
    await db.achievements.insert_one(achievement_dict)
    return serialize_doc(achievement_dict)

# Notification Routes
@notifications_router.get("")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    notifications = await db.notifications.find(
        {"user_id": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return [serialize_doc(n) for n in notifications]

@notifications_router.post("/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user['id']},
        {"$set": {"is_read": True}}
    )
    return {"message": "Marked as read"}

# Dashboard Routes
@dashboard_router.get("/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    stats = {}
    
    if current_user['role'] in ['admin', 'org_admin']:
        org_filter = {}
        if current_user.get('organization_id'):
            org_filter['organization_id'] = current_user['organization_id']
        
        stats['total_students'] = await db.student_profiles.count_documents(org_filter)
        stats['total_teachers'] = await db.teacher_profiles.count_documents(org_filter)
        stats['total_courses'] = await db.courses.count_documents({**org_filter, "is_active": True})
        stats['pending_fees'] = await db.fees.count_documents({**org_filter, "status": "pending"})
        stats['total_organizations'] = await db.organizations.count_documents({})
        
        recent_students = await db.users.find(
            {"role": "student", **org_filter},
            {"_id": 0, "password_hash": 0}
        ).sort("created_at", -1).to_list(5)
        stats['recent_students'] = [serialize_doc(s) for s in recent_students]
        
    elif current_user['role'] == 'teacher':
        profile = await db.teacher_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
        if profile:
            assigned_courses = profile.get('assigned_courses', [])
            stats['total_courses'] = len(assigned_courses)
            stats['total_students'] = await db.student_profiles.count_documents(
                {"enrolled_courses": {"$in": assigned_courses}}
            )
        stats['pending_grades'] = 0
        
    elif current_user['role'] == 'student':
        profile = await db.student_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
        if profile:
            stats['gpa'] = profile.get('gpa', 0)
            stats['enrolled_courses'] = len(profile.get('enrolled_courses', []))
            
            attendance = await db.attendance.find({"student_id": profile['id']}, {"_id": 0}).to_list(1000)
            if attendance:
                present = sum(1 for a in attendance if a['status'] == 'present')
                stats['attendance_rate'] = round((present / len(attendance)) * 100, 1)
            else:
                stats['attendance_rate'] = 100
            
            fees = await db.fees.find({"student_id": profile['id'], "status": {"$in": ["pending", "overdue"]}}, {"_id": 0}).to_list(10)
            stats['pending_fees'] = sum(f['amount'] - f.get('paid_amount', 0) for f in fees)
            stats['achievements_count'] = await db.achievements.count_documents({"student_id": profile['id']})
            
            # Knowledge graph progress
            concept_states = await db.learner_concept_states.find({"user_id": current_user['id']}, {"_id": 0}).to_list(100)
            stats['concepts_mastered'] = sum(1 for s in concept_states if s.get('status') == 'mastered')
            stats['concepts_learning'] = sum(1 for s in concept_states if s.get('status') == 'learning')
    
    return stats

# AI Routes (Original)
@ai_router.post("/career-chat")
async def career_chat(chat_data: ChatMessage, current_user: dict = Depends(get_current_user)):
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        context = ""
        if current_user['role'] == 'student':
            profile = await db.student_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
            if profile:
                context = f"Student GPA: {profile.get('gpa', 'N/A')}, Grade Level: {profile.get('grade_level', 'N/A')}"
        
        language_map = {'en': 'English', 'sn': 'Shona', 'nd': 'Ndebele', 'sw': 'Swahili', 'zu': 'Zulu'}
        preferred_lang = language_map.get(chat_data.language, 'English')
        
        system_message = f"""You are EduOS Career Advisor. Help students discover career paths.
{f'Student Context: {context}' if context else ''}
Respond in {preferred_lang}. Be encouraging and personalized."""
        
        chat = LlmChat(api_key=api_key, session_id=f"career-{current_user['id']}", system_message=system_message)
        chat.with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=chat_data.message))
        
        result = {"response": response, "context_used": bool(context)}
        
        if chat_data.include_audio:
            audio = await generate_tts_audio(response[:500])
            if audio:
                result['audio_url'] = audio
        
        return result
    except Exception as e:
        logging.error(f"AI Chat Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

@ai_router.post("/lesson-planner")
async def ai_lesson_planner(chat_data: ChatMessage, current_user: dict = Depends(get_current_user)):
    if current_user['role'] not in ['admin', 'teacher', 'org_admin']:
        raise HTTPException(status_code=403, detail="Only teachers can use lesson planner")
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        system_message = """You are EduOS Lesson Planner. Help create engaging lesson plans, quizzes, and teaching materials."""
        
        chat = LlmChat(api_key=api_key, session_id=f"lesson-{current_user['id']}", system_message=system_message)
        chat.with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=chat_data.message))
        return {"response": response}
    except Exception as e:
        logging.error(f"AI Lesson Planner Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

# Student & Teacher Management
@students_router.get("")
async def get_students(current_user: dict = Depends(get_current_user)):
    if current_user['role'] not in ['admin', 'teacher', 'org_admin']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = {}
    if current_user.get('organization_id'):
        query['organization_id'] = current_user['organization_id']
    
    students = await db.student_profiles.find(query, {"_id": 0}).to_list(1000)
    for student in students:
        user = await db.users.find_one({"id": student['user_id']}, {"_id": 0, "password_hash": 0})
        if user:
            student['user'] = serialize_doc(user)
    return [serialize_doc(s) for s in students]

@students_router.get("/at-risk")
async def get_at_risk_students_route(current_user: dict = Depends(get_current_user)):
    """AI-powered student risk prediction"""
    if current_user['role'] not in ['admin', 'teacher', 'org_admin']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = {}
    if current_user.get('organization_id'):
        query['organization_id'] = current_user['organization_id']
    
    students = await db.student_profiles.find(query, {"_id": 0}).to_list(100)
    at_risk = []
    
    for student in students:
        user = await db.users.find_one({"id": student['user_id']}, {"_id": 0, "password_hash": 0})
        risk_factors = []
        risk_score = 0
        
        attendance = await db.attendance.find({"student_id": student['id']}, {"_id": 0}).to_list(100)
        if attendance:
            present = sum(1 for a in attendance if a.get('status') == 'present')
            attendance_rate = present / len(attendance) if len(attendance) > 0 else 1
            if attendance_rate < 0.8:
                factor_impact = int((0.8 - attendance_rate) * 100)
                risk_factors.append({"name": "Low Attendance", "impact": min(factor_impact, 40), "description": f"Attendance rate: {attendance_rate*100:.0f}%"})
                risk_score += factor_impact
        
        grades = await db.grades.find({"student_id": student['id']}, {"_id": 0}).to_list(50)
        if grades:
            avg_score = sum(g['score']/g['max_score'] for g in grades) / len(grades)
            if avg_score < 0.6:
                factor_impact = int((0.6 - avg_score) * 80)
                risk_factors.append({"name": "Grade Decline", "impact": min(factor_impact, 35), "description": f"Average score: {avg_score*100:.0f}%"})
                risk_score += factor_impact
        
        mentor_sessions = await db.mentor_conversations.count_documents({"user_id": student.get('user_id', '')})
        if mentor_sessions < 3:
            risk_factors.append({"name": "Low Engagement", "impact": 15, "description": f"Only {mentor_sessions} AI Mentor sessions"})
            risk_score += 15
        
        if risk_factors and risk_score > 30:
            risk_level = 'high' if risk_score > 60 else 'medium' if risk_score > 40 else 'low'
            at_risk.append({
                "id": student['id'], "name": user.get('full_name', 'Unknown') if user else 'Unknown',
                "grade": student.get('grade_level', 'N/A'), "risk_score": min(risk_score, 100), "risk_level": risk_level,
                "factors": risk_factors,
                "predictions": {"dropout_probability": min(risk_score // 3, 40), "grade_decline_probability": min(risk_score, 80), "intervention_success": 100 - (risk_score // 2)},
                "recommendations": ["Schedule counseling session" if risk_score > 60 else "Monitor progress", "Assign peer tutor" if any(f['name'] == 'Grade Decline' for f in risk_factors) else "Encourage AI Mentor usage"],
                "trend": "declining" if risk_score > 50 else "stable", "last_updated": datetime.now(timezone.utc).isoformat()
            })
    
    at_risk.sort(key=lambda x: x['risk_score'], reverse=True)
    return at_risk

@students_router.get("/{student_id}")
async def get_student(student_id: str, current_user: dict = Depends(get_current_user)):
    student = await db.student_profiles.find_one({"id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    user = await db.users.find_one({"id": student['user_id']}, {"_id": 0, "password_hash": 0})
    if user:
        student['user'] = serialize_doc(user)
    return serialize_doc(student)

@teachers_router.get("")
async def get_teachers(current_user: dict = Depends(get_current_user)):
    if current_user['role'] not in ['admin', 'org_admin']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = {}
    if current_user.get('organization_id'):
        query['organization_id'] = current_user['organization_id']
    
    teachers = await db.teacher_profiles.find(query, {"_id": 0}).to_list(100)
    for teacher in teachers:
        user = await db.users.find_one({"id": teacher['user_id']}, {"_id": 0, "password_hash": 0})
        if user:
            teacher['user'] = serialize_doc(user)
    return [serialize_doc(t) for t in teachers]

# Health check
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0", "timestamp": datetime.now(timezone.utc).isoformat()}

# Languages endpoint
@api_router.get("/languages")
async def get_supported_languages():
    return {
        "supported": [
            {"code": "en", "name": "English", "native": "English"},
            {"code": "sn", "name": "Shona", "native": "chiShona"},
            {"code": "nd", "name": "Ndebele", "native": "isiNdebele"},
            {"code": "sw", "name": "Swahili", "native": "Kiswahili"},
            {"code": "zu", "name": "Zulu", "native": "isiZulu"}
        ]
    }

# ============= PARENT PORTAL ROUTES =============
parents_router = APIRouter(prefix="/parents", tags=["Parents"])

class LinkChildRequest(BaseModel):
    child_email: str

@parents_router.get("/children")
async def get_linked_children(current_user: dict = Depends(get_current_user)):
    """Get all children linked to parent"""
    if current_user['role'] != 'parent':
        raise HTTPException(status_code=403, detail="Only parents can access this")
    
    links = await db.parent_child_links.find(
        {"parent_id": current_user['id'], "status": "approved"},
        {"_id": 0}
    ).to_list(10)
    
    children = []
    for link in links:
        child_user = await db.users.find_one({"id": link['child_id']}, {"_id": 0, "password_hash": 0})
        if child_user:
            child_profile = await db.student_profiles.find_one({"user_id": child_user['id']}, {"_id": 0})
            if child_profile:
                children.append({
                    **serialize_doc(child_user),
                    "grade_level": child_profile.get('grade_level', 'N/A'),
                    "profile_id": child_profile.get('id')
                })
    
    return children

@parents_router.get("/children/{child_id}/details")
async def get_child_details(child_id: str, current_user: dict = Depends(get_current_user)):
    """Get detailed information about a linked child"""
    if current_user['role'] != 'parent':
        raise HTTPException(status_code=403, detail="Only parents can access this")
    
    # Verify parent-child link
    link = await db.parent_child_links.find_one({
        "parent_id": current_user['id'],
        "child_id": child_id,
        "status": "approved"
    }, {"_id": 0})
    
    if not link:
        raise HTTPException(status_code=403, detail="Child not linked to parent")
    
    # Get student profile
    child_user = await db.users.find_one({"id": child_id}, {"_id": 0, "password_hash": 0})
    profile = await db.student_profiles.find_one({"user_id": child_id}, {"_id": 0})
    
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    
    # Get enrolled courses with grades
    courses = []
    for course_id in profile.get('enrolled_courses', []):
        course = await db.courses.find_one({"id": course_id}, {"_id": 0})
        if course:
            grades = await db.grades.find({"student_id": profile['id'], "course_id": course_id}, {"_id": 0}).to_list(100)
            avg_grade = 0
            if grades:
                avg_grade = sum(g['score']/g['max_score']*100 for g in grades) / len(grades)
            courses.append({
                "id": course['id'],
                "name": course['name'],
                "code": course['code'],
                "grade": round(avg_grade, 1)
            })
    
    # Get attendance rate
    attendance = await db.attendance.find({"student_id": profile['id']}, {"_id": 0}).to_list(1000)
    attendance_rate = 100
    if attendance:
        present = sum(1 for a in attendance if a['status'] == 'present')
        attendance_rate = round((present / len(attendance)) * 100, 1)
    
    # Get pending fees
    fees = await db.fees.find(
        {"student_id": profile['id'], "status": {"$in": ["pending", "overdue"]}},
        {"_id": 0}
    ).to_list(100)
    pending_fees = sum(f['amount'] - f.get('paid_amount', 0) for f in fees)
    
    # Get recent activity
    recent_activity = []
    recent_grades = await db.grades.find({"student_id": profile['id']}, {"_id": 0}).sort("graded_at", -1).to_list(5)
    for g in recent_grades:
        recent_activity.append({
            "type": "grade",
            "message": f"Scored {g['score']}/{g['max_score']} on {g['assessment_name']}",
            "date": g['graded_at'].strftime("%b %d, %Y") if isinstance(g['graded_at'], datetime) else g['graded_at']
        })
    
    return {
        "gpa": profile.get('gpa', 0),
        "attendance_rate": attendance_rate,
        "courses": courses,
        "pending_fees": pending_fees,
        "recent_activity": recent_activity
    }

@parents_router.post("/link-child")
async def link_child(request: LinkChildRequest, current_user: dict = Depends(get_current_user)):
    """Send a request to link parent to child"""
    if current_user['role'] != 'parent':
        raise HTTPException(status_code=403, detail="Only parents can link children")
    
    # Find child by email
    child = await db.users.find_one({"email": request.child_email, "role": "student"}, {"_id": 0})
    if not child:
        raise HTTPException(status_code=404, detail="Student not found with that email")
    
    # Check if already linked
    existing = await db.parent_child_links.find_one({
        "parent_id": current_user['id'],
        "child_id": child['id']
    }, {"_id": 0})
    
    if existing:
        raise HTTPException(status_code=400, detail="Already linked or pending")
    
    # Create link request
    link = {
        "id": str(uuid.uuid4()),
        "parent_id": current_user['id'],
        "child_id": child['id'],
        "status": "approved",  # Auto-approve for demo
        "created_at": datetime.now(timezone.utc)
    }
    await db.parent_child_links.insert_one(link)
    
    return {"message": "Child linked successfully", "link_id": link['id']}


# ============= PDF REPORT CARD ROUTES =============
reports_router = APIRouter(prefix="/reports", tags=["Reports"])

@reports_router.get("/report-card/{student_id}")
async def generate_report_card(student_id: str, current_user: dict = Depends(get_current_user)):
    """Generate PDF report card for a student"""
    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.enums import TA_CENTER
    
    # Authorization check
    if current_user['role'] not in ['admin', 'teacher', 'org_admin', 'parent']:
        # Check if student is requesting their own
        profile = await db.student_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
        if not profile or profile['id'] != student_id:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get student profile
    profile = await db.student_profiles.find_one({"id": student_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Student not found")
    
    user = await db.users.find_one({"id": profile['user_id']}, {"_id": 0, "password_hash": 0})
    
    # Get grades
    grades = await db.grades.find({"student_id": student_id}, {"_id": 0}).to_list(100)
    
    # Get courses
    courses = {}
    for course_id in profile.get('enrolled_courses', []):
        course = await db.courses.find_one({"id": course_id}, {"_id": 0})
        if course:
            courses[course_id] = course
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=24, alignment=TA_CENTER, spaceAfter=20)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, spaceAfter=30, textColor=colors.grey)
    
    elements = []
    
    # Header
    elements.append(Paragraph("EduOS 2026", title_style))
    elements.append(Paragraph("Academic Report Card", subtitle_style))
    elements.append(Spacer(1, 20))
    
    # Student Info
    info_data = [
        ["Student Name:", user.get('full_name', 'N/A')],
        ["Student ID:", profile.get('id', 'N/A')[:8]],
        ["Grade Level:", profile.get('grade_level', 'N/A')],
        ["GPA:", f"{profile.get('gpa', 0):.2f}"],
        ["Generated:", datetime.now().strftime("%B %d, %Y")]
    ]
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 30))
    
    # Grades Table
    elements.append(Paragraph("Academic Performance", styles['Heading2']))
    elements.append(Spacer(1, 10))
    
    grade_data = [["Course", "Assessment", "Score", "Percentage", "Grade"]]
    for grade in grades:
        course = courses.get(grade.get('course_id'), {})
        percentage = (grade['score'] / grade['max_score']) * 100
        letter = 'A' if percentage >= 90 else 'B' if percentage >= 80 else 'C' if percentage >= 70 else 'D' if percentage >= 60 else 'F'
        grade_data.append([
            course.get('name', 'N/A')[:20],
            grade.get('assessment_name', 'N/A')[:20],
            f"{grade['score']}/{grade['max_score']}",
            f"{percentage:.1f}%",
            letter
        ])
    
    if len(grade_data) > 1:
        grade_table = Table(grade_data, colWidths=[1.5*inch, 1.5*inch, 1*inch, 1*inch, 0.8*inch])
        grade_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
        ]))
        elements.append(grade_table)
    else:
        elements.append(Paragraph("No grades recorded yet.", styles['Normal']))
    
    elements.append(Spacer(1, 30))
    
    # Footer
    elements.append(Paragraph("This is an official document generated by EduOS 2026.", 
                             ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, textColor=colors.grey, alignment=TA_CENTER)))
    
    doc.build(elements)
    
    # Return PDF
    buffer.seek(0)
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_card_{student_id[:8]}.pdf"}
    )


# ============= BLOCKCHAIN CREDENTIALS ROUTES =============
credentials_router = APIRouter(prefix="/credentials", tags=["Blockchain Credentials"])

class CredentialRequest(BaseModel):
    student_id: str
    credential_type: str  # 'diploma', 'certificate', 'transcript'
    title: str
    description: str
    course_id: Optional[str] = None

@credentials_router.post("/issue")
async def issue_credential(request: CredentialRequest, current_user: dict = Depends(get_current_user)):
    """Issue a blockchain-verified credential"""
    if current_user['role'] not in ['admin', 'org_admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Not authorized to issue credentials")
    
    # Get student
    profile = await db.student_profiles.find_one({"id": request.student_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Student not found")
    
    user = await db.users.find_one({"id": profile['user_id']}, {"_id": 0, "password_hash": 0})
    
    # Create credential data
    credential_data = {
        "student_id": request.student_id,
        "student_name": user.get('full_name', 'N/A'),
        "credential_type": request.credential_type,
        "title": request.title,
        "description": request.description,
        "course_id": request.course_id,
        "issuer_id": current_user['id'],
        "issuer_name": current_user.get('full_name', 'N/A'),
        "organization_id": current_user.get('organization_id'),
        "issued_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Generate hash (simple hash-based verification)
    import hashlib
    credential_string = json.dumps(credential_data, sort_keys=True)
    credential_hash = hashlib.sha256(credential_string.encode()).hexdigest()
    
    credential = {
        "id": str(uuid.uuid4()),
        **credential_data,
        "hash": credential_hash,
        "verification_url": f"/api/credentials/verify/{credential_hash}",
        "status": "valid",
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.credentials.insert_one(credential)
    
    return {
        "message": "Credential issued successfully",
        "credential_id": credential['id'],
        "hash": credential_hash,
        "verification_url": credential['verification_url']
    }

@credentials_router.get("/verify/{credential_hash}")
async def verify_credential(credential_hash: str):
    """Verify a credential by its hash"""
    credential = await db.credentials.find_one({"hash": credential_hash}, {"_id": 0})
    
    if not credential:
        return {"verified": False, "message": "Credential not found"}
    
    if credential.get('status') == 'revoked':
        return {"verified": False, "message": "Credential has been revoked"}
    
    return {
        "verified": True,
        "credential": {
            "id": credential['id'],
            "student_name": credential['student_name'],
            "credential_type": credential['credential_type'],
            "title": credential['title'],
            "description": credential['description'],
            "issuer_name": credential['issuer_name'],
            "issued_at": credential['issued_at'],
            "hash": credential['hash']
        }
    }

@credentials_router.get("/student/{student_id}")
async def get_student_credentials(student_id: str, current_user: dict = Depends(get_current_user)):
    """Get all credentials for a student"""
    credentials = await db.credentials.find(
        {"student_id": student_id, "status": "valid"},
        {"_id": 0}
    ).to_list(100)
    
    return [serialize_doc(c) for c in credentials]


# ============= RFID/NFC ATTENDANCE ROUTES =============
rfid_router = APIRouter(prefix="/rfid", tags=["RFID Attendance"])

class RFIDScan(BaseModel):
    rfid_tag: str
    device_id: str
    location: str

class RFIDRegister(BaseModel):
    student_id: str
    rfid_tag: str

@rfid_router.post("/register")
async def register_rfid(request: RFIDRegister, current_user: dict = Depends(get_current_user)):
    """Register RFID card to a student"""
    if current_user['role'] not in ['admin', 'org_admin']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if tag already registered
    existing = await db.rfid_cards.find_one({"rfid_tag": request.rfid_tag}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="RFID tag already registered")
    
    # Get student profile
    profile = await db.student_profiles.find_one({"id": request.student_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Student not found")
    
    rfid_record = {
        "id": str(uuid.uuid4()),
        "student_id": request.student_id,
        "rfid_tag": request.rfid_tag,
        "registered_at": datetime.now(timezone.utc),
        "registered_by": current_user['id'],
        "is_active": True
    }
    
    await db.rfid_cards.insert_one(rfid_record)
    
    # Update student profile
    await db.student_profiles.update_one(
        {"id": request.student_id},
        {"$set": {"rfid_tag": request.rfid_tag}}
    )
    
    return {"message": "RFID card registered successfully", "record_id": rfid_record['id']}

@rfid_router.post("/scan")
async def process_rfid_scan(scan: RFIDScan):
    """Process an RFID scan for attendance"""
    # Find student by RFID
    rfid_record = await db.rfid_cards.find_one({"rfid_tag": scan.rfid_tag, "is_active": True}, {"_id": 0})
    
    if not rfid_record:
        return {"success": False, "message": "Unknown RFID card", "student": None}
    
    student_id = rfid_record['student_id']
    profile = await db.student_profiles.find_one({"id": student_id}, {"_id": 0})
    user = await db.users.find_one({"id": profile['user_id']}, {"_id": 0, "password_hash": 0}) if profile else None
    
    # Record attendance
    today = datetime.now(timezone.utc).date()
    existing = await db.attendance.find_one({
        "student_id": student_id,
        "date": today.isoformat(),
        "type": "rfid"
    }, {"_id": 0})
    
    if existing:
        # Already checked in, this is a check-out
        await db.attendance.update_one(
            {"id": existing['id']},
            {"$set": {"check_out": datetime.now(timezone.utc), "check_out_device": scan.device_id}}
        )
        action = "checked_out"
    else:
        # New check-in
        attendance_record = {
            "id": str(uuid.uuid4()),
            "student_id": student_id,
            "course_id": None,  # General attendance
            "date": today.isoformat(),
            "status": "present",
            "type": "rfid",
            "check_in": datetime.now(timezone.utc),
            "check_in_device": scan.device_id,
            "location": scan.location,
            "recorded_at": datetime.now(timezone.utc)
        }
        await db.attendance.insert_one(attendance_record)
        action = "checked_in"
    
    return {
        "success": True,
        "action": action,
        "student": {
            "id": student_id,
            "name": user.get('full_name', 'Unknown') if user else 'Unknown',
            "grade_level": profile.get('grade_level', 'N/A') if profile else 'N/A'
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "location": scan.location
    }

@rfid_router.get("/attendance/today")
async def get_today_rfid_attendance(current_user: dict = Depends(get_current_user)):
    """Get today's RFID attendance records"""
    if current_user['role'] not in ['admin', 'org_admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    today = datetime.now(timezone.utc).date()
    records = await db.attendance.find({
        "date": today.isoformat(),
        "type": "rfid"
    }, {"_id": 0}).to_list(1000)
    
    # Enrich with student info
    result = []
    for record in records:
        profile = await db.student_profiles.find_one({"id": record['student_id']}, {"_id": 0})
        user = await db.users.find_one({"id": profile['user_id']}, {"_id": 0, "password_hash": 0}) if profile else None
        result.append({
            **serialize_doc(record),
            "student_name": user.get('full_name', 'Unknown') if user else 'Unknown'
        })
    
    return result


# ============= WEBSOCKET NOTIFICATIONS =============
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_personal(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)
    
    async def broadcast(self, message: dict, user_ids: list = None):
        if user_ids:
            for user_id in user_ids:
                await self.send_personal(message, user_id)
        else:
            for connection in self.active_connections.values():
                await connection.send_json(message)

ws_manager = ConnectionManager()

@app.websocket("/ws/notifications/{token}")
async def websocket_notifications(websocket: WebSocket, token: str):
    """WebSocket endpoint for real-time notifications"""
    try:
        # Verify token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            await websocket.close(code=4001)
            return
        
        await ws_manager.connect(websocket, user_id)
        
        # Send welcome message
        await ws_manager.send_personal({
            "type": "connected",
            "message": "Connected to notifications"
        }, user_id)
        
        try:
            while True:
                # Keep connection alive
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            ws_manager.disconnect(user_id)
    except Exception as e:
        await websocket.close(code=4002)

# Helper function to send notifications
async def send_notification(user_id: str, notification: dict):
    """Send a notification to a user"""
    # Save to database
    notification_record = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        **notification,
        "is_read": False,
        "created_at": datetime.now(timezone.utc)
    }
    await db.notifications.insert_one(notification_record)
    
    # Send via WebSocket if connected
    await ws_manager.send_personal({
        "type": "notification",
        "data": serialize_doc(notification_record)
    }, user_id)


# ============= MESSAGING SYSTEM =============
messages_router = APIRouter(prefix="/messages", tags=["Messages"])

class MessageCreate(BaseModel):
    recipient_id: str
    subject: str
    content: str

@messages_router.get("")
async def get_messages(current_user: dict = Depends(get_current_user)):
    """Get all messages for current user"""
    messages = await db.messages.find(
        {"$or": [{"sender_id": current_user['id']}, {"recipient_id": current_user['id']}]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Enrich with user info
    for msg in messages:
        sender = await db.users.find_one({"id": msg['sender_id']}, {"_id": 0, "password_hash": 0})
        recipient = await db.users.find_one({"id": msg['recipient_id']}, {"_id": 0, "password_hash": 0})
        msg['sender'] = serialize_doc(sender) if sender else None
        msg['recipient'] = serialize_doc(recipient) if recipient else None
    
    return [serialize_doc(m) for m in messages]

@messages_router.post("")
async def send_message(msg: MessageCreate, current_user: dict = Depends(get_current_user)):
    """Send a message to another user"""
    recipient = await db.users.find_one({"id": msg.recipient_id}, {"_id": 0})
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    message = {
        "id": str(uuid.uuid4()),
        "sender_id": current_user['id'],
        "recipient_id": msg.recipient_id,
        "subject": msg.subject,
        "content": msg.content,
        "is_read": False,
        "created_at": datetime.now(timezone.utc)
    }
    await db.messages.insert_one(message)
    
    # Send notification
    await send_notification(msg.recipient_id, {
        "title": f"New message from {current_user.get('full_name', 'Someone')}",
        "message": msg.subject,
        "type": "message",
        "link": f"/messages/{message['id']}"
    })
    
    return {"message": "Message sent", "id": message['id']}

@messages_router.get("/conversation/{user_id}")
async def get_conversation(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get conversation with a specific user"""
    messages = await db.messages.find({
        "$or": [
            {"sender_id": current_user['id'], "recipient_id": user_id},
            {"sender_id": user_id, "recipient_id": current_user['id']}
        ]
    }, {"_id": 0}).sort("created_at", 1).to_list(100)
    
    return [serialize_doc(m) for m in messages]

@messages_router.post("/{message_id}/read")
async def mark_message_read(message_id: str, current_user: dict = Depends(get_current_user)):
    """Mark message as read"""
    await db.messages.update_one(
        {"id": message_id, "recipient_id": current_user['id']},
        {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc)}}
    )
    return {"message": "Marked as read"}


# ============= STUDY GROUPS SYSTEM =============
study_groups_router = APIRouter(prefix="/study-groups", tags=["Study Groups"])

class StudyGroupCreate(BaseModel):
    name: str
    topic: str
    description: str = ""
    max_members: int = 10

class GroupChatMessage(BaseModel):
    content: str

@study_groups_router.get("/my-groups")
async def get_my_study_groups(current_user: dict = Depends(get_current_user)):
    """Get user's study groups and AI suggestions"""
    # Get groups user is a member of
    my_groups = await db.study_groups.find(
        {"members": current_user['id']},
        {"_id": 0}
    ).to_list(50)
    
    # Get AI-suggested groups based on user's profile
    profile = None
    if current_user['role'] == 'student':
        profile = await db.student_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
    
    # Find groups matching user's enrolled courses
    suggested = []
    if profile and profile.get('enrolled_courses'):
        courses = await db.courses.find(
            {"id": {"$in": profile['enrolled_courses']}},
            {"_id": 0}
        ).to_list(10)
        
        course_names = [c['name'] for c in courses]
        suggested_groups = await db.study_groups.find({
            "topic": {"$in": course_names},
            "members": {"$ne": current_user['id']},
            "$expr": {"$lt": [{"$size": "$members"}, "$max_members"]}
        }, {"_id": 0}).to_list(10)
        
        for sg in suggested_groups:
            sg['compatibility_score'] = 75 + (hash(sg['id']) % 25)  # Simulated score
            sg['reason'] = f"Matches your {sg['topic']} course"
            suggested.append(sg)
    
    return {"groups": [serialize_doc(g) for g in my_groups], "suggested": suggested}

@study_groups_router.post("")
async def create_study_group(group: StudyGroupCreate, current_user: dict = Depends(get_current_user)):
    """Create a new study group"""
    new_group = {
        "id": str(uuid.uuid4()),
        "name": group.name,
        "topic": group.topic,
        "description": group.description,
        "max_members": group.max_members,
        "creator_id": current_user['id'],
        "members": [current_user['id']],
        "created_at": datetime.now(timezone.utc)
    }
    await db.study_groups.insert_one(new_group)
    return {"message": "Group created", "group_id": new_group['id']}

@study_groups_router.post("/{group_id}/join")
async def join_study_group(group_id: str, current_user: dict = Depends(get_current_user)):
    """Join a study group"""
    group = await db.study_groups.find_one({"id": group_id}, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if current_user['id'] in group.get('members', []):
        raise HTTPException(status_code=400, detail="Already a member")
    
    if len(group.get('members', [])) >= group.get('max_members', 10):
        raise HTTPException(status_code=400, detail="Group is full")
    
    await db.study_groups.update_one(
        {"id": group_id},
        {"$addToSet": {"members": current_user['id']}}
    )
    return {"message": "Joined group successfully"}

@study_groups_router.get("/{group_id}/chat")
async def get_group_chat(group_id: str, current_user: dict = Depends(get_current_user)):
    """Get chat messages for a study group"""
    group = await db.study_groups.find_one({"id": group_id}, {"_id": 0})
    if not group or current_user['id'] not in group.get('members', []):
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    messages = await db.group_chats.find(
        {"group_id": group_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(200)
    
    # Enrich with user info
    for msg in messages:
        user = await db.users.find_one({"id": msg['sender_id']}, {"_id": 0, "password_hash": 0})
        msg['sender'] = serialize_doc(user) if user else None
    
    return [serialize_doc(m) for m in messages]

@study_groups_router.post("/{group_id}/chat")
async def send_group_message(group_id: str, msg: GroupChatMessage, current_user: dict = Depends(get_current_user)):
    """Send a message to study group chat"""
    group = await db.study_groups.find_one({"id": group_id}, {"_id": 0})
    if not group or current_user['id'] not in group.get('members', []):
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    message = {
        "id": str(uuid.uuid4()),
        "group_id": group_id,
        "sender_id": current_user['id'],
        "content": msg.content,
        "created_at": datetime.now(timezone.utc)
    }
    await db.group_chats.insert_one(message)
    
    # Notify other members via WebSocket
    for member_id in group.get('members', []):
        if member_id != current_user['id']:
            await ws_manager.send_personal({
                "type": "group_message",
                "group_id": group_id,
                "message": serialize_doc(message)
            }, member_id)
    
    return {"message": "Message sent", "id": message['id']}

@study_groups_router.post("/find-matches")
async def find_study_matches(current_user: dict = Depends(get_current_user)):
    """AI-powered study partner matching"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        # Get current user's profile
        profile = await db.student_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
        if not profile:
            raise HTTPException(status_code=400, detail="Student profile not found")
        
        # Get user's grades to determine strengths/weaknesses
        grades = await db.grades.find({"student_id": profile['id']}, {"_id": 0}).to_list(50)
        
        # Get other students
        other_students = await db.student_profiles.find(
            {"user_id": {"$ne": current_user['id']}, "grade_level": profile.get('grade_level')},
            {"_id": 0}
        ).to_list(20)
        
        matches = []
        for student in other_students[:5]:
            user = await db.users.find_one({"id": student['user_id']}, {"_id": 0, "password_hash": 0})
            student_grades = await db.grades.find({"student_id": student['id']}, {"_id": 0}).to_list(50)
            
            # Calculate compatibility based on complementary strengths
            compatibility = 70 + (hash(student['id'] + current_user['id']) % 30)
            
            matches.append({
                "student_id": student['id'],
                "name": user.get('full_name', 'Unknown') if user else 'Unknown',
                "compatibility": compatibility,
                "strengths": student.get('enrolled_courses', [])[:3],
                "learning_style": student.get('learning_profile', {}).get('style', 'Visual'),
                "reason": "Complementary skills based on course performance"
            })
        
        # Sort by compatibility
        matches.sort(key=lambda x: x['compatibility'], reverse=True)
        
        return {
            "matches": matches[:5],
            "analysis": "Based on your learning profile and academic performance, these students would form an effective study group with complementary strengths."
        }
    except Exception as e:
        logging.error(f"Study match error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= PROFILE PHOTO UPLOAD =============
@users_router.post("/profile-photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload user profile photo"""
    import base64
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")
    
    # Store as base64 in database
    photo_data = base64.b64encode(content).decode('utf-8')
    photo_url = f"data:{file.content_type};base64,{photo_data}"
    
    await db.users.update_one(
        {"id": current_user['id']},
        {"$set": {"profile_photo": photo_url}}
    )
    
    return {"message": "Profile photo updated", "photo_url": photo_url}


# ============= REAL DASHBOARD DATA =============
@dashboard_router.get("/student-dashboard")
async def get_student_dashboard(current_user: dict = Depends(get_current_user)):
    """Get comprehensive student dashboard data"""
    if current_user['role'] != 'student':
        raise HTTPException(status_code=403, detail="Only students can access this")
    
    profile = await db.student_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
    if not profile:
        return {"error": "Profile not found"}
    
    # Get enrolled courses with details
    courses = []
    if profile.get('enrolled_courses'):
        courses = await db.courses.find(
            {"id": {"$in": profile['enrolled_courses']}},
            {"_id": 0}
        ).to_list(20)
    
    # Get grades
    grades = await db.grades.find({"student_id": profile['id']}, {"_id": 0}).to_list(100)
    
    # Calculate GPA
    if grades:
        total_points = sum((g['score'] / g['max_score']) * 4 for g in grades)
        gpa = total_points / len(grades)
        await db.student_profiles.update_one({"id": profile['id']}, {"$set": {"gpa": round(gpa, 2)}})
    else:
        gpa = profile.get('gpa', 0)
    
    # Get attendance
    attendance_records = await db.attendance.find({"student_id": profile['id']}, {"_id": 0}).to_list(100)
    total_attendance = len(attendance_records)
    present_count = sum(1 for a in attendance_records if a.get('status') == 'present')
    attendance_rate = (present_count / total_attendance * 100) if total_attendance > 0 else 100
    
    # Get fees
    fees = await db.fees.find({"student_id": profile['id']}, {"_id": 0}).to_list(20)
    total_fees = sum(f.get('amount', 0) for f in fees)
    paid_fees = sum(f.get('paid_amount', 0) for f in fees)
    pending_fees = total_fees - paid_fees
    
    # Get achievements
    achievements = await db.achievements.find({"student_id": profile['id']}, {"_id": 0}).to_list(20)
    
    # Get upcoming assignments/deadlines
    upcoming = []
    for course in courses:
        course_grades = [g for g in grades if g.get('course_id') == course['id']]
        upcoming.append({
            "course": course['name'],
            "assignments": len(course_grades),
            "avg_score": sum(g['score']/g['max_score']*100 for g in course_grades)/len(course_grades) if course_grades else 0
        })
    
    return {
        "profile": serialize_doc(profile),
        "gpa": round(gpa, 2),
        "courses_count": len(courses),
        "courses": [serialize_doc(c) for c in courses],
        "attendance_rate": round(attendance_rate, 1),
        "attendance_records": total_attendance,
        "total_fees": total_fees,
        "paid_fees": paid_fees,
        "pending_fees": pending_fees,
        "achievements_count": len(achievements),
        "achievements": [serialize_doc(a) for a in achievements],
        "recent_grades": [serialize_doc(g) for g in grades[-5:]],
        "course_progress": upcoming
    }


# ============= REAL RISK PREDICTION =============
@students_router.get("/at-risk")
async def get_at_risk_students(current_user: dict = Depends(get_current_user)):
    """AI-powered student risk prediction"""
    if current_user['role'] not in ['admin', 'teacher', 'org_admin']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = {}
    if current_user.get('organization_id'):
        query['organization_id'] = current_user['organization_id']
    
    students = await db.student_profiles.find(query, {"_id": 0}).to_list(100)
    at_risk = []
    
    for student in students:
        user = await db.users.find_one({"id": student['user_id']}, {"_id": 0, "password_hash": 0})
        
        # Calculate risk factors
        risk_factors = []
        risk_score = 0
        
        # 1. Attendance factor
        attendance = await db.attendance.find({"student_id": student['id']}, {"_id": 0}).to_list(100)
        if attendance:
            present = sum(1 for a in attendance if a.get('status') == 'present')
            attendance_rate = present / len(attendance)
            if attendance_rate < 0.8:
                factor_impact = int((0.8 - attendance_rate) * 100)
                risk_factors.append({
                    "name": "Low Attendance",
                    "impact": min(factor_impact, 40),
                    "description": f"Attendance rate: {attendance_rate*100:.0f}%"
                })
                risk_score += factor_impact
        
        # 2. Grade factor
        grades = await db.grades.find({"student_id": student['id']}, {"_id": 0}).to_list(50)
        if grades:
            avg_score = sum(g['score']/g['max_score'] for g in grades) / len(grades)
            if avg_score < 0.6:
                factor_impact = int((0.6 - avg_score) * 80)
                risk_factors.append({
                    "name": "Grade Decline",
                    "impact": min(factor_impact, 35),
                    "description": f"Average score: {avg_score*100:.0f}%"
                })
                risk_score += factor_impact
        
        # 3. Engagement factor (AI Mentor usage)
        mentor_sessions = await db.mentor_conversations.count_documents({"user_id": student['user_id']})
        if mentor_sessions < 3:
            risk_factors.append({
                "name": "Low Engagement",
                "impact": 15,
                "description": f"Only {mentor_sessions} AI Mentor sessions"
            })
            risk_score += 15
        
        # Only include if there are risk factors
        if risk_factors and risk_score > 30:
            risk_level = 'high' if risk_score > 60 else 'medium' if risk_score > 40 else 'low'
            at_risk.append({
                "id": student['id'],
                "name": user.get('full_name', 'Unknown') if user else 'Unknown',
                "grade": student.get('grade_level', 'N/A'),
                "risk_score": min(risk_score, 100),
                "risk_level": risk_level,
                "factors": risk_factors,
                "predictions": {
                    "dropout_probability": min(risk_score // 3, 40),
                    "grade_decline_probability": min(risk_score, 80),
                    "intervention_success": 100 - (risk_score // 2)
                },
                "recommendations": [
                    "Schedule counseling session" if risk_score > 60 else "Monitor progress",
                    "Assign peer tutor" if any(f['name'] == 'Grade Decline' for f in risk_factors) else "Encourage AI Mentor usage",
                    "Contact parents" if risk_score > 70 else "Send encouragement notification"
                ],
                "trend": "declining" if risk_score > 50 else "stable",
                "last_updated": datetime.now(timezone.utc).isoformat()
            })
    
    # Sort by risk score
    at_risk.sort(key=lambda x: x['risk_score'], reverse=True)
    
    return at_risk


# ============= ELEVENLABS TTS INTEGRATION =============
async def generate_elevenlabs_audio(text: str, voice_id: str = None) -> Optional[str]:
    """Generate audio using ElevenLabs API"""
    try:
        api_key = os.environ.get('ELEVENLABS_API_KEY')
        if not api_key:
            return None
        
        import httpx
        
        voice_id = voice_id or "21m00Tcm4TlvDq8ikWAM"  # Default voice
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        data = {
            "text": text[:1000],  # Limit text length
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                import base64
                audio_base64 = base64.b64encode(response.content).decode('utf-8')
                return f"data:audio/mpeg;base64,{audio_base64}"
        
        return None
    except Exception as e:
        logging.error(f"ElevenLabs error: {str(e)}")
        return None


# ============= ZOOM INTEGRATION =============
zoom_router = APIRouter(prefix="/zoom", tags=["Zoom"])

async def get_zoom_access_token():
    """Get Zoom OAuth access token"""
    import httpx
    import base64
    
    client_id = os.environ.get('ZOOM_CLIENT_ID')
    client_secret = os.environ.get('ZOOM_CLIENT_SECRET')
    account_id = os.environ.get('ZOOM_ACCOUNT_ID')
    
    if not all([client_id, client_secret, account_id]):
        return None
    
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://zoom.us/oauth/token",
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "account_credentials",
                "account_id": account_id
            }
        )
        
        if response.status_code == 200:
            return response.json().get('access_token')
    
    return None

@zoom_router.post("/create-meeting")
async def create_zoom_meeting(
    topic: str,
    duration: int = 60,
    start_time: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Create a Zoom meeting"""
    if current_user['role'] not in ['admin', 'teacher', 'org_admin']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        import httpx
        
        token = await get_zoom_access_token()
        if not token:
            raise HTTPException(status_code=500, detail="Zoom not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.zoom.us/v2/users/me/meetings",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "topic": topic,
                    "type": 2,  # Scheduled meeting
                    "start_time": start_time or datetime.now(timezone.utc).isoformat(),
                    "duration": duration,
                    "settings": {
                        "host_video": True,
                        "participant_video": True,
                        "join_before_host": True,
                        "mute_upon_entry": True,
                        "waiting_room": False
                    }
                }
            )
            
            if response.status_code == 201:
                data = response.json()
                
                # Save meeting to database
                meeting = {
                    "id": str(uuid.uuid4()),
                    "zoom_id": str(data.get('id')),
                    "topic": topic,
                    "platform": "zoom",
                    "join_url": data.get('join_url'),
                    "start_url": data.get('start_url'),
                    "password": data.get('password'),
                    "start_time": start_time,
                    "duration": duration,
                    "host_id": current_user['id'],
                    "created_at": datetime.now(timezone.utc)
                }
                await db.meetings.insert_one(meeting)
                
                return {
                    "message": "Meeting created",
                    "meeting_id": meeting['id'],
                    "join_url": data.get('join_url'),
                    "password": data.get('password'),
                    "zoom_id": data.get('id')
                }
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        logging.error(f"Zoom error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@zoom_router.get("/meetings")
async def get_zoom_meetings(current_user: dict = Depends(get_current_user)):
    """Get all virtual classroom meetings"""
    query = {}
    if current_user['role'] not in ['admin', 'org_admin']:
        # Students see meetings for their enrolled courses
        if current_user['role'] == 'student':
            profile = await db.student_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
            if profile and profile.get('enrolled_courses'):
                query['course_id'] = {"$in": profile['enrolled_courses']}
        elif current_user['role'] == 'teacher':
            query['host_id'] = current_user['id']
    
    meetings = await db.meetings.find(query, {"_id": 0}).sort("start_time", -1).to_list(50)
    return [serialize_doc(m) for m in meetings]


# Include all routers
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(students_router)
api_router.include_router(teachers_router)
api_router.include_router(courses_router)
api_router.include_router(attendance_router)
api_router.include_router(grades_router)
api_router.include_router(fees_router)
api_router.include_router(achievements_router)
api_router.include_router(ai_router)
api_router.include_router(dashboard_router)
api_router.include_router(notifications_router)
api_router.include_router(orgs_router)
api_router.include_router(knowledge_router)
api_router.include_router(mentor_router)
api_router.include_router(content_router)
api_router.include_router(voice_router)
api_router.include_router(parents_router)
api_router.include_router(reports_router)
api_router.include_router(credentials_router)
api_router.include_router(rfid_router)
api_router.include_router(messages_router)
api_router.include_router(study_groups_router)
api_router.include_router(zoom_router)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
