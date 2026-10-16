"""Course management routes"""
from fastapi import APIRouter, HTTPException, Depends
from ..database import db
from ..auth import get_current_user, serialize_doc
from ..models import Course, CourseCreate

router = APIRouter(prefix="/courses", tags=["Courses"])

@router.get("")
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

@router.post("", status_code=201)
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

@router.get("/{course_id}")
async def get_course(course_id: str, current_user: dict = Depends(get_current_user)):
    course = await db.courses.find_one({"id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return serialize_doc(course)

@router.post("/{course_id}/enroll")
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
