# Deployment configuration handoff

The repository can be developed and tested without a Supabase project. Local
fixture auth, SQLite, mock adapters and the mock notification provider are the
safe defaults. Production secrets belong in the hosting provider's environment
configuration or an ignored `.env.local`; never commit them.

## Supabase values needed later

| Variable | Where it is used | Required when |
|---|---|---|
| `SUPABASE_URL` | Backend JWT issuer/JWKS and browser client | Supabase auth is enabled |
| `SUPABASE_ANON_KEY` | Farmer/officer browser clients | Browser auth is enabled |
| `DATABASE_URL` | Render backend and Alembic | Postgres deployment |
| `VAULT_ENCRYPTION_KEY` | Backend encrypted phone vault | Any non-local environment |
| `SUPABASE_SERVICE_KEY` | Backend-only administrative Supabase operations | Only if an admin API integration is enabled; never expose to Vercel |
| `SUPABASE_JWKS_URL` | Optional JWT key endpoint override | Only if the project does not use the derived Supabase URL |
| `SUPABASE_JWT_SECRET` | Legacy HS256 verification | Only for projects still issuing HS256 tokens |

The two browser apps only read `VITE_SUPABASE_URL` and
`VITE_SUPABASE_ANON_KEY`. They must never receive a service key, database URL,
JWT secret, or vault key.

## Provider values needed for live integrations

Set `LIVE_DATA_ENABLED=true` only after the selected source has been tested in
the target environment. `LIVE_SIGNAL_SOURCES` defaults to `imd,agmarknet` and
may add `bhuvan`, `msp`, `sentinel2`, or `soil` once each endpoint returns the
canonical observation envelope (or a supported native field shape).

| Source | Variables |
|---|---|
| IMD | `ADAPTER_MODE_IMD=real`, `IMD_ENDPOINT`, optional `IMD_API_KEY` |
| AGMARKNET/OGD | `ADAPTER_MODE_AGMARKNET=real`, `AGMARKNET_ENDPOINT`, optional `AGMARKNET_API_KEY` |
| Bhuvan | `ADAPTER_MODE_BHUVAN=real`, `BHUVAN_ENDPOINT`, optional `BHUVAN_API_KEY` |
| MSP | `ADAPTER_MODE_MSP=real`, `MSP_ENDPOINT`, optional `MSP_API_KEY` |
| Sentinel-2 proxy | `ADAPTER_MODE_SENTINEL2=real`, `SENTINEL2_ENDPOINT`, optional `SENTINEL2_API_KEY` |
| Soil proxy | `ADAPTER_MODE_SOIL=real`, `SOIL_ENDPOINT`, optional `SOIL_API_KEY` |

AgriStack profile prefill and Bhashini voice are separate adapter contracts;
they remain mock/template-first until their API Setu/Bhashini endpoint and
data-processing terms are approved. They are health-checked but are not fed
into the FDI scorer as generic signal rows.

## Notification values needed later

`NOTIFY_PROVIDER=mock` is the local default. A real SMS/voice provider requires
`SMS_PROVIDER_KEY`, a signed webhook secret, provider callback URL, approved
templates and a DLT-compliant sender configuration. The application does not
assume Twilio or any other provider until that choice is made.

## LLM / conversation values

Sarvam is the approved server-side provider for the bounded farmer-support
conversation agent. The key belongs only in the backend environment (Render or
an ignored `services/backend/.env.local`), never in Vercel/browser variables or
the Android project checked into source control.

| Variable | Local default | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `template` | Set to `sarvam` only after provider review |
| `LLM_MODEL` | `sarvam-105b-conversations` | Sarvam conversational model |
| `LLM_EXTERNAL_ALLOWED` | `false` | Explicit kill switch for outbound LLM calls |
| `SARVAM_API_KEY` | empty | Backend-only subscription key |
| `SARVAM_BASE_URL` | `https://api.sarvam.ai/v1` | Provider base URL |
| `SARVAM_TIMEOUT_SECONDS` | `20` | Per-request timeout |
| `LLM_MAX_OUTPUT_TOKENS` | `256` | Cost/latency cap |

The agent sends only a redacted, coarse profile and current deterministic risk
drivers. It never sends the farmer token, phone, Aadhaar, bank details, or raw
consent ledger. Provider failure, missing consent, stale events, or a disabled
kill switch return the template response instead.

## Release order

1. Apply `services/backend/alembic upgrade head` against a disposable Supabase
   branch/project and verify PostGIS.
2. Set backend-only variables on Render; set only the two `VITE_*` variables on
   Vercel.
3. Keep `AUTH_REQUIRED=true`, `ENV=production`, `LIVE_DATA_ENABLED=false` for
   the first authenticated smoke test.
4. Enable one live source at a time and verify `/readyz`, `/api/v1/ingestion/health`,
   `/api/v1/ingestion/preview`, and the stale-data replay before enabling live
   scoring.
5. If enabling Sarvam, add the key to the backend secret store, set
   `LLM_PROVIDER=sarvam` and `LLM_EXTERNAL_ALLOWED=true`, then exercise
   `/api/v1/copilot/chat` with synthetic data. Vercel receives no Sarvam key.
