# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform with HeyGen Avatar Integration

**Version:** 9.0 (Iteration 38 Complete)
**Date:** May 6, 2026

---

## LATEST - ITERATION 38

### Critical Fix: Backend Crash (Import Error)
- All `from .services.*` relative imports in server.py caused `ImportError: attempted relative import with no known parent package`
- Fixed ALL relative imports across server.py, routes/, database.py, auth_utils.py to use absolute imports
- Backend was completely down — now restored

### Premade Courses (Document Library) - NEW
| Feature | Status |
|---------|--------|
| Upload documents (PDF, DOCX, TXT, PPTX) up to 50MB | DONE |
| Browse documents with search and category filter | DONE |
| Download documents with counter | DONE |
| Preview document content (extracted text) | DONE |
| Delete by uploader or admin | DONE |
| Sidebar link for all roles | DONE |
| Category system (Science, Math, Tech, Business, etc.) | DONE |

### Bug Fixes (Production Issues)
| Fix | Status |
|-----|--------|
| Backend import crash (relative imports) | DONE |
| Avatar video default avatar ID not in user's HeyGen account | DONE |
| Research search frontend sending query as URL param instead of JSON body | DONE |
| Teacher messaging endpoint restricted to teacher/admin (missing org_admin) | DONE |
| Share content using fetch instead of axios, wrong endpoint | DONE |
| Certificates share endpoint using wrong collection | DONE |
| Teacher messaging route missing org_admin in allowedRoles | DONE |

---

## TEST REPORTS
| Iteration | Result | Focus |
|-----------|--------|-------|
| 33-34 | ALL PASS | Enrollment, course mgmt, participants |
| 35-36 | ALL PASS | Lessons, avatar orchestrator |
| 37 | 16/16 | Bug fixes (HeyGen, research, messaging, share) |
| 38 | Manual | Import fix, premade courses |

**Last Updated:** May 6, 2026
