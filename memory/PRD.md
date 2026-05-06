# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform with HeyGen Avatar Integration

**Version:** 10.0 (Iteration 39 Complete)
**Date:** May 6, 2026

---

## LATEST - ITERATION 39

### Avatar Video Generation Fix
- `handleAvatarTeach` now calls HeyGen `generate-video` endpoint (was only generating text script)
- Uses user's avatar settings (avatar_id, voice_id) from avatar_settings collection
- Shows HeyGen video player inline when video is ready
- "Check Video Status" button polls HeyGen for completion

### Video/Slides Generation Fix
- Converted from `fetch` to `axios` (was causing silent failures)
- Added `axios` import to CourseViewPage
- Added proper error handling with `e.response?.data?.detail`
- Added lesson content fallback chain: `text || content || displayText`

### Premade Courses in Sidebar
- Moved from standalone sidebar item into "My Courses" submenu for all roles (student, teacher, org_admin, admin)

---

## ARCHITECTURE
```
/app/backend/
├── server.py (~12,700 lines)
├── routes/
│   ├── certificates.py
│   └── avatar_orchestrator.py (HeyGen + AI pipeline)
├── services/ (email, AI, payment, LinkedIn, etc.)
```

**Last Updated:** May 6, 2026
