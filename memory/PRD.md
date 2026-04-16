# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform

**Version:** 5.0 (Iteration 31 Complete)
**Date:** April 16, 2026

---

## LATEST UPDATES - ITERATION 30-31

### Certificate Gallery (NEW)
| Feature | Status |
|---------|--------|
| Certificate Gallery page at /certificate-gallery | DONE |
| Shows all earned certificates with gradient cards | DONE |
| Share button with verification links | DONE |
| View other user's gallery (same org) | DONE |
| Sidebar link for students | DONE |

### Publish from AI Q&A Generator (NEW)
| Feature | Status |
|---------|--------|
| "Publish as Assignment" button for teacher/org_admin | DONE |
| "Publish as Exam" button for teacher/org_admin | DONE |
| Published assignments visible to enrolled students | DONE |
| Published exams visible to enrolled students | DONE |

### Avatar Voice Cloning (NEW)
| Feature | Status |
|---------|--------|
| Voice upload (5-second sample) via /api/avatar/upload-voice | DONE |
| Voice recording with 5-second timer | DONE |
| Voice status check via /api/avatar/voice-status | DONE |
| TTS with cloned voice via /api/avatar/tts-with-clone | DONE |
| OpenAI TTS integration via Emergent LLM Key | DONE |

### Audio Pause/Stop Controls (NEW)
| Feature | Status |
|---------|--------|
| Floating pause/stop controls on AI Mentor page | DONE |
| Pause/Stop buttons on Avatar Settings test voice | DONE |

### Bug Fixes (Iteration 31)
| Fix | Status |
|-----|--------|
| Org admin seeing 0 courses — fixed query to include global active courses | DONE |
| Org admin seeing 0 assignments — fixed get_assignments for org_admin role | DONE |
| Org admin seeing 0 exams — fixed get_exams for org_admin role | DONE |
| Custom course not displaying — added is_active=true, is_published=true, organization_id, name | DONE |
| serialize_doc ObjectId crash — added _id removal | DONE |
| StudentAssignmentsPage 403 for org_admin — added role-based API call | DONE |
| Org dashboard stats showing 0 courses — fixed count query | DONE |

---

## TECH STACK

- **Frontend:** React, Tailwind CSS, Shadcn UI, axios
- **Backend:** FastAPI, Pydantic, MongoDB (motor)
- **AI:** Emergent LLM Key (GPT-5.2, OpenAI TTS)
- **Email:** Resend
- **Auth:** JWT, Google OAuth via Emergent
- **PDF:** ReportLab, PyPDF2
- **Docs:** python-docx
- **Social:** Proxycurl API

---

## KEY API ENDPOINTS

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/certificates/gallery/my` | GET | User's certificate gallery |
| `/api/certificates/gallery/user/{id}` | GET | Other user's gallery (same org) |
| `/api/training-engine/publish-assignment` | POST | Publish Q&A as assignment |
| `/api/training-engine/publish-exam` | POST | Publish exam simulation |
| `/api/avatar/upload-voice` | POST | Upload voice sample |
| `/api/avatar/voice-status` | GET | Check voice clone status |
| `/api/avatar/tts-with-clone` | POST | TTS with user's voice |
| `/api/org/staff/assign-rights` | POST | Assign staff permissions |
| `/api/org/staff/{id}/rights` | GET | Get staff rights |

---

## REMAINING TASKS (Backlog)

### P1 - High Priority
- [ ] Continue server.py refactoring (extract org, teacher, AI routes)

### P2 - Medium Priority
- [ ] Mobile responsiveness verification
- [ ] Async background tasks for AI Course Generation

---

## FILE STRUCTURE

```
/app/
├── backend/
│   ├── server.py                    # Main API (~12,200 lines)
│   ├── config.py
│   ├── database.py
│   ├── auth_utils.py
│   ├── routes/
│   │   └── certificates.py
│   └── services/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── CertificateGalleryPage.js   # NEW
│   │   │   ├── AITrainingEnginePage.js      # + Publish buttons
│   │   │   ├── AvatarSettingsPage.js        # + Voice cloning
│   │   │   ├── AIMentorPage.js              # + Audio controls
│   │   │   ├── OrgAdminDashboardPage.js     # + Courses tab
│   │   │   └── OrgLoginPage.js              # Login/Register
│   │   └── components/
│   │       └── Sidebar.js                   # + Gallery link
└── memory/
    ├── PRD.md
    └── test_credentials.md
```

---

## TEST CREDENTIALS

| Role | Email | Password |
|------|-------|----------|
| Student | demo.student@cognify.edu | demo123 |
| Teacher | demo.teacher@eduos.edu | demo123 |
| Org Admin | test.orgadmin@cognify.edu | admin123 |

**Organization:** Cognify University (slug: `cognify`)

---

## TEST REPORTS

| Iteration | Result | Focus |
|-----------|--------|-------|
| 25-27 | ALL PASS | AI Training Engine, org portals |
| 28 | 18/18 PASS | Certificate verification, staff rights |
| 29 | 15/15 PASS | Post-refactoring verification |
| 30 | 22/22 PASS | New features (gallery, voice, publish) |
| 31 | 23/23 PASS | Bug fixes (courses/assignments/exams for org_admin) |

**Last Updated:** April 16, 2026
