# Module 4 — Explainable Scoring Engine

Package: `services/scoring-engine` · Owner concern: deterministic rules that turn `Observation`s into a
`RiskEvent`. Read `masterspecv1.md` (§3, §4, §14) and `module_0_architecture_overview.md` (§3, §4, §5)
first — this spec conforms to both and does not redefine any contract owned by M1.

> **Purity contract:** this module is a pure-Python library. No network calls, no DB writes, no imports
> of M2 (`identity-consent`) or M3 (`adapters`) runtime code. It imports only *type definitions* from M1.
> Same inputs → same outputs, always. This is what makes "the score is not a model" defensible.

> **Amendment (signal model v2 — FDI alignment).** This module now implements the FDI-aligned
> model in [`signal_model_fdi_aligned.md`](./signal_model_fdi_aligned.md). Changes:
>
> - **Structure:** `final_score = clamp(shock_score x vulnerability_multiplier, 0, 100)` —
>   acute signals produce the shock score (0-100); structural signals produce a 0.7-1.3 multiplier.
> - **Signals:** 5 -> **15**, mapped to CRIDA's 7 dimensions. New rule modules:
>   `rules/satellite_stress.py` (S3), `rules/pest_pressure.py` (S4), `rules/vulnerability.py`
>   (S6-S12), `rules/engagement_flag.py` (S15, non-scoring).
> - **Bands:** now **Green <50 / Amber 50-69 / Red >=70**, aligned to CRIDA's 0.5 / 0.7 cutoffs.
>   Our Red *is* CRIDA's "severe distress" band. `constants.py` is updated accordingly.
> - **D7 (socio-psychological) is NOT scored** (`D7_IS_SCORED = False`). S15 is an officer-side
>   context flag only, never a number, never shown to the farmer.
> - **Public contract unchanged:** `compute_risk_event()` still returns a `RiskEvent`, so M5/M6/M7/M8
>   need no changes. The purity rule (no I/O) still holds.

---

## 1. Module purpose & responsibilities

- Compute a 0–100 **support-priority score** from seven acute shock signals and a bounded structural
  vulnerability multiplier; S15 is an officer-only context flag.
- Assign a **band** (Green/Amber/Red) with two-observation/three-day **hysteresis** to prevent flapping.
- Compute a **confidence** value from data freshness + completeness.
- Select and render the **top-3 human-readable drivers**, each traceable to a rule + source.
- Compute an **expiry** (`expires_at`) — the score is a perishable claim.
- Apply **stale-feed suppression**: a feed past its TTL lowers confidence and can hold back escalation,
  never manufactures a false alert.
- Stamp every event with **`model_version`** for auditability and safe recalibration.
- Guarantee, architecturally, that the output is **never** a credit/default/insurance score.
- Expose a **shadow ML challenger** extension point that is logged but never influences the output.

---

## 2. Scope

### In scope
- The seven shock rule functions (S1–S5, S13–S14), seven vulnerability adjustments (S6–S12),
  and non-scoring engagement flag (S15).
- Band assignment + hysteresis state machine.
- Confidence computation (freshness × completeness, weight-normalised).
- Driver selection/rendering (top-3, human-readable, rule+source traceable).
- Expiry computation, stale-feed detection, escalation suppression.
- `model_version` stamping and the disclaimer constant.
- The shadow-ML extension point (interface + isolation guardrail, no real model required for MVP).
- Full unit/property test suite proving determinism and the masterspec §14 acceptance tests.

### Explicitly out of scope
- Fetching/polling IMD, Agmarknet, AgriStack, Bhashini, or any external source (M3).
- Persisting `RiskEvent`, `Observation`, or any row to Postgres (M1).
- Deciding *who* gets notified, on what channel, or rendering the action card copy (M6).
- Case creation, routing, SLA, officer workflow, or district analytics aggregation (M5).
- Consent enforcement/collection, tokenisation, RBAC (M2) — M4 *reads* `ConsentContext` but never
  mutates or issues it.
- Any generative/LLM text — driver strings are template lookups, not generated (that boundary belongs
  to M7's explainer, which further translates M4's driver strings; M4 never calls an LLM).
- Training, hosting, or serving the shadow ML model itself (future M-owner TBD — see §14).

---

## 3. Position in the architecture

