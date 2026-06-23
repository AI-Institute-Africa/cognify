# Test Credentials

## Default Users
| Role | Email | Password |
|------|-------|----------|
| Student | demo.student@cognify.edu | demo123 |
| Teacher | demo.teacher@eduos.edu | demo123 |
| Org Admin | test.orgadmin@cognify.edu | admin123 |
| Super Admin | takuechakanyuka@gmail.com | SuperAdmin@2026! |

## Organization
- **Name:** Cognify University
- **Slug:** cognify
- **Portal URL:** /org/cognify

## Bulk Enrolled Test Users
| Email | Temp Password | Role | Status |
|-------|--------------|------|--------|
| testbulk1@example.com | (auto-generated) | student | approved |
| testbulk2@example.com | (auto-generated) | student | approved |

## Auth Details
- Token field: `access_token`
- Token type: Bearer
- Login endpoint: POST /api/auth/login
- Super Admin redirects from `/dashboard` to `/super-admin` automatically
- Soft-deleted users (`is_active=false`) are blocked at login with HTTP 403
