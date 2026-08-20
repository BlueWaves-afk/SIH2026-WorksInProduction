# Live data integration (implemented)

KisanSetu now has one live-ingestion boundary for the first two external FDI
signals:

- **S1/S2 weather:** `IMDRealAdapter` parses the official IMD district-rainfall
  shape (`Daily Actual`, `Daily Normal`, `Daily Departure Per`) and can also
  consume a canonical department proxy.  See the [IMD API reference](https://api.imd.gov.in/public/api_reference.html).
- **S13 market stress:** `AgmarknetRealAdapter` parses the AGMARKNET/OGD daily
  market shape (`commodity`, `market`, `modal_price`, date) and accepts an
  explicit seasonal baseline, direct deviation, MSP, and below-MSP flag.  A
  single quote is never treated as a baseline.  The market dataset is published
  through the [India Open Government Data catalog](https://data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi).

## Runtime contract

The adapters return `ObservationPayload` DTOs.  The backend persists them as
canonical `Observation` rows and passes the same rows to the pure FDI scoring
engine.  Per-source TTLs are applied at the adapter boundary (`IMD=2 days`,
`AGMARKNET=3 days`); stale rows lower confidence and cannot create an automatic
escalation.

Live mode is intentionally opt-in:

```dotenv
LIVE_DATA_ENABLED=true
ADAPTER_MODE_IMD=real
ADAPTER_MODE_AGMARKNET=real
IMD_ENDPOINT=https://api.imd.gov.in/api/v1/districtrainfall
AGMARKNET_ENDPOINT=https://<approved-ogd-api-or-department-proxy>
IMD_API_KEY=
AGMARKNET_API_KEY=
LIVE_ADAPTER_TIMEOUT_SECONDS=10
```

The endpoint and keys are server-side settings.  They must never be exposed to
the browser or committed to Git.  Until the flag and both real adapter modes
are configured, `/api/v1/ingestion/preview` reports the source as unavailable
and the existing deterministic replay remains the only scoring input.

## API hooks

- `GET /api/v1/ingestion/health` — officer/admin-only configuration and circuit
  state; it does not make provider calls.
- `POST /api/v1/ingestion/preview` — officer/admin-only, returns parsed rows,
  freshness metadata, and sanitised provider errors without persisting data.
- `POST /api/v1/risk-events/recalculate` with
  `{ "farmer_token": "…", "source_mode": "live" }` — fetches IMD and
  AGMARKNET, de-duplicates observations, persists them, and invokes the FDI
  engine.  Any source failure returns `503`; it never falls back silently to a
  fixture.

Local and CI tests use `httpx.MockTransport`, not provider credentials.  A
deployment should first run `/ingestion/preview` for one district and compare
the provider's timestamps/coverage before enabling scheduled live scoring.
