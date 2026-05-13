# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform with HeyGen Avatar Integration, async AI Video/Slides generation, long-form audio (with browser-TTS fallback), original-format document viewer, multi-tenant org isolation, and Course Analytics.

**Version:** 13.0 (Iteration 42)
**Date:** May 13, 2026

---

## LATEST - ITERATION 42

### Premade Courses — View in ORIGINAL Format (no download)
- **PDF** → rendered with `react-pdf` (canvas), full page layout, multi-page scroll
- **DOCX** → rendered with `docx-preview`, preserves real Word styling (fonts, headings, bullets, sections, images)
- **PPT / PPTX / XLS / XLSX / DOC** → converted on-the-fly by LibreOffice (`/usr/bin/soffice`), cached at `/app/generated_pdf_cache/{doc_id}.pdf`, rendered with `react-pdf` so original slide visuals are preserved
- **Images** (PNG/JPG/GIF/WEBP/SVG) → inline `<img>` with disabled drag/right-click
- **TXT** → inline iframe
- Backend: new endpoint `GET /api/premade-courses/{id}/view` (auth required, X-Frame-Options SAMEORIGIN). Optional `?raw=1` to force original bytes.
- Download endpoint returns 403. No download buttons in UI. Dialog disables right-click, text-selection, copy.

### Audio Mode — Web Speech API Fallback (No more "Failed to generate audio")
- `handleGenerateAudio` first tries cloud TTS (`/api/advanced/tts`). If that fails (e.g., LLM budget exceeded), it automatically falls back to `window.speechSynthesis.speak()` reading the full lesson text in the browser's local voice. Toast updates accordingly: "Cloud audio quota reached — using browser voice instead."
- `playAudio` supports pause/resume for both the cloud (HTMLAudioElement) and the browser-TTS (speechSynthesis.pause/resume) paths
- Audio mode UI buttons (header bar + tab) flip between "Generate Audio" / "Play" / "Pause" / "Generating..." based on `audioUrl || audioPlaying`
- Result: users always get audio playback, even with zero LLM budget

### Dependencies added
- `react-pdf@10.4.1` + `pdfjs-dist` (worker at `/app/frontend/public/pdf.worker.min.mjs`, served locally)
- `docx-preview` (for DOCX rendering)
- System: `libreoffice-impress libreoffice-writer libreoffice-calc libreoffice-core` (for office → PDF conversion)

---

## ARCHITECTURE
```
/app/backend/
├── server.py (~13,200 lines)
├── routes/
│   ├── certificates.py
│   └── avatar_orchestrator.py
├── services/
└── tests/
    └── test_iteration39_premade_view_and_tts.py

/app/frontend/
├── public/
│   └── pdf.worker.min.mjs (1MB PDF.js worker)
└── src/pages/
    └── PremadeCoursesPage.js (react-pdf + docx-preview)
```

## KEY ENDPOINTS
- `GET /api/premade-courses/{id}/view?raw=0|1` — Inline view (original DOCX bytes, or office→PDF on the fly)
- `GET /api/premade-courses/{id}/download` — 403 (disabled)
- `POST /api/advanced/tts` — Long-form TTS, chunked + concatenated MP3
- `POST /api/research/search` — Returns ai_results + 12 verified-source direct links

## KNOWN ENVIRONMENTAL ISSUES
- **Emergent LLM Key budget exhausted** ($29.78 / $29.77). Refill via Profile → Universal Key → Add Balance to re-enable cloud TTS, AI research results, Sora 2 video, Nano Banana slides. **Browser-TTS fallback masks the audio issue end-to-end.**

## NEXT / BACKLOG
- (P0) Top up Emergent LLM Key budget
- (P1) Refactor `server.py` (~13,200 lines) into `/app/backend/routes/`
- (P1) Add async background generation for the office→PDF conversion (currently blocking up to 5s on first request per doc)
- (P2) Seed quiz_results + enrollments for demo org so Course Analytics shows non-zero data
- (P2) Migrate `TeacherMessagingPage` from `fetch` to `axios`
- (P2) CSV export from Course Analytics Dashboard
- (P2) Add per-page navigation chrome to the PDF viewer (page input, prev/next buttons)

**Last Updated:** May 13, 2026
