# Verified implementation status — 2026-08-21

Every claim below was **executed or read**, not inferred. Method: empirical signal
enumeration, spec §4 file-tree diffing, full test-suite runs, CI-equivalent invocation,
production build, and Dockerfile/import tracing.

Branch audited: `user_experience` working tree (509 files — the superset; `main` = 441).

---

## 1. Signal coverage — all 15 present ✅

Verified by instantiating every rule and printing emitted signals.

| Group | Signals | Result |
|---|---|---|
| Shock | S1 20 · S2 10 · S3 15 · S4 8 · S5 20 · S13 20 · S14 7 | **= 100.0 exactly** |
| Vulnerability | S6–S12 | → 0.7–1.3 multiplier |
| D7 | S15 | flag only, never scored (correct per spec §5) |

All 8 rule producers are wired in `engine.py:66-81`. The pure `scoring_engine`
package **is** the live engine: `app/integrations/canonical.py:22` imports
`compute_risk_event` from it.

---

## 2. Blockers

### B1 — Production container cannot boot ✅ FIXED 2026-08-21
`app/api/v1/endpoints/analytics.py:13` has a **top-level** import of
`identity_consent.policy.guardrails`. `infra/docker/backend.Dockerfile` copies and
installs `libs/adapters`, `services/scoring-engine`, `services/ai-copilot`,
`services/backend` — **never `libs/identity-consent`**.

Reproduced exactly: `ModuleNotFoundError: No module named 'identity_consent'` at
`router.py` → `analytics.py:13`. `main.py` imports the router, so the process dies at
startup. `ai_copilot` escapes the same fate only via a `sys.path` fallback in
`integrations/copilot.py`; `identity_consent` has no such fallback.

**Fixed:** `backend.Dockerfile` now copies and editable-installs `libs/identity-consent`.
Verified by simulating the container's exact module path: before → `ModuleNotFoundError`,
after → `app.main imported OK`. `ai_copilot` continues to resolve through its `sys.path`
fallback (`parents[4]` → `/app/services/ai-copilot`, which the image does copy).

### B2 — Channel decision is intentionally WhatsApp-first ✅
The original module 9 text ranked SMS/IVR first. The product decision was changed by
the owner to WhatsApp messaging plus an explicitly consented call path. The runtime now
uses `whatsapp` for message delivery and `whatsapp_call` only when call consent is true;
quiet hours, daily caps, idempotency, provider receipts and fail-closed behavior remain
enforced. SMS/IVR webhook parsing is retained as an inbound compatibility seam, not as
the selected outbound channel. This requires a Meta Cloud API account for messages and
either an approved calling partner or Sarvam Voice Agents telephony configuration for
calls; WhatsApp voice is not faked when that account capability is absent.

### B3 — Server-side voice pipeline is mounted; browser capture remains ✅/OPEN
Sarvam STT/TTS adapters are mounted at `/api/v1/copilot/speech/transcribe` and
`/api/v1/copilot/speech/synthesize`, with storage-consent, role checks and redacted audit
events. The frontend still needs `MediaRecorder` capture and audio playback wiring to
make the mobile voice button end-to-end; the existing visual waveform is not counted as
voice functionality. Sarvam chat, STT and TTS keys remain server-side.

### B4 — Flagship test uses the complete signal snapshot ✅
The integration acceptance flow now includes rainfall shock, price crash, opted-in due
window and the Sentinel-2 crop-stress observation, which produces Red and records all
drivers and sources. A deliberately bare three-driver fixture remains pinned at 68.12
(Amber) in `test_23b`; this is a calibration note, not a hidden failure. The product
must not claim that any three signals always force Red without the vulnerability and
quality context defined by the FDI model.

### B5 — CI never ran frontend unit tests ✅ FIXED 2026-08-21
`ci.yml` ran `build` + `test:e2e` only, so every `smoke.test.ts` silently never executed.
Added `npm run test --prefix internal_hackathon`. Verified all three suites pass
(farmer-pwa, officer-dashboard, ui-kit — 1 test each) before adding the step.

---

## 3. Verified working ✅

