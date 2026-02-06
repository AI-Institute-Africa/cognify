# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform

**Version:** 2.4 (Phase 4 Complete - Major Feature Batch)
**Date:** February 6, 2026

---

## PRODUCTION AUDIT STATUS

### Phase 1-3 ✅ Complete
- Authentication, Course Types, Organization Profile
- Email Verification, Google OAuth, Content Upload
- Assignment System, Study Groups, Enrollment Gate

### Phase 4 ✅ Complete (Iteration 17)
- Direct registration (skip email verification)
- Profile update with LinkedIn URL
- Study group delete/leave functionality
- Organization admin staff management
- Organization database & document upload
- Assignment linking to courses
- Multi-subject learning for students

---

## Feature Status Summary (Iteration 17)

| Feature | Status | Notes |
|---------|--------|-------|
| Direct Registration | ✅ Working | No email verification required |
| Profile Update (LinkedIn) | ✅ Working | LinkedIn URL saved to profile |
| Content Upload (JSON) | ✅ Working | Teachers can upload via JSON body |
| Study Group Leave | ✅ Working | Non-creators can leave |
| Study Group Delete | ✅ Working | Creator-only deletion |
| Org Participants | ✅ Working | View all students |
| Org Staff | ✅ Working | View all teachers/admins |
| Org Invite Staff | ✅ Working | Invite with temp password |
| Org Staff Rights | ✅ Working | Assign course/content/participant rights |
| Org Documents | ✅ Working | Upload PDFs, DOCX with text extraction |
| Org Database Connect | ✅ Working | Connect MongoDB external DB |
| Assignment (Course Link) | ⚠️ AI Budget | Links to course_id when budget available |
| Multi-Subject Learning | ⚠️ AI Budget | Students can access when budget available |

---

## New API Endpoints (Phase 4)

### Authentication
```
POST /api/auth/register          ✅ Direct registration (no email verify)
PUT  /api/auth/profile           ✅ Update profile with LinkedIn URL
```

### Study Groups
```
POST   /api/study-groups/{id}/leave   ✅ Leave group (non-creator)
DELETE /api/study-groups/{id}         ✅ Delete group (creator only)
```

### Organization Admin
```
GET  /api/org/participants           ✅ List all participants
GET  /api/org/staff                  ✅ List all staff
POST /api/org/invite-staff           ✅ Invite new staff member
POST /api/org/staff/assign-rights    ✅ Assign staff permissions
POST /api/org/documents/upload       ✅ Upload org documents
GET  /api/org/documents              ✅ List org documents
GET  /api/org/documents/{id}/content ✅ Get document content
POST /api/org/database/connect       ✅ Connect external database
GET  /api/org/database/status        ✅ Check database status
```

### Learning
```
POST /api/advanced/assignment/generate        ⚠️ Now links to course_id
POST /api/advanced/multidisciplinary/generate ⚠️ Now available to students
GET  /api/advanced/multi-subject/my-lessons   ✅ Get student's generated lessons
GET  /api/advanced/multi-subject/lesson/{id}  ✅ Get specific lesson
```

---

## Staff Rights System

Org admins can assign these rights to staff:
- `can_create_courses` - Create new courses
- `can_manage_participants` - Add/remove participants
- `can_upload_content` - Upload course content
- `can_invite_participants` - Send email invitations

---

## Organization Database Connection

Supports:
- MongoDB external connections
- Document uploads (PDF, DOCX, TXT)
- Text extraction from uploaded documents
- Course content can reference org documents

---

## Test Credentials

| Role | Email | Password |
|------|-------|----------|
| Student | demo.student@cognify.edu | demo123 |
| Teacher | demo.teacher@eduos.edu | demo123 |
| Org Admin | test.orgadmin@cognify.edu | admin123 |

---

## Test Reports

- `/app/test_reports/iteration_17.json` - Phase 4 (96% backend, 100% frontend)
- Backend: 22/23 tests passed
- Frontend: All pages working

---

## Known Limitations

1. **AI Budget Exceeded** - AI features (assignment generation, avatar teaching, multi-subject learning) return error until budget is replenished
2. **Email Delivery** - Resend requires verified domain
3. **Google OAuth** - Works via Emergent managed auth

---

## Fixed Issues (Phase 4)

1. ✅ Registration no longer requires email verification
2. ✅ Profile update saves LinkedIn URL correctly
3. ✅ Study group creator can delete group
4. ✅ Study group participants can leave group
5. ✅ Org admin can view participants (fixed org_id lookup)
6. ✅ Org admin can view staff (fixed org_id lookup)
7. ✅ Org admin can invite staff with temp password
8. ✅ Org admin can assign staff rights
9. ✅ Org admin can upload documents (PDF/DOCX extraction)
10. ✅ Org admin can connect external MongoDB database
11. ✅ Assignment generation now links to course_id
12. ✅ Multi-subject learning now available to students
13. ✅ Fixed duplicate function declaration in api.js

---

## P0 - Remaining Critical Tasks

1. **AI Budget** - Replenish Emergent LLM key for AI features
2. **Google OAuth Testing** - Full end-to-end test with valid session

---

## P1 - Next Phase

1. Organization-specific login page
2. File upload visibility fixes (if any remaining)
3. Teacher messaging improvements
4. Knowledge graph multi-subject start learning

---

## P2 - Future

1. Mobile App (React Native)
2. Blockchain credentials
3. Video conferencing integration

---

## Architecture

```
/app/
├── backend/
│   ├── server.py              # Main FastAPI (~10000 lines)
│   ├── services/
│   │   ├── email_service.py   # Resend
│   │   ├── payment_service.py # Paynow/Stripe
│   │   └── ai_service.py      # AI features
│   └── tests/
│       └── test_iteration17.py
├── frontend/
│   ├── src/
│   │   ├── pages/            # 35+ page components
│   │   ├── components/       # Shared UI
│   │   └── services/api.js   # API client (fixed duplicate)
└── memory/
    └── PRD.md
```
