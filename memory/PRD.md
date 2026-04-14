# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform

**Version:** 3.5 (Iteration 26 Complete)
**Date:** April 14, 2026

---

## LATEST UPDATES - ITERATION 26

### AI Training Intelligence Engine (NEW)
| Feature | Status |
|---------|--------|
| Q&A Generation from content (Basic/Intermediate/Advanced/Scenario/MCQ) | DONE |
| Flashcard generation with front/back/category | DONE |
| Exam Simulation generation (MCQ, Short Answer, Scenario sections) | DONE |
| Generation history tracking | DONE |
| Content upload via /api/content/upload-source (.pdf, .docx, .txt, .pptx) | DONE |
| Key Takeaways and Knowledge Gaps detection | DONE |
| Export questions to Markdown | DONE |
| Voice input for content entry | DONE |
| Interactive MCQ with instant feedback | DONE |
| Flashcard flip UI with navigation | DONE |

### Bug Fixes (Iteration 25-26)
| Fix | Status |
|-----|--------|
| Custom course "body stream already read" - switched fetch to axios | DONE |
| Custom course 502 timeout - disabled litellm retries | DONE |
| .docx upload failing - created /api/content/upload-source endpoint | DONE |
| Voice input missing on LearnByTeachingPage, HomePage | DONE |
| Dashboard KeyError profile['id'] (19 locations) | DONE |
| AI Grading Knowledge Graph sync | DONE |
| Social URL Analysis (LinkedIn + company + GitHub + Twitter) | DONE |

---

## TECH STACK

- **Frontend:** React, Tailwind CSS, Shadcn UI
- **Backend:** FastAPI, Pydantic
- **Database:** MongoDB
- **AI:** Emergent LLM Key (GPT-5.2)
- **Email:** Resend
- **Payments:** Paynow
- **Auth:** JWT, Google OAuth via Emergent
- **PDF:** ReportLab, PyPDF2
- **Docs:** python-docx
- **LinkedIn/Social:** Proxycurl API + AI Fallback

---

## KEY API ENDPOINTS

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/training-engine/generate-questions` | POST | Generate structured Q&A from content |
| `/api/training-engine/generate-flashcards` | POST | Generate flashcards from content |
| `/api/training-engine/generate-exam` | POST | Generate exam simulation |
| `/api/training-engine/history` | GET | Get generation history |
| `/api/content/upload-source` | POST | Upload & extract text from docs |
| `/api/courses/generate-custom` | POST | Generate custom course |
| `/api/dashboard/stats` | GET | Dashboard stats |
| `/api/mentor/analyze-social-url` | POST | Analyze social media URLs |
| `/api/achievements` | GET | User achievements |

---

## REMAINING TASKS (Backlog)

### P0 - Critical
- [ ] Refactor server.py monolith (~11,500 lines) into modular FastAPI routers

### P1 - High Priority
- [ ] Certificate visual verification (visual render confirmation)
- [ ] Org Admin Staff Rights Verification

### P2 - Medium Priority
- [ ] Mobile responsiveness improvements

---

## FILE STRUCTURE

```
/app/
├── backend/
│   ├── server.py                    # Main API (~11,500 lines)
│   └── services/
│       ├── linkedin_service.py      # Enhanced social URL analysis
│       └── ...
├── frontend/
│   ├── src/
│   │   ├── hooks/
│   │   │   └── useVoiceInput.js     # Shared voice recording hook
│   │   ├── pages/
│   │   │   ├── AITrainingEnginePage.js  # NEW - Q&A/Flashcards/Exam generator
│   │   │   ├── CreateCustomCoursePage.js # Fixed - uses axios
│   │   │   ├── QuestionAnalysisPage.js  # Voice input added
│   │   │   ├── LearnByTeachingPage.js   # Voice input added
│   │   │   ├── HomePage.js              # Voice recording fixed
│   │   │   └── AIMentorPage.js          # Social URL analysis
│   │   └── services/
│   │       └── api.js
└── memory/
    ├── PRD.md
    └── test_credentials.md
```

---

## TEST CREDENTIALS

| Role | Email | Password |
|------|-------|----------|
| Student | demo.student@cognify.edu | demo123 |
| Teacher | demo.teacher@eduos.edu | demo123 |
| Org Admin | test.orgadmin@cognify.edu | admin123 |

**Last Updated:** April 14, 2026
