<div align="center">

<img src="../docs/assets/kisansetu-hero.png" alt="KisanSetu — explainable support for smallholder farmers" width="100%" />

# KisanSetu · Internal Hackathon

**Sense the signal. Explain the need. Close the loop with a human.**

[![Status](https://img.shields.io/badge/status-internal%20hackathon%20prototype-2563EB?style=flat-square)](design/implementation_status_verified.md)
[![Decision record](https://img.shields.io/badge/architecture-ADR--001%20unified%20backend-0F766E?style=flat-square)](design/adr_001_unified_backend.md)
[![Scoring](https://img.shields.io/badge/scoring-FDI%20v2-7C3AED?style=flat-square)](design/signal_model_fdi_aligned.md)
[![API](https://img.shields.io/badge/API-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](services/backend/)
[![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20TypeScript-61DAFB?style=flat-square&logo=react&logoColor=111827)](apps/)
[![Data](https://img.shields.io/badge/data-Supabase%20%2B%20PostGIS-3ECF8E?style=flat-square&logo=supabase&logoColor=111827)](design/deployment_configuration.md)

<br />

### [Live preview](https://sih-2026-works-in-production.vercel.app/)

</div>

> **Scope and provenance.** This is the implementation home for the institute’s SIH 2026 PS-02 concept, not a claim that the problem statement is an official national SIH release. Reconcile the final wording and PS identifier with the SIH SPOC before submission.

> **Implementation truth.** The repository contains a runnable prototype, replay fixtures and production-shaped boundaries. External credentials, government approvals, field validation, clinical/agronomic sign-off and provider accounts are intentionally environment-gated. Read the [known limitations](#known-limitations-before-production) before treating any integration as live.

## Contents

- [Product thesis](#product-thesis)
- [System at a glance](#system-at-a-glance)
- [Architecture](#architecture)
- [FDI v2 scoring engine](#fdi-v2-scoring-engine)
- [Data contracts and persistence](#data-contracts-and-persistence)
- [Backend and API](#backend-and-api)
- [Identity, consent and privacy](#identity-consent-and-privacy)
- [Frontends](#frontends)
- [Adapters, live data and the copilot](#adapters-live-data-and-the-copilot)
- [Background work and outreach](#background-work-and-outreach)
- [Deployment topology](#deployment-topology)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Verification](#verification)
- [Repository map](#repository-map)
- [Known limitations before production](#known-limitations-before-production)
- [Design references](#design-references)

## Product thesis

KisanSetu is an **explainable farmer-support radar**, not a generic crop chatbot and not a credit, insurance or default score. It helps a smallholder farmer receive a useful, local-language next step earlier, while giving an extension officer a ranked queue that can be acknowledged, routed and closed.

The core loop is deliberately small:

| Stage | What happens | Evidence shown to a user |
| --- | --- | --- |
| **Sense** | Weather, market, crop, soil, scheme-access, farmer-report and opt-in timing signals are normalised through canonical adapters. | Source, observation time, freshness/TTL and quality flags. |
| **Score** | The pure FDI v2 engine combines shocks with farmer/field vulnerability. | Score, band, confidence, expiry and top drivers. |
| **Act** | A reviewed action card is delivered through the farmer PWA and approved contact channels. | Source-linked advice; no free-form pesticide or financial instruction. |
| **Close** | A human officer acknowledges, visits/refers, resolves or reopens the case. | SLA timer, case history, resolution code and audit event. |

The design intentionally favours a **thin, replayable end-to-end slice** over a technology-first demo. A judge should be able to move from a rainfall shock and market crash to a red event, see why it is red, see the source freshness, watch the officer hand-off and inspect the audit trail.

## System at a glance

~~~mermaid
flowchart LR
  sources["Weather · mandi · crop · soil · schemes\nfarmer reports · opt-in due window"] --> sense["Sense\ncanonical adapters"]
  sense --> score["Score\nFDI v2 deterministic engine"]
  score --> event["RiskEvent\nscore · band · confidence · drivers"]
  event --> act["Act\nreviewed cards + approved channels"]
  act --> farmer["Farmer\nmobile PWA"]
  event --> officer["Officer\nqueue + district view"]
  officer --> close["Close\nacknowledge → visited/referred → resolved"]
  close --> feedback["Outcome + audit\ncalibration evidence"]
  feedback -.-> score
~~~

### What is implemented versus proposed

The current checkout includes the unified FastAPI composition root, FDI v2 scorer, replay/mock adapters, consent and case boundaries, farmer/officer frontends, Sarvam speech/chat wiring and deployment manifests. Real government feeds, telecom/WhatsApp approvals, field outcomes, production-scale observability and formal user studies remain environment or pilot work. The machine-readable progress log is [tasks.md](../tasks.md); the verified review is [implementation_status_verified.md](design/implementation_status_verified.md).

## Architecture

### Runtime topology

~~~mermaid
flowchart LR
  farmer["Farmer PWA"] --> vercel["Vercel\nrole-aware frontend"]
  officer["Officer workspace"] --> vercel
  vercel -->|"Bearer Supabase JWT"| api["services/backend\nFastAPI composition root"]
  api --> auth["Auth + consent + audit"]
  api --> orchestration["Workflow orchestration"]
  orchestration --> adapters["libs/adapters\nmock · real · replay"]
  orchestration --> scorer["services/scoring-engine\npure FDI v2"]
  orchestration --> copilot["services/ai-copilot\ncited + guarded"]
  api --> db[("Supabase Postgres\nPostGIS + Alembic")]
  worker["Render worker\npython -m app.worker"] --> api
  worker --> db
  api --> providers["Sarvam · WhatsApp · SMTP\nserver-side only"]
~~~

### Sense → score → act → close

~~~mermaid
flowchart LR
  sources["IMD · Agmarknet · Sentinel-2 · MSP · soil\nfarmer reports / due window"] --> adapters["Canonical adapters\nquality · TTL · provenance"]
  adapters --> observations["Observation store"]
  observations --> score["FDI v2 scorer"]
  score --> event["RiskEvent\nscore · band · confidence · expiry"]
  event --> workflow["Deduplication + hysteresis\ncase workflow"]
  workflow --> case["AlertCase\nnew → acknowledged → visited/referred → resolved"]
  workflow --> outbox["Outbox / outreach policy"]
  outbox --> farmer["Farmer PWA · approved channels"]
  case --> officer["Officer queue + district analytics"]
  event --> copilot["Sarvam/template copilot\nread-only draft + citations"]
~~~

### Trust boundary and data protection

~~~mermaid
flowchart TB
  browser["Browser\npublic Supabase URL + anon key only"] --> jwt["Supabase Auth JWT"]
  jwt --> claims["app_metadata.role + district_id"]
  claims --> guards["RBAC + ownership + consent guards"]
  guards --> sensitive["Farmer · risk · case APIs"]
  sensitive --> audit["Audit events + request IDs"]
  secrets["Render secret store\nDB URL · service key · vault key · provider keys"] --> backend["Backend / worker"]
  backend --> db[("Postgres + vault fields")]
~~~

### Deployment topology

~~~mermaid
flowchart LR
  gh["GitHub main"] --> vercel["Vercel\nfarmer + officer static apps"]
  gh --> renderweb["Render web\nDocker FastAPI"]
  gh --> renderworker["Render worker\nscheduler"]
  renderweb --> supa["Supabase\nAuth + Postgres/PostGIS"]
  renderworker --> supa
  renderweb --> sarvam["Sarvam"]
  renderweb --> meta["WhatsApp Cloud / approved call provider"]
  renderworker --> smtp["SMTP digest"]
~~~

The editable Mermaid sources for these diagrams live in [design/diagrams](design/diagrams): [runtime topology](design/diagrams/runtime-topology.mmd), [sense-score-act-close](design/diagrams/sense-score-act-close.mmd), [trust boundary](design/diagrams/trust-boundary.mmd) and [deployment topology](design/diagrams/deployment-topology.mmd).

### One backend, explicit boundaries

[services/backend](services/backend) is the only runtime composition root. This resolves the earlier duplicate backend versus platform-core design:

| Boundary | Responsibility | Rule |
| --- | --- | --- |
| services/backend | HTTP gateway, auth, consent, orchestration, persistence, cases, outbox, notifications and worker entrypoint. | The only service that assembles dependencies and talks to the database. |
| libs/adapters | Weather, market, crop, satellite, soil, MSP, Bhuvan, language and notification source/provider interfaces. | Adapters return canonical records with provenance and freshness; they do not decide risk. |
| services/scoring-engine | Pure FDI v2 scoring. | No network, database, clock or provider calls. Same input gives same output. |
| services/ai-copilot | Template-first/cited explanation and conversational boundary. | It can explain and retrieve; it cannot change a score or autonomously dispatch a case. |
| services/platform-core | Historical/reference material retained for migration context. | Not a second deployable API. |

The full decision record is [adr_001_unified_backend.md](design/adr_001_unified_backend.md).

## FDI v2 scoring engine

The scorer is a deterministic implementation of the CRIDA-aligned Farmer Distress Index design. It separates **shock** from **vulnerability**:

~~~text
final_score = clamp(shock_score × vulnerability_multiplier, 0, 100)
~~~

Bands are aligned to the design instrument: **Green < 50**, **Amber 50–69**, **Red ≥ 70**. Equal weighting is used within dimensions to make the explanation stable and auditable. D7 (socio-psychological assessment) is deliberately not inferred from telemetry; S15 remains a non-scored outreach context flag.

### Fifteen signals

| Group | Signals | Meaning |
| --- | --- | --- |
| **Shock** | S1 rainfall deficit, S2 rainfall excess/flood, S3 satellite crop stress, S4 pest/disease pressure, S5 opt-in repayment window, S13 price shock/below MSP, S14 acute farmer report | Immediate external or self-reported stressors. Shock weights total 100. |
| **Vulnerability multiplier** | S6 scheme coverage gap, S7 institutional access, S8 land holding, S9 irrigation, S10 crop growth-stage sensitivity, S11 crop diversification, S12 soil retention | Factors that change how strongly a shock affects this farm. Multiplier is bounded by the design. |
| **Context only** | S15 engagement/withdrawal | Unanswered outreach or opt-out context for an officer; never shown as a psychological score. |

Every RiskEvent carries the score version, signal contributors, data freshness, confidence, creation time and expiry. Missing or stale critical data lowers confidence and suppresses escalation rather than fabricating a red event. The scorer is implemented in services/scoring-engine/scoring_engine/engine.py, with the normative model in [signal_model_fdi_aligned.md](design/signal_model_fdi_aligned.md).

## Data contracts and persistence

Canonical records cross the system through typed schemas. The important contracts are:

| Contract | Purpose | Privacy rule |
| --- | --- | --- |
| FarmerProfile | Tokenised farmer, village, locale, crop, sowing date, area band, irrigation and consent flags. | No Aadhaar, bank, lender or raw account identifiers in the MVP. |
| Observation | Source, observed time, village/plot grid, metric, value, unit, quality and TTL. | Retain only the precision required for the workflow. |
| MarketQuote | Commodity, mandi, date, modal price, arrivals, source and quality. | Public market data is still provenance-labelled. |
| RiskEvent | Score, band, confidence, contributors, action IDs, model version, creation and expiry. | Explainable event; not a credit/insurance decision. |
| AlertCase | Event, owner role, status, SLA deadline, resolution code and history. | Exact farmer details are role- and consent-gated. |
| OutboxMessage | Idempotency key, channel, provider status, retries, delivery receipt and dead-letter state. | Contact is only attempted for the relevant consent purpose. |
| AuditEvent | Actor, request ID, action, purpose, resource and timestamp. | Redacted payload; immutable retention policy. |

Supabase Postgres/PostGIS is the production database. SQLite is retained for local fixture/replay mode. Alembic migrations live under services/backend/alembic/versions/ and cover the initial schema, PostGIS/audit/consent, case SLA, outbox, unified backend contracts, farmer-auth binding and farmer email channel.

## Backend and API

The FastAPI app is under [services/backend/app](services/backend/app). All sensitive routes require a verified Supabase JWT, role/ownership checks and the relevant consent purpose. Request IDs are propagated into logs and audit events.

### Public health and readiness

| Method | Path | Use |
| --- | --- | --- |
| GET | /health, /healthz | Liveness. |
| GET | /readyz | Readiness including configured dependencies. |
| GET | /api/v1/ingestion/health | Adapter/source health summary. |

### Farmer profile, observations and risk

| Method | Path | Use |
| --- | --- | --- |
| GET / POST | /api/v1/farmer-profiles/me | Read or create the authenticated farmer profile. |
| POST | /api/v1/observations | Submit a farmer/field observation. |
| GET | /api/v1/risk-events | List consent-allowed events for the current farmer or officer scope. |
| POST | /api/v1/risk-events/recalculate | Recalculate from the current canonical inputs. |
| GET | /api/v1/mandis/compare | Compare current market quotes with the configured baseline. |
| POST | /api/v1/replay/scenario | Run a deterministic demo/replay scenario. |

### Officer cases and analytics

| Method | Path | Use |
| --- | --- | --- |
| GET | /api/v1/cases | Officer queue, filtered by allowed district/village scope. |
| POST | /api/v1/cases/{case_id}/acknowledge | Start the case SLA. |
| POST | /api/v1/cases/{case_id}/transition | Move through the allowed state machine. |
| POST | /api/v1/cases/{case_id}/resolve | Resolve with a fixed resolution code. |
| POST | /api/v1/cases/{case_id}/reopen | Reopen under the policy and append history. |
| GET | /api/v1/cases/{case_id}/history | Read the immutable case timeline. |
| POST | /api/v1/cases/sla/scan | Scan overdue cases and enqueue escalation. |
| GET | /api/v1/analytics/district | Cohort-safe district metrics for officers/admins. |

### Copilot and speech

| Method | Path | Use |
| --- | --- | --- |
| POST | /api/v1/copilot/brief | Cited, read-only explanation for a risk event/case. |
| POST | /api/v1/copilot/chat | Context-bounded conversational answer. |
| GET | /api/v1/copilot/speech/health | Provider/configuration health. |
| POST | /api/v1/copilot/speech/transcribe | Browser audio → transcript. |
| POST | /api/v1/copilot/speech/synthesize | Text → audio for user-gesture playback. |

Sarvam is the current live conversational/STT/TTS provider when configured. Bhashini-compatible adapters remain available for language-source interoperability, but the conversation path is not dependent on Bhashini. The copilot is template-first and citation-aware; it is not allowed to invent a signal, prescribe pesticide dosage, expose protected data or dispatch outreach.

### Consent, notification, ingestion and outreach

| Method | Path | Use |
| --- | --- | --- |
| GET / PUT | /api/v1/consents/{farmer_token} | Read or update granular consent. |
| GET | /api/v1/consents/{farmer_token}/export | Export the farmer’s permitted data. |
| DELETE | /api/v1/consents/{farmer_token} | Request deletion/withdrawal under retention policy. |
| POST | /api/v1/notifications/dispatch | Enqueue a consent-checked message. |
| GET | /api/v1/notifications/{message_id}/status | Read delivery/outbox state. |
| POST | /api/v1/notifications/webhooks/provider | Provider delivery receipt. |
| POST | /api/v1/notifications/webhooks/inbound | Inbound reply/missed-call event. |
| POST | /api/v1/outreach/cycle | Evaluate band-change/sustained-red outreach policy. |
| POST | /api/v1/ingestion/preview | Inspect an adapter payload before persistence. |

## Identity, consent and privacy

Authentication is Supabase Auth. The backend verifies asymmetric JWKS tokens where available, with a constrained HS256 fallback for configured projects, and validates issuer/audience. Role and district claims come from trusted app_metadata; user-editable metadata cannot elevate access.

Supported roles are farmer, extension_officer, district_admin, admin and auditor.

The privacy boundary is explicit:

- a farmer token identifies a record but is never a password or bearer credential;
- the browser receives only the public Supabase URL and anon key;
- service role keys, database URLs, vault encryption keys and provider credentials stay server-side;
- farmer resources are bound to the authenticated Supabase subject;
- storage, officer-contact, analytics, email and due-window consent are separate purposes;
- export, withdrawal, deletion, retention and audit enforcement are first-class operations;
- exact coordinates and personal contact data are role-gated;
- district analytics suppress cohorts below n >= 10 and do not expose raw journal text;
- every sensitive read/write has a request ID and audit event.

Farmer email is an additive opt-in channel. An actual SMTP provider and a production WhatsApp/calling account are deployment prerequisites; the mock provider is the honest default for local replay.

## Frontends

Both user experiences are served from the same Vercel deployment and use the Supabase session to select the workspace:

| App | Audience | Stack and notable behavior |
| --- | --- | --- |
| apps/farmer-pwa | Farmer on a mobile/low-bandwidth device. | React 18, Vite, TypeScript, Framer Motion, Supabase Auth, Vite PWA, localised English/Hindi/Marathi UI, offline-aware replay path, MediaRecorder and Sarvam speech controls. |
| apps/officer-dashboard | Extension officer/district administrator. | React, Vite, TypeScript, Supabase Auth, MapLibre and role-scoped queue/analytics/case workspace. |
| packages/ui-kit | Shared visual system. | Shared branded logo, rainbow outline treatment, primitives, accessibility styles and design tokens. |

Production must point both apps at the same API base and Supabase project. The browser should never call provider APIs directly.

## Adapters, live data and the copilot

Canonical adapters can run in mock, replay or real mode. Every adapter must return a common record with source, observed_at, quality, ttl, provenance and a safe missing/stale state. This lets the hackathon demo use deterministic fixtures while keeping the production boundary honest.

Current adapter families include:

- weather and rainfall (IMD-compatible source);
- mandi prices and arrivals (Agmarknet/data.gov.in-compatible source);
- farmer/crop/scheme registries (AgriStack-compatible boundary);
- Sentinel-2 crop stress and soil-health signals;
- MSP reference values;
- Bhuvan/geospatial layers;
- language and speech adapters;
- notification, email and WhatsApp provider adapters.

No adapter should silently turn a failed source into a confident signal. The scoring path marks data stale/unknown, reduces confidence and can suppress escalation. A provider credential is not evidence that a feed is approved for production; data-sharing, rate-limit, licence and operational approvals still belong in the pilot plan.

## Background work and outreach

The dedicated Render worker runs python -m app.worker. The default schedule is configurable and currently designed around:

| Job | Default cadence | Purpose |
| --- | ---: | --- |
| Ingestion | 45 minutes | Fetch/replay configured source adapters. |
| Rescore | after ingestion | Recompute storage-consented farmer cohorts. |
| Outreach policy | 5 minutes | Band-change and sustained-red decisions. |
| Outbox delivery | 1 minute | Retry provider messages and dead-letter exhausted jobs. |
| SLA scan | 5 minutes | Escalate overdue cases. |
| Retention | 24 hours | Apply deletion/expiry policy. |
| District digest | daily | Produce consent-safe officer summary/email. |

The channel ladder is consent-aware, quiet-hour-aware and capped. WhatsApp outbound is the preferred product channel when an approved provider/account is configured. WhatsApp calling is not simulated as a successful call: it requires a provider with that capability, template/account approval and explicit farmer consent. Email can be used for demo digests with SMTP; real delivery requires SMTP credentials and verified sender policy.

## Deployment topology

| Component | Hosting | Required boundary |
| --- | --- | --- |
| Farmer PWA + officer workspace | Vercel | One role-aware build; public VITE_* values only. |
| FastAPI web | Render Docker web service | internal_hackathon/infra/docker/backend.Dockerfile, root directory internal_hackathon, health /readyz. |
| Worker | Render background worker | Same image/config; runs python -m app.worker; web keeps ENABLE_BACKGROUND_JOBS=false. |
| Auth + database | Supabase | Auth, Postgres/PostGIS, migrations and project-level RLS/keys. |
| Conversational AI and speech | Sarvam, server-side | LLM_PROVIDER=sarvam, LLM_EXTERNAL_ALLOWED=true, SARVAM_API_KEY. |
| Notifications | Mock or approved provider | Provider keys, sender identity, templates and webhook secret stay in Render. |

The Render manifest is [render.yaml](render.yaml). The deployment guide is [deployment_configuration.md](design/deployment_configuration.md). Exact production origins are allow-listed in backend CORS configuration, including the current Vercel deployment aliases.

## Quick start

The commands below start fixture mode without requiring government or notification credentials.

~~~bash
cd internal_hackathon

# Python environment
python3 -m venv .venv
source .venv/bin/activate
make PYTHON=.venv/bin/python install-python

# Frontend dependencies
npm install

# Create local browser configuration from the examples.
cp apps/farmer-pwa/.env.local.example apps/farmer-pwa/.env.local
cp apps/officer-dashboard/.env.local.example apps/officer-dashboard/.env.local

# Backend (from internal_hackathon/)
.venv/bin/uvicorn --app-dir services/backend app.main:app --reload --port 8000

# In another terminal, start the farmer PWA.
npm run dev --workspace apps/farmer-pwa

# In another terminal, start the officer dashboard if testing it separately.
npm run dev --workspace apps/officer-dashboard
~~~

For a local database-backed run, set DATABASE_URL and the Supabase values in a local backend env file, then run:

~~~bash
cd internal_hackathon/services/backend
../../.venv/bin/alembic upgrade head
~~~

To build the same backend context used by Render:

~~~bash
cd internal_hackathon
docker build -f infra/docker/backend.Dockerfile .
~~~

Use the replay endpoint or the frontend demo mode to exercise the flagship path: rainfall shock + price crash + opt-in due window → red event → explained drivers → officer case → resolution.

## Configuration

### Browser-visible variables

Examples live at:

- [apps/farmer-pwa/.env.local.example](apps/farmer-pwa/.env.local.example)
- [apps/officer-dashboard/.env.local.example](apps/officer-dashboard/.env.local.example)

They include VITE_API_BASE_URL, VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_AUTH_REDIRECT_URL, VITE_AUTH_REQUIRED, VITE_DEMO_MODE and VITE_MAP_STYLE_URL.

### Backend-only variables

The backend configuration is in services/backend/app/core/config.py. Production validates the database URL, Supabase URL and vault encryption key. Live Sarvam requires LLM_PROVIDER=sarvam, LLM_EXTERNAL_ALLOWED=true and SARVAM_API_KEY. Live source adapters require LIVE_DATA_ENABLED=true, the matching ADAPTER_MODE_* = real setting, and their endpoint/key. SMTP and WhatsApp/calling variables are only needed when those channels are enabled.

Never commit .env.local, service-role keys, database URLs, vault keys, provider tokens or webhook secrets. Put them in the local ignored env file for development and in Vercel/Render/Supabase secret stores. The repository’s env examples contain names and safe placeholders, not credentials.

## Verification

The current main branch has a documented verification record in [tasks.md](../tasks.md). The latest local frontend verification on this checkout includes:

~~~text
farmer-pwa:        lint ✓   tests ✓   build ✓
officer-dashboard: lint ✓   tests ✓   build ✓
ui-kit:            lint ✓   tests ✓
~~~

The repository also records backend test, lint, migration, replay and end-to-end checks in the implementation-status document. Re-run the backend suite after setting up the target Supabase/PostGIS environment, because provider credentials and database extensions are deployment-specific.

There is currently no GitHub Actions workflow in this checkout. Before a production or judging deployment, add CI gates for Python tests/ruff, Alembic migration validation, frontend lint/tests/build, dependency audits and a smoke test against /readyz.

## Repository map

~~~text
.
├── apps/
│   ├── farmer-pwa/                 # Mobile-first farmer experience
│   └── officer-dashboard/          # Officer/admin workspace
├── packages/ui-kit/                # Shared visual system and branded assets
├── design/                         # Master spec, module specs, ADRs and status reviews
├── libs/adapters/                  # Canonical source/provider/replay adapters
├── services/
│   ├── backend/                    # Only FastAPI composition root + worker
│   ├── scoring-engine/             # Pure FDI v2 engine
│   ├── ai-copilot/                 # Guarded, cited copilot boundary
│   └── platform-core/              # Historical/reference material, not a second API
├── infra/docker/backend.Dockerfile # Render backend image
├── render.yaml                     # Render web + worker definition
├── docs/assets/kisansetu-hero.png  # README hero banner
└── tasks.md                        # Built-only progress ledger
~~~

### Module map

| Module | Focus | Primary locations |
| --- | --- | --- |
| M0 | Architecture, contracts and safety boundaries | design/module_0_architecture_overview.md |
| M1 | Farmer onboarding, identity and consent | apps/farmer-pwa, backend auth/consent |
| M2 | Canonical source adapters and ingestion | libs/adapters, backend ingestion |
| M3 | FDI v2 scoring and explanations | services/scoring-engine, design/signal_model_fdi_aligned.md |
| M4 | Risk events, deduplication and hysteresis | backend risk-event orchestration |
| M5 | Officer cases, routing and SLA | backend cases, apps/officer-dashboard |
| M6 | Outreach, outbox and provider webhooks | backend notifications/outreach |
| M7 | Copilot, citations and speech | services/ai-copilot, /api/v1/copilot |
| M8 | District analytics and reporting | backend analytics, officer dashboard |
| M9 | Deployment, observability and retention | infra, render.yaml, backend worker |

## Known limitations before production

These are deliberate, documented gaps—not features to hide behind a demo:

1. **Live data is not automatically guaranteed.** Government feed credentials, licences, quotas and approvals must be configured and monitored per environment. Fixture/replay mode is the default safety net.
2. **A real notification account is required.** Mock delivery proves the workflow; it does not prove WhatsApp, calling, SMS or SMTP delivery. WhatsApp calling also needs a capable approved provider.
3. **Browser speech is permission- and gesture-dependent.** Sarvam speech health, microphone permission, MIME support, user-gesture playback and provider credentials must all be healthy for audio.
4. **The farmer email-channel profile update is an additive integration.** Existing consent and outbox boundaries are present; a production SMTP sender and address-verification policy are still required.
5. **No field impact claim is made.** Lead time, precision, action uptake, closure and distress-sale proxies must be measured in a supervised pilot with agronomist/extension review.
6. **Officer localisation is incomplete.** The farmer PWA carries the current language experience; dashboard language switching is a follow-on surface.
7. **No production CI workflow is checked in yet.** Add GitHub Actions and environment-scoped smoke/deploy gates before relying on unattended releases.
8. **Security and scale need deployment testing.** Run threat modelling, dependency scans, load tests, backup/restore drills, RLS review and an incident runbook against the chosen Supabase/Render projects.

## Design references

- [masterspecv1.md](design/masterspecv1.md) — system master specification.
- [Module specs](design/) — module contracts and execution plans.
- [adr_001_unified_backend.md](design/adr_001_unified_backend.md) — one FastAPI backend decision.
- [signal_model_fdi_aligned.md](design/signal_model_fdi_aligned.md) — authoritative FDI v2 signal model.
- [deployment_configuration.md](design/deployment_configuration.md) — Vercel, Render and Supabase configuration.
- [implementation_status_verified.md](design/implementation_status_verified.md) — code-aligned status review.
- [live_data_integration.md](design/live_data_integration.md) — live/mock adapter strategy.
- [research_risk_modelling.md](design/research_risk_modelling.md) — evidence and risk-model research.
- [tasks.md](../tasks.md) — what is actually built, kept separate from proposals.

The best next step is not adding another model. It is a timed, replayable pilot slice with a named district owner, a validated source contract, a consented farmer, an extension officer and an auditable outcome.
