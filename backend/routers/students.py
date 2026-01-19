"""Student management routes"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from ..database import db
from ..auth import get_current_user, serialize_doc

router = APIRouter(prefix="/students", tags=["Students"])

@router.get("/at-risk")
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
        risk_factors = []
        risk_score = 0
        
        # Check attendance
        attendance = await db.attendance.find({"student_id": student['id']}, {"_id": 0}).to_list(100)
        if attendance:
            present = sum(1 for a in attendance if a.get('status') == 'present')
            attendance_rate = present / len(attendance) if len(attendance) > 0 else 1
            if attendance_rate < 0.8:
                factor_impact = int((0.8 - attendance_rate) * 100)
                risk_factors.append({
                    "name": "Low Attendance", 
                    "impact": min(factor_impact, 40), 
                    "description": f"Attendance rate: {attendance_rate*100:.0f}%"
                })
                risk_score += factor_impact
        
        # Check grades
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
        
        # Check engagement
        mentor_sessions = await db.mentor_conversations.count_documents({"user_id": student.get('user_id', '')})
        if mentor_sessions < 3:
            risk_factors.append({
                "name": "Low Engagement", 
                "impact": 15, 
                "description": f"Only {mentor_sessions} AI Mentor sessions"
            })
            risk_score += 15
        
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
                    "Assign peer tutor" if any(f['name'] == 'Grade Decline' for f in risk_factors) else "Encourage AI Mentor usage"
                ],
                "trend": "declining" if risk_score > 50 else "stable",
                "last_updated": datetime.now(timezone.utc).isoformat()
            })
    
    at_risk.sort(key=lambda x: x['risk_score'], reverse=True)
    return at_risk

@router.get("")
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

@router.get("/{student_id}")
async def get_student(student_id: str, current_user: dict = Depends(get_current_user)):
    student = await db.student_profiles.find_one({"id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    user = await db.users.find_one({"id": student['user_id']}, {"_id": 0, "password_hash": 0})
    if user:
        student['user'] = serialize_doc(user)
    return serialize_doc(student)
