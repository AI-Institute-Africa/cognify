# Cognify - Product Requirements Document

## Overview
AI-Powered School Management, Learning & Career Intelligence Platform with HeyGen Avatar Integration, async AI Video/Slides generation, multi-tenant org isolation, and now Course Analytics.

**Version:** 11.0 (Iteration 40)
**Date:** May 12, 2026

---

## LATEST - ITERATION 40

### Course Analytics Dashboard (P0)
- New page: `/course-analytics` accessible to teacher, admin, org_admin
- New endpoint: `GET /api/analytics/course-dashboard`
  - Role-aware scoping: org_admin/admin see all org courses; teacher sees only their own
  - Returns: `summary`, `per_course[]`, `at_risk[]`, `top_students[]`, `engagement_trend[14]`
- Dashboard UI (`CourseAnalyticsDashboardPage.js`):
  - 7 summary stat cards (Courses, Enrolled, Completion %, At-Risk, Avg Grade, Pass Rate, Active Students)
  - Engagement Trend line chart (Quiz attempts vs passes, last 14 days)
  - Course Completion donut
  - Per-course performance table (click row to filter, badges for grade tiers)
  - Avg Grade by Course bar chart
  - At-Risk students panel with risk reasons + Email CTA
  - Top Performers panel
- Sidebar entries added for teacher / admin / org_admin

### Send Message Verification
- TeacherMessagingPage E2E flow verified (PASS): org_admin -> student round-trip through `/api/messages` + `/api/messages/conversation/{user_id}`

### Bug fixed during iteration 40
- `/api/analytics/course-dashboard` 500 for teacher role: max() compared a `datetime` (users.last_login) with isoformat strings (quiz_results.completed_at). Normalized via `_to_str` helper.

---

## ARCHITECTURE
```
/app/backend/
├── server.py (~13,000 lines)
├── routes/
│   ├── certificates.py
│   └── avatar_orchestrator.py (HeyGen + AI pipeline)
├── services/
└── tests/
    └── test_iteration37_course_analytics_messaging.py

/app/frontend/src/pages/
└── CourseAnalyticsDashboardPage.js (new)
```

## KEY ENDPOINTS
- `GET /api/analytics/course-dashboard` — Role-scoped analytics
- `POST /api/messages` + `GET /api/messages/conversation/{user_id}` — DM flow
- `POST /api/content/generate-video` (Sora 2 async) + `/video-status/{task_id}`
- `POST /api/content/generate-slides` (Gemini async) + `/slides-status/{task_id}`
- `POST /api/avatar-orchestrator/generate-video` (HeyGen)

## NEXT / BACKLOG
- P1: Refactor `server.py` (~13k lines) into `/app/backend/routes/`
- P1: Seed enrollments + quiz_results for the demo org so the analytics dashboard shows non-zero data
- P2: Add data-testid coverage on TeacherMessagingPage for stable future E2E
- P2: Migrate TeacherMessagingPage from `fetch` to `axios` (consistency)
- P2: Add CSV export from Course Analytics Dashboard

**Last Updated:** May 12, 2026
