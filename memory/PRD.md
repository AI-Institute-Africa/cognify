# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform

**Version:** 3.1 (Iteration 23 - Bug Fixes)
**Date:** February 11, 2026

---

## LATEST BUG FIXES - ITERATION 23

### Fixed Issues:
| Bug | Status | Fix Applied |
|-----|--------|-------------|
| Certificate hash copy error | ✅ FIXED | Updated `copyToClipboard` to handle null/undefined |
| Credential not visible after issue | ✅ FIXED | `handleIssueCredential` now properly constructs credential object from response |
| Assignments not visible to students | ✅ FIXED | Added `status: active` to all assignment creation endpoints |
| Missing course_title in assignments | ✅ FIXED | Student assignments endpoint now includes course_title |
| AI Mentor audio playback failure | ✅ FIXED | Added browser TTS fallback when ElevenLabs fails |

### Files Modified:
- `/app/frontend/src/pages/CredentialsPage.js` - Fixed credential issuance and hash copy
- `/app/frontend/src/pages/AIMentorPage.js` - Added fallback TTS using browser speechSynthesis
- `/app/backend/server.py` - Fixed assignment creation with status field and course_title

---

## PREVIOUS TEST RESULTS - ITERATION 22

| Category | Pass Rate | Tests |
|----------|-----------|-------|
| Backend | 100% | 23/23 |
| Frontend | 100% | All 6 features verified |

---

## NEW FEATURES IMPLEMENTED (Iteration 22)

### 1. AI Features Selection Grid (Mandatory Gate) ✅
| Feature | Status | Details |
|---------|--------|---------|
| Modal Trigger | ✅ | Opens when selecting Standard or Customized Course |
| Role Selection | ✅ | Step 1: Student, Teacher, Org Admin, Org Staff |
| Feature Grid | ✅ | Step 2: 7 AI capabilities with pricing |
| Fee Calculation | ✅ | Dynamic additional fee based on selections |

**AI Features Available:**
| Feature | Price | Description |
|---------|-------|-------------|
| KTCE | $9.99 | Knowledge Time Compression |
| Outcome Based Learning | $7.99 | Goal-oriented with measurable outcomes |
| Adaptive Learning | $12.99 | Personalized learning paths |
| Avatar Tutor | $14.99 | Virtual AI instructor |
| Multi-disciplinary | $8.99 | Cross-subject integration |
| Multilingual Support | $5.99 | Auto-translate content |
| AI Mentor | $11.99 | Personal AI guidance |

### 2. Organization-Specific Architecture ✅
| Feature | Status | Details |
|---------|--------|---------|
| Org Catalog Page | ✅ | `/org-catalog` with strict data isolation |
| Branded Login | ✅ | `/org/{slug}/login` page |
| Data Isolation | ✅ | Courses not visible outside organization |
| Course Management | ✅ | "Add Course" for org admins |
| User Association | ✅ | Auto-associate on first org login |

### 3. Certificate Generation & Verification ✅
| Feature | Status | Details |
|---------|--------|---------|
| Generation | ✅ | POST `/api/certificates/generate` |
| PDF Download | ✅ | Downloadable PDF certificate |
| QR Code | ✅ | QR code for verification |
| Public Verify | ✅ | GET `/api/certificates/verify/{code}` |
| Shareable Link | ✅ | `/verify-certificate/{code}` |

### 4. Navigation Structure ✅
**Updated Sidebar Order:**
1. Standard Courses (was "My Courses")
2. **Organization Catalog** (NEW)
3. **Customized Courses** (NEW)
4. Assignments, Exams, Grades...

**Org Admin Navigation:**
- "Add Course" (renamed from "Create Course")
- Organization Settings
- Content Ingestion

### 5. Terminology Changes ✅
| Old Term | New Term |
|----------|----------|
| Syllabus Ingestion | Content Ingestion |
| Upload Documents | Upload Sources |
| Create Course | Add Course (for orgs) |

