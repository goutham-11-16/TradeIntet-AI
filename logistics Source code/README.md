# TradeSentinel

**AI-Powered Cross-Border Logistics Resilience Platform**
_Predict Disruptions. Protect Trade. Recover Smarter._

TradeSentinel helps e-commerce & logistics teams detect international logistics disruptions,
predict impact, identify affected shipments, simulate scenarios, optimize routes, and
recommend explainable recovery actions — with a human always in the loop.

## Tech Stack
- **Frontend:** React 19, React Router 7, Tailwind CSS, shadcn/ui, Recharts, React-Leaflet, TanStack Query
- **Backend:** FastAPI, Embedded VectorDB Engine (`vectordb.py`), PyJWT, bcrypt
- **Database:** VectorDB (Persistent SQLite Store with 128-dim Dense Semantic Embeddings & Cosine Search)
- **AI/ML:** Deterministic statistical engines (`ml.py`) on seeded historical data + LLM layer
  (`llm.py`, Claude Sonnet via Emergent Universal Key) for NLP event classification, recovery
  recommendations, customer notification drafting, and autonomous workflow parsing.

## Architecture
```
backend/
  server.py       FastAPI app + all /api routers
  vectordb.py     Embedded persistent VectorDB engine (cosine similarity + SQLite WAL)
  seed_vectordb.py Vector database initializer & semantic embedding seeder
  auth.py         JWT (access/refresh cookies + bearer), bcrypt, RBAC
  ml.py           Risk scoring, customs & ETA prediction, route optimization,
                  impact/cascade analysis, simulation, financial impact, root-cause
  llm.py          NLP classification, recovery recommendations, customer messages
  automation/     PS4 AI Copilot (NL parser, DSL schema, conflict engine, simulator, executor)
frontend/
  src/pages/      Landing, auth, Dashboard, Shipments(+detail), Risk, Customs,
                  Geopolitical, Impact, Simulator, Routes, Recovery, Compliance,
                  Analytics, Reports, Alerts, Integrations, Settings, AutomationCopilot,
                  WorkflowStudio, ConflictCenter, AutomationInsights
  src/components/ DashboardLayout, WorldMap, common (badges/states), ProtectedRoute
  src/lib/api.js  Central API client
  src/context/AuthContext.jsx
```

## Setup
Services run under supervisor (backend :8001, frontend :3000). VectorDB auto-seeds on startup.
- Backend deps: `pip install -r backend/requirements.txt`
- Frontend deps: `cd frontend && yarn install`
- Restart: `sudo supervisorctl restart backend frontend`

## Demo Accounts
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@tradesentinel.demo | Admin@123 |
| Manager | manager@tradesentinel.demo | Manager@123 |
| Viewer | viewer@tradesentinel.demo | Viewer@123 |

## Roles (RBAC)
- **Admin** — user/role management, audit logs, system analytics, everything.
- **Manager** — shipment CRUD, CSV import, run predictions/simulations, approve/reject/modify recovery, compliance upload, classify events.
- **Viewer** — read-only (cannot mutate operational data).

## Key API Endpoints (prefix `/api`)
- Auth: `POST /auth/register|login|logout|refresh|forgot-password|reset-password`, `GET /auth/me`
- Shipments: `GET/POST /shipments`, `GET/PUT/DELETE /shipments/{id}`, `GET /shipments/export/csv`, `POST /shipments/import/csv`
- Dashboard/Analytics: `GET /dashboard/overview`, `GET /analytics/overview`
- Risk/Predictions: `GET /risks`, `POST /risks/analyze`, `POST /predictions/customs|eta`, `GET /predictions/performance`
- Geo/Impact/Sim/Routes: `GET /geopolitical/events`, `POST /geopolitical/classify`, `POST /impact/analyze`, `POST /simulation/run`, `POST /routes/optimize`, `POST /financial/impact`
- Recovery: `GET /recovery/recommendations`, `POST /recovery/generate`, `POST /recovery/{id}/approve|reject|modify`, `GET /approvals`
- Alerts/Compliance/Reports/Integrations/Settings/Admin — see `server.py`.

## Notes & Limitations
- Predictions are **estimates with confidence scores, not guarantees**.
- Compliance module is a **risk-screening / document-assistance** feature, not legal certification.
- Integrations are **mock adapters**; connect real credentials to enable live sync.
- Customer notifications require manager approval before sending (no auto-send).

## Future Improvements
Replace statistical engines with trained ML models (same interface), connect live carrier/customs/news feeds, real email/SMS delivery, PDF report export.
