"""
EduOS 2026 - Main Application Entry Point
AI-Powered School Management Platform

This is the new modular entry point. It imports from:
- New modular routers (auth, courses, students, dashboard)
- Legacy server.py for routes not yet migrated

Migration Status:
✅ Migrated: auth, courses, students, dashboard
⏳ Legacy: organizations, knowledge, mentor, content, voice, fees, grades, 
          attendance, achievements, notifications, parents, reports, 
          credentials, rfid, messages, study_groups, zoom
"""
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
import logging

from .config import CORS_ORIGINS
from .database import close_db

# Import new modular routers
from .routers import (
    auth_router,
    courses_router,
    students_router,
    dashboard_router,
)

# Import legacy routers from server.py (routes not yet migrated)
from .server import (
    users_router,
    teachers_router,
    attendance_router,
    grades_router,
    fees_router,
    achievements_router,
    ai_router,
    notifications_router,
    orgs_router,
    knowledge_router,
    mentor_router,
    content_router,
    voice_router,
    parents_router,
    reports_router,
    credentials_router,
    rfid_router,
    messages_router,
    study_groups_router,
    zoom_router,
)

# Create the main app
app = FastAPI(
    title="EduOS 2026",
    description="AI-Powered School Management Platform - Modular Architecture",
    version="4.1.0"
)

# Create main API router
api_router = APIRouter(prefix="/api")

# Health check at root level
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "EduOS 2026 API", "version": "4.1.0"}

# Include NEW modular routers
api_router.include_router(auth_router)
api_router.include_router(courses_router)
api_router.include_router(students_router)
api_router.include_router(dashboard_router)

# Include LEGACY routers (from server.py)
api_router.include_router(users_router)
api_router.include_router(teachers_router)
api_router.include_router(attendance_router)
api_router.include_router(grades_router)
api_router.include_router(fees_router)
api_router.include_router(achievements_router)
api_router.include_router(ai_router)
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

# Include main router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_db()
