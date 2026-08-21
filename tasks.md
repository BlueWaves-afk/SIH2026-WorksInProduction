# Build Record — `user_experience`

> This file records only functionality that has actually been implemented and verified in the repository. It is not a proposal list or a future backlog. Planned work remains in the design specifications and issue tracker.

## Verified implementation

### M8 — Frontend Apps

- [x] Added typed farmer API client with replay fixtures restricted to explicit demo mode; production failures remain visible and retryable.
- [x] Built farmer onboarding flow with language, crop, season and irrigation pickers.
- [x] Built conservative consent controls for storage, officer contact, analytics and the optional repayment window.
- [x] Built farmer status card rendering the upstream `RiskEvent` band, score, confidence, expiry and disclaimer without recomputing them.
- [x] Built shared farmer/officer `ScoreBreakdown` rendering from the same `contributors[]` shape.
- [x] Built farmer action-card view with reviewer and source references.
- [x] Built farmer mandi comparison view from typed quote data.
- [x] Built farmer settings/re-consent flow and local demo onboarding state.
- [x] Built offline detection, honest last-known-result banner and stale-status badge.
- [x] Built typed officer queue client with replay fixtures restricted to explicit demo mode.
- [x] Built officer ranked-case presentation, band filter and case selection.
- [x] Built officer case detail with shared score explanation and M5 action controls.
- [x] Built officer district KPI strip and an interactive village-centroid MapLibre map without exposing farm coordinates.
- [x] Built officer copilot panel with cited scheme references, draft-message review warning and fixed-action display.
- [x] Added shared UI-kit tokens and reusable primitives: buttons, band chips, traffic-light disc, driver cards, score breakdown, action cards, case cards, consent toggles, pickers, KPI tiles, lazy MapLibre maps, offline banner and stale badge.

### M7 — AI and Agentic Copilot

- [x] Built deterministic template-first `CopilotBrief` generation from an upstream `RiskEvent` and `AlertCase`.
- [x] Added fixed playbook selection; the copilot can select only predefined actions.
- [x] Added expiry protection so stale risk events cannot be narrated.
- [x] Added citation completeness validation for scheme matches.
- [x] Added PII redaction for phone, identity-number and account-like values before model context use.
- [x] Added prompt-injection sanitisation for untrusted document/officer text.
- [x] Added output validation rejecting dosage, diagnosis and guaranteed-eligibility language.
- [x] Added contact-consent gating so a draft message is omitted when contact consent is absent.
- [x] Added template-first driver narration with the upstream explanation preserved.
- [x] Added a server-side Sarvam chat-completions adapter using `api-subscription-key`, with no key in frontend code or logs.
- [x] Added the bounded `POST /api/v1/copilot/chat` agent with farmer ownership/storage-consent checks, active-event grounding, redacted context, prompt-injection sanitisation, safety validation and deterministic fallback.
- [x] Connected the farmer copilot UI to the live conversation endpoint while preserving an explicit first-run demo fixture path.
- [x] Added Sarvam provider transport tests and an API integration test covering grounded citations and template fallback.
- [x] Added M7 tests for draft-only behavior, consent gating, expiry rejection, PII redaction and prompt-injection sanitisation.

### Farmer copilot voice — verified

- [x] Added browser microphone capture with MediaRecorder, WebM/MP4/OGG selection and explicit permission/unsupported-device fallbacks.
- [x] Added short-clip validation, server-side Sarvam STT upload with locale mapping and transcript review before a farmer sends the question.
- [x] Added Sarvam TTS playback for the latest copilot answer with stop controls, object-URL cleanup and truthful playback errors.
- [x] Updated the backend speech contract to preserve browser audio MIME types and reject unsupported containers before provider dispatch.
- [x] Added browser interaction coverage for denied microphone access plus mocked end-to-end capture, STT request, TTS request and audio playback.

### Mobile-first interface refresh — verified

- [x] Reworked the farmer home screen into a compact status-first mobile layout with a fixed bottom navigation bar.
- [x] Added a hybrid support-chat surface with quick replies, typed questions and safe fixture-backed responses.
- [x] Added locale-aware farmer copy and localized next-step cards for English, Hindi and Marathi.
- [x] Removed visible implementation labels from farmer and officer screens and replaced them with human task language.
- [x] Reworked the officer queue into a mobile-responsive support workspace with clearer urgency, ownership and case-state labels.
- [x] Added an editable officer copilot message review flow with explicit approval state before delivery integration.
- [x] Refined shared surfaces, spacing, colors, focus states, bottom navigation and mobile breakpoints across both apps.
- [x] Replaced visible fixture-source wording with user-facing source labels such as IMD rainfall feed, Agmarknet market feed and Sentinel-2 crop observation.

### Shield-style farmer experience — verified

