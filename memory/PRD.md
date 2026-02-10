# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform

**Version:** 2.8 (Iteration 21 Complete)
**Date:** February 10, 2026

---

## LATEST TEST RESULTS - ITERATION 21

| Category | Pass Rate | Tests |
|----------|-----------|-------|
| Backend | 100% | 19/19 |
| Frontend | 100% | All 6 features verified |

---

## NEW FEATURES IMPLEMENTED (Iteration 21)

### 1. Organization-Specific Login Page ✅
| Feature | Status | Details |
|---------|--------|---------|
| Branded Login | ✅ | Custom login page per organization |
| Org Stats | ✅ | Shows students, courses, certificates count |
| Custom Branding | ✅ | Primary/secondary colors, logo support |
| URL Format | ✅ | `/org/{slug}/login` |

**Test URL:** `/org/test-university-of-zimbabwe/login`

### 2. Pop-up Quizzes During Lessons ✅
| Feature | Status | Details |
|---------|--------|---------|
| Quiz Modal | ✅ | PopupQuiz component with timer |
| Question Display | ✅ | Multiple choice with A/B/C/D options |
| Progress Tracking | ✅ | Shows score and completion |
| Auto Trigger | ✅ | Triggers every 3rd lesson for students |
| Result Storage | ✅ | Saves quiz results to database |

### 3. Advanced Course Creation with AI Features ✅
| Feature | Status | Details |
|---------|--------|---------|
| Course Types | ✅ | Free, Basic ($49.99), Advanced ($149.99) |
| AI Features Grid | ✅ | 6 selectable AI capabilities |
| KTCE | ✅ | Knowledge Time Compression |
| Adaptive Learning | ✅ | Personalized learning paths |
| AI Avatar | ✅ | Virtual AI instructor |
| Real-time Feedback | ✅ | Instant AI feedback |
| Multilingual | ✅ | Auto-translate content |
| Micro-Hints | ✅ | Context-aware learning hints |

### 4. Student Profile File Uploads ✅
| Feature | Status | Details |
|---------|--------|---------|
| My Documents Section | ✅ | In Settings page for students |
| Upload Button | ✅ | Upload CVs, certificates |
| File Types | ✅ | PDF, DOC, DOCX, JPG, PNG |
| Document Management | ✅ | View, download, delete |
| Document Types | ✅ | Auto-detect CV vs Certificate |

### 5. "Enrolled" Tag on Course Cards ✅
| Feature | Status | Details |
|---------|--------|---------|
| Visual Badge | ✅ | Green badge with CheckCircle icon |
| Position | ✅ | Top right of course card |
| Condition | ✅ | Shows only for enrolled courses |

### 6. Export Reports for Org Admins ✅
| Report Type | Status | Format |
|-------------|--------|--------|
| Staff Report | ✅ | CSV with name, email, role, status |
| Participants Report | ✅ | CSV with name, email, GPA, courses |
| Enrollments Report | ✅ | CSV with student, course, date |
| Analytics Summary | ✅ | CSV with key metrics |

---

## PREVIOUSLY VERIFIED FEATURES (Iteration 19-20)

### Study Groups ✅
- Browse All Groups (visible to all students)
- Search, Join, Leave, Delete Groups
- Chat within groups

### Organization Settings Page ✅
- Profile management
- Social media links
- Document uploads
- External database connection

### Teacher Messaging ✅
- Student list by teacher's courses
- Direct messaging interface
- Voice Input for AI Mentor (Web Speech API)

### Content Display ✅
- Text, Video, Image, Slides modes
- YouTube embed support
- Course content management

---

## API ENDPOINTS

### New in Iteration 21
```
GET  /api/org/public/{org_slug}     - Get org info for branded login
GET  /api/student/documents         - Get student's uploaded documents
POST /api/student/documents/upload  - Upload CV/certificate
DEL  /api/student/documents/{id}    - Delete a document
GET  /api/lessons/{id}/quiz-questions - Get quiz questions for lesson
POST /api/lessons/{id}/quiz-result  - Save quiz result
```

### Existing
```
GET  /api/teacher/students          - Get all students for teacher messaging
POST /api/teacher/send-message      - Send message to student
GET  /api/study-groups/all          - Browse all study groups
POST /api/org/upload-document       - Org document upload
POST /api/org/db/connect            - External DB connection
```

---

## TECH STACK

- **Frontend:** React, Tailwind CSS, Shadcn UI
- **Backend:** FastAPI, Pydantic
- **Database:** MongoDB
- **AI:** Emergent LLM Key (GPT-5.2)
- **Voice:** Web Speech API (browser-native)

---

## TEST CREDENTIALS

| Role | Email | Password |
|------|-------|----------|
| Teacher | demo.teacher@eduos.edu | demo123 |
| Student | demo.student@cognify.edu | demo123 |
| Org Admin | test.orgadmin@cognify.edu | admin123 |

---

## REMAINING/FUTURE TASKS (Backlog)

### P1 - High Priority
- [ ] Fix AI features when budget is available (Avatar Teaching, AI Lesson Planner)
- [ ] Certificate Generation with QR codes
- [ ] Google OAuth fix (currently has issues)

### P2 - Medium Priority
- [ ] Bulk enrollment improvements
- [ ] Source ingestion (external database/document integration for courses)
- [ ] Advanced analytics dashboard

### P3 - Low Priority
- [ ] Refactor server.py into feature-based routers
- [ ] Clean up OrgAdminDashboardPage.js components
- [ ] Mobile responsiveness improvements

---

## FILE STRUCTURE

```
/app/
├── backend/
│   ├── server.py                 # Main backend (needs refactoring)
│   ├── services/
│   │   ├── email_service.py
│   │   └── payment_service.py
│   └── tests/
│       └── test_iteration21_features.py
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── OrgLoginPage.js           # NEW: Org branded login
│   │   │   ├── TeacherMessagingPage.js   # Teacher messaging
│   │   │   ├── CourseViewPage.js         # Quiz integration
│   │   │   ├── CoursesPage.js            # Enrolled badge
│   │   │   ├── SettingsPage.js           # Document uploads
│   │   │   ├── OrgAdminDashboardPage.js  # Export reports
│   │   │   └── CreateCustomCoursePage.js # AI features selection
│   │   └── components/
│   │       └── PopupQuiz.js              # NEW: Quiz popup
└── test_reports/
    ├── iteration_20.json
    └── iteration_21.json
```

---

**Last Updated:** February 10, 2026
