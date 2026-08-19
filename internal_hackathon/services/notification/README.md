# Module 6 — Notification & Multi-Channel Delivery

PWA push / SMS / voice / IVR delivery, ActionCard rendering, offline outbox, daily caps.

**Spec:** [`design/module_6_notification_delivery.md`](../../design/module_6_notification_delivery.md)

## Boundary

Mock providers first. Consent-gated by M2. Writes DeliveryAttempt only — never AlertCase.status.

## Shared contracts

Import cross-module types from `services/platform-core/app/schemas/` — never redefine them.

## Status

Scaffolded. See the spec's §11 for acceptance criteria and §12 for the MVP boundary.
