# Module 2 — Identity, Consent & Privacy

Auth (Supabase), RBAC/MFA, farmer token vault, consent ledger, retention/deletion, audit log.

**Spec:** [`design/module_2_identity_consent_privacy.md`](../../design/module_2_identity_consent_privacy.md)

## Boundary

The privacy firewall. `tokenisation/token_vault.py` is the only path allowed to resolve a farmer token to a phone number.

## Shared contracts

Import cross-module types from `services/platform-core/app/schemas/` — never redefine them.

## Status

Scaffolded. See the spec's §11 for acceptance criteria and §12 for the MVP boundary.
