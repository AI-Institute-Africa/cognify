from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional
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

# Create the main app
app = FastAPI(title="EduOS 2026", description="AI-Powered School Management Platform")

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

security = HTTPBearer()

# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"

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

# Models
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

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
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
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    enrolled_courses: List[str] = []
    gpa: float = 0.0
    career_aptitude_score: Optional[dict] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TeacherProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    employee_id: str
    department: str
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
    grade_level: str
    credits: int = 3
    schedule: Optional[dict] = None
    syllabus: Optional[str] = None
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

# Helper Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
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
    return doc

# Auth Routes
@auth_router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role
    )
    user_dict = user.model_dump()
    user_dict['password_hash'] = hash_password(user_data.password)
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    # Create profile based on role
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
    
    token = create_token(user['id'], user['role'])
    return TokenResponse(
        access_token=token,
        user={"id": user['id'], "email": user['email'], "full_name": user['full_name'], "role": user['role']}
    )

@auth_router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user_data = {k: v for k, v in current_user.items() if k != 'password_hash'}
    
    # Get profile based on role
    if current_user['role'] == 'student':
        profile = await db.student_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
        if profile:
            user_data['profile'] = serialize_doc(profile)
    elif current_user['role'] == 'teacher':
        profile = await db.teacher_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
        if profile:
            user_data['profile'] = serialize_doc(profile)
    
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
    if current_user['role'] not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    course = Course(**course_data.model_dump())
    course_dict = course.model_dump()
    course_dict['created_at'] = course_dict['created_at'].isoformat()
    await db.courses.insert_one(course_dict)
    
    # Remove MongoDB _id and return the course data
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
    
    # Update student profile
    await db.student_profiles.update_one(
        {"user_id": current_user['id']},
        {"$addToSet": {"enrolled_courses": course_id}}
    )
    # Update course
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
    if current_user['role'] not in ['admin', 'teacher']:
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
    if current_user['role'] not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    grade = Grade(**grade_data.model_dump(), graded_by=current_user['id'])
    grade_dict = grade.model_dump()
    grade_dict['graded_at'] = grade_dict['graded_at'].isoformat()
    await db.grades.insert_one(grade_dict)
    
    # Update student GPA
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
        # Get children's fees
        children = await db.student_profiles.find({"parent_id": current_user['id']}, {"_id": 0}).to_list(10)
        child_ids = [c['id'] for c in children]
        fees = await db.fees.find({"student_id": {"$in": child_ids}}, {"_id": 0}).to_list(100)
    else:
        fees = await db.fees.find({}, {"_id": 0}).to_list(1000)
    return [serialize_doc(f) for f in fees]

