# Implementation Gap Audit

What the design docs specify vs. what exists in code, as of **21 Aug 2026**.

Branches audited: `origin/manikanta` (backend, `dbb8b9d`) · `origin/user_experience` (frontend, `d07134a`)
Also checked: `origin/dev1` (`755b040`, schema only) · `origin/Harini` (no commits beyond main)

Legend: 🟢 done · 🟡 partial · 🔴 not started

---

## Summary

| Module | Owner | Status | Headline gap |
|---|---|---|---|
| M1 Platform Core | Dev 1 | 🟡 | 3 of 10 endpoints, 1 of 8 contracts, no observability |
| M2 Identity/Consent | Dev 1 | 🔴 | **All 23 files are untouched 3-line stubs** |
| M3 Adapters | Dev 2 | 🟡 | Core + replay real; **all 8 source adapters still `# TODO`** |
| M4 Scoring | Dev 2 | 🔴 | **Implements superseded v1 model, wrong bands** |
| M5 Case workflow | Dev 3 | 🟡 | 2 of 4 transitions, no SLA/routing/analytics |
| M6 Notification | Dev 3 | 🟡 | Outbox works; no channel ladder, caps or idempotency |
| M7 AI Copilot | Dev 4 | 🔴 | **Absent entirely** (planned as milestone 2) |
| M8 Frontend | Dev 4 | 🟢 | Built; missing map, e2e/a11y tests, officer i18n |
| M9 Outreach | Dev 3 | 🟡 | Scheduler + quiet hours; **no inbound paths at all** |

---

## M1 — Platform Core 🟡

**Exists:** FastAPI app, 3 endpoint modules, 9 ORM model files, 3 Alembic migrations, config, DB session, Dockerfile, PostGIS migration.

**Missing:**
- **7 of 10 endpoints** (masterspec §12): `POST /observations`, `POST /risk-events/recalculate`, `GET /risk-events`, `GET /mandis/compare`, `GET /analytics/district`, `POST /copilot/brief`, plus `GET /cases` (only the two transitions exist)
- **7 of 8 shared contracts** (module_0 §4) — only `schemas/farmer.py`. Missing `Observation`, `RiskEvent`, `AlertCase`, `ActionCard`, `AuthContext`, `ConsentContext`, `CopilotBrief`, `DeliveryAttempt`
- `ErrorEnvelope` + `Page` (error/pagination shapes, module_1 §5.3)
- **Observability**: structured logging, request-ID tracing, `/healthz` + `/readyz`
- **5 of 12 tables**: `crop_cycles`, `farmer_reports`, `action_cards`, `case_status_history`, `scheme_chunks` (pgvector)
- Spec indexes (village/district, crop+date, commodity+mandi+date, band, geospatial, vector)
- Tests: model round-trip, API contract, migration up/down, pagination, index perf, consent-gate, audit-trail, health

## M2 — Identity, Consent & Privacy 🔴

**Every file is the untouched scaffold** (3 lines: docstring + `# TODO`). Nothing implemented.

Missing in full: Supabase auth · RBAC + MFA · `AuthContext` · farmer token vault · field encryption · consent ledger with versioning · `ConsentContext` · `/me/export` + `/me/delete` · policy guardrails (cohort suppression n≥10, `assert_not_scoring_language`, PII redaction) · audit logger + query · retention scheduler · 4 route modules.

> ⚠️ The **privacy firewall is a headline claim** of this project ("no Aadhaar, bank or lender data") and the **CI banned-field grep** that enforces it is also absent. Currently the guarantee rests on nothing but convention.

## M3 — Ingestion & Adapters 🟡

**Exists:** `adapters/core/*` (interfaces, registry, normalizer, quality, ttl, health) and `adapters/replay/*` (driver, scenarios) appear implemented; 5 replay scenario fixtures present.

**Missing:**
- **All 8 source adapters still `# TODO` stubs** — 24 files (`imd`, `agmarknet`, `agristack`, `bhashini`, `bhuvan`, `sentinel2`, `msp`, `soil` × mock/real/schemas)
- The backend instead has its own `app/adapters/*` (7 files, **8–18 lines each**) that bypass the specced `AdapterInterface` — so the mock↔real swap contract doesn't hold
- Consent gate on `ProfileAdapter.fetch_profile`
- `ProfilePrefill` compile-time field-leak guarantee
- 90-day fixture dataset (`fixtures/90_day/` is empty)
- All 8 spec tests (contract parity, normalizer, TTL/quality, registry swap, replay scenarios, consent gate, field leak, circuit breaker)

## M4 — Scoring Engine 🔴 (highest-impact gap)

`app/scoring/engine.py` implements the **v1 5-signal model**, superseded by `signal_model_fdi_aligned.md`.

| | Spec (v2) | Implemented |
|---|---|---|
| Signals | **15** across CRIDA's 7 dimensions | **5** |
| Bands | Green <50 · Amber 50–69 · **Red ≥70** | **30 / 60** |
| Vulnerability | multiplier **0.7–1.3** on the shock total | **1.0–1.7**, applied per-signal |
| Missing signals | S2 flood · **S3 satellite** · S4 pest · S13 below-MSP | none present |
| Hysteresis | 2 observations / 3 days | absent |
| Drivers | `Contributor{signal, points, max_points, explanation, source, observed_at}` | bare strings |
| Stamps | `model_version`, `expires_at`, `SCORE_DISCLAIMER` | all absent |
| D7 | explicit `D7_IS_SCORED = False` | not represented |

