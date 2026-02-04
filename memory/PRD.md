# Cognify 2026 - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform

## Current Status: Active Development (Feb 4, 2026)

### What's Been Implemented Today

#### P1 Feature: User-Created Courses ✅
- **New Page:** `/create-custom-course` with 4-step wizard
  - Step 1: Define course title and learning goals
  - Step 2: Configure audience, duration, lessons, content options
  - Step 3: Review and generate with AI (GPT-5.2)
  - Step 4: Preview and publish
- **Course Types:**
  - Free Custom Course ($0)
  - Basic Custom Course ($49.99)
  - Advanced Custom Course ($149.99)
- **Backend Endpoint:** `POST /api/courses/generate-custom`
- **Auto-generates:** Lessons, quizzes, and content structure
- **Sidebar Link:** "Create My Course" under Learning section

#### P1 Feature: Live Search Content Crawling ✅
- **PDF Upload:** Upload and analyze research papers
- **Content Extraction:** Crawl academic papers from URLs
- **AI Analysis:** Extracts title, authors, abstract, key points, conclusions
- **New Endpoints:**
  - `POST /api/research/crawl-content` - Extract content from URLs
  - `POST /api/research/summarize-pdf` - Upload and analyze PDFs
- **Frontend Updates:**
  - "Upload PDF" button on Live Research page
  - "Read" button on search results to extract content
  - Content modal displays structured analysis

#### Bug Fixes (Earlier Today)
- AI Mentor file upload, voice recording, image analysis
- Landing page chatbot file analysis
- AI course content rendering
- System rebrand: EduOS → Cognify

#### New Integrations
- Paynow Zimbabwe (EcoCash, OneMoney, Card)
- LinkedIn Scraping via Proxycurl
- WhatsApp & Email Notifications

### Technology Stack
- **Frontend:** React 18, Tailwind CSS, Shadcn UI
- **Backend:** FastAPI, Python 3.11
- **Database:** MongoDB
- **AI:** Emergent LLM Key (GPT-5.2)
- **Payments:** Paynow Zimbabwe, Stripe

## Prioritized Backlog

### P1 - Remaining
- [ ] Platform-wide Translation (t() function)
- [ ] Organizational Training Data Ingestion

### P2 - Upcoming
- [ ] KTCE Frontend Implementation
- [ ] Full ElevenLabs Voice Cloning
- [ ] Mobile App (React Native)

## API Endpoints (New Today)
- `POST /api/courses/generate-custom` - Generate custom course
- `POST /api/courses/{id}/publish` - Publish custom course
- `POST /api/research/crawl-content` - Extract web content
- `POST /api/research/summarize-pdf` - Analyze PDF papers
- `POST /api/payments/paynow/initiate` - Paynow payment
- `POST /api/notifications/send` - Send notifications

## Test Credentials
- Student: demo.student@cognify.edu / demo123
