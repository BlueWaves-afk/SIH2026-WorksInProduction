# Module 8 — Farmer PWA

Voice-first, offline-first React PWA: onboarding, traffic-light status, 'why' screen, action cards.

**Spec:** [`design/module_8_frontend_apps.md`](../../design/module_8_frontend_apps.md)

## Boundary

No business logic — all decisions come from the M1 API. Every element operable eyes-free.

## Shared contracts

Import cross-module types from `services/platform-core/app/schemas/` — never redefine them.

## Status

First vertical slice implemented on `user_experience`: onboarding, consent, status/why/action/mandi/settings
views, typed API seam, replay fixture fallback and honest offline/stale rendering. See the root `tasks.md`
for verified build output and the spec's §11 for remaining acceptance criteria.