### 6. Sharing Capabilities ✅
| Content Type | Shareable |
|--------------|-----------|
| AI Responses | ✅ |
| Assignments | ✅ |
| Grades | ✅ |
| Achievements | ✅ |

---

## PREVIOUSLY VERIFIED FEATURES (Iteration 20-21)

### Organization Features ✅
- Org-specific login pages
- Enrolled badge on course cards
- Export Reports (CSV)
- Staff/Participants management

### Learning Features ✅
- Pop-up quizzes during lessons
- Teacher-Student Messaging
- Voice Input for AI Mentor (Web Speech API)
- Study Groups visibility

### Content Features ✅
- Video/Image display on CourseViewPage
- Student document uploads (CV, certificates)
- Advanced course creation

---

## API ENDPOINTS

### New in Iteration 22
```
POST /api/user/ai-preferences       - Save AI feature selections
GET  /api/user/ai-preferences       - Get saved preferences
GET  /api/org/my-organization       - Get user's organization
GET  /api/org/catalog               - Get org-isolated courses
POST /api/org/courses/add           - Add course to org catalog
POST /api/certificates/generate     - Generate certificate with QR
GET  /api/certificates/{id}         - Get certificate details
GET  /api/certificates/verify/{code} - Public verification
GET  /api/certificates/{id}/pdf     - Download PDF
POST /api/share/content             - Create shareable content
GET  /api/shared/{code}             - Access shared content
POST /api/knowledge-graph/update    - Update knowledge graph
GET  /api/knowledge-graph/recommendations - Get recommendations
```

---

## TECH STACK

- **Frontend:** React, Tailwind CSS, Shadcn UI
- **Backend:** FastAPI, Pydantic, ReportLab (PDF)
- **Database:** MongoDB
- **AI:** Emergent LLM Key (GPT-5.2)
- **Voice:** Web Speech API (browser-native)
- **QR Code:** qrcode library

---

## TEST CREDENTIALS

| Role | Email | Password |
|------|-------|----------|
| Teacher | demo.teacher@eduos.edu | demo123 |
| Student | demo.student@cognify.edu | demo123 |
| Org Admin | test.orgadmin@cognify.edu | admin123 |

---

## REMAINING TASKS (Backlog)

### P1 - High Priority (Critical Fixes)
- [x] ~~Fix AI Mentor audio playback ("Audio Playback failed")~~ - FIXED: Added browser TTS fallback
- [x] ~~Generated assignments not visible to students~~ - FIXED: Added status:active and course_title
- [x] ~~Certificate hash copy error~~ - FIXED: Proper null handling
- [ ] Fix LinkedIn analysis failure (Proxycurl API key needed)
- [ ] Student messaging system malfunction

### P2 - Medium Priority
- [ ] AI Grading synchronization with Knowledge Graph
- [ ] Avatar voice settings persistence
- [ ] Multi-Subject support for all roles
- [ ] Complete MultiSubjectPage.js implementation
- [ ] Complete ShareContentPage.js implementation

### P3 - Low Priority
- [ ] Refactor server.py into feature-based routers
- [ ] Mobile responsiveness improvements

---

## FILE STRUCTURE

```
/app/
├── backend/
│   ├── server.py                 # Main backend (10,000+ lines)
│   ├── services/
│   └── tests/
│       └── test_iteration22_features.py
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── OrgLoginPage.js
│   │   │   ├── OrganizationCatalogPage.js
│   │   │   ├── CertificateViewPage.js
│   │   │   ├── CoursesPage.js (AI Features Modal)
│   │   │   └── SyllabusIngestionPage.js (Content Ingestion)
│   │   └── components/
│   │       ├── AIFeaturesGridModal.js (NEW)
│   │       └── Sidebar.js (updated nav)
└── test_reports/
    ├── iteration_21.json
    └── iteration_22.json
```

---

**Last Updated:** February 10, 2026
