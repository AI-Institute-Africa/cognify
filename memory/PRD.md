# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform with HeyGen Avatar Integration, async AI Video/Slides generation, original-format document viewer with python-pptx fallback, robust PDF.js worker loading, strict org-isolation for premade courses, browser-TTS audio fallback, Course Analytics, Super Admin Console, Public Content portal for summit presentations, original-file download, multi-modal learner viewer (PDF/DOCX/PPTX/image/text) with on-demand AI video/audio generation, animated avatar teacher, multi-language translation, and Resend HTTP-API email notifications.

**Version:** 17.0 (Iteration 45 — Learner AI video, prod email URLs, animated avatar)
**Date:** June 23, 2026

---

## LATEST - ITERATION 45 (Avatar gestures + Learner AI video + Production email URLs)

### 1. Learner-side AI video generation — NEW
- Any logged-in user can generate an AI explainer video for a public/summit doc if none is attached
- `POST /api/public/content/{id}/generate-video?duration=8` + `GET /api/public/content/{id}/video-job/{jobId}` polling
- Uses the same Sora 2 chain as courses, idempotent (same doc returns same job_id while in-flight)
- Result is shared across all learners — once generated, everyone sees the same video
- Video tab on `/public/{id}` now shows "Generate AI video" button when no video exists

### 2. Animated Avatar Teacher — NEW
- Avatar face now has CSS keyframe animations: `avatar-breathe` (idle), `avatar-talk` (scale + rotation), `avatar-blink-anim` (eye-blink overlay), `avatar-bar-bounce` (speaking bars)
- New GestureCaption chip cycles through 8 action phrases (✋ gestures, 🤔 pauses, 👀 looks, 👉 highlights, 🙌 emphasises, etc.) while narrating
- Halo + ping animations + brightness boost on the avatar while speaking
- 3-stage progress indicator on Avatar button: "Generating lesson…" → "Generating voice…" → speaking

### 3. Email notifications point to production
- `PUBLIC_FRONTEND_URL=https://cognify.aiinstituteafrica.com` in backend/.env
- All 3 org notification hooks (new content, new assignment, new exam) now use `PUBLIC_FRONTEND_URL || FRONTEND_URL` fallback chain
- Resend HTTP API delivery confirmed (sent=1) to the verified owner; cross-recipient delivery requires domain verification at resend.com/domains

### 4. Audio route regression — FIXED
- An orphan `@public_router.get` decorator left over from a previous edit was binding to the wrong function, breaking `/api/public/{id}/audio/{aid}` registration
- Decorator removed; `public_serve_audio` re-registered with proper `Depends(get_current_user)` gating
- Regression test confirms 401/403 without auth, 404 only when authed with non-existent ids

## Testing — Iteration 45
- 8/9 backend pytest pass + 1 expected skip
- Frontend Playwright: all 3 new feature flows + audio regression verified

---

## Inherited from earlier iterations


### 1. Super Admin Console (`/super-admin`) — NEW
- Top-level role `super_admin` that bypasses org_isolation
- Tabs: **Analytics** (system-wide stat cards + users-by-role + top organizations), **Users** (search, role filter, active filter, soft-delete/reactivate), **Organizations** (cascading deactivate + per-org counts), **Public Content** (upload, delete, audio/video generation polling)
- Auto-redirect from `/dashboard` to `/super-admin` for super_admin users
- Role-gated sidebar with only the items super admin needs
- Seed: `SUPER_ADMIN_EMAIL` / `SUPER_ADMIN_PASSWORD` env on startup

### 2. Public Content Portal (`/public`, `/public/:docId`) — NEW
- No-login listing of summit presentations and public resources (PDF/PPTX/DOCX)
- Search + 5 category chips (All / Summit / Public / Keynotes / Workshops)
- Native document rendering: react-pdf for PDF, slides_json fallback for PPTX (via python-pptx) when LibreOffice is unavailable
- Audio narration and Video presentation versions are gated behind login (Sign-in CTA in sidebar)
- Audio/Video generation triggered by Super Admin in background; polling job endpoint

### 3. Soft-delete enforcement at login
- `/api/auth/login` now rejects `is_active=false` accounts with HTTP 403 ("Account has been deactivated")
- Verified live by deactivating demo.student → 403 → reactivate → 200

### 4. SMTP email notifications (backend hook, already deployed)
- `/app/backend/services/smtp_notifications.py` ready for course content / assignment / exam triggers

## Testing — Iteration 41
- Backend: 8/8 pytest cases pass (`/app/backend/tests/test_iteration41_super_admin_public.py`)
- Frontend: 9/9 user scenarios verified by testing agent (analytics, user toggle, org cascade, public listing, sign-in gate, role-gated sidebar)

---

## Inherited from earlier iterations


### 1. Upload Failure → FIXED
- **Root cause**: Frontend was sending `Content-Type: 'multipart/form-data'` explicitly, which strips the auto-generated `boundary` parameter. Many proxies (incl. K8s ingress) reject body parts without boundary, returning "Failed to upload document"
- **Fix**: Let axios set the multipart header itself
- **Upload limit raised from 50MB → 100MB** (server + client-side guard)
- Upload timeout raised to **5 minutes** for large files
- Better error messages: 413 → "File too large for server", 401 → "Session expired", ECONNABORTED → "Upload timed out", and surfaces the actual server detail

### 2. PDF "Could not render this document" → FIXED with Blob-URL Worker
- **Most robust PDF.js worker strategy**: fetch the worker bytes ourselves, wrap them in a Blob URL with forced `application/javascript` MIME, and use THAT as the worker source. Browsers always serve Blob URLs with the correct MIME, bypassing any static-server misconfiguration on production
- Multi-stage fallback: local `/pdf.worker.min.js` → unpkg CDN
- Production-resilient: works no matter how `.js`/`.mjs` are served

### Inherited from iterations 40/41/42
- python-pptx slides_json fallback for PPTX when LibreOffice missing (production)
- Strict org-isolation on premade courses
- Friendly budget-exceeded errors on `/generate-slides` and `/generate-video`
- docx-preview for DOCX rendering
- react-pdf for PDF rendering with ArrayBuffer source

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

/app/frontend/
├── public/
│   └── pdf.worker.min.js (PDF.js worker — fetched & blob-wrapped at runtime)
└── src/pages/
    └── PremadeCoursesPage.js (react-pdf + docx-preview + slides_json renderer)
```

## KEY ENDPOINTS
- `POST /api/premade-courses/upload` — 100MB limit, multipart
- `GET /api/premade-courses` — strictly org-scoped
- `GET /api/premade-courses/{id}/view` — PDF/DOCX raw, PPTX via LibreOffice or slides_json fallback
- `POST /api/content/generate-slides` — 503 with friendly message on LLM budget exhaustion
- `POST /api/content/generate-video` — friendly error in status record

## KNOWN ENVIRONMENTAL ISSUES
- **Emergent LLM Key budget exhausted** ($29.82 / $29.82). Refill via Profile → Universal Key → Add Balance.
- **LibreOffice missing on production base image**: PPTX uses python-pptx slides_json fallback automatically.

## NEXT / BACKLOG
- (P0) Top up Emergent LLM Key budget
- (P0) **Deploy** to push the upload + PDF.js fixes to production
- (P1) Refactor `server.py` (~13.4k lines) into `/app/backend/routes/`
- (P1) Fix `demo.teacher@eduos.edu` seed (organization_id=None)
- (P2) CSV export from Course Analytics + PDF page-navigation controls

**Last Updated:** May 19, 2026
