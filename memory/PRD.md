# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform

**Version:** 4.0 (Iteration 29 Complete)
**Date:** April 14, 2026

---

## LATEST UPDATES - ITERATION 28-29

### Certificate Visual Verification (P0) - COMPLETE
| Feature | Status |
|---------|--------|
| Certificate view page with full details (recipient, course, grade, duration, credits) | DONE |
| QR code generation for verification | DONE |
| Print layout with @page landscape CSS | DONE |
| PDF download via ReportLab | DONE |
| Public verification page at /verify-certificate/:code | DONE |
| Share button with Web Share API | DONE |
| fetch -> axios migration (3 instances fixed) | DONE |

### Org Admin Staff Rights Enforcement (P0) - COMPLETE
| Feature | Status |
|---------|--------|
| Staff rights assignment POST /api/org/staff/assign-rights | DONE |
| Staff rights retrieval GET /api/org/staff/{id}/rights | DONE |
| GET /api/org/staff returns rights field for each member | DONE |
| check_staff_permission helper function | DONE |
| Enforcement on course creation (create_course, create_course_with_details) | DONE |
| Enforcement on content upload (upload_course_content, upload_course_file) | DONE |
| Enforcement on bulk enrollment (org_bulk_enroll_participants) | DONE |
| 4-checkbox UI in Org Admin Dashboard | DONE |

### Server.py Refactoring (P1) - IN PROGRESS
| Change | Status |
|--------|--------|
| Created shared database.py module | DONE |
| Created shared config.py module | DONE |
| Created shared auth_utils.py module | DONE |
| Extracted certificate routes to routes/certificates.py | DONE |
| Extract organization routes to routes/organizations.py | TODO |
| Extract teacher routes to routes/teacher.py | TODO |
| Extract AI tool routes to routes/ai_tools.py | TODO |

### Previous Bug Fixes (Iterations 25-27)
| Fix | Status |
|-----|--------|
| Custom course "body stream already read" - switched fetch to axios | DONE |
| Custom course 502 timeout - disabled litellm retries | DONE |
| .docx upload failing - created /api/content/upload-source endpoint | DONE |
| Voice input missing on LearnByTeachingPage, HomePage | DONE |
| Dashboard KeyError profile['id'] (19 locations) | DONE |
| AI Grading Knowledge Graph sync | DONE |
| Social URL Analysis (LinkedIn + company + GitHub + Twitter) | DONE |

---

## TECH STACK

- **Frontend:** React, Tailwind CSS, Shadcn UI, axios (standardized)
- **Backend:** FastAPI, Pydantic
- **Database:** MongoDB (motor async driver)
- **AI:** Emergent LLM Key (GPT-5.2)
- **Email:** Resend
- **Payments:** Paynow
- **Auth:** JWT, Google OAuth via Emergent
- **PDF:** ReportLab, PyPDF2
- **Docs:** python-docx
- **LinkedIn/Social:** Proxycurl API + AI Fallback

---

## KEY API ENDPOINTS

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/certificates/generate` | POST | Generate course completion certificate |
| `/api/certificates/verify/{code}` | GET | Public certificate verification |
| `/api/certificates/{id}` | GET | Get certificate details |
| `/api/certificates/{id}/pdf` | GET | Download certificate as PDF |
| `/api/org/staff` | GET | Get org staff with rights |
| `/api/org/staff/assign-rights` | POST | Assign staff permissions |
| `/api/org/staff/{id}/rights` | GET | Get individual staff rights |
| `/api/training-engine/generate-questions` | POST | Generate Q&A from content |
| `/api/training-engine/generate-flashcards` | POST | Generate flashcards |
| `/api/training-engine/generate-exam` | POST | Generate exam simulation |
| `/api/content/upload-source` | POST | Upload & extract text from docs |
| `/api/courses/generate-custom` | POST | Generate custom AI course |
| `/api/organizations/register` | POST | Org portal user registration |
| `/api/organizations/approve-user` | POST | Approve pending org users |

---

## REMAINING TASKS (Backlog)

### P1 - High Priority
- [ ] Continue server.py refactoring (extract org, teacher, AI routes)

### P2 - Medium Priority
- [ ] Mobile responsiveness verification
- [ ] Async background task queues for AI Course Generation (if 120s timeout recurs)

---

## FILE STRUCTURE

```
/app/
├── backend/
│   ├── server.py                    # Main API (~11,930 lines - reduced from 12,100)
│   ├── config.py                    # Shared configuration
│   ├── database.py                  # Shared DB connection
│   ├── auth_utils.py                # Shared auth utilities
│   ├── routes/
│   │   ├── __init__.py
│   │   └── certificates.py          # Certificate CRUD & PDF (extracted)
│   └── services/
│       ├── linkedin_service.py
│       └── email_service.py
├── frontend/
│   ├── src/
│   │   ├── hooks/
│   │   │   └── useVoiceInput.js
│   │   ├── pages/
│   │   │   ├── AITrainingEnginePage.js
│   │   │   ├── CreateCustomCoursePage.js
│   │   │   ├── CertificateViewPage.js    # Updated - uses axios
│   │   │   ├── OrgAdminDashboardPage.js  # Staff rights UI
│   │   │   ├── OrgLoginPage.js
│   │   │   └── ...
│   │   └── services/
│   │       └── api.js
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
| 25 | 18/18 PASS | AI Training Engine, voice input |
| 26 | 18/18 PASS | Org portals, user approvals |
| 27 | 17/17 PASS | Cross-org isolation, course generation |
| 28 | 18/18 PASS | Certificate verification, staff rights |
| 29 | 15/15 PASS | Post-refactoring verification |

**Last Updated:** April 14, 2026
