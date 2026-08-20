# Build Record — `user_experience`

> This file records only functionality that has actually been implemented and verified in the repository. It is not a proposal list or a future backlog. Planned work remains in the design specifications and issue tracker.

## Verified implementation

### M8 — Frontend Apps

- [x] Added typed farmer API client with a labelled replay-fixture fallback while M1 endpoints are unavailable.
- [x] Built farmer onboarding flow with language, crop, season and irrigation pickers.
- [x] Built conservative consent controls for storage, officer contact, analytics and the optional repayment window.
- [x] Built farmer status card rendering the upstream `RiskEvent` band, score, confidence, expiry and disclaimer without recomputing them.
- [x] Built shared farmer/officer `ScoreBreakdown` rendering from the same `contributors[]` shape.
- [x] Built farmer action-card view with reviewer and source references.
- [x] Built farmer mandi comparison view from typed quote data.
- [x] Built farmer settings/re-consent flow and local demo onboarding state.
- [x] Built offline detection, honest last-known-result banner and stale-status badge.
- [x] Built typed officer queue client with replay-fixture fallback.
- [x] Built officer ranked-case presentation, band filter and case selection.
- [x] Built officer case detail with shared score explanation and M5 action controls.
- [x] Built officer district KPI strip and map integration placeholder.
- [x] Built officer copilot panel with cited scheme references, draft-message review warning and fixed-action display.
- [x] Added shared UI-kit tokens and reusable primitives: buttons, band chips, traffic-light disc, driver cards, score breakdown, action cards, case cards, consent toggles, pickers, KPI tiles, map placeholder, offline banner and stale badge.

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
- [x] Added M7 tests for draft-only behavior, consent gating, expiry rejection, PII redaction and prompt-injection sanitisation.

## Verification run

- `make PYTHON=.venv/bin/python lint` — passed.
- `make PYTHON=.venv/bin/python test` — 16 Python tests passed; all three frontend workspace test suites passed.
- `npm run build` — farmer PWA and officer dashboard production builds passed.

## Design-spec comparison

The implemented slice covers the M7/M8 MVP presentation and safety boundaries that can run before M1/M2/M5/M6 APIs are complete. It deliberately uses replay fixtures and keeps the API seam typed. It does not claim that backend persistence, authentication, real map tiles, Workbox service-worker caching, live Bhashini, live RAG retrieval, or M7 HTTP mounting are built; those are not recorded here until implemented and verified.
