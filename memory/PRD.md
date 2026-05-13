# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform with HeyGen Avatar Integration, async AI Video/Slides generation, long-form audio, multi-tenant org isolation, and Course Analytics.

**Version:** 12.0 (Iteration 41)
**Date:** May 13, 2026

---

## LATEST - ITERATION 41 (5 production bug fixes)

### 1. Premade Courses — View Only
- Removed `handleDownload` function and Download icon import from `PremadeCoursesPage.js`
- View dialog disables right-click, copy and text selection
- Backend `GET /api/premade-courses/{id}/download` now returns 403 unconditionally
- Stats card now shows "View-Only Documents" instead of Downloads count

### 2. Video Upload Restricted to Teacher/Org Admin
- Already correctly gated via `isTeacher` flag (teacher / admin / org_admin)
- No changes needed — verified

### 3. Live Research Black Screen — FIXED
- Root cause: `getCategoryIcon` was referenced in JSX but never defined → ReferenceError unmounted the tree
- Added helper mapping category → Lucide icon
- Normalized backend response (type→category, abstract→snippet, year→date)
- Backend `/api/research/search` now ALWAYS returns 12 verified-source `direct_search_links` (Google Scholar, arXiv, PubMed, IEEE, Reuters, BBC, AP, Google News, The Guardian, Nature, MIT Tech Review) even when the LLM fails
- New `ai_error` field surfaces the AI status so the toast can show "AI search temporarily unavailable"
- Added optional `category` body param to scope to 'news' (forces verified publishers only)

### 4. AI Videos Length
- Sora 2 default duration raised from 4 → 12 seconds (Sora 2 max)
- Backend clamps duration to [4..12] range
- `services/api.js` `generateVideoContent` default 4 → 12
- `CourseViewPage.js` Generate dialog and inline button both pass 12

### 5. Long-Form Audio (TTS)
- `/api/advanced/tts` switched from URL-query params → JSON body (`LongTTSRequest`)
- Added `_split_text_for_tts()` helper splitting at sentence/paragraph boundaries (~3500 char windows)
- Multi-chunk mode concatenates raw MP3 bytes from each chunk and serves via `/api/content/audio/{id}` URL
- Frontend `playAudio` and `playAvatarAudio` prefix relative `/api/...` URLs with `REACT_APP_BACKEND_URL`
- Removed 4096-char truncation on the frontend
- NOTE: Currently blocked at runtime by Emergent LLM Key BUDGET EXCEEDED ($29.78 / $29.77). Code path verified by test agent.

---

## ARCHITECTURE
```
/app/backend/
├── server.py (~13,000 lines)
├── routes/
│   ├── certificates.py
│   └── avatar_orchestrator.py
├── services/
└── tests/
    ├── test_iteration37_course_analytics_messaging.py
    └── test_iteration38_bug_fixes.py
```

## KEY ENDPOINTS
- `POST /api/research/search` — Returns ai_results + direct_search_links + ai_error
- `POST /api/advanced/tts` — JSON body, long-form via chunking
- `POST /api/content/generate-video?duration=12` — Sora 2 async, default 12s
- `GET /api/premade-courses/{id}/download` — 403 (disabled)
- `GET /api/analytics/course-dashboard` — Role-scoped analytics

## KNOWN ENVIRONMENTAL ISSUES
- **Emergent LLM Key budget exhausted** ($29.78 / $29.77). Top up via Profile → Universal Key → Add Balance to restore: long TTS, AI research results, AI Q&A generation, Sora 2 video, Nano Banana slides.

## NEXT / BACKLOG
- P0: User to top up Emergent LLM Key budget
- P1: Convert long-form TTS to async background generation (avoid K8s ingress 80s timeout on 3+ chunk inputs)
- P1: Refactor `server.py` (~13k lines) into `/app/backend/routes/`
- P2: Seed quiz_results + enrollments for demo org so Course Analytics shows non-zero data
- P2: Migrate TeacherMessagingPage from `fetch` to `axios`
- P2: CSV export from Course Analytics

**Last Updated:** May 13, 2026