```mermaid
flowchart LR
    M3["M3 Adapters\n(IMD, Agmarknet, farmer opt-in)"] -->|Observation[]| M1["M1 Platform Core\n(persists + orchestrates)"]
    M1 -->|Observation[], FarmerProfile,\nConsentContext, prior RiskEvent[]| M4["M4 Scoring Engine\n(pure)"]
    M4 -->|RiskEvent| M1
    M1 --> M5["M5 Case/Workflow"]
    M1 --> M6["M6 Notification"]
    M1 --> M7["M7 AI Copilot (read-only)"]
```

- **Consumes:** `Observation[]` (M1 type, produced by M3), `FarmerProfile` subset (M1), `ConsentContext`
  (M2, passed through by M1 — M4 never calls M2), and the farmer's recent `RiskEvent[]` history (for
  hysteresis — M1/M5 query and pass this in; M4 has no storage of its own).
- **Produces:** `RiskEvent` (M1 type) — the single output type. Nothing else leaves this module.
- **Upstream:** M1 (invokes M4 synchronously, in-process, from `POST /api/v1/risk-events/recalculate`).
- **Downstream:** M5 (case creation on Amber/Red), M6 (action-card trigger), M7 (read-only brief input).
  M4 never calls any of them — it returns a value and exits.

---

## 4. Internal structure

```
services/scoring-engine/
  scoring_engine/
    __init__.py
    constants.py        # weights, band cutoffs, TTL defaults, MODEL_VERSION, SCORE_DISCLAIMER
    types.py             # SubScoreResult, Contributor, FarmerContext, BandDecision (local types)
    guardrails.py         # banned-field scan, disclaimer export, purity assertions
    confidence.py          # freshness() + completeness() + weighted aggregate
    drivers.py              # driver text templates + top-3 selection
    bands.py                 # band_from_score() + BandHysteresis state machine
    rules/
      rainfall.py             # S1 deficit + S2 excess
      satellite_stress.py     # S3 Sentinel-2 anomaly
      pest_pressure.py        # S4 bounded pest/advisory signal
      repayment.py            # S5 opt-in due window
      vulnerability.py        # S6-S12 multiplier adjustments
      price.py                # S13 market shock + below-MSP
      farmer_report.py        # S14 acute farmer-reported shock
      engagement_flag.py      # S15 officer context only (never scored)
    engine.py                     # compute_risk_event() — the single public entrypoint
    shadow/
      __init__.py
      challenger.py                # ShadowChallenger.predict() — logged only, isolated return channel
  tests/
    fixtures/scenarios.py           # synthetic Observation sets: normal / rainfall shock / price crash /
                                     # rainfall+price+due-window / stale-data
    test_rainfall.py
    test_price.py
    test_repayment.py
    test_vulnerability.py
    test_farmer_report.py
    test_bands_hysteresis.py
    test_confidence.py
    test_drivers.py
    test_guardrails.py
    test_engine_acceptance.py        # masterspecv1.md §14, verbatim
  pyproject.toml
```

### Rule tables (MVP calibration placeholders — see §14 open questions)

> ⚠️ **Rescaled by signal model v2.** Rainfall now splits into **S1 deficit (0–20)** and
> **S2 excess/flood (0–10)**, and `irrigation_type` moves *out* of this rule into the
> **vulnerability multiplier (S9)**. Authoritative weights:
> [`signal_model_fdi_aligned.md`](./signal_model_fdi_aligned.md).

**S1 rainfall deficit (0–20)** — `metric="rainfall_deviation_pct"`, source IMD.

| Cumulative deviation from normal | Points |
|---|---:|
| ≥ 0% (normal/surplus) | 0 |
| (−10%, 0%) | 3 |
| (−20%, −10%] | 9 |
| (−30%, −20%] | 14 |
| ≤ −30% (severe drought) | 20 |

**S2 rainfall excess / flood (0–10)** — distinct `flood_risk` driver text.

| Cumulative deviation from normal | Points |
|---|---:|
| < +40% | 0 |
| [+40%, +50%) | 5 |
| ≥ +50% (flood risk) | 10 |

Intervals are evaluated from most severe to least severe; exact boundaries belong to the more severe
row (for example, `−10%` scores 9, while `−9.99%` scores 3). Irrigation is intentionally not a
rainfall modifier; it is scored once as vulnerability signal S9.