| Area | Evidence |
|---|---|
| Scoring engine | 34/34 pass; all 15 signals; FDI v2 live in backend |
| CI-equivalent suite | **76 passed**, `ruff` clean |
| Frontend build | both apps build; home→why→action ≈ **86 kB gzip** (under the 100 KB budget — maplibre is correctly `import()`-split) |
| Adapters | 9 source families, real+mock; IMD, Agmarknet, AgriStack, Bhuvan, MSP, Sentinel-2, Soil Health, plus Sarvam chat/STT/TTS and WhatsApp delivery (Bhashini is compatibility-only) |
| M9 policy engine | band-change/sustained-Red, consent gate, quiet hours, daily cap, idempotency, low-confidence suppression, APScheduler |
| Inbound (app-free) | `POST /notifications/webhooks/inbound` handles sms/whatsapp/ivr/missed_call → `acute_farmer_report` + callback outbox (URL differs from spec, function present) |
| Masterspec AT#2–#6 | suppress_escalation, case state machine, district analytics, citations, offline statusCache — all present |
| Farmer i18n | en/hi/mr at **105 keys each**, parity verified |
| **API surface** | **all 10 masterspec §12 endpoints implemented**, 29 paths total (verified via OpenAPI, not route introspection — this FastAPI/Starlette pair *mounts* sub-routers, so `app.routes` under-reports) |
| **DPDP rights** | `GET` (access), `PUT` (withdraw), `DELETE` (erasure), `/export` (portability) all present on `/consents/{token}` |
| Scheduled jobs | outbox 1 min · outreach 5 min · SLA 5 min · **retention 24 h** — all registered |
| Data layer | 11 models, 6 Alembic migrations |
| Prod config guard | `ENV=production` correctly refuses to boot without `SUPABASE_URL` + `VAULT_ENCRYPTION_KEY` |

---

## 4. Remaining gaps

| # | Gap | Severity |
|---|---|---|
| 1 | **Zero tests** in identity-consent, notification, case-workflow, outreach, platform-core. Spec'd but absent: M2 ×6, M3 ×5, M6 ×5 test files | High |
| 2 | **ADR-001 contradiction** — ai-copilot is *not* independently testable; `citation_validator.py` imports `app.schemas` from backend (standalone pytest → `No module named 'app'`) | Medium |
| 3 | **No CI bundle-size gate** — `module_8 §11` requires a per-route gzip check | Medium |
| 5 | **Officer i18n missing** — `apps/officer-dashboard/src/i18n/` is empty | Medium |
| 6 | **Dead code** — `app/scoring/engine.py` (95 LOC legacy facade, nothing imports it) | Low |
| 7 | **Brand leftovers** — "kisansetu" in 15 files incl. `pyproject.toml` name, localStorage keys, asset filenames; name was never finalised | Low |
| 8 | `engagement_flag.py` counts *observations* and silently ignores `Observation.value`; also emits "1 outreach attempt**s**" | Low |
| 9 | maplibre CSS is a **static** import — ships on every route although its JS is lazy | Low |
| 10 | `sla.py:19` uses deprecated `datetime.utcnow()` | Low |
| 11 | e2e is thin — 1 test per app | Low |
| 12 | Backend test suite reads a gitignored `.env.local`; one transient failure observed in `test_copilot_conversation.py` that did not reproduce across 5 later runs | Low |
| 13 | `services/backend/requirements.txt` is **UTF-16LE + CRLF** (Windows `pip freeze`). pip's BOM auto-detection parses it fine — verified — so this is hygiene, not a blocker | Low |
| 14 | `run_retention_cycle` hardcodes `"audit_deleted": 0` — audit rows are never purged (may be deliberate, but it is unstated) | Low |

### Doc drift (not defects)
Per-module dirs (`case-workflow` 80 LOC, `outreach` 54, `notification` 133,
`identity-consent` 178, `platform-core` 418 all-TODO) are near-empty **by ADR-001
design** — the real code is `services/backend` (4,480 LOC). The module specs' §4
still describe those dirs as the implementation home. Specs should point to ADR-001.

---

## 5. Suggested order

1. ~~**B1**~~ — done.
2. ~~**B2**~~ — WhatsApp-first override implemented; supply Meta/calling credentials before live delivery.
3. **B3** — wire browser microphone capture and TTS playback; server routes and adapters are ready.
4. ~~**B4**~~ — complete FDI snapshot acceptance test is green; keep the bare-three calibration note explicit.
5. Gaps 1 (zero tests in 5 packages) and 5 (officer i18n).

---

## 6. Live-loop implementation — 2026-08-21 (the "fully operational" pass)

Built the automatic end-to-end loop over the existing scaffolding. All new code
is tested and lint-clean; **Python CI suite 90 passed, ruff clean; all frontend
suites pass; both apps build.**

