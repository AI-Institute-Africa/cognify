"""Health check and dashboard routes"""
from fastapi import APIRouter, Depends
from ..database import db
from ..auth import get_current_user, serialize_doc

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "EduOS 2026 API"}

@router.get("/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics based on user role"""
    stats = {}
    
    if current_user['role'] == 'student':
        profile = await db.student_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
        if profile:
            # Get enrolled courses
            enrolled = profile.get('enrolled_courses', [])
            stats['enrolled_courses'] = len(enrolled)
            
            # Get grades
            grades = await db.grades.find({"student_id": profile['id']}, {"_id": 0}).to_list(100)
            if grades:
                total_score = sum(g['score']/g['max_score'] for g in grades)
                stats['average_grade'] = round(total_score / len(grades) * 100, 1)
                stats['total_assessments'] = len(grades)
            else:
                stats['average_grade'] = 0
                stats['total_assessments'] = 0
            
            # Get attendance
            attendance = await db.attendance.find({"student_id": profile['id']}, {"_id": 0}).to_list(100)
            if attendance:
                present = sum(1 for a in attendance if a.get('status') == 'present')
                stats['attendance_rate'] = round(present / len(attendance) * 100, 1)
            else:
                stats['attendance_rate'] = 100
            
            # Get achievements
            achievements = await db.achievements.find({"student_id": profile['id']}, {"_id": 0}).to_list(50)
            stats['achievements_count'] = len(achievements)
            
    elif current_user['role'] == 'teacher':
        profile = await db.teacher_profiles.find_one({"user_id": current_user['id']}, {"_id": 0})
        
        # Count students in teacher's courses
        query = {"teacher_id": current_user['id']}
        if profile and profile.get('assigned_courses'):
            query = {"id": {"$in": profile['assigned_courses']}}
        
        courses = await db.courses.find(query, {"_id": 0}).to_list(100)
        stats['active_courses'] = len(courses)
        
        student_ids = set()
        for course in courses:
            student_ids.update(course.get('enrolled_students', []))
        stats['total_students'] = len(student_ids)
        
        # Pending grades
        stats['pending_grades'] = 0  # Could implement if needed
        
    elif current_user['role'] in ['admin', 'org_admin']:
        query = {}
        if current_user.get('organization_id'):
            query['organization_id'] = current_user['organization_id']
        
        stats['total_students'] = await db.student_profiles.count_documents(query)
        stats['total_teachers'] = await db.teacher_profiles.count_documents(query)
        stats['total_courses'] = await db.courses.count_documents(query)
        stats['total_users'] = await db.users.count_documents(query if query else {})
    
    return stats