**S3 satellite crop stress (0–15)** — `ndvi_anomaly_pct`/`ndwi_anomaly_pct`, Sentinel-2. The MVP
uses a bounded anomaly score and reports `unknown` when the source is absent or stale; it never
claims a disease diagnosis from imagery alone.

**S4 pest/disease pressure (0–8)** — a bounded advisory or farmer-report signal. It is a decision
support input, not a pesticide prescription.

**S13 market price shock (0–20)** — `metric="mandi_price_deviation_pct"`, source Agmarknet/eNAM,
versus the 90-day seasonal median, with a static government MSP reference flag.

| Deviation from normal | Points |
|---|---:|
| ≥ 0% | 0 |
| (−10%, 0%) | 4 |
| (−20%, −10%] | 9 |
| (−30%, −20%] | 14 |
| ≤ −30% | 20 |

An observation at or below MSP receives at least the minimum price-shock points. Boundary cases are
mandatory fixtures.

**Repayment window (0–20)** — opt-in only. Absent entirely (no `due_window` observation, or
`consent.due_window == False`) ⇒ sub-score **omitted from `contributors[]`**, not scored as zero-with-a-driver.

| Days to due date (band midpoint) | Base points |
|---|---:|
| > 30 days | 4 |
| 15–30 days | 10 |
| 7–14 days | 16 |
| ≤ 6 days | 20 |

Amount-band modulation: `low ×0.7`, `medium ×1.0`, `high ×1.15`, result clamped to `[0, 20]`.

**S6–S12 vulnerability multiplier (0.7–1.3)** — apply the adjustments in
`signal_model_fdi_aligned.md` exactly once, then clamp `1.0 + sum(adjustments)` to `[0.7, 1.3]`.
This includes scheme coverage, institutional access, land holding, irrigation, growth stage,
diversification and soil retention. These signals are explainability context, not shock points.

**S14 acute farmer-reported shock (0–7)** — `metric="acute_farmer_report"` or `farmer_report`,
with the bounded intents `health_expense`, `livestock_death`, `no_buyer`, `crop_damaged`, and
`request_callback`.

### Constants (`constants.py`)

```python
MODEL_VERSION: Final[str] = "rules-fdi-0.2.0"       # bump on any rule-table or signal change
SCORE_DISCLAIMER: Final[str] = (
    "This is not a credit, loan-default, or insurance score."
)
BAND_CUTOFFS: Final[dict[str, tuple[int, int]]] = {
    "green": (0, 49), "amber": (50, 69), "red": (70, 100),
}
SHOCK_WEIGHTS: Final[dict[str, int]] = {
    "S1": 20, "S2": 10, "S3": 15, "S4": 8, "S5": 20, "S13": 20, "S14": 7,
}
VULNERABILITY_MULTIPLIER: Final[tuple[float, float]] = (0.7, 1.3)
HYSTERESIS_MIN_OBSERVATIONS: Final[int] = 2
HYSTERESIS_MIN_SPAN_DAYS: Final[int] = 3
DEFAULT_EXPIRY_HOURS: Final[int] = 48
STALE_FRESHNESS_FLOOR: Final[float] = 0.3   # below this, domain is "stale" for suppression purposes
```

---

## 5. Data models / contracts

### Owned by M4 (local, not shared contracts — inputs to compute contributors[])

```python
@dataclass(frozen=True)
class SubScoreResult:
    signal: str                 # S1..S14; S15 is never a SubScoreResult
    points: float               # 0..max_points
    max_points: float
    applicable: bool            # False when a source/opt-in is absent
    stale: bool
    freshness: float            # 0..1
    rule_id: str                # e.g. "rainfall.deficit.severe"
    source: str                 # e.g. "IMD" | "farmer_opt_in" | "farmer_report"
    observed_at: datetime | None
    driver_text: str | None     # human-readable, template-filled

@dataclass(frozen=True)
class Contributor:              # <-- proposed concrete shape for RiskEvent.contributors[]
    signal: str
    points: float
    max_points: float
    explanation: str
    source: str
    observed_at: datetime

@dataclass(frozen=True)
class FarmerContext:            # narrowed, read-only view of M1's FarmerProfile
    farmer_token: str
    village_id: str
    crop: str
    sowing_date: date
    irrigation_type: Literal["rainfed", "partial", "assured"]
    area_band: Literal["<1", "1-2", ">2"] | None = None
    secondary_crop: str | None = None
    schemes_enrolled: list[str] = field(default_factory=list)
    institutional_access: Literal["good", "limited", "unknown"] = "unknown"
    soil_retention: Literal["poor", "medium", "good", "unknown"] = "unknown"

@dataclass(frozen=True)
class BandDecision:
    confirmed_band: Literal["green", "amber", "red"]
    raw_band: Literal["green", "amber", "red"]
    pending_band: str | None
    pending_since: datetime | None
    pending_observation_count: int
    suppressed_escalation: bool
```

