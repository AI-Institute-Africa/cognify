"""Certificate generation, verification, and PDF download routes"""
from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import StreamingResponse

try:
    from backend.auth_utils import get_current_user
    from backend.database import db
except ImportError:  # pragma: no cover - compatibility with script execution
    from auth_utils import get_current_user
    from database import db

certificates_api_router = APIRouter(prefix="/certificates", tags=["Certificates"])


@certificates_api_router.post("/generate")
async def generate_certificate(
    course_id: str = Body(...),
    student_id: str = Body(None),
    grade: str = Body("Pass"),
    current_user: dict = Depends(get_current_user)
):
    """Generate a certificate for course completion"""
    if current_user.get('role') not in ['teacher', 'org_admin', 'admin']:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    course = await db.courses.find_one({"id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    target_student_id = student_id or current_user['id']
    student = await db.users.find_one({"id": target_student_id}, {"_id": 0, "password_hash": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    verification_code = str(uuid.uuid4())[:8].upper()
    
    org = None
    if course.get('organization_id'):
        org = await db.organizations.find_one({"id": course['organization_id']}, {"_id": 0})
    
    certificate = {
        "id": str(uuid.uuid4()),
        "verification_code": verification_code,
        "course_id": course_id,
        "course_name": course.get('name') or course.get('title'),
        "student_id": target_student_id,
        "recipient_name": student.get('full_name', 'Student'),
        "organization_id": course.get('organization_id'),
        "organization_name": org.get('name') if org else None,
        "instructor_name": course.get('teacher_name'),
        "grade": grade,
        "duration_weeks": course.get('duration_weeks', 4),
        "credits": course.get('credits', 3),
        "issued_by": current_user['id'],
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "status": "active"
    }
    
    await db.certificates.insert_one(certificate)
    
    credential = {
        "id": str(uuid.uuid4()),
        "user_id": target_student_id,
        "certificate_id": certificate['id'],
        "verification_code": verification_code,
        "course_id": course_id,
        "course_name": certificate['course_name'],
        "type": "certificate",
        "issued_at": certificate['issued_at'],
        "organization_id": course.get('organization_id')
    }
    await db.credentials.insert_one(credential)
    
    return {
        "message": "Certificate generated successfully",
        "certificate_id": certificate['id'],
        "verification_code": verification_code,
        "verification_url": f"/verify-certificate/{verification_code}"
    }


@certificates_api_router.get("/verify/{verification_code}")
async def verify_certificate(verification_code: str):
    """Public endpoint to verify certificate authenticity"""
    cert = await db.certificates.find_one(
        {"verification_code": verification_code},
        {"_id": 0}
    )
    
    if cert:
        return {
            "verified": True,
            "certificate": {
                "course_name": cert.get('course_name'),
                "recipient_name": cert.get('recipient_name'),
                "issued_at": cert.get('issued_at'),
                "grade": cert.get('grade'),
                "organization_name": cert.get('organization_name')
            }
        }
    
    return {"verified": False, "certificate": None}


@certificates_api_router.get("/{certificate_id}/pdf")
async def download_certificate_pdf(certificate_id: str, current_user: dict = Depends(get_current_user)):
    """Download certificate as PDF"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    import io
    
    cert = await db.certificates.find_one({"id": certificate_id}, {"_id": 0})
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=50, bottomMargin=50)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=28, textColor=colors.darkblue, alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=14, alignment=TA_CENTER, textColor=colors.grey)
    name_style = ParagraphStyle('Name', parent=styles['Title'], fontSize=32, alignment=TA_CENTER)
    
    elements = []
    elements.append(Paragraph("CERTIFICATE OF COMPLETION", title_style))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("This certifies that", subtitle_style))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(cert.get('recipient_name', 'Student'), name_style))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("has successfully completed", subtitle_style))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(cert.get('course_name', 'Course'), title_style))
    elements.append(Spacer(1, 30))
    
    data = [
        ["Issue Date", "Grade", "Duration", "Verification Code"],
        [
            cert.get('issued_at', '')[:10] if cert.get('issued_at') else 'N/A',
            cert.get('grade', 'Pass'),
            f"{cert.get('duration_weeks', 4)} Weeks",
            cert.get('verification_code', 'N/A')
        ]
    ]
    
    table = Table(data, colWidths=[150, 100, 100, 150])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=certificate-{cert.get('verification_code', certificate_id)}.pdf"}
    )


@certificates_api_router.get("/{certificate_id}")
async def get_certificate(certificate_id: str, current_user: dict = Depends(get_current_user)):
    """Get certificate details"""
    cert = await db.certificates.find_one({"id": certificate_id}, {"_id": 0})
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return cert
