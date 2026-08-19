# Module 5 — Case Management & Officer Workflow

Case lifecycle state machine, routing, ranked queue, SLA, closure, aggregate district analytics.

**Spec:** [`design/module_5_case_workflow.md`](../../design/module_5_case_workflow.md)

## Boundary

Owns `AlertCase.status`. Analytics are aggregate-only with cohort suppression from M2 — never individual surveillance.

## Shared contracts

Import cross-module types from `services/platform-core/app/schemas/` — never redefine them.

## Status

Scaffolded. See the spec's §11 for acceptance criteria and §12 for the MVP boundary.
