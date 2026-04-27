# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform

**Version:** 6.0 (Iteration 33 Complete)
**Date:** April 27, 2026

---

## LATEST UPDATES - ITERATION 33

### Course Enrollment Fix (BUG FIX)
| Fix | Status |
|-----|--------|
| Org admin/teacher can now enroll in courses (was "Only students can enroll") | DONE |
| Auto-creates student_profile for non-student roles when enrolling | DONE |
| Teachers/org_admin bypass payment for courses they created | DONE |

### Bulk Enrollment Rewrite (BUG FIX + FEATURE)
| Fix | Status |
|-----|--------|
| Bulk enroll no longer requires course_id | DONE |
| Enrolls participants into ORGANIZATION with temp passwords | DONE |
| Sends welcome email with temp password | DONE |
| Role selector (student/teacher) in enrollment dialog | DONE |
| Removed course selector from bulk enroll dialog | DONE |

### Course Management (NEW)
| Feature | Status |
|---------|--------|
| PUT /api/courses/{id} - edit course details | DONE |
| DELETE /api/courses/{id} - delete course + lessons | DONE |
| POST /api/courses/{id}/lessons - add lesson | DONE |
| POST /api/courses/{id}/generate-lessons-from-content - AI lesson gen from docs | DONE |
| CourseManagePage with edit/delete/upload UI | DONE |
| "Manage Course" button for org_admin on courses page | DONE |

### AI Lesson Generation from Documents (NEW)
| Feature | Status |
|---------|--------|
| Upload PDF/DOCX/TXT to generate real lessons | DONE |
| AI structures document into 3-8 lessons with actual content | DONE |
| Lessons have title, description, content (200-400 words), key points | DONE |
| Source filename tracked per lesson | DONE |

---

## KEY API ENDPOINTS (New/Updated)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/courses/{id}/enroll` | POST | Enroll (all roles) |
| `/api/courses/{id}` | PUT | Update course |
| `/api/courses/{id}` | DELETE | Delete course |
| `/api/courses/{id}/lessons` | POST | Add lesson |
| `/api/courses/{id}/generate-lessons-from-content` | POST | AI lesson gen from doc |
| `/api/org/bulk-enroll` | POST | Bulk enroll into org |

---

## REMAINING TASKS (Backlog)

### P1 - High Priority
- [ ] Continue server.py refactoring (extract org, teacher, AI routes)

### P2 - Medium Priority
- [ ] Mobile responsiveness verification
- [ ] Async background tasks for AI Course Generation

---

## TEST REPORTS

| Iteration | Result | Focus |
|-----------|--------|-------|
| 25-29 | ALL PASS | Core features, refactoring |
| 30-31 | ALL PASS | Gallery, voice clone, publish |
| 32 | ALL PASS | Publish visibility, voice placement |
| 33 | 16/16 PASS | Enrollment fix, bulk enroll, course management |

**Last Updated:** April 27, 2026
