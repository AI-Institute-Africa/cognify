# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform

**Version:** 3.2 (Iteration 23 Complete)
**Date:** February 11, 2026

---

## LATEST UPDATES - ITERATION 23

### Features Implemented:

| Feature | Status | Description |
|---------|--------|-------------|
| AI Features Selection Canvas | ✅ DONE | Changed from grid to checkbox-based canvas with tick boxes |
| Standard Course Features | ✅ DONE | Limited to: Multi Modal, Multi-Language, Avatar, AI Mentor |
| Customized Course Features | ✅ DONE | All 8 features available |
| Course Creation Methods | ✅ DONE | 3 options: From Scratch, Upload Content, Import from Standard |
| Organization Login Page | ✅ DONE | Branded login at /org/{slug} with custom colors and stats |
| Student Messaging Fix | ✅ DONE | Backend API updated to handle message_type field |
| Multi-Subject Page | ✅ DONE | Complete UI with AI features integration |
| Share Content Page | ✅ DONE | 6 content types, visibility settings, expiry dates |
| Avatar Voice Settings | ✅ EXISTS | Already implemented in previous iteration |

### Bug Fixes Applied:

| Bug | Status | Fix |
|-----|--------|-----|
| Race condition in CreateCustomCoursePage | ✅ FIXED | Removed onClose() call after onComplete() in AIFeaturesGridModal |
| Certificate hash copy error | ✅ FIXED | Added null handling in copyToClipboard |
| Assignments not visible to students | ✅ FIXED | Added status: active field |
| AI Mentor audio playback | ✅ FIXED | Added browser TTS fallback |

---

## PREVIOUS ITERATION (22) - Test Results

| Category | Pass Rate | Tests |
|----------|-----------|-------|
| Backend | 100% | 23/23 |
| Frontend | 100% | All 6 features verified |

---

## AI FEATURES CONFIGURATION

### Standard Courses (4 Features):
1. Multi-Modal Learning (Free)
2. Multilingual Support (+$5.99)
3. Avatar Tutor (+$14.99)
4. AI Mentor (+$11.99)

### Customized Courses (8 Features - All of above plus):
5. KTCE - Knowledge Time Compression (+$9.99)
6. Outcome Based Learning (+$7.99)
7. Adaptive Learning (+$12.99)
8. Multi-disciplinary (+$8.99)

---

## COURSE CREATION METHODS

1. **Create from Scratch** - Design a completely new course with AI assistance
2. **Upload Content** - Create from uploaded documents, PDFs, or files
3. **Import from Standard** - Start from an existing standard course and customize

---

## TECH STACK

- **Frontend:** React, Tailwind CSS, Shadcn UI
- **Backend:** FastAPI, Pydantic
- **Database:** MongoDB
- **AI Integration:** Emergent LLM Key (GPT-5.2)
- **Email:** Resend
- **Payments:** Paynow
- **Authentication:** JWT, Google OAuth via Emergent
- **PDF Generation:** ReportLab
- **QR Codes:** react-qr-code

---

## TEST CREDENTIALS

| Role | Email | Password |
|------|-------|----------|
| Teacher | demo.teacher@eduos.edu | demo123 |
| Student | demo.student@cognify.edu | demo123 |
| Org Admin | test.orgadmin@cognify.edu | admin123 |

**Organization:** Cognify University (slug: `cognify`)
- URL: `/org/cognify`

---

## REMAINING TASKS (Backlog)

### P1 - High Priority
- [ ] LinkedIn analysis fix (Proxycurl API key needed)
- [ ] Full certificate display after issuance (visual verification)

### P2 - Medium Priority
- [ ] AI Grading synchronization with Knowledge Graph
- [ ] Voice input for "Create Your Own Questions"

### P3 - Low Priority
- [ ] Refactor server.py into modular routers
- [ ] Mobile responsiveness improvements

---

## FILE STRUCTURE

```
/app/
├── backend/
│   ├── server.py                 # Main API server (~11,000 lines)
│   └── services/
│       └── email_service.py
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── CreateCustomCoursePage.js  # Course creation with 3 methods
│   │   │   ├── MultiSubjectPage.js        # Multi-subject learning paths
│   │   │   ├── ShareContentPage.js        # Content sharing
│   │   │   ├── OrgLoginPage.js            # Organization-branded login
│   │   │   ├── TeacherMessagingPage.js    # Teacher-student messaging
│   │   │   └── ...
│   │   └── components/
│   │       ├── AIFeaturesGridModal.js     # Checkbox-based feature selection
│   │       ├── Sidebar.js                 # Navigation with My Courses dropdown
│   │       └── ...
└── memory/
    └── PRD.md
```

---

## KEY API ENDPOINTS

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/org/public/{org_slug}` | GET | Organization public info for branded login |
| `/api/courses/generate-custom` | POST | Generate customized course with AI |
| `/api/share/my-shared` | GET | Get user's shared content |
| `/api/share/create` | POST | Create shareable link |
| `/api/share/available/{type}` | GET | Get content available for sharing |
| `/api/multi-subject/my-paths` | GET | Get user's multi-subject paths |
| `/api/multi-subject/create` | POST | Create multi-subject learning path |
| `/api/messages` | POST | Send message |
| `/api/messages/conversation/{user_id}` | GET | Get conversation |
| `/api/user/avatar-settings` | GET/POST | Avatar settings persistence |

---

**Last Updated:** February 11, 2026