> **Proposed to M1:** `Contributor` above is put forward as the concrete schema behind
> `RiskEvent.contributors[]`. This needs M1 sign-off to become canonical (see §14).

### Imported from M1 (canonical — never redefined here)

```python
Observation   { source, observed_at, village_id|plot_grid, metric, value: JsonValue, unit, quality, ttl }
RiskEvent     { event_id, farmer_token, village_id, score, band, confidence,
                contributors[], action_ids[], model_version, evaluated_at, expires_at, context_flags[] }
ConsentContext{ farmer_token, storage, contact, analytics, due_window, consent_scopes[] }
FarmerProfile { farmer_token, village_id, locale, crop, sowing_date, irrigation_type,
                area_band, secondary_crop, schemes_enrolled, consent_flags }
```

`Observation.metric` values M4 recognises: `rainfall_deviation_pct`, `ndvi_anomaly_pct`,
`ndwi_anomaly_pct`, `pest_pressure`, `mandi_price_deviation_pct`, `due_window` (value is the
`{days_to_due, amount_band}` shape, `source="farmer_opt_in"`), `acute_farmer_report` and
`farmer_report`.

---

## 6. Interfaces & APIs

M4 has **no HTTP surface**. It is a library called in-process. All functions are pure and synchronous.

### Inbound — public functions

```python
def compute_risk_event(
    farmer: FarmerContext,
    observations: list[Observation],
    consent: ConsentContext,
    prior_events: list[RiskEvent] | None = None,
    as_of: datetime | None = None,
    model_version: str = MODEL_VERSION,
) -> RiskEvent: ...

# Sub-score rule functions — each independently unit-testable
def score_rainfall_signals(observations: list[Observation], as_of: datetime) -> list[SubScoreResult]: ...
def score_satellite_stress(observations: list[Observation], as_of: datetime) -> SubScoreResult: ...
def score_pest_pressure(observations: list[Observation], as_of: datetime) -> SubScoreResult: ...
def score_price_stress(observations: list[Observation], crop: str, as_of: datetime) -> SubScoreResult: ...
def score_repayment_window(observations: list[Observation], consent: ConsentContext, as_of: datetime) -> SubScoreResult: ...
def vulnerability_signals(farmer: FarmerContext, as_of: datetime) -> list[SubScoreResult]: ...
def score_farmer_reported_shock(observations: list[Observation], as_of: datetime) -> SubScoreResult: ...

# Composable helpers
def band_from_score(score: float) -> Literal["green", "amber", "red"]: ...
def apply_hysteresis(raw_band: str, prior_events: list[RiskEvent], as_of: datetime) -> BandDecision: ...
def compute_confidence(sub_scores: list[SubScoreResult]) -> float: ...
def select_top_drivers(contributors: list[Contributor], n: int = 3) -> list[Contributor]: ...
def compute_expiry(observations: list[Observation], as_of: datetime) -> datetime: ...
```

### Outbound calls to other modules

**None.** Zero network, zero DB, zero imports of `libs/adapters` or `libs/identity-consent` runtime code.
Enforced by a CI guardrail test (see §10).

---

## 7. Dependencies

| Type | Dependency | Why |
|---|---|---|
| Internal (type-only) | M1 `platform_core.models` | `Observation`, `RiskEvent`, `ConsentContext`, `FarmerProfile` type definitions only — no DB session, no FastAPI app import |
| Runtime | Python stdlib only (`dataclasses`, `datetime`, `enum`, `typing`, `statistics`) | Keep the flagship differentiator dependency-free and fast |
| Dev/test | `pytest`, `hypothesis` (property-based determinism tests), `coverage` | Testing strategy §11 |
| Dev | `import-linter` (or equivalent AST check) | Enforces the purity contract in CI |
| Optional (isolated) | `shadow/` extra: e.g. `scikit-learn` | Only inside `shadow/`, never a core dependency, feature-flagged off by default |

