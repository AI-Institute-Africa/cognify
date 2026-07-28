# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform with HeyGen Avatar Integration, async AI Video/Slides generation, original-format document viewer with python-pptx fallback, robust PDF.js worker loading, strict org-isolation for premade courses, browser-TTS audio fallback, Course Analytics, Super Admin Console, Public Content portal for summit presentations, original-file download, multi-modal learner viewer (PDF/DOCX/PPTX/image/text) with on-demand AI video/audio generation, animated avatar teacher, multi-language translation, Resend HTTP-API email notifications, complete provider-independent Payment Management Platform, Emergent Object Storage for persistent file/video storage, live RSS-based AI research digest, Organization Public Join Link with pending-approval workflow, and async (Cloudflare-safe) course generation.

**Version:** 20.0 (Iteration 49 — Org Join Link, Async Course Gen)
**Date:** July 28, 2026

---

## LATEST — ITERATION 49

### 1. Organization Public Join Link
- Public URL `/join/<org-slug>` — anonymous landing page with org info, member count, list of public courses
- New endpoints in `/app/backend/routes/org_join_routes.py`:
  - `GET  /api/public/org/{slug}` — landing data
  - `POST /api/public/org/{slug}/signup` — application (pending by default)
  - `GET/PUT /api/org-admin/join-settings` — enable, require-approval, domain allow-list
  - `GET  /api/org-admin/pending-members` / `members`
  - `POST /api/org-admin/pending-members/{uid}/approve` / `/reject`
- Frontend: `/app/frontend/src/pages/OrgJoinPage.js` (landing) + `OrgMembersPage.js` (3-tab admin: Pending / Members / Join Link Settings with copy button, QR, toggles, domain chips)
- Login now blocks users with `member_status='pending'` or `'rejected'`
- Email notifications on: new signup (to org admin), approval, rejection

### 2. Cloudflare-524 fix: Async Course Generation
- `/api/courses/generate-custom` and `/api/org-admin/create-course-from-pdf` now return in <15s with `generation_status='generating'`
- LLM structuring runs via `asyncio.create_task()` in the background
- New endpoint `GET /api/courses/{id}/generation-status` for polling
- Frontend polls every 3s for up to 5 minutes; renders full course once `status='ready'`
- Fixes the Cloudflare 100-second edge timeout that was blocking course creation from PDFs and from scratch

### 3. Small fixes
- Mark-orphans endpoint now idempotent (second call returns marked_lost=0)
- `create-course-from-pdf` role gate now includes `super_admin`

## Testing — Iteration 49
- **Backend**: 26/26 pytest pass (`tests/test_iteration49_org_join_and_async_courses.py` + iteration 47 regression)
- **Frontend**: `/join/:slug` landing and `/org-admin/members` 3-tab console verified by Playwright

## Previous — Iteration 47 (Persistent Object Storage + Real-Time AI Digest)
[unchanged — see below]

---

## LATEST — ITERATION 47 (Production Bug Fixes)

### 1. Persistent Object Storage (fixes ephemeral-disk data loss on production)
- New helper `/app/backend/services/object_storage.py` wraps Emergent Object Storage (`put_file`, `get_object`, `stream_object`, `make_path`)
- Public content **upload** endpoint now writes to disk AND persists to object storage (`storage_path`)
- Public content **download** endpoint (`/api/public/content/{id}/download`) now cascades: disk → object storage → legacy base64
- Public content **video** endpoint (`/api/public/{doc_id}/video/{video_id}`) same cascade with `video_storage_path`
- Both AI-generated and manually-uploaded videos push to object storage
- **Startup migration**: on backend boot, all existing docs with `file_path` (disk) but no `storage_path` are automatically backfilled to object storage in a background task
- **Verified in production scenario**: physically moved `.pptx` and `.mp4` files off disk — endpoints STILL returned 200 with correct bytes from object storage
- Files now survive pod restarts, redeploys, and preview↔production cutover

### 2. Real-time AI Research Digest (replaces stale DB-only digest)
- New `/app/backend/services/research_digest.py` fetches from 21 live RSS feeds:
  - OpenAI Blog, Anthropic, Google DeepMind, Google AI, Google Research, Microsoft AI, Meta AI, Hugging Face
  - arXiv cs.AI / cs.LG / cs.CL (peer-reviewed research)
  - TechCrunch AI, MIT Tech Review, The Verge, Wired, VentureBeat
  - Google News RSS: AI, Labs, Policy, Funding, Africa AI (with `when:1d` scope)
- URL-based deduplication against `research_digest_sent` collection (unique index on `url`)
- Optional GPT-5.2 "why-it-matters" enrichment (best-effort, non-blocking)
- Runs every 4 hours, delivers to `dennis@rubiem.com` AND `takuechakanyuka@gmail.com`
- Concurrency-safe: `asyncio.Lock` prevents scheduler-vs-manual double-runs
- Manual trigger: `POST /api/super-admin/research-digest/run-now`
- Status: `GET /api/super-admin/research-digest/status`

