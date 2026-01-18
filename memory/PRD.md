# EduOS 2026 - Product Requirements Document

## Project Overview
**Name:** EduOS 2026 - AI-Powered School Management, Learning & Career Intelligence Platform  
**Version:** 2.0.0 (Phase 2 AI Learning Features)  
**Date:** January 18, 2026  
**Status:** Phase 2 Complete - AI Learning Platform

## Vision
A Unified Digital Education Operating System that manages a learner's full life-cycle: Admission → Learning → Assessment → Achievements → Career Guidance → University → Employment. Enhanced with AI-powered personalized learning, multi-tenancy for organizations, and multi-language support.

## User Personas

### 1. Student (Primary)
- **Needs:** View grades, track attendance, pay fees, access courses, get AI-powered learning support
- **Key Features:** Dashboard with GPA, AI Mentor, Knowledge Graph, Learn by Teaching, Career Guide

### 2. Teacher
- **Needs:** Manage classes, enter grades, track attendance, plan lessons, create courses from syllabi
- **Key Features:** AI Lesson Planner, Syllabus Ingestion, Grade entry, Attendance marking

### 3. Administrator (Platform)
- **Needs:** Manage students/teachers, oversee finances, verify organizations
- **Key Features:** Student/Teacher management, Finance overview, Organization verification

### 4. Organization Admin (Multi-tenant)
- **Needs:** Register organization, manage participants, upload programs
- **Key Features:** Organization registration, Participant enrollment, Program management

### 5. Parent
- **Needs:** Track child progress, pay fees, receive notifications
- **Key Features:** Child dashboard view, Fee payments, Attendance alerts

## Core Requirements

### Phase 1 - School Management System (COMPLETE)
- [x] JWT-based authentication
- [x] Role-based access control (student, teacher, admin, parent, org_admin)
- [x] Student/Teacher profiles
- [x] Course management with enrollment
- [x] Grade entry with GPA calculation
- [x] Attendance tracking
- [x] Fee management with payments
- [x] Achievement tracking
- [x] AI Career Guidance (GPT-5.2)
- [x] AI Lesson Planner for teachers

### Phase 2 - AI Learning Platform (COMPLETE)
- [x] **Multi-Tenancy:** Organizations (schools, universities, governments) can register
- [x] **Organization Types:** School (K-12), University, Government, Institution, Corporate
- [x] **Organization Verification:** Pending → Verified → Active workflow
- [x] **Participant Enrollment:** Org admins can enroll students/teachers
- [x] **Multi-Language UI:** English, Shona, Ndebele, Swahili, Zulu
- [x] **AI Personal Mentor:** Lifelong learning companion with memory
- [x] **Knowledge Graph:** Visual concept map with mastery tracking
- [x] **Syllabus Ingestion:** Upload documents → Generate courses
- [x] **Learn by Teaching:** Feynman technique with AI student avatar
- [x] **Live Research Engine:** Real-time industry signals and papers

### Phase 2 Features Detail

#### AI Personal Mentor
- Personalized chat with GPT-5.2 via Emergent LLM Key
- Multi-language responses (English, Shona, Ndebele, Swahili, Zulu)
- Learning style adaptation (visual, auditory, kinesthetic, reading)
- Pace customization (slow, moderate, fast)
- Conversation memory across sessions
- Audio output support (when ElevenLabs configured)

#### Knowledge Graph
- Visual concept tracking with mastery levels
- Status: Not Started → Learning → Mastered → Needs Review
- Confidence scores and retention tracking
- Spaced repetition scheduling
- 30-second AI hints for concepts
- Prerequisites and dependency mapping

#### Syllabus Ingestion
- Drag & drop file upload (PDF, TXT, MD, DOCX)
- AI-powered content extraction
- Automatic concept generation
- Course linking capability
- Processing status tracking

#### Learn by Teaching
- Feynman Technique implementation
- AI student avatar asks clarifying questions
- Evaluation with rating (1-10)
- Misconception identification
- Improvement suggestions

#### Live Research Engine
- Search across research papers, news, tools, tutorials
- Category filtering
- Relevance scoring
- Mock data (ready for real API integration)

## Architecture

### Tech Stack
- **Frontend:** React 19, Tailwind CSS, Shadcn/UI, Lucide Icons
- **Backend:** FastAPI, Motor (MongoDB async driver)
- **Database:** MongoDB
- **AI:** Emergent LLM Integration (GPT-5.2)
- **Voice:** ElevenLabs (MOCKED - no API key)
- **Auth:** JWT with bcrypt hashing

### API Structure
```
/api/auth/* - Authentication
/api/users/* - User management
/api/students/* - Student profiles
/api/teachers/* - Teacher profiles
/api/courses/* - Course management
/api/attendance/* - Attendance tracking
/api/grades/* - Grade management
/api/fees/* - Finance management
/api/achievements/* - Achievement tracking
/api/organizations/* - Multi-tenant organization management
/api/mentor/* - AI Personal Mentor
/api/knowledge/* - Knowledge Graph
/api/content/* - Multimodal content & Syllabus Ingestion
/api/voice/* - Voice & Avatar (mocked)
/api/ai/* - AI services (Career, Lesson Planner)
/api/dashboard/* - Dashboard stats
/api/notifications/* - Notifications
```

### Frontend Routes (Phase 2)
```
/ai-mentor - AI Personal Mentor chat
/knowledge-graph - Visual concept map
/learn-by-teaching - Feynman technique interface
/live-research - Research engine
/syllabus-ingestion - Document to course converter
/register-organization - Multi-step org registration
```

## Demo Accounts
```
Student: demo.student@eduos.edu / demo123
Teacher: demo.teacher@eduos.edu / demo123
Admin: demo.admin@eduos.edu / demo123
Org Admin: dr.moyo@testuniv.edu.zw / secure123
```

## Prioritized Backlog

### P0 (Critical) - Completed
- [x] Phase 1: Core SIS/LMS
- [x] Phase 2: AI Learning features
- [x] Multi-tenancy for organizations

### P1 (High Priority) - Next Phase
- [ ] Real ElevenLabs integration for voice cloning
- [ ] Parent portal with child linking
- [ ] Real-time notifications (WebSockets)
- [ ] Report card PDF generation
- [ ] Blockchain credential verification
- [ ] Graph visualization library (react-flow) for Knowledge Graph

### P2 (Medium Priority) - Future
- [ ] Mobile app (React Native)
- [ ] Smart campus IoT integration
- [ ] Biometric attendance
- [ ] Student risk prediction
- [ ] AI-powered quiz generation
- [ ] Real research API integration (arxiv, news APIs)

### P3 (Low Priority) - Later
- [ ] Third-party LMS integrations (Canvas, Moodle)
- [ ] Advanced scheduling system
- [ ] Virtual classroom integration (Zoom, Meet)

## Technical Notes
- Frontend hot reload enabled
- Backend hot reload enabled
- MongoDB connection via MONGO_URL environment variable
- AI features require EMERGENT_LLM_KEY in backend/.env
- ElevenLabs features require ELEVENLABS_API_KEY (currently mocked)

## Mocked Components
- **ElevenLabs TTS:** Voice output not functional without API key
- **ElevenLabs Voice Cloning:** Clone feature returns mock responses
- **Live Research Engine:** Uses mock data, ready for real API integration
