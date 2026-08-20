# Module 8 — Shared UI Kit

Design tokens and shared components used by both apps.

**Spec:** [`design/module_8_frontend_apps.md`](../../design/module_8_frontend_apps.md)

## Boundary

`ScoreBreakdown` is shared verbatim by the farmer 'why' screen and the officer case detail.

## Shared contracts

Import cross-module types from `services/platform-core/app/schemas/` — never redefine them.

## Status

The first shared presentation slice is implemented: design tokens, traffic-light status, shared driver
explanation, action/case cards, consent toggles, pickers, KPI tiles and offline/stale indicators. See the
root `tasks.md` for verified build output and the spec's §11 for remaining acceptance criteria.
