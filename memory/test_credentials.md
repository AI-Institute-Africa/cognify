# Test Credentials

## Active Production Accounts
| Role | Email | Password |
|------|-------|----------|
| Super Admin | takuechakanyuka@gmail.com | SuperAdmin@2026! |

## Demo Accounts Removed
All `demo.*`, `test.*`, and `@example.com` accounts have been wiped by the Super Admin "Wipe demo data" action (June 23, 2026). To recreate any test user, register normally through `/register`.

## Auth Details
- Token field: `access_token`
- Token type: Bearer
- Login endpoint: POST /api/auth/login
- Soft-deleted users (`is_active=false`) are blocked at login with HTTP 403
- Super admin redirects from `/dashboard` → `/super-admin`
