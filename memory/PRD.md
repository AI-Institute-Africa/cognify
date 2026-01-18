# EduOS 2026 - Product Requirements Document

## Project Overview
**Name:** EduOS 2026 - AI-Powered School Management, Learning & Career Intelligence Platform  
**Version:** 3.0.0 (Phase 3 Smart Campus & Blockchain)  
**Date:** January 18, 2026  
**Status:** Phase 3 Complete - Smart Campus Features

## Vision
A Unified Digital Education Operating System that manages a learner's full life-cycle: Admission → Learning → Assessment → Achievements → Career Guidance → University → Employment. Enhanced with AI-powered personalized learning, multi-tenancy for organizations, blockchain credentials, and smart campus IoT features.

## Core Features Implemented

### Phase 1 - School Management System ✅
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

### Phase 2 - AI Learning Platform ✅
- [x] Multi-Tenancy: Organizations (schools, universities, governments) registration
- [x] Organization Verification workflow
- [x] Participant Enrollment
- [x] Multi-Language UI (English, Shona, Ndebele, Swahili, Zulu)
- [x] AI Personal Mentor with conversation memory
- [x] Knowledge Graph with react-flow visualization
- [x] Syllabus Ingestion (document → course)
- [x] Learn by Teaching (Feynman technique)
- [x] Live Research Engine

### Phase 3 - Smart Campus & Blockchain ✅
- [x] **Interactive Knowledge Graph**: React-flow powered visualization with draggable nodes
- [x] **Learning Journey Timeline**: Progress tracking with milestones and activity feed
- [x] **Parent Portal**: Link parent accounts to children, view grades/attendance
- [x] **PDF Report Cards**: Generate downloadable academic reports
- [x] **Real-time Notifications**: WebSocket integration for instant updates
- [x] **Blockchain Credentials**: Hash-based verification for diplomas/certificates
- [x] **RFID/NFC Attendance**: Smart campus attendance via card scanning
- [x] **Issue Credentials**: Teachers/admins can issue verifiable credentials

## Architecture

### Tech Stack
- **Frontend:** React 19, Tailwind CSS, Shadcn/UI, Lucide Icons, React-Flow
- **Backend:** FastAPI, Motor (MongoDB async driver), python-socketio
- **Database:** MongoDB
- **AI:** Emergent LLM Integration (GPT-5.2)
- **PDF:** ReportLab for PDF generation
- **Auth:** JWT with bcrypt hashing

### API Endpoints (New)
```
# Parent Portal
GET /api/parents/children - Get linked children
GET /api/parents/children/{child_id}/details - Get child details
POST /api/parents/link-child - Link parent to child

# PDF Report Cards
GET /api/reports/report-card/{student_id} - Generate PDF report

# Blockchain Credentials
POST /api/credentials/issue - Issue new credential
GET /api/credentials/verify/{hash} - Verify credential
GET /api/credentials/student/{student_id} - Get student credentials

# RFID Attendance
POST /api/rfid/register - Register RFID card
POST /api/rfid/scan - Process RFID scan
GET /api/rfid/attendance/today - Get today's RFID attendance

# WebSocket
WS /ws/notifications/{token} - Real-time notifications
```

### Frontend Routes (New)
```
/learning-journey - Progress timeline with milestones
/parent-portal - Parent dashboard for children
/rfid-attendance - RFID attendance management
/credentials - Blockchain credentials management
```

## Demo Accounts
```
Student: demo.student@eduos.edu / demo123
Teacher: demo.teacher@eduos.edu / demo123
Admin: demo.admin@eduos.edu / demo123
Org Admin: dr.moyo@testuniv.edu.zw / secure123
```

## MOCKED Components
- **ElevenLabs Voice Cloning** - No API key (mock responses)
- **Live Research Engine** - Mock data (ready for real API)

## Prioritized Backlog

### P0 (Critical) - Completed ✅
- [x] Phase 1: Core SIS/LMS
- [x] Phase 2: AI Learning features
- [x] Phase 3: Smart Campus & Blockchain

### P1 (High Priority) - Next
- [ ] Real ElevenLabs integration for voice cloning
- [ ] Real research API integration (arxiv, news)
- [ ] Student risk prediction AI
- [ ] Advanced scheduling system

### P2 (Medium Priority)
- [ ] Mobile app (React Native/PWA)
- [ ] Third-party LMS integrations (Canvas, Moodle)
- [ ] Virtual classroom integration (Zoom, Meet)
- [ ] AI-powered quiz generation

### P3 (Low Priority)
- [ ] Biometric attendance (fingerprint, face)
- [ ] IoT environmental monitoring
- [ ] Blockchain on Ethereum/Polygon testnet
