# Internal Hackathon — Platform Monorepo

An **explainable farmer-support radar**: it detects when a farmer may need help early,
explains *why* in their own language, sends a safe advisory, and routes the case to a
human agriculture officer who closes the loop.

> Product name is **not finalised**. All code and docs refer to "the platform".

## Two decisions that define this system

1. **Push, not pull.** A farmer will never open our site. The daily cycle reaches *out* —
   WhatsApp message first, then an explicitly approved call provider when opted in. See
   [Module 9](design/module_9_outreach_automation.md).
2. **ML perceives, rules decide.** ML where it has ground truth (satellite crop stress, price
   forecasting); a deterministic index for the decision to contact a person.
   Evidence: [research_risk_modelling.md](design/research_risk_modelling.md).

## Design docs

Start with [`design/masterspecv1.md`](design/masterspecv1.md), then
[`design/module_0_architecture_overview.md`](design/module_0_architecture_overview.md)
(module map, shared contracts, cross-module decisions). Each module has its own spec.
Deployment variables and the Supabase/Vercel/Render handoff are recorded in
[`design/deployment_configuration.md`](design/deployment_configuration.md).

The Vercel portal is a single role-aware deployment: a farmer session renders
the farmer PWA, while a Supabase user with `extension_officer`,
`district_admin`, `admin`, or `auditor` in `app_metadata.role` renders the
officer workspace in the same build. No `VITE_OFFICER_APP_URL` or second
frontend deployment is required.

## Module map

| # | Module | Location | Spec |
|---|---|---|---|
| 1 | Platform Core & Data Layer | `services/backend` | [spec](design/module_1_platform_core.md) |
| 2 | Identity, Consent & Privacy | `libs/identity-consent` | [spec](design/module_2_identity_consent_privacy.md) |
| 3 | Ingestion & Government Adapters | `libs/adapters` | [spec](design/module_3_ingestion_adapters.md) |
| 4 | Explainable Scoring Engine | `services/scoring-engine` | [spec](design/module_4_scoring_engine.md) |
| 5 | Case Management & Officer Workflow | `services/case-workflow` | [spec](design/module_5_case_workflow.md) |
| 6 | Notification & Delivery | `services/notification` | [spec](design/module_6_notification_delivery.md) |
| 7 | AI & Agentic Copilot | `services/ai-copilot` | [spec](design/module_7_ai_copilot.md) |
| 8 | Frontend Apps | `apps/*`, `packages/ui-kit` | [spec](design/module_8_frontend_apps.md) |
| 9 | Outreach Automation & Channels | `services/outreach` | [spec](design/module_9_outreach_automation.md) |

## Runtime architecture rule

**`services/backend` is the only FastAPI composition root.** It owns the API gateway,
SQLAlchemy/Alembic database boundary, Supabase JWT verification, consent enforcement,
orchestration, case workflow, notifications, and background workers. The pure packages remain
isolated: `libs/adapters` produces transport DTOs, `services/scoring-engine` computes FDI v2
without I/O, and `services/ai-copilot` produces draft-only cited briefs. The former
`services/platform-core` app is retained as contract/reference material during migration and
its runtime entrypoint is retired and must not be started as a second server. See [ADR-001](design/adr_001_unified_backend.md).

The backend's canonical HTTP contracts live in `services/backend/app/schemas/`; pure module
contracts live in their owning packages. Never create another server or duplicate scoring rules
inside an endpoint.

The bounded farmer conversation agent is exposed at `POST /api/v1/copilot/chat`.
Sarvam is the approved live conversation/STT/TTS provider; Bhashini is no
longer used by the runtime. Sarvam is enabled only server-side with
`LLM_PROVIDER=sarvam`, `LLM_EXTERNAL_ALLOWED=true`, and `SARVAM_API_KEY` in an
ignored backend environment file or deployment secret store. Never put that key
in a `VITE_*` variable or browser bundle. Outbound farmer outreach uses
WhatsApp by default; WhatsApp calling is an optional provider bridge and must
not be reported as placed unless an approved Meta/telephony partner confirms it.

```
Observation → M3 produces, M4 consumes
RiskEvent   → M4 produces, M5/M6/M7/M8 consume
AlertCase   → M5 produces, M6/M7/M8 consume
DeliveryAttempt → M6 produces, M5/M7/M8 read
CopilotBrief    → M7 produces, M8 consumes
OutreachDecision / InboundEvent → M9 produces
AuthContext / ConsentContext → M2 issues, everyone honours
```

## Quick start

```bash
# Python services (3.11+)
python3 -m venv .venv
make PYTHON=.venv/bin/python install

# Frontend (Node 20+)
npm install
npm run dev --workspace apps/farmer-pwa

# Apply Supabase/Postgres migrations (copy .env.local.example first)
cd services/backend
alembic upgrade head

# Render/container deployment (Docker context is internal_hackathon)
docker build -f infra/docker/backend.Dockerfile .
```

### Getting the backend URL

Create a Render **Web Service** from the GitHub repository. Set the root
directory to `internal_hackathon`, Dockerfile path to
`infra/docker/backend.Dockerfile`, and health check path to `/healthz`. Render
will provide an HTTPS `*.onrender.com` URL after the first successful deploy;
that is the value for `VITE_API_BASE_URL`. Add backend secrets in Render's
environment settings, not Vercel. The Docker command applies `alembic upgrade
head` before serving traffic, then honors Render's `PORT` variable and falls
back to port `8000` locally. A deployment with a schema migration failure fails
health checks instead of serving an API whose models are ahead of Supabase.

## Layout

```
apps/        farmer-pwa, officer-dashboard          (M8)
packages/    ui-kit                                  (M8)
services/    backend, platform-core, scoring-engine, (M1, M4, M5,
             case-workflow, notification, ai-copilot, M6, M7, M9)
             outreach
libs/        identity-consent, adapters              (M2, M3)
fixtures/    90-day replay datasets + scenarios      (M3)
infra/       docker, CI/CD
design/      specs (source of truth)
```
