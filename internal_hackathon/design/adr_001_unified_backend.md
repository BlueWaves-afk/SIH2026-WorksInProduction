# ADR-001 — Unified backend composition root

**Status:** Accepted  
**Date:** 2026-08-21

## Decision

`internal_hackathon/services/backend` is the only runtime FastAPI application.
It owns the HTTP gateway, SQLAlchemy session boundary, Alembic migrations,
Supabase JWT verification, consent enforcement, orchestration, and background
outbox worker.

The pure sibling packages remain independently testable:

- `libs/adapters` owns source/replay interfaces and never writes to the DB.
- `services/scoring-engine` owns the pure FDI v2 rules engine and never performs I/O.
- `services/ai-copilot` owns template-first copilot logic and guardrails.

`services/platform-core` is contract/reference material during the migration. It
must not be started as a second server or reimplement routes/models already
owned by `services/backend`.

## Supabase boundary

Supabase is the production Postgres/PostGIS and Auth provider. The browser only
receives the public Supabase URL/anon key through Vercel environment variables;
the service-role key, JWT secret, vault encryption key, provider keys, and
database URL are backend-only Render/Supabase environment variables. Local
development uses `internal_hackathon/.env.local`, which is ignored by Git.
JWT role claims are read from `app_metadata.role` (and `app_metadata.district_id`
for officer scoping); the browser never receives the service-role key.

## Request flow

```text
Vercel farmer/officer app
        │ Bearer Supabase JWT
        ▼
services/backend/app/main.py
  request-id + CORS + error envelope + readiness
        ▼
  API routes → auth/consent → orchestration
        ├── libs/adapters (mock/real/replay)
        ├── services/scoring-engine (FDI v2)
        ├── services/ai-copilot (draft-only, cited)
        ├── case/notification/outreach policies
        └── Supabase Postgres/PostGIS via SQLAlchemy/Alembic
```

## Consequences

There is one deployment target and one API contract. Any future module must be
mounted in `services/backend/app/api/v1/router.py`, add an integration test, and
use the canonical contracts instead of creating another FastAPI app.

The production container is `infra/docker/backend.Dockerfile` and must be built
with `internal_hackathon` as its context so the adapter, scorer, and copilot
packages are installed into the same image.