**Explicitly forbidden runtime imports:** `requests`, `httpx`, `sqlalchemy`, `psycopg`, `boto3`, `socket`,
anything from `libs/adapters`, `libs/identity-consent`, `services/platform-core.db`.

---

## 8. Tech stack

| Concern | Choice |
|---|---|
| Language | Python 3.11+ |
| Data classes | `@dataclass(frozen=True)` for local types; M1's Pydantic models consumed as-is (validation only, no I/O) |
| Testing | Pytest + Hypothesis (property tests for determinism/order-independence) |
| Coverage gate | 100% branch coverage on `rules/`, `bands.py`, `confidence.py` (flagship differentiator — no untested rule) |
| Purity enforcement | `import-linter` contract in CI: `scoring_engine` may depend on `platform_core.models` only |
| Packaging | `uv`/`setuptools`, versioned as a standalone installable package so M1 pins it explicitly |
| Versioning | `MODEL_VERSION` semver constant, bumped on any threshold/weight/rule change |

---

## 9. Key workflows / sequences

### 9.1 Happy path — recalculation

```mermaid
sequenceDiagram
    participant M3 as M3 Adapters
    participant M1 as M1 Platform Core
    participant M4 as M4 Scoring Engine (pure)
    M3->>M1: POST /api/v1/observations
    M1->>M1: fetch FarmerProfile, ConsentContext,\nlast 3+ days of RiskEvent history
    M1->>M4: compute_risk_event(farmer, observations, consent, prior_events, as_of)
    M4->>M4: 1. validate minimum context
    M4->>M4: 2. per domain: select latest qualifying Observation(s)
    M4->>M4: 3. staleness check (ttl vs as_of) -> freshness
    M4->>M4: 4. run S1-S5 and S13-S14 rules; derive S6-S12 multiplier
    M4->>M4: 5. shock × vulnerability -> final score, clamp [0,100]
    M4->>M4: 6. compute_confidence from shock observations
    M4->>M4: 7. raw_band = band_from_score(total)
    M4->>M4: 8. apply_hysteresis(raw_band, prior_events) -> BandDecision
    M4->>M4: 9. stale-feed suppression check on escalating domains
    M4->>M4: 10. select_top_drivers (top 3, rule+source traced)
    M4->>M4: 11. compute_expiry (min ttl of contributing obs, capped 48h)
    M4->>M4: 12. stamp model_version, assemble RiskEvent
    M4-->>M1: RiskEvent
    M1->>M5: new/updated RiskEvent (case creation on Amber/Red)
    M1->>M6: new/updated RiskEvent (action-card trigger)
```

### 9.2 Step-by-step algorithm (`compute_risk_event`)

1. **Validate minimum context** — `village_id`, `crop`, `irrigation_type`, `sowing_date` present (masterspec
   §4.1). Missing any ⇒ raise `MissingRequiredContextError` (M4 refuses to guess).
2. **Guardrail scan** — reject any `Observation` whose `metric`/value keys match a banned-field pattern
   (`aadhaar`, `bank_account`, `lender_id`, `cibil`, `credit_score`, …) ⇒ `PrivacyGuardrailError`.
   Defense-in-depth; M2/M3 should already prevent this.
3. **Per domain, select observations** — most recent qualifying `Observation`(s) per `metric`, sorted for
   determinism (order-independence guaranteed regardless of input list order).
4. **Staleness** — `freshness = 1.0` if `age ≤ ttl × 0.5`; linear decay to `0.3` at/past the
   TTL (data is still used, never dropped — "stale lowers confidence, never deletes").
5. **Run S1–S5 and S13–S14** → shock `SubScoreResult[]`, each clamped to its authoritative max.
6. **Derive S6–S12** → `vulnerability_multiplier = clamp(1.0 + Σ adjustments, 0.7, 1.3)`.
7. **Final score** — `clamp(sum(shock_points) × vulnerability_multiplier, 0, 100)`.
8. **Confidence** — average freshness/completeness of applicable shock observations; absent opt-in
   repayment is excluded rather than treated as a missing source.
