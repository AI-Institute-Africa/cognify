# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform

**Version:** 2.3 (Phase 3 Complete - Full Feature Set)
**Date:** February 5, 2026

---

## PRODUCTION AUDIT STATUS

### Phase 1 ✅ Complete (Iteration 14)
- Authentication (login, registration)
- Course types & pricing (8 types)
- Zimbabwe academic levels (15 levels)
- Organization profile management

### Phase 2 ✅ Complete (Iteration 15)
- Email verification with Resend API
- Google OAuth flow
- Course content upload/visibility

### Phase 3 ✅ Complete (Iteration 16)
- Assignment generation & visibility
- Avatar teaching integration
- Risk alerts for parents
- Study groups (all visible)
- **Enrollment Gate** - Payment enforcement

---

## Feature Status Summary

| Feature | Status | Notes |
|---------|--------|-------|
| **Enrollment Gate** | ✅ Working | Restricts content & assignments for unpaid students |
| Assignments | ✅ Working | 3 sample assignments, auto-grading |
| Avatar Teaching | ✅ Working | Endpoint exists, AI budget dependent |
| Risk Alerts | ✅ Working | Teachers can alert parents |
| Study Groups | ✅ Working | 7 groups, AI matching, join/create |
| Content Upload | ✅ Working | 5 content items in test course |
| Course Creation | ✅ Working | Paid/free, type, grade level |

---

## Enrollment Gate Implementation

### How It Works:
1. **Content Access**: Unpaid students see only preview content (first item)
2. **Assignments**: Unpaid students cannot access course assignments
3. **UI Banner**: Shows "Full Content Locked" with payment button
4. **Payment Flow**: Redirects to `/payment/{courseId}` page

### API Responses:
```json
// Unpaid student - content endpoint
{
  "contents": [...preview items...],
  "access_restricted": true,
  "message": "Please complete payment to access full course content",
  "course_price": 99.99,
  "total_items": 5,
  "preview_items": 3
}

// Paid student - full access
[...all content items...]
```

### Test Accounts:
- **Paid Student**: demo.student@cognify.edu / demo123 (full access)
- **Unpaid Student**: unpaid.student@test.edu / test123 (preview only)

---

## API Endpoints - Complete List

### Authentication
```
POST /api/auth/login                     ✅
POST /api/auth/register                  ✅
POST /api/auth/register-with-verification ✅
POST /api/auth/verify-email              ✅
POST /api/auth/google/session            ✅
```

### Courses & Content
```
GET  /api/courses                        ✅
POST /api/courses                        ✅
GET  /api/courses/{id}                   ✅
GET  /api/content/course/{id}/content    ✅ (with enrollment gate)
POST /api/content/course/{id}/content    ✅
POST /api/content/lesson/{id}/avatar-teach ✅
```

### Assignments
```
GET  /api/assignments/student/my-assignments ✅ (with enrollment gate)
POST /api/assignments/{id}/submit-and-grade  ✅
GET  /api/assignments/{id}/suggested-answer  ✅
```

### Study Groups
```
GET  /api/study-groups/all               ✅
GET  /api/study-groups/my-groups         ✅
POST /api/study-groups                   ✅
POST /api/study-groups/{id}/join         ✅
POST /api/study-groups/{id}/chat         ✅
```

### Risk Alerts
```
POST /api/risk/set-alert                 ✅ (teacher only)
POST /api/risk/notify-parent             ✅
```

### Organization
```
PUT  /api/org/profile                    ✅
GET  /api/org/profile                    ✅
```

---

## Test Data Summary

### Courses (3):
1. **Introduction to Programming** - Certificate, $99.99, Form 1
2. **Advanced Mathematics** - Diploma, $499.99, Form 5
3. **English Language Basics** - Free, $0, Grade 1

### Assignments (3 for Programming course):
1. Python Variables Practice (coding, 100 pts, due Feb 12)
2. Control Flow Quiz (essay, 50 pts, due Feb 19)
3. Loops Challenge (coding, 100 pts, due Feb 26)

### Study Groups (7):
- Python Beginners, Math Study Circle, Exam Prep - O Levels, etc.

### Content Items (5 for Programming course):
- Lesson 1: Introduction to Python
- Lesson 2: Variables and Data Types
- Video: Python Fundamentals
- And more...

---

## Test Credentials

| Role | Email | Password | Notes |
|------|-------|----------|-------|
| Paid Student | demo.student@cognify.edu | demo123 | Full access |
| Unpaid Student | unpaid.student@test.edu | test123 | Preview only |
| Teacher | demo.teacher@eduos.edu | demo123 | Can create content |
| Org Admin | test.orgadmin@cognify.edu | admin123 | Org management |

---

## Test Reports

- `/app/test_reports/iteration_14.json` - Phase 1 (100% pass)
- `/app/test_reports/iteration_15.json` - Phase 2 (100% pass)
- `/app/test_reports/iteration_16.json` - Phase 3 (100% pass, 15 tests)

---

## Known Limitations

1. **AI Budget**: Avatar teaching, AI grading require Emergent LLM key budget
2. **Email Delivery**: Resend requires verified domain
3. **Paynow**: Requires Zimbabwe merchant credentials
4. **Risk Alerts**: Parent notifications require parent-child DB link

---

## Completed in Phase 3

1. **Enrollment Gate (Backend)**
   - Content access restriction for unpaid students
   - Assignment access restriction
   - Payment status verification via enrollments collection

2. **Enrollment Gate (Frontend)**
   - CourseViewPage banner showing lock status
   - Payment redirect button with course price
   - Preview content indicator

3. **Assignments System**
   - Created 3 sample assignments
   - Student can view and submit assignments
   - Auto-grading support (AI dependent)

4. **Study Groups**
   - Created 7 study groups
   - All groups visible to all students
   - AI-powered matching suggestions
   - Join/create functionality

5. **Risk Alerts**
   - Teacher can set alerts for students
   - Alert types: academic, behavioral, attendance
   - Parent notification via email/WhatsApp

---

## P0 - Remaining Tasks

1. **Paynow Payment Testing** - With merchant credentials
2. **Parent Portal** - Link parents to students for risk alerts

---

## P1 - Next Phase

1. Video conferencing integration
2. Blockchain credential verification
3. Mobile responsive improvements

---

## P2 - Future

1. Mobile App (React Native)
2. Advanced analytics dashboard
3. AI-powered course recommendations
