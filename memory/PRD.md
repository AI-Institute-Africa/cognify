# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform

**Version:** 3.3 (Iteration 25 Complete)
**Date:** April 13, 2026

---

## LATEST UPDATES - ITERATION 25

### Features Implemented:

| Feature | Status | Description |
|---------|--------|-------------|
| Dashboard Stats KeyError Fix | DONE | Fixed profile['id'] KeyError across 19 locations using profile.get('id', profile['user_id']) |
| AI Grading Knowledge Graph Sync | DONE | Graded assignments now update learner_concept_states for adaptive learning |
| Social URL Analysis | DONE | New endpoint /api/mentor/analyze-social-url supports LinkedIn individual/company, GitHub, Twitter URLs |
| LinkedIn Company Scraping | DONE | Enhanced linkedin_service.py to scrape company pages via Proxycurl + AI fallback |
| Voice Input for Questions | DONE | Web Speech API added to QuestionAnalysisPage for both question and answer textareas |
| Social URL Analysis UI | DONE | AI Mentor page has "Analyze URL" button with inline URL input panel |

### Previous Iteration (23-24) Features:

| Feature | Status |
|---------|--------|
| AI Features Selection Canvas | DONE |
| Custom Course Creation (3 methods) | DONE |
| Organization Login Page | DONE |
| Student Messaging Fix | DONE |
| Multi-Subject Learning Fix | DONE |
| Assignment Visibility + File Uploads | DONE |
| Certificate Hash Copy Fix | DONE |
| AI Mentor Audio Playback Fix | DONE |

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
- **QR Codes:** react-qr-code, qrcode (Python)
- **LinkedIn/Social:** Proxycurl API + AI Fallback
- **Document Parsing:** PyPDF2, python-docx

---

## REMAINING TASKS (Backlog)

### P0 - Critical
- [ ] Refactor server.py monolith into modular FastAPI routers (courses.py, users.py, assignments.py, orgs.py etc.)

### P1 - High Priority
- [ ] Full certificate visual verification (visual render confirmation needed)
- [ ] Org Admin Staff Rights Verification

### P2 - Medium Priority
- [ ] Mobile responsiveness improvements

---

## KEY API ENDPOINTS

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard/stats` | GET | Dashboard stats for all roles |
| `/api/achievements` | GET | User achievements |
| `/api/mentor/analyze-linkedin` | POST | Analyze user's linked LinkedIn |
| `/api/mentor/analyze-social-url` | POST | Analyze any social media URL |
| `/api/assignments/{id}/submit` | POST | Submit and auto-grade assignment |
| `/api/certificates/generate` | POST | Generate certificate |
| `/api/certificates/{id}` | GET | Get certificate details |
| `/api/certificates/{id}/pdf` | GET | Download certificate PDF |
| `/api/credentials/verify/{hash}` | GET | Verify credential |

---

## FILE STRUCTURE

```
/app/
├── backend/
│   ├── server.py                 # Main API server (~11,400 lines)
│   └── services/
│       ├── linkedin_service.py   # Enhanced: company + individual + social URLs
│       ├── email_service.py
│       ├── ai_service.py
│       ├── advanced_ai.py
│       └── ...
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── QuestionAnalysisPage.js  # Voice input added
│   │   │   ├── AIMentorPage.js          # Social URL analysis UI
│   │   │   ├── CredentialsPage.js       # Certificate issuance/verification
│   │   │   ├── CertificateViewPage.js   # Certificate visual display
│   │   │   └── ...
│   │   └── services/
│   │       └── api.js                   # analyzeSocialUrl added
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

**Last Updated:** April 13, 2026
