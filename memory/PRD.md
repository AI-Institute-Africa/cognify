# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform with HeyGen Avatar Integration, async AI Video/Slides generation, original-format document viewer (with python-pptx fallback for production), strict org-isolation for premade courses, multi-tenant org isolation, browser-TTS audio fallback, and Course Analytics.

**Version:** 14.0 (Iteration 43)
**Date:** May 19, 2026

---

## LATEST - ITERATION 43 (4 production fixes)

### 1. PowerPoint Renders on Production (no LibreOffice required)
- New pure-Python fallback `_pptx_to_slides_json()` uses `python-pptx` (already in requirements.txt) to extract slides as structured JSON: `{index, title, bullets[level], images[base64], notes}`
- `/api/premade-courses/{id}/view` returns `application/json` with `type: "slides_json"` when LibreOffice is unavailable for PPTX
- Frontend `PremadeCoursesPage` detects JSON response and renders each slide as a 16:9 white card with title + bullets + embedded images
- LibreOffice path still works on hosts that have it (preserves original visuals)

### 2. Strict Org-Isolation on Premade Courses
- `GET /api/premade-courses` returns ONLY documents from the user's organization
- Platform admins (role=admin, no org) see all; orphaned users (no org, not admin) see none
- `_ensure_premade_access()` guards `/{id}` and `/{id}/view` with 403 on cross-org access

### 3. Friendly Budget-Exceeded Error Messages
- `/api/content/generate-slides` returns **HTTP 503** with detail: *"Emergent LLM Key budget exceeded. Please top up the Universal Key via Profile → Universal Key → Add Balance, then try again."*
- `/api/content/generate-video` background task writes the same friendly message into `generated_videos.error` (instead of cryptic "No video bytes returned")
- Detection: any caught exception with "budget" or "quota" in the message

### 4. Production PDF Worker MIME Fix (carried from iteration 42)
- Local worker at `/public/pdf.worker.min.js` (`.js` extension, correct MIME everywhere)
- Pass PDF bytes via `ArrayBuffer` to react-pdf
- CDN fallback to unpkg if local worker fails

---

## ARCHITECTURE
```
/app/backend/
├── server.py (~13,400 lines)
├── routes/
│   ├── certificates.py
│   └── avatar_orchestrator.py
├── services/
└── tests/
    └── test_iteration40_premade_org_isolation.py
```

## KEY ENDPOINTS
- `GET /api/premade-courses` — Strictly org-scoped list
- `GET /api/premade-courses/{id}/view` — Inline view (PDF native, DOCX raw, PPTX → PDF via LibreOffice OR slides_json via python-pptx, others)
- `POST /api/content/generate-slides` — Returns 503 with friendly message on LLM budget exhaustion
- `POST /api/content/generate-video` — Status records carry friendly error on budget exhaustion
- `GET /api/analytics/course-dashboard` — Role-scoped analytics

## KNOWN ENVIRONMENTAL ISSUES
- **Emergent LLM Key budget exhausted** ($29.82 / $29.82). Top up via Profile → Universal Key → Add Balance to re-enable: cloud TTS (browser fallback masks this), AI research results, Sora 2 video, Nano Banana slides.
- **LibreOffice missing on production base image**: PowerPoint now uses python-pptx slides_json fallback automatically. Word & PDF use docx-preview and react-pdf respectively (no server deps).

## NEXT / BACKLOG
- (P0) Top up Emergent LLM Key budget
- (P1) Refactor `server.py` (~13.4k lines) into `/app/backend/routes/`
- (P1) Fix demo.teacher@eduos.edu seed — currently has `organization_id=None`. Assign to Cognify or a dedicated "Demo School" org.
- (P2) Add image extraction from PPT (older legacy format) — only PPTX is parsed by python-pptx
- (P2) CSV export from Course Analytics Dashboard
- (P2) PDF page navigation controls (page input, prev/next)

**Last Updated:** May 19, 2026
