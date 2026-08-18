# Full-system review — internal hackathon baseline

**Review date:** 19 August 2026<br>
**Scope:** `masterspecv1.md`, Module 0, and Modules 1–8 in this folder<br>
**Review type:** architecture, contract, privacy/security, operational, hosting, and delivery-readiness review

## Executive conclusion

The design is a credible SIH prototype direction. Its strongest choices are a deterministic,
explainable support-priority score; an officer case loop; offline/replay-first operation; opt-in,
coarse repayment timing; and an explicit separation between AI assistance and the safety-critical
score. Those choices match the practical pattern that SIH judges tend to reward: a named user, a
bounded government workflow, a working end-to-end slice, and measurable operational outcomes.

The repository is **not implementation-ready without the gates below**. It currently contains
design documents only: there is no application code, dependency manifest, migration, CI workflow,
OpenAPI artifact, or executable test suite. The review therefore validates the written architecture
and static consistency, not runtime correctness.

The attached [`problem_statement_inventory.md`](../problem_statement_inventory.md) now records the
seven internal statements and their provenance. PS-02 is the selected internal brief; its exact
title/identifier/owner must still be reconciled against the authenticated SIH SPOC portal before a
national submission.

## System reviewed

| Area | Intended responsibility | Assessment |
|---|---|---|
| M1 Platform Core | FastAPI gateway, shared contracts, persistence, migrations, observability | Sound foundation; needs executable API and transaction boundaries. |
| M2 Identity/Consent/Privacy | Auth, RBAC/MFA, token vault, consent ledger, retention, audit | Strong privacy intent; session, DB-role, deletion, and key-management controls must be implemented, not only documented. |
| M3 Adapters | IMD, market, AgriStack/API Setu, Bhashini, geospatial adapters, replay | Correct adapter boundary; production credentials and data-quality contracts remain open. |
| M4 Scoring | Pure deterministic rules, confidence, drivers, hysteresis, expiry | Best-defined technical core; boundary fixtures and calibration governance are required. |
| M5 Case Workflow | Routing, case lifecycle, SLA, district aggregates | Good human-in-the-loop loop; event-to-case delivery needs durable integration. |
| M6 Delivery | Action cards, channels, outbox, retries, receipts | Good safety controls; provider secrets and exactly-once/idempotent behavior need implementation tests. |
| M7 AI Copilot | Cited scheme retrieval, officer draft, optional voice narration | Appropriate as an edge/stretch layer; external-model governance must be a hard gate. |
| M8 Frontends | Farmer PWA, officer dashboard, shared components, offline UX | Strong demo story; generated API types and session handling must precede UI work. |

## Corrections applied in this review

The following inconsistencies were found across the documents and normalized before commit:

1. **Role vocabulary:** `district_admin` is now canonical; the earlier district-level role variant was
   removed from shared contracts and workflow examples.
2. **Phone privacy boundary:** encrypted phone data belongs only to the M2 vault. It is no longer
   part of the M1 `FarmerProfile` row or shared profile contract.
3. **Observation values:** `Observation.value` is now `JsonValue`, with metric-specific closed
   schemas. This is required because due-window and farmer-report observations are not floats.
4. **Case contract:** `AlertCase` now consistently carries `case_id`, `event_id`, recipient role,
   channel preferences, and case timestamps. M5 owns case status; M6 owns `DeliveryAttempt` status.
5. **Consent scopes:** `ConsentContext` now carries purpose scopes, including a separately auditable
   AgriStack-prefill grant. M2 is the only consent authority and exposes `verify_consent`.
6. **Optional AI output:** `CopilotBrief.draft_message` is optional because it must be absent when
   contact consent is missing or the model is unavailable.
7. **Package dependency cycle:** M1 must depend on an `IdentityConsentPort` protocol rather than
   importing M2. M2 may use M1 database/session ports; the composition root injects M2 at startup.
8. **Farmer authentication:** `farmer_token` is explicitly an identifier, never a bearer credential.
   Farmer status, consent, export, and deletion calls require a short-lived M2 `FarmerSession`.
9. **Analytics privacy threshold:** the M5 suppression examples now consistently use `n < 10`.
10. **Scoring boundaries:** rainfall and price bands now use unambiguous half-open intervals, with
    exact-boundary fixtures required.
11. **AI provider boundary:** no farmer identifier leaves the platform to an external LLM provider;
    provider no-training/no-retention controls are required, and templates are the fallback.
12. **Repository hygiene:** `.env.*`, private-key material, and OS metadata are ignored while an
    example environment file remains committable.
13. **MVP boundary:** live Bhashini is now consistently a stretch integration. The MVP uses the same
    adapter contract with cached/template audio, so network, quota, and provider policy cannot break
    the scored replay.

## Findings and implementation gates

### High priority — resolve before a public demo

