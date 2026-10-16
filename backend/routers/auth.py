"""Authentication routes"""
from fastapi import APIRouter, HTTPException, Depends
import uuid
from ..database import db
from ..auth import hash_password, verify_password, create_token, get_current_user, serialize_doc
from ..models import (
    UserCreate, UserLogin, User, TokenResponse, 
    StudentProfile, TeacherProfile, UserRole
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
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

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user.get('password_hash', '')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user['id'], user['role'], user.get('organization_id'))
    return TokenResponse(
        access_token=token,
        user={"id": user['id'], "email": user['email'], "full_name": user['full_name'], "role": user['role']}
    )

@router.get("/me")
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
    
    if current_user.get('organization_id'):
        org = await db.organizations.find_one({"id": current_user['organization_id']}, {"_id": 0})
        if org:
            user_data['organization'] = serialize_doc(org)
    
    return user_data
