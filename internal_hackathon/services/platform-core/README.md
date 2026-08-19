# Module 1 — Platform Core & Data Layer

FastAPI gateway, shared data models (SQLAlchemy + Pydantic), Postgres/PostGIS/pgvector, migrations, config, observability.

**Spec:** [`design/module_1_platform_core.md`](../../design/module_1_platform_core.md)

## Boundary

Owns the **shared contracts** in `app/schemas/` that every other module imports. Routes to M2–M7; implements none of their logic.

## Shared contracts

Import cross-module types from `services/platform-core/app/schemas/` — never redefine them.

## Status

Scaffolded. See the spec's §11 for acceptance criteria and §12 for the MVP boundary.
