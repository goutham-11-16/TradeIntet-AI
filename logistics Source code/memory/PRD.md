# TradeSentinel — PRD

## Original Problem Statement
Build TradeSentinel — an AI-Powered Cross-Border Logistics Resilience Platform (enterprise SaaS).
Predict Disruptions. Protect Trade. Recover Smarter. Full functional app (not a mockup): auth+RBAC,
dashboard, shipment management, risk/customs/geopolitical intelligence, impact & cascade analysis,
what-if simulator, route optimizer, recovery (human-in-the-loop), compliance, analytics, reports,
alerts, integrations, settings, landing page.

## Architecture
- React 19 + Tailwind + shadcn/ui + Recharts + React-Leaflet (frontend, routes under /app/*)
- FastAPI + Embedded Persistent VectorDB (`vectordb.py` with dense semantic vectors & SQLite WAL, all routes /api)
- Auth: JWT access/refresh (httpOnly cookies + Bearer fallback), bcrypt, RBAC (admin/manager/viewer)
- AI/ML: statistical engines (ml.py) on seeded data + Claude LLM (llm.py via EMERGENT_LLM_KEY) with template fallbacks + PS4 AI Automation Copilot (automation/)

## User Personas
- Admin: manages users/roles, views audit logs & system analytics
- Logistics Manager: shipment CRUD, predictions, simulations, approves recovery plans
- Viewer: read-only dashboards, shipments, risks, reports

## Core Requirements (static)
RBAC auth; dashboard KPIs+risk+map+feed+prediction; shipment CRUD+CSV; customs & ETA prediction with
confidence; geopolitical NLP monitor; impact+cascade; what-if simulator+comparison+financial; route
optimizer; recovery approve/reject/modify with audit; compliance screening; analytics; reports+CSV;
alerts; integrations (mock); settings; landing page. Predictions labeled estimates, not guarantees.

## Implemented (2026-08-10) — MVP COMPLETE, tested 100% backend + 100% frontend
- Auth (register/login/logout/refresh/forgot/reset), RBAC enforced (403 for unauthorized)
- Executive dashboard: 8 KPIs, 6 risk gauges, global Leaflet map, live disruption feed, ETA chart
- Shipments: 126 seeded, CRUD, search/filter/sort, CSV import+export, detail (timeline, ETA best/likely/worst,
  risk breakdown, root cause, AI recovery gen, customer message draft)
- Customs delay prediction, geopolitical events + NLP classifier
- Impact analysis + cascade chain, what-if simulator + A–D comparison + financial impact
- Route optimizer (weighted scoring, 5 priorities), carrier intelligence
- Recovery center (human-in-the-loop), compliance upload screening, analytics (6 charts), reports (6 types + CSV),
  alerts (read/archive/filter), integrations (mock toggle), settings (profile/prefs/admin users/audit logs)
- Landing page, light/dark theme
- Demo accounts seeded; README + .env.example written

## Backlog / Remaining
- P1: Gate `debug_token` in forgot-password behind DEMO/DEBUG env flag before production
- P1: PDF export for reports (currently CSV only)
- P2: Continuous-learning retraining UI (data model + predictions collection already seeded)
- P2: Real integration adapters (currently mock), real email/SMS delivery for customer notifications
- P2: Harden login lockout to sliding window with absolute ceiling

## Next Tasks
Address P1 items if user requests production hardening; otherwise gather feedback on the demo.