| Finding | Why it matters | Required gate |
|---|---|---|
| No executable system exists yet | The documents describe tests, but none can pass until code, migrations, fixtures, and CI exist. | Create a minimal monorepo and make the replay vertical slice green before adding stretch integrations. |
| Event side effects are described synchronously | A request can persist a score while case creation or notification fails, or duplicate them on retry. | Persist `RiskEvent` and an outbox record transactionally; use idempotency keys on ingestion/replay and idempotent M5/M6 consumers. |
| Storage consent semantics are not fully decided | “Storage off” conflicts with the need to show a current status and maintain a safety/audit trail. | Decide whether enrollment requires storage consent or supports an explicitly ephemeral mode; encode it in M2, API responses, retention jobs, and UI copy. |
| Farmer-session enforcement is only a design rule | A raw token in a URL is an account-enumeration/data-disclosure risk if implementation treats it as authorization. | Add integration tests proving token-only requests fail, sessions are short-lived/scoped, and export/delete require re-authentication. |
| Action-card freshness is underspecified | A stale agronomy or scheme card can be harmful even when its wording is approved. | Add `version`, `effective_at`, `expires_at`, `crop/region`, `source_refs`, and approval/content hash; M6 must refuse expired cards. |
| External LLM and voice providers create data-governance risk | Provider retention, training, logging, and cross-border processing may not match the consent promise. | Default external calls off; use template-only demo mode, approved provider terms, redacted payload tests, key rotation, spend limits, and an incident switch. |
| Internal PS versus official SIH PS is not yet proven equivalent | A strong prototype can still be rejected if the national PS ID, owner, wording, or submission constraints differ. | SPOC exports the authenticated official record; reconcile it in a dated file before PPT submission or national nomination. |

### Medium priority — resolve before pilot

| Finding | Required treatment |
|---|---|
| Outbox “offline” behavior is described but not operationally bounded | Define retry/backoff, dead-letter ownership, maximum retention, provider webhook signature validation, and replay-safe delivery receipts. |
| Exact locations can expose farmers or vulnerable villages | Exact coordinates must be role-gated; public/aggregate maps must be coarse; define location retention and export/deletion behavior. |
| Vault isolation depends on database privileges | Implement separate schema/service roles, deny-by-default grants, rotation, and a migration check that proves other roles cannot read `vault`. |
| Government data contracts are inherently unstable | Every adapter needs source/version/observed-at/TTL/quality fields, fixture parity, schema-change alarms, and a named production owner. |
| Synthetic replay can be mistaken for impact evidence | Label every chart and demo fixture as synthetic; pilot KPIs need a baseline, matched comparison, confidence intervals, and language/land-size/gender slices. |
| Score rules can encode regional or crop bias | Keep score support-only, never eligibility/pricing; version every rule table; review red precision, false-negative rate, and alert burden by subgroup. |
| Browser caching can outlive consent | Clear caches on revocation, logout, expiry, and account switch; test service-worker and IndexedDB deletion on real browsers. |
| Hosting assumptions are prototype-grade | Verify Supabase has PostGIS/pgvector enabled, Render worker/cron capacity and health checks, Vercel CORS/HTTPS configuration, backups, and migration rollback before pilot. |

### Low priority — backlog / stretch

- Live Bhashini streaming, VAD/barge-in, and multi-language voice.
- Officer copilot polish beyond cited templates and fixed playbooks.
- Additional crops, districts, satellite/soil signals, and a shadow ML challenger.
- Push notifications, advanced analytics, multi-tenant deployment, and route optimization.

## Recommended implementation sequence

1. **Scaffold and contracts:** Python/FastAPI backend, React/Vite apps, typed OpenAPI client,
   PostgreSQL migrations, local fixture loader, and environment validation.
2. **Privacy foundation:** M2 sessions, consent ledger, vault schema/roles, audit events, cache
   deletion, and authorization tests.
3. **Deterministic vertical slice:** IMD/market fixture adapters → M4 score → M1 persistence → M5
   case → officer acknowledgement/resolve → farmer status card.
4. **Reliability:** transactional outbox, idempotency, retry/dead-letter, stale-feed handling,
   replay acceptance tests, and observability.
5. **Demo UX:** one district, two crops, Hindi/Marathi, offline banner, explainable drivers,
   action-card citations, and a timed three-minute replay.
6. **Stretch only after the slice is stable:** mock delivery, then approved Bhashini, then cited
   copilot. Never make an external provider or live government credential a demo dependency.

## Hosting assessment

The proposed prototype topology is coherent:

`Vercel (two static frontends) → Render (Dockerized FastAPI + worker) → private Supabase Postgres`

The browser must call FastAPI only; it must never connect directly to the database. For the prototype,
this keeps deployment simple and matches the documented stack. Validate the following before wiring
real data:

- Supabase project extensions (`postgis`, `vector`), separate vault schema/roles, backups, and
  connection-pool limits.
- Render health endpoint, worker/cron separation, migration-before-release runbook, request timeouts,
  and secret injection from the platform secret store.
- Vercel environment separation, API allow-list/CORS, secure cookies, service-worker cache versioning,
  and preview builds that cannot reach production data.
- GitHub Actions gates for formatting/lint, type checks, unit/integration/e2e tests, migration dry
  run, dependency/security audit, and a deploy approval for production.

Official hosting references: [Vercel Next.js deployment guidance](https://vercel.com/docs/frameworks/full-stack/nextjs),
[Render Docker deployment](https://render.com/docs/docker), [FastAPI container deployment](https://fastapi.tiangolo.com/deployment/docker/),
and [Supabase database extensions](https://supabase.com/docs/guides/database/extensions).

## Verification performed

- Confirmed all eight module specs are present and follow the 14-section template.
- Checked shared-contract names and the corrected role, phone, consent, case, and copilot fields.
- Checked that the reviewed reference URLs in the master spec respond successfully.
- Checked scoring boundary prose and the M5 privacy threshold after correction.
- Ran whitespace/error checks with Git before staging.
- Confirmed no application source, dependency lockfile, migration, environment file, private key, or
  test suite exists yet; runtime tests are therefore intentionally reported as **not run**.

## Go/no-go decision

**Go for implementation and internal judging preparation.** Do not claim production readiness or field
impact yet. The minimum go/no-go milestone is a deterministic replay that passes the master acceptance
tests with session enforcement, consent audit, transactional event handoff, and an honest offline
failure path.
