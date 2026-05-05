# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform with HeyGen Avatar Integration

**Version:** 8.0 (Iteration 36 Complete)
**Date:** May 5, 2026

---

## LATEST - ITERATION 36: Avatar Learning Orchestrator

### Avatar Orchestrator (HeyGen Integration) - NEW
| Feature | Endpoint | Status |
|---------|----------|--------|
| Get HeyGen avatars (1281 available) | GET /api/avatar-orchestrator/avatars | DONE |
| Get HeyGen voices (2386 available) | GET /api/avatar-orchestrator/voices | DONE |
| Generate avatar teaching video | POST /api/avatar-orchestrator/generate-video | DONE |
| Check video status | GET /api/avatar-orchestrator/video-status/{id} | DONE |
| Interactive tutor Q&A | POST /api/avatar-orchestrator/interactive-tutor | DONE |
| Translate teaching script | POST /api/avatar-orchestrator/translate-script | DONE |
| Generate assessment/quiz | POST /api/avatar-orchestrator/generate-assessment | DONE |
| Adaptive difficulty rewrite | POST /api/avatar-orchestrator/adaptive-rewrite | DONE |
| Generate slides from lessons | POST /api/avatar-orchestrator/generate-slides | DONE |

### Bug Fixes
| Fix | Status |
|-----|--------|
| Live Research search (query param → JSON body) | DONE |
| Video/Slides generation available to ALL users (not just teachers) | DONE |
| Key Points display in CourseViewPage for generated lessons | DONE |

---

## ARCHITECTURE
```
/app/backend/
├── server.py (~12,500 lines)
├── routes/
│   ├── certificates.py
│   └── avatar_orchestrator.py   # NEW: HeyGen + AI pipeline
├── services/
│   └── email_service.py
```

## TEST REPORTS
| Iteration | Result | Focus |
|-----------|--------|-------|
| 33 | 16/16 | Enrollment, course mgmt |
| 34 | 15/15 | Email, participants/staff pages |
| 35 | 13/13 | Lesson generation, content merge |
| 36 | 31/31 | Avatar orchestrator, HeyGen, research fix |

**Last Updated:** May 5, 2026