@fees_router.post("")
async def create_fee(fee_data: FeeCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can create fees")
    
    fee = Fee(**fee_data.model_dump())
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
    if current_user['role'] not in ['admin', 'teacher']:
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
    
    if current_user['role'] == 'admin':
        stats['total_students'] = await db.student_profiles.count_documents({})
        stats['total_teachers'] = await db.teacher_profiles.count_documents({})
        stats['total_courses'] = await db.courses.count_documents({"is_active": True})
        stats['pending_fees'] = await db.fees.count_documents({"status": "pending"})
        
        # Recent enrollments
        recent_students = await db.users.find(
            {"role": "student"},
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
            
            # Attendance rate
            attendance = await db.attendance.find({"student_id": profile['id']}, {"_id": 0}).to_list(1000)
            if attendance:
                present = sum(1 for a in attendance if a['status'] == 'present')
                stats['attendance_rate'] = round((present / len(attendance)) * 100, 1)
            else:
                stats['attendance_rate'] = 100
            
            # Pending fees
            fees = await db.fees.find({"student_id": profile['id'], "status": {"$in": ["pending", "overdue"]}}, {"_id": 0}).to_list(10)
            stats['pending_fees'] = sum(f['amount'] - f.get('paid_amount', 0) for f in fees)
            
            # Achievements count
            stats['achievements_count'] = await db.achievements.count_documents({"student_id": profile['id']})
    
    elif current_user['role'] == 'parent':
        children = await db.student_profiles.find({"parent_id": current_user['id']}, {"_id": 0}).to_list(10)
        stats['children_count'] = len(children)
        child_ids = [c['id'] for c in children]
        fees = await db.fees.find({"student_id": {"$in": child_ids}, "status": {"$in": ["pending", "overdue"]}}, {"_id": 0}).to_list(100)
        stats['pending_fees'] = sum(f['amount'] - f.get('paid_amount', 0) for f in fees)
    
    return stats

# AI Career Guidance Routes
@ai_router.post("/career-chat")
async def career_chat(chat_data: ChatMessage, current_user: dict = Depends(get_current_user)):
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        # Get student profile for context
        context = ""
        if current_user['role'] == 'student':
            profile = await db.student_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
            if profile:
                context = f"Student GPA: {profile.get('gpa', 'N/A')}, Grade Level: {profile.get('grade_level', 'N/A')}"
        
        system_message = f"""You are EduOS Career Advisor, an AI assistant specialized in educational and career guidance.
You help students discover their potential, recommend career paths, suggest subject combinations, and provide actionable advice.
Be encouraging, informative, and personalized in your responses.
{f'Student Context: {context}' if context else ''}
{f'Additional Context: {chat_data.context}' if chat_data.context else ''}"""
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"career-{current_user['id']}",
            system_message=system_message
        )
        chat.with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(text=chat_data.message)
        response = await chat.send_message(user_message)
        
        return {"response": response, "context_used": bool(context)}
    except ImportError:
        raise HTTPException(status_code=500, detail="AI module not available")
    except Exception as e:
        logging.error(f"AI Chat Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

@ai_router.post("/lesson-planner")
async def ai_lesson_planner(chat_data: ChatMessage, current_user: dict = Depends(get_current_user)):
    if current_user['role'] not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Only teachers can use lesson planner")
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        system_message = """You are EduOS Lesson Planner, an AI assistant for teachers.
Help create engaging lesson plans, generate quiz questions, suggest teaching strategies, and provide educational resources.
Be practical and provide structured, actionable content."""
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"lesson-{current_user['id']}",
            system_message=system_message
        )
        chat.with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(text=chat_data.message)
        response = await chat.send_message(user_message)
        
        return {"response": response}
    except ImportError:
        raise HTTPException(status_code=500, detail="AI module not available")
    except Exception as e:
        logging.error(f"AI Lesson Planner Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

# Student Management (Admin)
@students_router.get("")
async def get_students(current_user: dict = Depends(get_current_user)):
    if current_user['role'] not in ['admin', 'teacher']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    students = await db.student_profiles.find({}, {"_id": 0}).to_list(1000)
    # Enrich with user data
    for student in students:
        user = await db.users.find_one({"id": student['user_id']}, {"_id": 0, "password_hash": 0})
        if user:
            student['user'] = serialize_doc(user)
    return [serialize_doc(s) for s in students]

@students_router.get("/{student_id}")
async def get_student(student_id: str, current_user: dict = Depends(get_current_user)):
    student = await db.student_profiles.find_one({"id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    user = await db.users.find_one({"id": student['user_id']}, {"_id": 0, "password_hash": 0})
    if user:
        student['user'] = serialize_doc(user)
    return serialize_doc(student)

# Teacher Management (Admin)
@teachers_router.get("")
async def get_teachers(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized")
    
    teachers = await db.teacher_profiles.find({}, {"_id": 0}).to_list(100)
    for teacher in teachers:
        user = await db.users.find_one({"id": teacher['user_id']}, {"_id": 0, "password_hash": 0})
        if user:
            teacher['user'] = serialize_doc(user)
    return [serialize_doc(t) for t in teachers]

# Health check
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Seed demo data
@api_router.post("/seed-demo")
async def seed_demo_data():
    """Seed demo data for testing"""
    try:
        # Check if demo data already exists
        existing_user = await db.users.find_one({"email": "demo.student@eduos.edu"})
        if existing_user:
            return {"message": "Demo data already exists", "status": "skipped"}
        
        # Create demo student
        demo_student_user = {
            "id": str(uuid.uuid4()),
            "email": "demo.student@eduos.edu",
            "full_name": "Alex Johnson",
            "role": "student",
            "password_hash": hash_password("demo123"),
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(demo_student_user)
        
        demo_student_profile = {
            "id": str(uuid.uuid4()),
            "user_id": demo_student_user["id"],
            "student_id": "STU2024001",
            "grade_level": "Grade 11",
            "section": "A",
            "gpa": 3.75,
            "enrolled_courses": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.student_profiles.insert_one(demo_student_profile)
        
        # Create demo teacher
        demo_teacher_user = {
            "id": str(uuid.uuid4()),
            "email": "demo.teacher@eduos.edu",
            "full_name": "Dr. Sarah Williams",
            "role": "teacher",
            "password_hash": hash_password("demo123"),
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(demo_teacher_user)
        
        demo_teacher_profile = {
            "id": str(uuid.uuid4()),
            "user_id": demo_teacher_user["id"],
            "employee_id": "TCH2024001",
            "department": "Science",
            "subjects": ["Physics", "Mathematics"],
            "assigned_courses": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.teacher_profiles.insert_one(demo_teacher_profile)
        
        # Create demo admin
        demo_admin_user = {
            "id": str(uuid.uuid4()),
            "email": "demo.admin@eduos.edu",
            "full_name": "Principal Robert Chen",
            "role": "admin",
            "password_hash": hash_password("demo123"),
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(demo_admin_user)
        
        # Create demo courses
        courses_data = [
            {"code": "PHY101", "name": "Physics Fundamentals", "description": "Introduction to mechanics, thermodynamics, and waves", "grade_level": "Grade 11", "credits": 4},
            {"code": "MTH201", "name": "Advanced Mathematics", "description": "Calculus, linear algebra, and statistics", "grade_level": "Grade 11", "credits": 4},
            {"code": "CHM101", "name": "Chemistry Basics", "description": "Atomic structure, chemical bonds, and reactions", "grade_level": "Grade 11", "credits": 3},
            {"code": "BIO101", "name": "Biology Essentials", "description": "Cell biology, genetics, and evolution", "grade_level": "Grade 11", "credits": 3},
            {"code": "ENG201", "name": "English Literature", "description": "Classic and contemporary literature analysis", "grade_level": "Grade 11", "credits": 3},
            {"code": "CS101", "name": "Computer Science Intro", "description": "Programming fundamentals and algorithms", "grade_level": "Grade 11", "credits": 3},
        ]
        
        course_ids = []
        for course_data in courses_data:
            course = {
                "id": str(uuid.uuid4()),
                **course_data,
                "teacher_id": demo_teacher_user["id"],
                "enrolled_students": [demo_student_user["id"]],
                "max_students": 30,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.courses.insert_one(course)
            course_ids.append(course["id"])
        
        # Update student with enrolled courses
        await db.student_profiles.update_one(
            {"id": demo_student_profile["id"]},
            {"$set": {"enrolled_courses": course_ids[:4]}}
        )
        
        # Update teacher with assigned courses
        await db.teacher_profiles.update_one(
            {"id": demo_teacher_profile["id"]},
            {"$set": {"assigned_courses": course_ids[:2]}}
        )
        
        # Create demo grades
        grades_data = [
            {"course_id": course_ids[0], "assessment_type": "Midterm", "assessment_name": "Midterm Exam", "score": 88, "max_score": 100},
            {"course_id": course_ids[0], "assessment_type": "Quiz", "assessment_name": "Quiz 1", "score": 92, "max_score": 100},
            {"course_id": course_ids[1], "assessment_type": "Midterm", "assessment_name": "Midterm Exam", "score": 85, "max_score": 100},
            {"course_id": course_ids[1], "assessment_type": "Assignment", "assessment_name": "Homework 1", "score": 95, "max_score": 100},
            {"course_id": course_ids[2], "assessment_type": "Lab", "assessment_name": "Lab Report 1", "score": 90, "max_score": 100},
        ]
        
        for grade_data in grades_data:
            grade = {
                "id": str(uuid.uuid4()),
                "student_id": demo_student_profile["id"],
                **grade_data,
                "weight": 1.0,
                "graded_by": demo_teacher_user["id"],
                "graded_at": datetime.now(timezone.utc).isoformat()
            }
            await db.grades.insert_one(grade)
        
        # Create demo attendance
        from datetime import timedelta
        for i in range(30):
            date = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
            status = "present" if i % 7 != 0 else "absent"  # Absent on Sundays
            for course_id in course_ids[:4]:
                attendance = {
                    "id": str(uuid.uuid4()),
                    "student_id": demo_student_profile["id"],
                    "course_id": course_id,
                    "date": date,
                    "status": status,
                    "marked_by": demo_teacher_user["id"],
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.attendance.insert_one(attendance)
        
        # Create demo fees
        fees_data = [
            {"fee_type": "Tuition Fee", "amount": 5000, "due_date": "2026-02-15", "status": "pending", "paid_amount": 2000},
            {"fee_type": "Library Fee", "amount": 200, "due_date": "2026-01-30", "status": "paid", "paid_amount": 200},
            {"fee_type": "Lab Fee", "amount": 500, "due_date": "2026-02-28", "status": "pending", "paid_amount": 0},
            {"fee_type": "Sports Fee", "amount": 300, "due_date": "2026-03-15", "status": "pending", "paid_amount": 0},
        ]
        
        for fee_data in fees_data:
            fee = {
                "id": str(uuid.uuid4()),
                "student_id": demo_student_profile["id"],
                **fee_data,
                "description": f"Academic year 2025-2026 {fee_data['fee_type']}",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.fees.insert_one(fee)
        
        # Create demo achievements
        achievements_data = [
            {"title": "Honor Roll", "description": "Achieved GPA above 3.5 for Fall semester", "category": "Academic", "date_awarded": "2025-12-20"},
            {"title": "Science Fair Winner", "description": "1st place in Regional Science Fair", "category": "Science", "date_awarded": "2025-11-15"},
            {"title": "Perfect Attendance", "description": "No absences for entire semester", "category": "Academic", "date_awarded": "2025-12-20"},
            {"title": "Math Olympiad", "description": "Bronze medal in State Math Olympiad", "category": "Academic", "date_awarded": "2025-10-30"},
        ]
        
        for achievement_data in achievements_data:
            achievement = {
                "id": str(uuid.uuid4()),
                "student_id": demo_student_profile["id"],
                **achievement_data,
                "awarded_by": demo_teacher_user["id"],
                "is_verified": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.achievements.insert_one(achievement)
        
        # Create notifications
        notifications_data = [
            {"title": "Welcome to EduOS!", "message": "Your account has been set up. Explore your dashboard to get started.", "type": "info"},
            {"title": "New Grade Posted", "message": "Your Physics Midterm grade has been posted. Check your grades page.", "type": "grade"},
            {"title": "Fee Reminder", "message": "Your tuition fee payment is due on February 15. Please make the payment to avoid late fees.", "type": "fee"},
        ]
        
        for notif_data in notifications_data:
            notification = {
                "id": str(uuid.uuid4()),
                "user_id": demo_student_user["id"],
                **notif_data,
                "is_read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.notifications.insert_one(notification)
        
        return {
            "message": "Demo data created successfully",
            "status": "success",
            "credentials": {
                "student": {"email": "demo.student@eduos.edu", "password": "demo123"},
                "teacher": {"email": "demo.teacher@eduos.edu", "password": "demo123"},
                "admin": {"email": "demo.admin@eduos.edu", "password": "demo123"}
            }
        }
    except Exception as e:
        logging.error(f"Error seeding demo data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to seed demo data: {str(e)}")

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

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
