# Module 1 — Platform Core & Data Layer

Historical Module 1 scaffold. The deployable gateway and data layer now live in
`services/backend`; this directory is retained only for migration/reference.

**Spec:** [`design/module_1_platform_core.md`](../../design/module_1_platform_core.md)

## Boundary

The canonical runtime contracts are in `services/backend/app/schemas/`. Pure
module contracts remain in their owning package. Do not add new runtime routes
or models here.

## Shared contracts

Import HTTP boundary types from `services/backend/app/schemas/`; never import
the retired platform-core app as a server.

## Status

Retired as a runtime. See the unified architecture decision in
`design/adr_001_unified_backend.md`.
# Platform Core contracts (not a second server)

The runtime backend is now **`services/backend`**. It is the single FastAPI
composition root and owns database sessions, migrations, middleware, API
routes, and module orchestration.

This directory remains as the design-contract package while the migration is
completed. Its schemas and module notes are reference material; do not start
`services/platform-core/app/main.py` as a separate server or add routes here.
New runtime code belongs in `services/backend/app` and should consume the
canonical pure packages (`libs/adapters` and `services/scoring-engine`).
