# Internal Hackathon — KisanSetu platform

This folder is the working design baseline for the SIH problem-statement-2 prototype. It contains
the master product specification, the eight module specifications, and the cross-system review.
It is intentionally a specification-first commit: the implementation scaffold has not yet been
created.

## Read in this order

1. [`design/masterspecv1.md`](design/masterspecv1.md) — product, users, scoring, MVP, hosting, and acceptance tests.
2. [`design/module_0_architecture_overview.md`](design/module_0_architecture_overview.md) — module map, dependency rules, and canonical contracts.
3. [`design/module_1_platform_core.md`](design/module_1_platform_core.md) — FastAPI gateway, database, API, and deployment wiring.
4. [`design/module_2_identity_consent_privacy.md`](design/module_2_identity_consent_privacy.md) — authentication, consent, token vault, retention, and audit.
5. [`design/module_3_ingestion_adapters.md`](design/module_3_ingestion_adapters.md) — replay fixtures and government-data adapters.
6. [`design/module_4_scoring_engine.md`](design/module_4_scoring_engine.md) — deterministic score, confidence, drivers, and hysteresis.
7. [`design/module_5_case_workflow.md`](design/module_5_case_workflow.md) — officer queue, case state machine, SLAs, and aggregates.
8. [`design/module_6_notification_delivery.md`](design/module_6_notification_delivery.md) — action-card rendering, outbox, retries, and provider adapters.
9. [`design/module_7_ai_copilot.md`](design/module_7_ai_copilot.md) — guarded officer copilot and voice narration stretch layer.
10. [`design/module_8_frontend_apps.md`](design/module_8_frontend_apps.md) — farmer PWA, officer dashboard, and shared UI.
11. [`design/system_review.md`](design/system_review.md) — review findings, decisions already applied, residual risks, and implementation gates.

## Current implementation order

The first build slice should be one replayable vertical path:

`fixture → adapter → score → RiskEvent → AlertCase → officer acknowledgement → farmer status card`

Keep live government credentials, real telecom delivery, live Bhashini voice, and external-LLM
copilot calls out of the critical demo path until the replay path, privacy controls, and audit trail
pass. The master specification labels those integrations as stretch or production handoff work.

## Source-of-truth rules

- Shared wire contracts are owned by M1 and summarized in Module 0.
- Consent is owned by M2; a profile cache must not become a second consent authority.
- `farmer_token` identifies a farmer but is never a credential. Farmer requests require M2's
  short-lived session.
- M4's score is deterministic and read-only from the AI layer.
- M5 owns case status; M6 owns delivery-attempt status.
- Synthetic replay data is for demonstration and testing, not evidence of field impact.