### 3. External constraint noted
- Resend is in TEST MODE — emails to `dennis@rubiem.com` are accepted by the API but blocked from delivery until user verifies a domain at `resend.com/domains`. `takuechakanyuka@gmail.com` (verified owner) receives them normally. This is a Resend account state, not a code issue.

## Testing — Iteration 47
- **Backend**: 10/10 pytest pass — `/app/backend/tests/test_iteration47_object_storage_and_digest.py`
- Verified download & video endpoints work with disk file removed (fallback to object storage)
- Verified digest fetches 136 real items across 21 feeds, dedups correctly, sends to both recipients

## Previous — Iteration 46 (Payment Management Platform)
[unchanged — see below]

---

## LATEST — ITERATION 46 (Payment Management Platform — Pre-Paynow Live)

### 1. Super Admin → Payment Management (`/super-admin/payment-management`)
- 22 sub-modules in a single left-rail navigation page:
  Dashboard · Providers · Products · Subscriptions · Transactions · Invoices · Receipts · Refunds · Payment Logs · Webhook Logs · Audit Logs · Revenue Analytics · Pricing Plans · Coupons · Taxes · Currencies · Settings · API Configuration · Notification Settings · Email Templates · User Activity · Security
- 40+ backend endpoints under `/api/super-admin/payments/*` and `/api/payments/*` (`/app/backend/routes/payment_routes.py`)
- `PaymentPlatform` service facade (`/app/backend/services/payment_platform.py`) — single entry point for `create_payment / verify_payment / refund_payment / cancel_payment`
- Provider-independent architecture: `PaynowProvider` (primary) + 4 stub providers (Stripe, Flutterwave, Pesepay, PayPal) ready for activation

### 2. 14 new MongoDB collections
- `payment_providers, payment_products, payment_transactions, payment_subscriptions, payment_invoices, payment_receipts, payment_refunds, payment_logs, payment_audit_logs, payment_webhook_events, payment_settings, payment_pricing_plans, payment_coupons, payment_taxes, payment_currencies, payment_email_templates`
- All timestamped, with `deleted_at` soft-delete

### 3. Fernet-encrypted secrets
- `PAYMENT_ENCRYPTION_KEY` (backend/.env) encrypts `integration_key, api_key, secret_key, webhook_secret, encryption_key, client_secret`
- Secrets are NEVER returned in list responses — masked with `…•••…1234` previews

### 4. Fail-open contract — VERIFIED
- `/api/payments/status` returns `{available:false, fail_open:true, message:"Payment service is temporarily unavailable…"}` HTTP 200 until a provider is enabled
- Customers continue to access premium features — the platform never blocks while Paynow merchant activation is pending

### 5. Activity tracking middleware
- `/app/backend/middleware/activity_tracker.py` updates `users.last_seen_at` and increments `users.total_active_seconds` (max +300s per request to filter idle time)
- Anonymous public-page hits logged to `anonymous_visits` collection (IP + referrer + UA)
- External-referrer detection populates `users.last_referrer`
- Surfaced in **User Activity** panel: Online now / Hours spent / Anonymous visitors / External-referred users

### 6. 4-hour Research Digest
- `/app/backend/services/research_digest.py` — scheduler runs every 4h; emails new Live Research + Public Library items to `RESEARCH_DIGEST_EMAIL=dennis@rubiem.com`
- Skips email when no new items; daily summary email at 09:00 UTC regardless

## Testing — Iteration 46
- Backend: 25/25 pytest pass (`/app/backend/tests/test_iteration46_payment_platform.py`)
- Frontend: 22/22 sub-modules + Products CRUD + Providers Configure + Settings + Notifications + API Config + Activity + Security + Revenue verified by Playwright

## How to go live with Paynow
1. Open Super Admin → Payment Management → Providers → Paynow → Configure
2. Enter Integration ID + Integration Key + Result URL + Return URL
3. Click "Test" — must return healthy
4. Switch environment to `production`
5. Enable the Paynow provider toggle
6. Optionally toggle off `fail_open` in Settings once live

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
- (P0) Activate Paynow merchant account → paste real Integration ID/Key into Providers → enable Paynow toggle
- (P0) "Pin to course" action on Premade Documents: one-click promote a verified PDF/PPT/DOCX to a live course lesson
- (P0) Verify a domain at resend.com/domains so org-wide notification emails escape Resend test mode
- (P1) "Save to My Knowledge Base": save verified Live Research articles directly into course materials
- (P1) Refactor `server.py` (~14.5k lines) into `/app/backend/routes/*` modular routers (`payment_routes.py` already extracted)
- (P1) Split `PaymentManagementPage.js` (1074 lines) into per-panel files under `/pages/payment-management/`
- (P2) Object Storage integration for persistent uploads (production disk is ephemeral)
- (P2) Resolve PPTX `DocumentTooLarge` regression for doc id `fa26b059-d70d-4dbe-a6c9-3907a0408956`

**Last Updated:** June 30, 2026