9. **`raw_band = band_from_score(final_score)`** via CRIDA-aligned cutoffs 50/70.
10. **Hysteresis** (`apply_hysteresis`):
   - No prior `RiskEvent` for this farmer ⇒ **bootstrap**: `confirmed_band = raw_band` immediately.
   - `raw_band == confirmed_band` (from most recent prior event) ⇒ band unchanged, pending cleared.
   - `raw_band != confirmed_band` ⇒ update/extend a *pending* band candidate. Confirm the flip only once
     `pending_observation_count ≥ 2` **and** `(as_of − pending_since) ≥ 3 days`. Until then, `confirmed_band`
     stays at the last confirmed value. Applied **symmetrically** for escalation and de-escalation (see
     §14 open question on asymmetric hysteresis).
   - *Demo-timing note:* replay fixtures (`POST /api/v1/replay/scenario`) carry `observed_at` timestamps
     already spaced ≥3 simulated days apart; hysteresis is evaluated on **observation time**, not
     wall-clock processing time, so the "Red within 24h" acceptance test (real demo runtime) and the
     "two observations / three days" hysteresis rule (simulated data time) are not in tension.
11. **Stale-feed suppression** — if an acute signal among the raw top-3 contributors (by point contribution) has
    `freshness < STALE_FRESHNESS_FLOOR`, set `suppressed_escalation = True`: the outgoing `band` is capped
    at `min(raw_band, confirmed_band_before_this_event)`, and `confidence` reflects the staleness. De-escalation
    is never suppressed (dropping risk is always safe to report).
12. **Top-3 drivers** — sort `Contributor[]` by point contribution descending, take top 3, each carrying
    `signal` + `source` + `observed_at` (acceptance: "every driver traces to a rule + source").
13. **Engagement context** — derive S15 text flags from delivery/outreach observations; never add points.
14. **Expiry** — `expires_at = as_of + min(ttl of supplied observations)`, with a 48-hour default when
    no observation is available.
15. **Stamp** `model_version`, `evaluated_at`, disclaimer and assemble `RiskEvent`.

### 9.3 Failure path — stale price feed during a drought

```mermaid
sequenceDiagram
    participant M1 as M1
    participant M4 as M4
    M1->>M4: compute_risk_event(... price obs stale, rainfall obs fresh+severe ...)
    M4->>M4: freshness(price) = 0.1 (past ttl)
    M4->>M4: raw total pushes score to 60+ (Red) but price is a top contributor
    M4->>M4: suppressed_escalation = True -> band capped at prior confirmed band
    M4-->>M1: RiskEvent{band=amber (held), confidence=0.42, contributors include\n"price data unavailable (stale since 2026-08-15)"}
    M1->>M5: no new Red case opened; officer dashboard shows "stale feed" flag instead
```

---

## 10. Error handling, failure modes & guardrails

