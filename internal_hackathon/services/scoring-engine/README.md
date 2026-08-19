# Module 4 — Explainable Scoring Engine

Deterministic rules producing the 0-100 support-priority score, bands, confidence, hysteresis and top-3 drivers.

**Spec:** [`design/module_4_scoring_engine.md`](../../design/module_4_scoring_engine.md)

## Boundary

**Pure Python — no I/O, no network, no DB.** Consumes Observations, returns a RiskEvent. Fully unit-testable. This is the differentiator: not a model.

## Shared contracts

Import cross-module types from `services/platform-core/app/schemas/` — never redefine them.

## Status

The pure FDI-aligned engine and its acceptance tests are runnable. Source ingestion, persistence,
workflow, delivery, and copilot modules remain separate scaffolds and are exercised through DTOs
and replay fixtures rather than live services.