- [x] Rebuilt the farmer home as a location-aware alert feed with KisanSetu branding, a live support strip, filter chips and horizontally scrollable update cards.
- [x] Added an original, project-owned cotton-field alert image and wired it into the alert and detail surfaces.
- [x] Replaced the old fixed tab bar with a compact floating four-action dock using accessible icons and gradient alert accents.
- [x] Built a photographic field-alert detail screen with an explainable signal timeline, confidence and support-only guardrail.
- [x] Built a reviewed three-step action-plan screen with explicit completion controls and copilot handoff.
- [x] Built a nearby-market experience with search, a lightweight visual map, market pins and comparable price rows.
- [x] Rebuilt the copilot as a mobile conversation surface with field-signal context, quick prompts, voice affordance and a gradient message composer.
- [x] Rebuilt profile, language, privacy and consent screens in the same mobile design system.
- [x] Reworked onboarding with a KisanSetu introduction, agricultural signal artwork and Shield-style controls while preserving consent defaults.
- [x] Added navigation scroll restoration, keyboard focus treatment and responsive behavior for a 390×844 mobile viewport.
- [x] Added project-local AI-generated imagery for the farmer profile, cotton stress, heavy rain, mandi market, pest watch and field-map surfaces, with text-free crops optimized for mobile cards.
- [x] Added rainbow gradient rings around farmer/profile avatars, live alert thumbnails, timeline avatars and copilot field pins; verified the imagery and rings across home, alerts, profile and copilot screens at 390×844.
- [x] Replaced onboarding crop, season and irrigation emojis with Lucide icons, changed selected farm options from black fills to rainbow-outline cards, and reset onboarding scroll to the top on each step.
- [x] Replaced shield brand marks with the project-local transparent rainbow KisanSetu three-leaf logo across farmer home, onboarding and inner headers.
- [x] Replaced the nearby-market illustration with an interactive public-market map and kept the farmer marker deliberately approximate.
- [x] Excluded the route-level map engine from PWA precache, reducing the install shell from roughly 1.8 MB to 0.8 MB while preserving runtime caching.

### Officer workspace — verified

- [x] Rebuilt the officer dashboard as a reference-inspired split workspace with a slim navigation rail, document-style case report, searchable case table, driver comparison chart and persistent copilot thread.
- [x] Preserved officer workflows for case selection, acknowledgement, resolution, copilot briefing, cited references and draft-message approval.
- [x] Added responsive collapse for phone-sized officer views and replaced the officer rail shield mark with the project-local KisanSetu logo.

### Browser diagnostics — verified

- [x] Reused one browser-level Supabase client across the farmer and officer workspaces, removing duplicate GoTrue listeners for the shared auth storage key.
- [x] Added the project-local KisanSetu favicon to both app shells and verified it is emitted in each production build, eliminating the app-owned favicon 404.
- [x] Confirmed the remaining `chrome-extension://` frame/runtime messages originate in browser tooling rather than the KisanSetu bundles.

### Unified backend — verified

