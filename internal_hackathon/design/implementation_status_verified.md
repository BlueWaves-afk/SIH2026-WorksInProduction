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
