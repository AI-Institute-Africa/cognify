# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform

**Version:** 2.1 (Production Audit - Phase 1 Complete)
**Date:** February 5, 2026

---

## PRODUCTION AUDIT STATUS: ✅ Phase 1 Complete

### Features Verified Working (Iteration 14):

| Feature | Status | Notes |
|---------|--------|-------|
| Authentication | ✅ Working | Login, registration for teacher, student, org_admin |
| Course Types | ✅ Working | 8 types with pricing ($0 - $999.99) |
| Zimbabwe Academic Levels | ✅ Working | 15 levels (Primary, Secondary, Tertiary) |
| Course Creation | ✅ Working | Paid/free toggle, course type, grade level |
| Course Display | ✅ Working | Price badges, type badges, grade levels |
| Organization Profile | ✅ Working | Social media links, contact info editing |
| AI File Upload | ✅ Code Ready | Endpoint works, budget exceeded expected |
| Teacher Dashboard | ✅ Working | Stats, courses, quick actions |
| Org Admin Dashboard | ✅ Working | Profile section, staff/participants tabs |

---

## Required Environment Variables

### Configured (Production Ready):
```env
RESEND_API_KEY=re_2a42c7kW_CfzY1KaWc7p18DTzFopwzaZD
SENDER_EMAIL=takuechakanyuka@gmail.com
GOOGLE_CLIENT_ID=219528317269-xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxx
EMERGENT_LLM_KEY=sk-emergent-xxx
```

### Needs Configuration at Deployment:
```env
# Paynow Zimbabwe Payment Gateway
PAYNOW_INTEGRATION_ID=<your-paynow-id>
PAYNOW_INTEGRATION_KEY=<your-paynow-key>

# Twilio WhatsApp Notifications
TWILIO_ACCOUNT_SID=<your-twilio-sid>
TWILIO_AUTH_TOKEN=<your-twilio-token>
TWILIO_WHATSAPP_NUMBER=<your-whatsapp-number>

# LinkedIn Crawling
PROXYCURL_API_KEY=<your-proxycurl-key>
```

---

## Zimbabwe Academic Levels (15 Total)

### Primary School:
- Grade 1, Grade 2, Grade 3, Grade 4, Grade 5, Grade 6, Grade 7

### Secondary School:
- Form 1, Form 2, Form 3, Form 4, Form 5 (Lower 6), Form 6 (Upper 6)

### Tertiary:
- Undergraduate, Postgraduate

---

## Course Types (8 Total)

| Type | Price | Branch | Accredited |
|------|-------|--------|------------|
| Free Course | $0 | Standard | No |
| 3-Day Course | $29.99 | Standard | No |
| Certificate | $99.99 | Standard | Yes |
| Certification | $199.99 | Standard | Yes |
| Diploma | $499.99 | Standard | Yes |
| Custom Basic | $49.99 | Customized | No |
| Custom Advanced | $149.99 | Customized | No |
| Custom Enterprise | $999.99 | Customized | No |

---

## Test Credentials

| Role | Email | Password |
|------|-------|----------|
| Student | demo.student@cognify.edu | demo123 |
| Teacher | demo.teacher@eduos.edu | demo123 |
| Org Admin | test.orgadmin@cognify.edu | admin123 |

---

## API Endpoints Summary

### Authentication
- `POST /api/auth/login` - User login ✅
- `POST /api/auth/register` - User registration ✅
- `GET /api/auth/me` - Current user profile ✅

### Courses
- `GET /api/courses` - List courses (with price, type, is_paid) ✅
- `GET /api/course-types` - 8 course types with pricing ✅
- `GET /api/academic-levels` - 15 Zimbabwe levels ✅
- `POST /api/courses` - Create course ✅

### Organization
- `PUT /api/org/profile` - Update org profile (including social media) ✅
- `GET /api/org/profile` - Get org profile ✅
- `GET /api/org/staff` - List staff members ✅
- `GET /api/org/participants` - List participants ✅

### AI Features
- `POST /api/ai/landing-upload` - File analysis (budget dependent) ✅
- `POST /api/mentor/upload-document` - Mentor file analysis ✅

### Payments
- `POST /api/payments/paynow/initiate` - Paynow payment ⏳
- `POST /api/payments/paynow/check-status` - Check status ⏳

---

## Completed Work (February 5, 2026)

1. **Fixed StudentAssignmentsPage.js syntax error** - JSX closing tag issue
2. **Fixed localStorage token key** - Changed from 'token' to 'cognify_token' in multiple files
3. **Added OrgProfileSection component** - Organization profile editing with social media
4. **Added org profile backend endpoint** - PUT /api/org/profile
5. **Created sample courses** - 3 courses with proper fields (Certificate, Diploma, Free)
6. **Added concept learning from Knowledge Graph** - useSearchParams for concept navigation

---

## P0 - Remaining Critical Tasks

1. **Paynow Payment Testing** - Requires production credentials
2. **Email Verification Flow** - Test with Resend API
3. **Google OAuth** - Test complete OAuth flow
4. **AI Budget** - Monitor and manage Emergent LLM key budget

---

## P1 - Important Features (Next Phase)

1. **Content Visibility** - Verify teacher-uploaded content displays for students
2. **Assignment Generation** - Test AI-powered assignment creation
3. **Avatar Teaching** - Test with adequate AI budget
4. **Risk Alerts** - Test email/WhatsApp notifications to parents

---

## P2 - Future Tasks

1. Mobile App (React Native)
2. Blockchain Credentials
3. Advanced Analytics Dashboard
4. Video Conferencing Integration

---

## Test Reports

- `/app/test_reports/iteration_14.json` - Latest comprehensive test (100% pass rate)
- All 10 backend tests passed
- All frontend UI elements verified

---

## Known Limitations

### Budget/Quota:
- AI features require Emergent LLM key budget
- Current budget may be exceeded for AI features

### External Services:
- Paynow requires Zimbabwe merchant account credentials
- Twilio WhatsApp requires approved business number
- Proxycurl has rate limits for LinkedIn scraping

---

## Architecture

```
/app/
├── backend/
│   ├── server.py              # Main FastAPI application
│   ├── services/              # Service modules
│   │   ├── payment_service.py # Paynow/Stripe integration
│   │   ├── email_service.py   # Resend email service
│   │   └── ai_service.py      # AI services
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/            # React pages
│   │   ├── components/       # UI components
│   │   └── services/api.js   # API client
└── memory/
    └── PRD.md               # This file
```