- [x] Selected `services/backend` as the only FastAPI composition root; documented the decision in `design/adr_001_unified_backend.md`.
- [x] Added Supabase-aware settings with `.env.local` precedence, JWT verification, local-only fixture auth, CORS, request IDs, structured error fallback, `/healthz` and `/readyz`.
- [x] Added the complete master-spec API surface: profiles, observations, recalculation, risk-event listing, mandi comparison, replay, cases, district analytics and copilot brief.
- [x] Added consent ledger updates, storage/contact checks, token generation, encrypted-or-hashed phone storage, data export/delete routes and audit events.
- [x] Wired canonical M3 replay scenarios to the pure FDI v2 scorer, including TTL conversion, Red flagship flow and stale-data suppression.
- [x] Added case state transitions, fixed resolution codes, status history and SLA timestamps.
- [x] Added consent-aware outbox delivery with idempotency, quiet hours, retry/dead-letter handling, delivery attempts and provider webhook/status routes.
- [x] Added interchangeable mock/real adapter contracts for IMD, Agmarknet, AgriStack, Bhashini, Bhuvan, MSP, Sentinel-2 and soil sources.
- [x] Implemented HTTP-backed IMD and AGMARKNET adapters with provider field parsing, API-key headers, timeouts, circuit health, source-specific TTLs and fail-closed errors.
- [x] Added opt-in live ingestion health/preview endpoints and a live recalculation mode that persists de-duplicated weather/market observations before invoking the canonical FDI scorer.
- [x] Added MockTransport coverage for official IMD rainfall fields, AGMARKNET modal/baseline/MSP parsing, missing endpoints, and the live provider-to-score API path.
- [x] Added an API integration test covering profile → replay → Red event → officer case → copilot → resolution and stale-data suppression.
- [x] Added frontend API-base/environment support and adapted farmer/officer clients to the paginated backend contracts.
- [x] Bootstrapped a conservative first RiskEvent during farmer profile creation so a new farmer has an honest initial status before live/replay observations arrive; bootstrap placeholders are excluded from scoring hysteresis once real signals exist.
- [x] Added an authenticated farmer-side recovery recalculation when a legacy profile has no status event, so existing onboarded sessions do not need to repeat setup.
- [x] Added browser-safe Supabase session/token integration to both apps; only `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are accepted client-side.
- [x] Added farmer phone-OTP and officer email/password session gates, role guards and explicit production connection states.
- [x] Bound opaque farmer resources to the Supabase Auth subject; possession of a farmer token no longer authorizes access.
- [x] Added cached Supabase JWKS verification for asymmetric signing keys with a legacy HS256 fallback, issuer/audience checks and key-rotation refresh.
- [x] Removed the unused legacy JWT dependency module so the hardened Supabase verifier is the only backend authentication path.
- [x] Restricted role and district claims to server-controlled custom claims/app metadata; user-editable metadata cannot promote a farmer.
- [x] Enforced JWT district scope across case, risk and analytics reads and added cross-district denial tests.
- [x] Retired the platform-core FastAPI entrypoint; it cannot be deployed as a second runtime.
- [x] Added farmer-token ownership to observations so export/delete cannot remove another farmer's village data.
- [x] Added a canonical FDI facade for legacy scorer imports; old v1 rules are no longer executable.
- [x] Added error envelopes for HTTP/validation failures and fixed Alembic URL handling for Supabase async URLs.
- [x] Added SQLite-safe PostGIS migration guards and verified `alembic upgrade head` on a local fixture.
- [x] Added a single live-signal source registry for IMD, AGMARKNET, Bhuvan, MSP, Sentinel-2 and soil, with the profile/voice adapters kept on their separate contracts.
- [x] Added canonical observation boundary validation for source, TTL, numeric ranges, due-window shape, reports and banned privacy fields.
- [x] Added one score-to-workflow projection used by replay and recalculation, with open-case deduplication, case-history refreshes and consent/idempotent outbox creation.
- [x] Added durable SLA breach fields, a breach scanner endpoint, ranked Red/SLA-first queues and scheduled SLA scans.
- [x] Added n≥10 analytics suppression using storage + analytics consent and returned an explicit suppressed state for small cohorts.
- [x] Added stale-event suppression at outbox delivery, manual dispatch caps/idempotency, validated provider statuses and inbound event deduplication.
- [x] Added deployment configuration handoff documentation covering Supabase, Vercel, Render and live-source activation order.
- [x] Added case deduplication, assignment on acknowledgement, SLA breach audit, reopen policy and an outreach cycle endpoint.
- [x] Added consent-aware band-change/sustained-Red outreach, quiet-hours fallback, daily caps, inbound SMS/missed-call/IVR handling and signed provider webhooks.
- [x] Added scheduled retention cleanup for old observations and completed outbox messages while retaining audit history.
- [x] Made both backend container entrypoints apply Alembic migrations before Uvicorn starts, preventing Render from serving models ahead of Supabase.
- [x] Made repeated farmer onboarding idempotent: an authenticated farmer reuses the existing profile/token instead of receiving a duplicate-profile conflict, with frontend recovery for older backend deployments.
- [x] Added mobile-farmer and desktop-officer Playwright journeys and wired them into CI.
- [x] Upgraded Vite, Vitest and Playwright to audited versions and deduplicated the JavaScript dependency tree.

## Verification run

- `make PYTHON=.venv/bin/python lint` — passed.
- Full Python package test run — 69 tests passed with an isolated SQLite database.
- `npm run lint` — farmer PWA, officer dashboard and UI kit TypeScript checks passed.
- `npm run test` — farmer PWA, officer dashboard and UI kit test suites passed.
- `npm run build` — farmer PWA and officer dashboard production builds passed.
- `npm run test:e2e` — mobile farmer and desktop officer browser journeys passed.
- Voice interaction journey — microphone fallback, mocked MediaRecorder upload and mocked Sarvam WAV playback passed on the Pixel 7 profile.
- `npm audit` — zero production or development dependency vulnerabilities.
- Live adapter tests — IMD/AGMARKNET provider parsing and live-score persistence path passed with HTTP mock transports; no provider credentials were used.
- Sarvam provider tests — OpenAI-compatible chat transport/header parsing and missing-key safety boundary passed with HTTP mock transport; no Sarvam credential was used.
- CI now installs the unified backend, runs the monorepo checks and executes both Playwright journeys.
- Unified backend tests — 9 tests passed, including Auth ownership, role-claim and district-isolation cases.
- Alembic migration smoke test — initial schema through the unified backend revision passed on SQLite; PostGIS geometry is enabled only on PostgreSQL/Supabase.
- SLA migration smoke test — the case breach/resolution revision applies cleanly through Alembic on SQLite.

## Design-spec comparison

The implemented slice covers the M1/M2/M3/M4/M5/M6/M7/M8/M9 MVP seams in the unified backend and the mobile presentation layer. It still deliberately uses mock providers/replay fixtures by default. It does not claim live government credentials, production Supabase deployment, live Bhashini, pgvector scheme ingestion, or live provider delivery until those are configured and verified in their target environments.
