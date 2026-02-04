# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform (formerly EduOS 2026)

## Current Status: Active Development (Feb 4, 2026)

---

## What's Been Implemented

### Session 12 (Current) - Feb 4, 2026

#### Mobile Responsiveness ✅
- **DashboardLayout.js:** Added collapsible sidebar for mobile with hamburger menu
- **Sidebar.js:** Slide-in/out animation, close button, overlay backdrop
- **Header.js:** Responsive header with condensed actions on mobile
- **HomePage.js:** Mobile-optimized hero, nav, features, and footer sections
- **LoginPage.js:** Mobile-friendly form layout
- **CoursesPage.js:** Responsive tabs and course cards
- **DashboardPage.js:** Responsive bento grid (1-col mobile, 2-col tablet, 4-col desktop)
- **App.css:** Updated bento-grid breakpoints for 480px+

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

## Mobile Responsiveness Breakpoints
- **xs (< 480px):** Single column layouts, compact UI
- **sm (480-768px):** 2-column grids where applicable
- **md (768-1024px):** 3-column grids
- **lg (1024px+):** Full desktop layout with persistent sidebar

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
│   │   ├── components/
│   │   │   ├── DashboardLayout.js  # Mobile-responsive layout
│   │   │   ├── Sidebar.js          # Collapsible sidebar
│   │   │   └── Header.js           # Responsive header
│   │   ├── pages/
│   │   │   ├── AcceptInvitePage.js
│   │   │   ├── BulkEnrollmentPage.js
│   │   │   ├── CourseViewPage.js
│   │   │   └── ...
│   │   ├── services/api.js
│   │   └── App.css                 # Responsive grid styles
│   └── package.json
├── course_uploads/           # Uploaded course files
└── memory/PRD.md
```
