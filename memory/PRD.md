# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform

**Version:** 7.0 (Iteration 34 Complete)
**Date:** April 27, 2026

---

## LATEST UPDATES - ITERATION 34

### Email Fix (BUG FIX)
- SENDER_EMAIL changed from gmail.com to onboarding@resend.dev — emails now send successfully
- Bulk enroll dialog shows temp passwords in results so admin can share manually

### Lesson Generation Fix (BUG FIX)
- Fixed `UnboundLocalError: cannot access local variable 'json'` — moved import outside try block
- Fixed `'str' object has no attribute 'text'` — added hasattr check on LLM response
- AI now generates 3-8 real lessons with actual document content (200-400 words each)

### Participants & Staff Pages (REWRITTEN)
- `/students` (Participants): Stats cards (Total, Active, With Courses, Pending) + table with name, email, status badges, courses, join date
- `/teachers` (Staff): Stats cards (Total, Teachers, Admins, Courses) + table with name, role badges, course count, permission badges, join date
- Fixed App.js route permissions — org_admin was missing from allowedRoles causing dashboard redirect

---

## COMPLETED FEATURES (All Sessions)
- Custom course creation with AI
- AI Mentor with voice TTS
- Knowledge Graph syncing & AI grading
- Multi-subject learning
- Voice input (global hook)
- Cross-org data isolation
- Org portal registration with admin approval
- AI Training Intelligence Engine (Q&A, flashcards, exam generation)
- Certificate generation, verification, PDF download, gallery
- Staff rights enforcement (RBAC)
- Publish assignments & exams from AI Q&A Generator
- Avatar voice cloning (5-second recording)
- Audio pause/stop controls
- Course management (edit/delete/upload content)
- Bulk enrollment into organization with temp passwords
- AI lesson generation from uploaded documents
- Org-specific Participants and Staff pages

---

## KEY API ENDPOINTS

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/courses/{id}/generate-lessons-from-content` | POST | AI lesson gen from doc |
| `/api/courses/{id}` | PUT/DELETE | Edit/delete course |
| `/api/org/bulk-enroll` | POST | Bulk enroll into org |
| `/api/students` | GET | Org participants list |
| `/api/teachers` | GET | Org staff list |
| `/api/training-engine/publish-assignment` | POST | Publish Q&A as assignment |
| `/api/training-engine/publish-exam` | POST | Publish exam |
| `/api/avatar/upload-voice` | POST | Voice clone upload |
| `/api/certificates/gallery/my` | GET | Certificate gallery |

---

## REMAINING TASKS

### P1 - High Priority
- [ ] server.py refactoring (~12,400 lines)

### P2 - Medium Priority
- [ ] Mobile responsiveness
- [ ] Async background tasks for AI generation

---

## TEST REPORTS

| Iteration | Result | Focus |
|-----------|--------|-------|
| 25-29 | ALL PASS | Core features |
| 30-32 | ALL PASS | Gallery, voice, publish |
| 33 | 16/16 PASS | Enrollment, course mgmt |
| 34 | 15/15 PASS | Email, lessons, participants/staff pages |

**Last Updated:** April 27, 2026