| # | Required item | Delivered | Files |
|---|---|---|---|
| 1 | Scheduled live-ingestion job (30–60 min) | `run_ingestion_cycle` on a 45-min APScheduler job (interval configurable) | `services/ingestion.py`, `outreach/scheduler.py` |
| 2 | Recalculate all eligible farmers after ingestion | The cycle ingests + rescores the whole storage-consented cohort, failure-isolated per farmer | `services/ingestion.py` |
| 3 | Trigger outreach from newly changed events | Ingestion writes events via the same workflow the 5-min outreach cycle already consumes → band changes drive outreach automatically | (existing `services/outreach.py`) |
| 4 | Replace `demoAlerts` with API-backed alerts | `buildAlerts(status)` derives the alerts feed from the real scored `risk_event.contributors` | `features/alerts/fromStatus.ts` (+ test), `app/App.tsx` |
| 5 | Frontend polling / auto-refresh | 60 s poll while visible + online, plus refresh on regaining focus | `app/App.tsx` |
| 6 | Sarvam health check + clearer TTS errors | `GET /copilot/speech/health`; 503s now distinguish `not_configured` vs `provider_error` via `x-speech-status` | `api/v1/endpoints/copilot.py` |
| 7 | Email provider (officer digest) | SMTP + logging-mock provider; identity-light district digest on a daily cron. **Officer channel only** (never farmer email) | `integrations/email.py`, `services/digest.py` |
| 8 | Dedicated worker instead of in-web scheduler | `python -m app.worker` + `render.yaml` (web + worker); `ENABLE_BACKGROUND_JOBS=false` on web prevents double-runs | `app/worker.py`, `render.yaml`, `app/main.py` |

### Honest operational caveats (config, not code)

1. **Fresh live data needs real adapter credentials.** `fetch_live` deliberately
   refuses mock-mode adapters ("no fabricated freshness" — masterspec guardrail).
   With `LIVE_DATA_ENABLED=true` + `ADAPTER_MODE_*=real` + keys, the cycle fetches
   and persists real observations (`live_fetched` increments). Without them it
   runs and rescores stored/replay rows — the loop is live, the *data* is not.
2. **Voice needs `SARVAM_API_KEY`** on the backend; `/copilot/speech/health` now
   reports this. Auto-speaking every reply stays gated by browser autoplay policy
   (needs a user gesture) — a browser constraint, not a code gap.
3. **Digest needs `DISTRICT_DIGEST_RECIPIENTS`** (+ SMTP creds for real send;
   logs otherwise). No recipients configured = safe no-op.

---

## 7. Farmer email channel — 2026-08-21 (opt-in, additive)

Reversed the earlier officer-only decision on request: farmers can now opt into
email alerts. Implemented as an **additive, opt-in** channel (never the primary,
like PWA push) so it respects the "farmers rarely check email" reality without
denying the option. **Backend 98 pass, ruff clean; both apps build; i18n 108/108/108.**

**Backend**
- `email_enc` on `farmer_profiles` (Alembic `d4e9a1f7c2b8`), encrypted via the same
  vault path as the phone — `encrypt_email`/`decrypt_email`.
- `ConsentFlags.email_alerts` + `email` on profile create (blank→None, format-validated);
  `ConsentUpdate.email_alerts` toggle.
- Outreach cycle enqueues an **additive** `email` outbox message when
  `email_alerts` + an email are present — independently idempotent
  (`outreach:{event}:email`), rides the same contact decision (not re-capped).
- Delivery routes `channel == "email"` to the email provider, destination decrypted
  from `email_enc`, gated by **both** `contact_me` (umbrella) and `email_alerts`;
  missing address → dead-letter, withdrawn consent → cancelled.
- 7 new tests (`test_farmer_email.py`): encrypted storage, blank/invalid email,
  additive creation, opt-out skip, delivery, consent-withdrawal cancel.

**Frontend**
- `ConsentState.email_alerts`; onboarding privacy step gains an "Email me alerts"
  toggle + email input (persisted at profile create → `email_enc`); settings screen
  gains the matching toggle; `email`/`email_alerts` flow through `submitFarmerProfile`.
- New i18n keys in en/hi/mr (`onboarding.privacy.email[Body]`, `onboarding.email.placeholder`).

**Known limitation:** changing the email address *after* onboarding needs a profile
update endpoint (not yet built) — the consent PUT toggles the flag but does not edit
the stored address. Fixture mode stores a non-recoverable hash (no vault key), so real
email send needs `VAULT_ENCRYPTION_KEY` + `EMAIL_PROVIDER=smtp` in deployment.
