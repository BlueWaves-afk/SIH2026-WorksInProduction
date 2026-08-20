# Module 8 — Officer Dashboard

Triage cockpit: ranked queue, map, case detail, action panel, copilot brief.

**Spec:** [`design/module_8_frontend_apps.md`](../../design/module_8_frontend_apps.md)

## Boundary

Shows the *same* explanation the farmer sees (trust through symmetry).

## Shared contracts

Import cross-module types from `services/platform-core/app/schemas/` — never redefine them.

## Status

First vertical slice implemented on `user_experience`: ranked queue, band filter, case detail, shared score
explanation, KPI strip, map placeholder and cited copilot panel with replay fixture fallback. See the root
`tasks.md` for verified build output and the spec's §11 for remaining acceptance criteria.
