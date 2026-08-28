# TradeSentinel — Test Credentials

Auth: JWT (httpOnly cookies + Bearer token). Base: `${REACT_APP_BACKEND_URL}/api`

## Accounts
| Role | Email | Password |
|------|-------|----------|
| Admin (owner) | kaniksha20suresh@gmail.com | Admin@123 |
| Admin | admin@tradesentinel.demo | Admin@123 |
| Manager | manager@tradesentinel.demo | Manager@123 |
| Viewer | viewer@tradesentinel.demo | Viewer@123 |

## Auth endpoints
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- GET  /api/auth/me
- POST /api/auth/refresh
- POST /api/auth/forgot-password
- POST /api/auth/reset-password

## Role permissions
- admin: everything incl. /api/admin/* (users, audit logs, analytics)
- manager: shipment CRUD, CSV import, recovery approve/reject/modify, compliance upload, classify events, integrations toggle
- viewer: read-only (cannot mutate operational data)
