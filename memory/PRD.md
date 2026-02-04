# Cognify 2026 - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform (formerly EduOS 2026)

## Current Status: Active Development - Major Updates (Feb 4, 2026)

### What's Been Implemented Today

#### 1. Bug Fixes - AI Mentor & File Processing ✅
- **File Upload Handler** - AI Mentor now properly reads and analyzes uploaded files (PDF, images, text, CSV, JSON)
- **Voice Recording** - Full voice recording implementation with WebRTC MediaRecorder API
- **Audio Transcription** - `/api/ai/transcribe` endpoint using OpenAI Whisper
- **Image Analysis** - Vision AI analysis for uploaded images in mentor and landing chatbot
- **Landing Page File Upload** - `/api/ai/landing-upload` endpoint for public file analysis

#### 2. System Rebranding: EduOS → Cognify ✅
- All frontend pages rebranded to "Cognify 2026"
- Backend system prompts updated
- Landing page, login, register, sidebar all updated
- API responses reference Cognify

#### 3. Paynow Zimbabwe Integration ✅
- **Backend Service** - `/app/backend/services/payment_service.py` with full Paynow integration
- **Web Payments** - Card payments via Paynow redirect
- **Mobile Payments** - EcoCash and OneMoney support with USSD instructions
- **API Endpoints:**
  - `POST /api/payments/paynow/initiate` - Initiate payment
  - `POST /api/payments/paynow/check-status` - Poll payment status
  - `POST /api/payments/paynow/result` - Webhook for payment updates
- **Test Credentials:** Uses Paynow test mode (auto-approved)

#### 4. LinkedIn Scraping Service ✅
- **Proxycurl API Integration** - `/app/backend/services/linkedin_service.py`
- **Profile Data Extraction** - Skills, experience, education, headline
- **AI Fallback** - Uses GPT-5.2 if Proxycurl API unavailable
- **Learner Profile Generation** - Strengths, weaknesses, goals, recommended topics

#### 5. WhatsApp & Email Notifications ✅
- **Notification Service** - `/app/backend/services/notification_service.py`
- **Email Templates** - Welcome, enrollment, payment, reminders
- **WhatsApp Messages** - MVP mode generates wa.me links
- **API Endpoints:**
  - `POST /api/notifications/send` - Send notification
  - `POST /api/notifications/test-whatsapp` - Test WhatsApp
  - `POST /api/notifications/test-email` - Test email

#### 6. Course Structure (Standard vs Customized) ✅
- **Standard Courses** - Formal, accredited (Certificate, Certification, Diploma)
- **Customized Subjects** - Flexible, user-created (Basic, Advanced, Enterprise)
- **Branch Tabs** - UI shows three tabs: All, Standard, Customized
- **Pricing** - USD and ZWL prices for each course type

### Technology Stack
- **Frontend:** React 18, Tailwind CSS, Shadcn UI
- **Backend:** FastAPI, Python 3.11
- **Database:** MongoDB
- **AI:** Emergent LLM Key (GPT-5.2, Whisper, Vision)
- **Payments:** Paynow Zimbabwe, Stripe
- **Email:** Resend
- **LinkedIn:** Proxycurl API

## Services Created
1. `/app/backend/services/payment_service.py` - Stripe & Paynow payments
2. `/app/backend/services/linkedin_service.py` - LinkedIn profile scraping
3. `/app/backend/services/notification_service.py` - Email & WhatsApp notifications

## API Endpoints (New)
- `POST /api/ai/transcribe` - Audio transcription
- `POST /api/ai/landing-upload` - Public file analysis
- `POST /api/payments/paynow/initiate` - Paynow payment
- `POST /api/payments/paynow/check-status` - Check Paynow status
- `POST /api/notifications/send` - Send notification

## Prioritized Backlog

### P1 - In Progress
- [ ] User-Created Courses in Customized Subjects (similar to Outcome-based)
- [ ] Live Search Content Crawling
- [ ] Platform-wide Translation (t() function)
- [ ] Organizational Training Data Ingestion

### P2 - Upcoming
- [ ] KTCE Frontend Implementation
- [ ] Full ElevenLabs Voice Cloning
- [ ] Mobile App (React Native)

## Test Credentials
- Student: demo.student@cognify.edu / demo123
- Teacher: demo.teacher@cognify.edu / demo123
- Admin: demo.admin@cognify.edu / demo123

## Environment Variables (New)
- `PAYNOW_INTEGRATION_ID` - Paynow merchant ID
- `PAYNOW_INTEGRATION_KEY` - Paynow integration key
- `PROXYCURL_API_KEY` - LinkedIn scraping API key
- `WHATSAPP_API_KEY` - WhatsApp Business API (optional)

## Notes
- LinkedIn scraping falls back to AI inference if Proxycurl unavailable
- WhatsApp uses wa.me links in MVP mode (no API key required)
- Paynow test mode auto-approves payments
