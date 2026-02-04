# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform (formerly EduOS 2026)

## Current Status: Active Development (Feb 4, 2026)

---

## What's Been Implemented

### Session 12 (Current) - Feb 4, 2026

#### P0 Feature: Bulk Enrollment with Magic Links ✅
- **Purpose:** Allow organization admins to bulk enroll participants via email list
- **How it works:**
  1. Org admin enters list of emails on `/bulk-enrollment` page
  2. System generates unique magic link tokens (72-hour expiry) for each email
  3. Emails are sent with personalized invitation containing org name and course name
  4. Recipients click link, redirected to `/accept-invite?token=xxx`
  5. Users set their password and are automatically enrolled in the course
- **Backend Endpoints:**
  - `POST /api/org/bulk-enroll` - Accept emails array + course_id
  - `GET /api/org/pending-enrollments` - List pending invitations
  - `POST /api/org/resend-invitation/{id}` - Resend expired/lost invitations
  - `GET /api/auth/verify-magic-link` - Verify token validity
  - `POST /api/auth/accept-magic-link` - Accept invitation, create account
- **Frontend Pages:** `/bulk-enrollment`, `/accept-invite`

#### P1 Feature: Teacher File Upload from Device ✅
- **Purpose:** Allow teachers to upload course content directly from their device
- **Previously:** Only URL-based content (YouTube, Vimeo links)
- **Now supports:**
  - Documents: PDF, DOC, DOCX, PPT, PPTX
  - Videos: MP4, MOV, WEBM
  - Audio: MP3, WAV, OGG
  - Images: JPG, PNG, GIF, WEBP
- **Max file size:** 100MB
- **Storage:** Files saved to `/app/course_uploads/{course_id}/`
- **Backend Endpoints:**
  - `POST /api/content/course/{course_id}/upload-file`
  - `GET /api/content/files/{course_id}/{filename}`

### Previous Sessions

#### Bug Fixes (Completed)
- AI Mentor file/image/audio processing
- Landing page chatbot file analysis
- AI course content rendering (videos/slides to course_content collection)

#### Rebranding (Completed)
- System renamed from "EduOS 2026" to "Cognify"
- All email templates updated
- Frontend branding updated

#### Features Implemented
- User-Created Courses (`/create-custom-course`)
- Live Search Content Crawling
- Course Structure (Standard vs Customized branches)
- LinkedIn Scraping via Proxycurl
- Paynow Zimbabwe payment integration
- WhatsApp & Email notifications service

---

## Technology Stack
- **Frontend:** React 18, Tailwind CSS, Shadcn UI
- **Backend:** FastAPI, Python 3.11
- **Database:** MongoDB
- **AI:** Emergent LLM Key (GPT-5.2)
- **Payments:** Paynow Zimbabwe, Stripe
- **Email:** Resend API (simulated in dev)

---

## Prioritized Backlog

### P1 - In Progress/Upcoming
- [ ] Platform-wide Language Translation (t() function)
- [ ] Paynow Payment Checkout Flow (frontend)
- [ ] Live Search Content Crawling (finalize)

### P2 - Future
- [ ] KTCE Frontend Implementation
- [ ] Full ElevenLabs Voice Cloning
- [ ] Mobile App (React Native)

---

## Database Collections

### New Collections
- `magic_link_enrollments` - Stores pending bulk enrollment invitations
  - Fields: id, email, token, org_id, course_id, course_name, org_name, status, expires_at, created_at

### Updated Collections
- `course_contents` - Now includes uploaded files
  - New fields: file_path, original_filename, file_size, mime_type

---

## Test Credentials
- **Org Admin:** test.orgadmin@cognify.edu / admin123
- **Student:** demo.student@cognify.edu / demo123
- **Test Course:** test-course-1

---

## API Endpoints (New This Session)

### Bulk Enrollment
```
POST /api/org/bulk-enroll
Body: {"emails": ["user1@example.com"], "course_id": "xxx"}

GET /api/org/pending-enrollments
Authorization: Bearer token (org_admin/teacher/admin)

POST /api/org/resend-invitation/{enrollment_id}
Authorization: Bearer token

GET /api/auth/verify-magic-link?token=xxx
Public endpoint

POST /api/auth/accept-magic-link?token=xxx&password=xxx&full_name=xxx
Public endpoint
```

### File Upload
```
POST /api/content/course/{course_id}/upload-file
Content-Type: multipart/form-data
Form fields: file, title, description (optional), content_type (optional)

GET /api/content/files/{course_id}/{filename}
Returns the uploaded file with correct MIME type
```

---

## Known Limitations

### Mocked Services
- **Resend Email:** Emails are logged but not actually sent in development mode
- **ElevenLabs Voice Cloning:** Not fully implemented

---

## File Structure (Key Files)
```
/app/
├── backend/
│   ├── server.py              # Main API routes
│   ├── services/
│   │   ├── email_service.py   # Email templates including magic link
│   │   ├── payment_service.py
│   │   └── linkedin_service.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── AcceptInvitePage.js    # Magic link acceptance
│   │   │   ├── BulkEnrollmentPage.js  # Bulk enrollment UI
│   │   │   ├── CourseViewPage.js      # File upload UI
│   │   │   └── ...
│   │   └── services/api.js
│   └── package.json
├── course_uploads/           # Uploaded course files
└── memory/PRD.md
```