Also: `app/adapters/sentinel.py` exists but is 8 lines and **unused** — the satellite signal isn't wired in.
Tests: 29 lines vs the spec's 30-case table (incl. band-boundary tests at 49/50 and 69/70).

> **Red currently fires at 60, not CRIDA's 70.** The "our Red *is* CRIDA severe distress" claim doesn't hold, and the officer queue over-escalates.

## M5 — Case Workflow 🟡

**Exists:** `POST /cases/{id}/acknowledge`, `POST /cases/{id}/resolve`, `alert_cases` table.

**Missing:** `visit` + `refer` endpoints · `GET /cases` (ranked queue) · state-machine guards (409 on illegal transition) · officer routing + district fallback · ranked ordering (§9.7) · **SLA timers + breach scanner** · dedup of repeat Red events · reopen/cooldown · **district analytics + cohort suppression** · `case_status_history` rows · consent-gated phone redaction · queue perf index.

## M6 — Notification & Delivery 🟡

**Exists:** `outbox_messages` table, retry with backoff, quiet-hours gate, `MockNotificationAdapter`.

**Missing:** `DeliveryAttempt` contract · **channel ladder** (SMS → IVR → WhatsApp → push) — currently generic · per-channel providers · `ActionCard` rendering + locale selection · consent gate at delivery · **daily caps** · **idempotency key** `(farmer_token, event_id, channel)` · stale-event suppression (`expires_at`) · truthful queued/sent/failed reporting · all 8 spec tests.

## M7 — AI & Agentic Copilot 🔴

**Nothing exists on any branch.** Correctly deferred to milestone 2, but the full surface is outstanding: officer copilot graph + 6 tools · scheme RAG over pgvector · `CopilotBrief` · **all 5 guardrails** (citation validator, PII redactor, prompt-injection filter, output-schema validator, no-send action gate) · farmer voice copilot · driver→sentence explainer · shadow-ML isolation.

The frontend already renders `CopilotBrief` and an `Unverified` badge against fixtures, so the contract shape is settled.

## M8 — Frontend 🟢

**Exists:** farmer PWA (5-step onboarding wizard, home, alerts + WebGL globe, signal timeline, copilot with live waveform, markets, privacy), officer workspace (collapsible triage / analysis / copilot, pinning, complaint queue), `ui-kit`, i18n **105 keys × en/hi/mr**, service worker + offline status cache.

**Missing:**
- **Map** (Leaflet/MapLibre) with village hotspots + mandi pins — masterspec §8.3 centre panel; only a stylised placeholder exists
- History sparkline on case detail · one-tap call / send-approved-message
- Officer login screen (`screens/login/` empty)
- Demo control (`POST /replay/scenario`) behind a dev-only flag
- **Officer UI is English-only** (i18n covers the farmer app)
- **Testing/CI**: no Playwright e2e, no `axe-core` a11y, no bundle-size budget, no i18n key-coverage check — all four are named in module_8 §11

## M9 — Outreach Automation 🟡

**Exists:** APScheduler background job, quiet-hours check (20:00–08:00), outbox processing loop.

**Missing:** **the daily cycle itself** (refresh → rescore → diff bands → dispatch) · cohort batching · trigger policy (band-change / sustained-Red) · per-farmer caps · escalation ladder · channel selector · **all four inbound paths** (missed call, IVR keypress, SMS reply, `to_observation`) · `OutreachDecision` + `InboundEvent` models · outreach audit log · all 5 endpoints.

> Quiet hours are implemented as **20:00–08:00**; the spec says **21:00–07:00** (module_9 §12).

---

## Cross-cutting

**Architecture.** The spec's six services are consolidated into one `services/backend`. Defensible for a hackathon, but it drops **M4's purity boundary** — the property that lets us say the score isn't a black box. The engine is I/O-free today; nothing enforces it.

**Contract divergence — will break the frontend at integration:**
| Field | Backend | Frontend contract |
|---|---|---|
| Band | `'Green' \| 'Amber' \| 'Red'` | `'green' \| 'amber' \| 'red'` |
| Case id | `int` | `string` (`case_id`) |
| Status | `'Acknowledged'` | `'acknowledged'` |

**Tests.** 5 files repo-wide (2 backend ≈ 29 lines, 3 frontend smoke). Every module spec's §11 is essentially unmet.

**CI.** Runs ruff + pytest + build only. Missing: `alembic upgrade/downgrade`, banned-field grep, axe, bundle size, i18n coverage.

**Still unpromoted contracts:** `InboundEvent` and `VillagerComplaint` are typed locally in the officer app; `MandiQuote` and `CopilotMessage` live only in `ui-kit`. All four need promoting to M1 before the freeze.

---

## Suggested priority

1. **M4 → v2 scoring** (bands 50/70, 15 signals). Highest impact; the FDI alignment is a pitch differentiator and the band error is user-visible.
2. **Align enums + IDs** (lowercase bands/status, string ids). Cheap now, painful later.
3. **M5 `visit` + `refer` + `GET /cases`** — the officer UI already calls all four.
4. **M9 inbound paths** — "a farmer who never installs anything can still raise their hand" is a core claim with zero implementation.
5. **M2 minimum viable** — consent gate + banned-field CI check, enough to make the privacy claim true.
6. **M1 contracts + remaining endpoints** — unblocks everyone.
7. **M7** last, as planned.
