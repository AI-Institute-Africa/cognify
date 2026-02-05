# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform

**Version:** 2.2 (Production Audit - Phase 2 Complete)
**Date:** February 5, 2026

---

## PRODUCTION AUDIT STATUS

### Phase 1 ✅ Complete (Iteration 14)
- Authentication (login, registration)
- Course types & pricing (8 types)
- Zimbabwe academic levels (15 levels)
- Organization profile management
- Basic course display

### Phase 2 ✅ Complete (Iteration 15)
- Email verification with Resend API
- Google OAuth flow
- Course content upload by teachers
- Course content visibility for students

---

## Feature Status Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Email Verification | ✅ Working | Codes generated, stored in DB. Email delivery requires domain verification |
| Google OAuth | ✅ Working | Uses Emergent auth at auth.emergentagent.com |
| Content Upload | ✅ Working | Teachers can upload text, video, files via JSON API |
| Content Visibility | ✅ Working | Students can view all course content |
| Course Creation | ✅ Working | Paid/free toggle, course type, grade level |
| Teacher Dashboard | ✅ Working | Shows 3 courses with stats |
| Student Dashboard | ✅ Working | Course browsing, enrollment |

---

## API Endpoints - Tested & Verified

### Authentication
```
POST /api/auth/login                    ✅ Working
POST /api/auth/register                 ✅ Working
POST /api/auth/register-with-verification ✅ Working (JSON body)
POST /api/auth/verify-email             ✅ Working
POST /api/auth/resend-verification      ✅ Working
POST /api/auth/google/session           ✅ Working (Emergent auth)
```

### Content Management
```
POST /api/content/course/{id}/content   ✅ Working (JSON body)
GET  /api/content/course/{id}/content   ✅ Working
POST /api/content/course/{id}/upload-file ✅ Working (multipart)
```

### Courses
```
GET  /api/courses                       ✅ Working
POST /api/courses                       ✅ Working
GET  /api/courses/{id}                  ✅ Working
GET  /api/course-types                  ✅ Working (8 types)
GET  /api/academic-levels               ✅ Working (15 levels)
```

---

## Test Credentials

| Role | Email | Password |
|------|-------|----------|
| Student | demo.student@cognify.edu | demo123 |
| Teacher | demo.teacher@eduos.edu | demo123 |
| Org Admin | test.orgadmin@cognify.edu | admin123 |

---

## Environment Configuration

### Required for Production
```env
# Email (Resend)
RESEND_API_KEY=re_2a42c7kW_CfzY1KaWc7p18DTzFopwzaZD
SENDER_EMAIL=your-verified-domain@example.com  # Must be verified domain

# Google OAuth (via Emergent)
GOOGLE_CLIENT_ID=219528317269-xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxx

# AI Features
EMERGENT_LLM_KEY=sk-emergent-xxx

# Payments (Zimbabwe)
PAYNOW_INTEGRATION_ID=xxx
PAYNOW_INTEGRATION_KEY=xxx

# Notifications
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
```

---

## Known Limitations

1. **Email Delivery**: Resend requires domain verification. Use a verified sender domain (not gmail.com)
2. **AI Budget**: Emergent LLM key may have budget limits
3. **Paynow**: Requires Zimbabwe merchant account for payment testing

---

## Test Reports

- `/app/test_reports/iteration_14.json` - Phase 1 tests (100% pass)
- `/app/test_reports/iteration_15.json` - Phase 2 tests (100% pass)
- `/app/backend/tests/test_iteration15_features.py` - Pytest file

---

## Completed Work Log

### February 5, 2026

**Phase 2 Fixes:**
1. Fixed `register-with-verification` endpoint to accept JSON body (was query params)
2. Fixed `upload_course_content` endpoint to accept JSON body with `CourseContentUpload` model
3. Updated courses to have proper `teacher_id` field
4. Enrolled demo student in Introduction to Programming course
5. Added 5 content items to test course (text lessons, video)
6. Verified student can view all course content

**Phase 1 Fixes:**
1. Fixed StudentAssignmentsPage.js syntax error
2. Fixed localStorage token key from 'token' to 'cognify_token'
3. Added OrgProfileSection component
4. Added PUT /api/org/profile endpoint
5. Created 3 sample courses with proper metadata

---

## P0 - Remaining Critical Tasks

1. **Verify Resend Domain** - Add verified sending domain in Resend dashboard
2. **Test Paynow Payment** - Requires merchant credentials

---

## P1 - Important Features (Next Phase)

1. Assignment generation and visibility
2. Avatar teaching with AI
3. Risk alerts (email/WhatsApp notifications)
4. Study groups visibility

---

## P2 - Future Tasks

1. Mobile App (React Native)
2. Blockchain credentials
3. Video conferencing integration
4. Advanced analytics

---

## Architecture

```
/app/
├── backend/
│   ├── server.py              # Main FastAPI (9500+ lines)
│   ├── services/
│   │   ├── email_service.py   # Resend integration
│   │   ├── payment_service.py # Paynow/Stripe
│   │   └── ai_service.py      # AI features
│   └── tests/
│       └── test_iteration15_features.py
├── frontend/
│   ├── src/
│   │   ├── pages/            # 30+ page components
│   │   ├── components/       # Shared UI
│   │   └── services/api.js   # API client
└── memory/
    └── PRD.md
```