| Condition | Handling |
|---|---|
| Missing minimum context (`village_id`/`crop`/`irrigation_type`/`sowing_date`) | Raise `MissingRequiredContextError`; M1 must not call recalc until profile is complete |
| Domain has zero observations ever | `applicable=True`, `value=0`, `completeness=0` for that domain — conservative, not silently dropped; contributor note `insufficient_data` |
| Observation past `ttl` | Never discarded; `freshness` decays (step 4); can trigger suppression (step 10) |
| `Observation.value` is `NaN`/`inf`/out of declared unit range | Raise `ScoringInputError` — fail closed, do not silently clamp a corrupt input |
| Banned-field metric/keys (credit/bank/aadhaar-shaped) | Raise `PrivacyGuardrailError` — refuses to score rather than silently including it |
| All domains missing/low completeness | Score defaults low (mostly zeros), `confidence` low, event carries a `confidence_below_threshold` note; M4 does **not** decide routing — that's M5's call |
| Non-deterministic input ordering | Engine sorts/normalises internally before processing; property-tested (Hypothesis) for order-independence |
| Shadow challenger enabled | Runs in a **separate return channel** (`ShadowPrediction`, logged by caller); `engine.py` has no code path that reads shadow output back into `total_score`/`band`/`confidence`/`contributors` — enforced by a dedicated isolation test (§11 #22) |
| Any attempt to expose a probability-of-default-shaped field | Architecturally impossible — `RiskEvent` has no such field, and `SCORE_DISCLAIMER` is exported as the single source of truth for downstream copy (M6/M8 import it rather than re-authoring) |

**Privacy/safety guardrails (module-level):**
- No field, variable, or rule_id in this package may be named/aliased to imply creditworthiness (lint-checked keyword denylist: `credit`, `default_prob`, `cibil`, `score_to_lend`, …).
- `repayment` sub-score is the *only* domain gated by `ConsentContext.due_window`; if false, the domain is fully excluded (not zeroed) from both scoring and confidence denominators.
- Purity is enforced in CI, not just code review (`import-linter` contract fails the build on a forbidden import).

---

## 11. Testing strategy & acceptance criteria

Every rule function, the band/hysteresis state machine, confidence, and driver selection have dedicated
unit tests. Determinism and order-independence are property-tested with Hypothesis. Coverage gate: 100%
branch coverage on `rules/`, `bands.py`, `confidence.py`.

| # | Test | Scenario | Expected result |
|---|---|---|---|
| 1 | Rainfall — severe deficit | −32% deviation | 20 pts, driver "rainfall −32%" |
| 2 | Vulnerability — irrigation | Same shock, assured vs rainfed | S9 changes multiplier by ±0.10 |
| 3 | Rainfall — flood risk | +45% deviation | 5 pts, flood-risk driver text |
| 4 | Price — below-MSP shock | −20% deviation + below-MSP | 14 pts, price driver and MSP flag |
| 5 | Price — no deviation | 0% or positive | 0 pts, no driver text |
| 6 | Repayment — not opted in | `consent.due_window=False`, no `due_window` observation | domain `applicable=False`, absent from `contributors[]`, excluded from confidence denominator |
| 7 | Repayment — opted in, due in 12 days, high amount | consent true | 16×1.15=18.4→18 pts (clamped ≤20), driver "loan due in 12 days" |
| 8 | Growth-stage vulnerability | 40 days since sowing | S10 adds +0.10 multiplier |
| 9 | Soil-retention vulnerability | poor soil | S12 adds +0.05 multiplier |
| 10 | Farmer-reported acute shock | `crop_damaged` | S14 adds 7 points |
| 11 | Engagement context | 2 unanswered outreach attempts | S15 flag only; score unchanged |
| 12 | Band boundary — Green/Amber | score=49 vs score=50 | green vs amber exactly at cutoff |
| 13 | Band boundary — Amber/Red | score=69 vs score=70 | amber vs red exactly at cutoff |
| 14 | Hysteresis — bootstrap | No prior `RiskEvent` for farmer, raw_band=red | `confirmed_band=red` immediately, no delay |
| 15 | Hysteresis — single anomalous observation | Prior confirmed green, one red-qualifying event | band stays green, `pending_band=red`, `pending_observation_count=1` |
| 16 | Hysteresis — confirmed flip | Two red-qualifying events ≥3 days apart (by `observed_at`) | `confirmed_band` flips to red |
| 17 | Hysteresis — de-escalation flip | Two green-qualifying events ≥3 days apart after a confirmed red | `confirmed_band` flips to green (symmetric) |
| 18 | Confidence — full freshness/completeness | All applicable shock signals fresh + present | confidence ≈1.0 |
| 19 | Confidence — one stale feed | Price observation freshness=0.3 | confidence drops proportionally to price's 0.30 weight fraction |
| 20 | Confidence — signal never reported | No farmer report ever | confidence reflects missing applicable signal |
| 21 | Stale-feed suppression | Price stale (freshness<0.3) while otherwise Red-qualifying | `suppressed_escalation=True`, band capped at prior confirmed band, confidence lowered, **no false Red** (masterspec §14 acceptance) |
| 22 | Top-3 drivers traceability | Any qualifying scenario | Contributors carry non-null `signal` + `source`; every driver traces to a rule/source (masterspec §14 acceptance) |
| 23 | **Flagship acceptance test** | Drought (rainfall ≤−30%) + 20% price crash + opted-in due window (≤14 days) + high vulnerability | `total_score ≥ 70`, `band="red"`, `contributors[:3]` includes S1 + S13 + S5, all three driver texts present (masterspec §14 acceptance) |
| 24 | Expiry — bounded by shortest TTL | Rainfall ttl=48h, price ttl=72h | `expires_at ≤ as_of + 48h` |
| 25 | `model_version` stamping | Default call | `RiskEvent.model_version == "rules-fdi-0.2.0"`; changing `MODEL_VERSION` changes the stamp (regression pin) |
| 26 | Guardrail — banned field | `Observation.metric="bank_account_balance"` | Raises `PrivacyGuardrailError`, no `RiskEvent` produced |
| 27 | Determinism / order-independence | Same observation set, shuffled input order (Hypothesis) | Byte-identical `RiskEvent` output |
| 28 | Shadow challenger isolation | Shadow flag enabled, arbitrary shadow prediction | `RiskEvent` output is bit-for-bit identical to shadow-disabled run |
| 29 | Missing minimum context | `sowing_date=None` | Raises `MissingRequiredContextError` |
| 30 | Corrupt input | `Observation.value = float("nan")` | Raises `ScoringInputError` |

**Traceability to masterspec §14:** tests 21, 22, 23 map directly and verbatim to the three named
acceptance tests ("drought+price crash+due window → Red with all three drivers", "stale data lowers
confidence and suppresses escalation", "every action card traces to a rule + source").

---

## 12. MVP boundary vs. stretch

| Build now (MVP) | Stretch / post-prototype |
|---|---|
| All 7 shock rules + S6–S12 multiplier + S15 flag with the bounded tables in §4 | Agronomist-calibrated thresholds per crop, informed by pilot data (§19 KPI: Red precision ≥60% after calibration) |
| Symmetric 2-observation/3-day hysteresis | Asymmetric hysteresis (fast escalate, slow de-escalate) if product decides it's safer |
| Confidence, expiry, stale-feed suppression | Per-domain confidence breakdown surfaced to officer UI (M8) beyond the single scalar |
| Two illustrative MVP crops (cotton, soybean) plus profile vulnerability fields | Full crop table for all-India coverage (explicitly out of MVP per masterspec §13) |
| `model_version` constant, hand-bumped per release | Config-driven, versioned weight/threshold sets loadable without a code redeploy (needed for live recalibration during a pilot) |
| Shadow ML extension point (interface + isolation test), no real model wired | An actual calibrated shadow model once labelled outcomes exist (masterspec §10.D, §20 roadmap) |
| `SCORE_DISCLAIMER` constant exported | Formal legal/compliance review of the disclaimer copy |

---

## 13. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Hysteresis delays a genuinely urgent Red | Bootstrap rule fires immediately for first-ever event; replay fixtures pre-space observations ≥3 simulated days apart so the demo is not blocked; flagged for product review (asymmetric hysteresis candidate, §14) |
| Fixed rule thresholds don't generalise across crops/regions | `model_version` stamping + versioned rule tables make every score attributable to an exact ruleset; pilot recalibration path is a config change, not a rewrite |
| Score misread as a credit/eligibility score despite the label | `SCORE_DISCLAIMER` is a single exported constant (no re-authored copy drift across M6/M8); keyword denylist prevents credit-shaped field names in code itself |
| Irrigation/crop modulation encodes unintended bias (e.g. under-weighting rainfed farmers) | All sub-scores and the multiplier tables are versioned and testable per-crop/irrigation combination; equity reporting data (`area_band`, `crop`) is available to M5 analytics for audit |
| Stale-feed suppression hides a real emergency by holding the band down too aggressively | Suppression only *caps* the band and lowers confidence — it never withholds the event entirely; officer dashboard still sees a flagged, lower-confidence case rather than nothing |
| Shadow ML scope creep into the safety path | Architectural isolation: separate return type/channel, no merge point in `engine.py`, enforced by a dedicated isolation test (§11 #28) |

---

## 14. Open questions / decisions needed

| # | Question | Owner to resolve with |
|---|---|---|
| 1 | Canonicalise `Contributor` (§5) as the concrete schema behind `RiskEvent.contributors[]` | M1 (Platform Core) |
| 2 | Confirm the two MVP crops (spec uses illustrative `cotton`/`soybean`) and their rule-table values | Product / agronomist |
| 3 | Symmetric vs. asymmetric hysteresis (should de-escalation be faster than escalation, or vice versa?) | Product/safety review |
| 4 | Who queries and supplies `prior_events` (last ≥3 days of `RiskEvent` history) — M1 directly or M5? | M1, M5 |
| 5 | Source of `soil_context` (AgriStack prefill via M3, or a static reference table)? | M3 |
| 6 | Ownership of the eventual shadow-ML model (training pipeline, hosting) — M7 or a future dedicated module? | M7 / roadmap owner |
| 7 | Should weight/threshold config become hot-reloadable during a live pilot, or remain a versioned code release? | Platform architecture decision |
