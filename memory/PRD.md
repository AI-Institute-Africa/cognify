# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform

**Version:** 2.5 (Phase 4 Complete - All Features Verified)
**Date:** February 6, 2026

---

## FEATURE STATUS - ALL VERIFIED WORKING

### ✅ Authentication
| Feature | Status | Endpoint |
|---------|--------|----------|
| Direct Registration | ✅ | POST /api/auth/register |
| Login | ✅ | POST /api/auth/login |
| Profile Update (LinkedIn) | ✅ | PUT /api/auth/profile |
| Get Profile | ✅ | GET /api/auth/me |
| Google OAuth | ✅ | POST /api/auth/google/session |

### ✅ Study Groups
| Feature | Status | Endpoint |
|---------|--------|----------|
| List All Groups | ✅ | GET /api/study-groups/all |
| My Groups | ✅ | GET /api/study-groups/my-groups |
| Create Group | ✅ | POST /api/study-groups |
| Delete Group (creator) | ✅ | DELETE /api/study-groups/{id} |
| Leave Group (non-creator) | ✅ | POST /api/study-groups/{id}/leave |
| Join Group | ✅ | POST /api/study-groups/{id}/join |

### ✅ Organization Admin
| Feature | Status | Endpoint |
|---------|--------|----------|
| View Staff | ✅ | GET /api/org/staff |
| View Participants | ✅ | GET /api/org/participants |
| Invite Staff | ✅ | POST /api/org/invite-staff |
| Assign Staff Rights | ✅ | POST /api/org/staff/assign-rights |
| Update Org Profile | ✅ | PUT /api/org/profile |
| Upload Documents | ✅ | POST /api/org/documents/upload |
| Connect Database | ✅ | POST /api/org/database/connect |

### ✅ Content Management
| Feature | Status | Endpoint |
|---------|--------|----------|
| Upload Content | ✅ | POST /api/content/course/{id}/content |
| Get Content | ✅ | GET /api/content/course/{id}/content |
| Upload File | ✅ | POST /api/content/course/{id}/upload-file |
| Enrollment Gate | ✅ | Restricts unpaid students |

### ⚠️ AI Features (Budget Dependent)
| Feature | Status | Note |
|---------|--------|------|
| Avatar Teaching | ⚠️ | Works when AI budget available |
| AI Lesson Planner | ⚠️ | Works when AI budget available |
| Assignment Generation | ⚠️ | Works when AI budget available |
| Multi-Subject Learning | ⚠️ | Works when AI budget available |
| Custom Course Gen | ⚠️ | Works when AI budget available |
| Ask Cognify | ⚠️ | Works when AI budget available |
| AI Mentor | ⚠️ | Works when AI budget available |

---

## Test Results Summary

| Iteration | Tests | Pass Rate | Focus |
|-----------|-------|-----------|-------|
| 17 | 23 | 96% | Initial Phase 4 |
| 18 | 20 | 100% | All Phase 4 fixes verified |

---

## Test Credentials

| Role | Email | Password |
|------|-------|----------|
| Student | demo.student@cognify.edu | demo123 |
| Teacher | demo.teacher@eduos.edu | demo123 |
| Org Admin | test.orgadmin@cognify.edu | admin123 |

---

## What Was Implemented (Iteration 18)

### 1. Profile Update with LinkedIn URL
- **Backend**: PUT /api/auth/profile accepts JSON body
- **Frontend**: Settings page has LinkedIn Profile URL field
- **Verified**: LinkedIn URL saves and retrieves correctly

### 2. Study Group Delete/Leave
- **Backend**: DELETE /api/study-groups/{id} (creator only)
- **Backend**: POST /api/study-groups/{id}/leave (non-creator)
- **Frontend**: Delete/Leave buttons added to StudyGroupsPage
- **Verified**: Creator can delete, non-creator can leave

### 3. Organization Admin Staff/Participants
- **Backend**: GET /api/org/staff - Fixed org_id lookup
- **Backend**: GET /api/org/participants - Fixed org_id lookup
- **Frontend**: Staff tab shows members with Actions column
- **Frontend**: Participants tab shows enrolled students
- **Verified**: Both endpoints return data correctly

### 4. Staff Invitation & Rights
- **Backend**: POST /api/org/invite-staff - Creates user with temp password
- **Backend**: POST /api/org/staff/assign-rights - Updates staff permissions
- **Frontend**: Invite Staff dialog with email, name, role
- **Frontend**: Rights dialog with checkboxes for permissions
- **Verified**: Staff can be invited and rights assigned

### 5. Content Upload & Visibility
- **Backend**: POST /api/content/course/{id}/content - JSON body
- **Frontend**: API updated to use JSON instead of query params
- **Verified**: Teachers can upload, students can view

### 6. Organization Documents & Database
- **Backend**: POST /api/org/documents/upload - PDF/DOCX with extraction
- **Backend**: POST /api/org/database/connect - MongoDB connection
- **Frontend**: Upload Document dialog added
- **Verified**: Documents can be uploaded with text extraction

---

## Staff Rights System

Org admins can assign these rights:
- `can_create_courses` - Create new courses
- `can_upload_content` - Upload course materials
- `can_manage_participants` - Add/remove students
- `can_invite_participants` - Send email invitations

---

## Enrollment Gate

- Unpaid students see only preview content (first item)
- Unpaid students cannot access assignments
- UI shows "Full Content Locked" banner with payment button
- Paid students get full access

---

## API Reference

### Profile
```bash
# Update profile with LinkedIn
curl -X PUT "$API/auth/profile" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"linkedin_url": "https://linkedin.com/in/user", "bio": "Bio"}'
```

### Study Groups
```bash
# Delete group (creator only)
curl -X DELETE "$API/study-groups/{group_id}" \
  -H "Authorization: Bearer $TOKEN"

# Leave group (non-creator)
curl -X POST "$API/study-groups/{group_id}/leave" \
  -H "Authorization: Bearer $TOKEN"
```

### Org Admin
```bash
# Get staff
curl "$API/org/staff" -H "Authorization: Bearer $TOKEN"

# Invite staff
curl -X POST "$API/org/invite-staff?email=x@y.com&full_name=Name&role=teacher" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Known Limitations

1. **AI Budget**: All AI features require Emergent LLM key budget
2. **Email Delivery**: Resend requires verified sending domain
3. **Payment**: Paynow requires Zimbabwe merchant credentials

---

## Test Reports

- `/app/test_reports/iteration_18.json` - Phase 4 (100% pass)
- `/app/backend/tests/test_phase4_fixes.py` - Test file

---

## Next Steps

### P0 - Critical
1. Replenish AI budget for AI features
2. Set up parent-child links for risk alerts

### P1 - Important
1. Organization-specific login page
2. Teacher messaging improvements
3. Voice input for AI Mentor

### P2 - Future
1. Mobile App (React Native)
2. Video conferencing
3. Blockchain credentials
