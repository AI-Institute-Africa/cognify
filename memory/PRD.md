# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform

**Version:** 2.6 (Iteration 19 Complete)
**Date:** February 6, 2026

---

## LATEST TEST RESULTS - ITERATION 19

| Category | Pass Rate | Tests |
|----------|-----------|-------|
| Backend | 100% | 20/20 |
| Frontend | 100% | All verified |

---

## FEATURES VERIFIED WORKING

### Study Groups
| Feature | Status | Notes |
|---------|--------|-------|
| Browse All Groups | ✅ | New section shows all groups to all students |
| Search Groups | ✅ | Search input filters groups |
| Join Groups | ✅ | Any student can join any group |
| Leave Groups | ✅ | Non-creators can leave |
| Delete Groups | ✅ | Creator can delete |

### Organization Settings (NEW PAGE)
| Tab | Status | Features |
|-----|--------|----------|
| Profile | ✅ | Name, website, phone, address, description, logo |
| Social Media | ✅ | Facebook, Twitter, LinkedIn, Instagram |
| Documents | ✅ | Upload PDFs, DOCX with text extraction |
| Database | ✅ | Connect external MongoDB |

**Access:** `/organization-settings` (org_admin only)

### Assignment Generator
| Feature | Status | Notes |
|---------|--------|-------|
| Course Selection | ✅ | Dropdown shows all courses |
| Course Linking | ✅ | Assignment saved with course_id |
| Generate | ✅ | Creates assignment (AI budget needed) |

### Content Display
| Type | Status | Notes |
|------|--------|-------|
| Text | ✅ | Markdown rendering |
| Video | ✅ | YouTube embed + native video |
| Images | ✅ | Image display with url field support |
| Slides | ✅ | Slide presentation |

---

## API ENDPOINTS VERIFIED

```
# Study Groups
GET  /api/study-groups/all              ✅ All groups visible
GET  /api/study-groups/all?search=X     ✅ Search groups

# Organization Settings
GET  /api/org/profile                   ✅ Get org profile
PUT  /api/org/profile                   ✅ Update with social media
GET  /api/org/documents                 ✅ List documents
POST /api/org/documents/upload          ✅ Upload with text extraction
GET  /api/org/database/status           ✅ Check DB status
POST /api/org/database/connect          ✅ Connect MongoDB

# Assignments
POST /api/advanced/assignment/generate?course_id=X  ✅ Linked to course
```

---

## SIDEBAR UPDATES

### Org Admin Menu (Updated)
1. Dashboard
2. **Org Dashboard** (Staff/Participants management)
3. **Organization Settings** (NEW - Profile, Social, Documents, DB)
4. Participants
5. Staff
6. Programs
7. Finance
8. AI Tools (Syllabus, Risk, Mentor)
9. Smart Campus (Virtual, RFID, Biometric, Credentials)

---

## BUG FIXES (Iteration 19)

1. **PUT /api/org/profile** - Fixed to check both `org_id` and `organization_id`
2. **Video Display** - Added support for `url` field (not just `video_url`)
3. **Image Display** - Added support for `url` field with type check
4. **Study Groups** - Removed `is_public` filter so all groups visible

---

## TEST CREDENTIALS

| Role | Email | Password |
|------|-------|----------|
| Student | demo.student@cognify.edu | demo123 |
| Teacher | demo.teacher@eduos.edu | demo123 |
| Org Admin | test.orgadmin@cognify.edu | admin123 |

---

## TEST REPORTS

- `/app/test_reports/iteration_19.json` - Latest (100% pass)
- `/app/backend/tests/test_iteration19_features.py`

---

## REMAINING TASKS

### P1 - Important
1. Teacher messaging to students
2. Voice input for AI Mentor
3. Organization-specific login page (separate URL)

### P2 - Enhancement
1. AI features (require budget replenishment)
2. Mobile app
3. Video conferencing

---

## FILE CHANGES (Iteration 19)

### New Files
- `/app/frontend/src/pages/OrganizationSettingsPage.js`

### Modified Files
- `/app/frontend/src/pages/StudyGroupsPage.js` - Browse All section
- `/app/frontend/src/pages/CourseViewPage.js` - Video/Image url support
- `/app/frontend/src/pages/AssignmentGeneratorPage.js` - Course selection
- `/app/frontend/src/components/Sidebar.js` - Org admin menu
- `/app/frontend/src/services/api.js` - Course ID parameter
- `/app/frontend/src/App.js` - OrganizationSettingsPage route
- `/app/backend/server.py` - org_id fix
