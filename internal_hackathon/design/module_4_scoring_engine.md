# Module 4 — Explainable Scoring Engine

Package: `services/scoring-engine` · Owner concern: deterministic rules that turn `Observation`s into a
`RiskEvent`. Read `masterspecv1.md` (§3, §4, §14) and `module_0_architecture_overview.md` (§3, §4, §5)
first — this spec conforms to both and does not redefine any contract owned by M1.

> **Purity contract:** this module is a pure-Python library. No network calls, no DB writes, no imports
> of M2 (`identity-consent`) or M3 (`adapters`) runtime code. It imports only *type definitions* from M1.
> Same inputs → same outputs, always. This is what makes "the score is not a model" defensible.

---

## 1. Module purpose & responsibilities

- Compute a 0–100 **support-priority score** from up to five weighted sub-scores.
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
- The five sub-score rule functions (rainfall, price, repayment, crop/soil, farmer-reported).
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
    types.py             # SubScoreResult, Contributor, FarmerContext, ScoreContext, BandDecision (local types)
    guardrails.py         # banned-field scan, disclaimer export, purity assertions
    confidence.py          # freshness() + completeness() + weighted aggregate
    drivers.py              # driver text templates + top-3 selection
    bands.py                 # band_from_score() + BandHysteresis state machine
    rules/
      rainfall.py             # score_rainfall_shock()
      price.py                 # score_price_stress()
      repayment.py              # score_repayment_window()
      crop_soil.py               # score_crop_soil_vulnerability()
      farmer_report.py            # score_farmer_reported_shock()
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
    test_crop_soil.py
    test_farmer_report.py
    test_bands_hysteresis.py
    test_confidence.py
    test_drivers.py
    test_guardrails.py
    test_engine_acceptance.py        # masterspecv1.md §14, verbatim
  pyproject.toml
```

### Rule tables (MVP calibration placeholders — see §14 open questions)

**Rainfall shock (0–35)** — `metric="rainfall_deviation_pct"`, source IMD.

| Cumulative deviation from normal | Base points (rainfed, multiplier 1.0) |
|---|---:|
| ≥ 0% (normal/surplus) | 0 |
| (−10%, 0%) | 5 |
| (−20%, −10%] | 15 |
| (−30%, −20%] | 25 |
| ≤ −30% (severe drought) | 35 |
| ≥ +40% (flood risk) | 20 (distinct `flood_risk` driver text) |

Intervals are half-open and evaluated from most severe to least severe; the exact boundary belongs
to the more severe row (for example, `−10%` scores 15, while `−9.99%` scores 5). Values between
`−0%` and `0%` are normalized to zero. The positive flood-risk rule is evaluated independently.

Irrigation modulation (applied after base lookup): `rainfed × 1.0`, `irrigated × 0.4` (irrigation absorbs
most of the rainfall shock but not all — irrigation infrastructure itself can fail).

**Mandi price stress (0–30)** — `metric="mandi_price_deviation_pct"`, source Agmarknet/eNAM, vs. crop's
trailing 30-day normal modal price.

| Deviation from normal | Points |
|---|---:|
| ≥ 0% | 0 |
| (−10%, 0%) | 8 |
| (−20%, −10%] | 18 |
| (−30%, −20%] | 26 |
| ≤ −30% | 30 |

The price intervals use the same half-open convention as rainfall: `−10%` belongs to the 18-point
row, `−20%` to 26 points, and `−30%` to 30 points. Boundary cases are mandatory fixtures.

**Repayment window (0–20)** — opt-in only. Absent entirely (no `due_window` observation, or
`consent.due_window == False`) ⇒ sub-score **omitted from `contributors[]`**, not scored as zero-with-a-driver.

| Days to due date (band midpoint) | Base points |
|---|---:|
| > 30 days | 4 |
| 15–30 days | 10 |
| 7–14 days | 16 |
| ≤ 6 days | 20 |

Amount-band modulation: `low ×0.7`, `medium ×1.0`, `high ×1.15`, result clamped to `[0, 20]`.

**Crop/soil vulnerability (0–10)** — illustrative MVP crops `cotton`, `soybean` (confirm with product —
see §14).

| Days since sowing | Points |
|---|---:|
| 0–20 (germination) | 6 |
| 21–60 (flowering/vegetative — most sensitive) | 10 |
| 61–90 (maturation) | 5 |
| > 90 (near-harvest) | 2 |

Crop sensitivity multiplier: `cotton ×1.0`, `soybean ×0.8`. Optional `soil_context.poor_soil == True`
adds a flat `+1`, result clamped to `[0, 10]`.

**Farmer-reported shock (0–5)** — `metric="farmer_report"`, enum `{pest_seen, no_buyer, crop_damaged, other}`,
7-day lookback.

| Distinct events in window | Points |
|---|---:|
| 0 | 0 |
| 1 | 3 |
| ≥ 2 | 5 |

### Constants (`constants.py`)

```python
MODEL_VERSION: Final[str] = "rules-v1.0.0"          # semver; bump on any rule-table change
SCORE_DISCLAIMER: Final[str] = (
    "This is not a credit, loan-default, or insurance score."
)
BAND_CUTOFFS: Final[dict[str, tuple[int, int]]] = {
    "green": (0, 29), "amber": (30, 59), "red": (60, 100),
}
WEIGHTS: Final[dict[str, int]] = {
    "rainfall": 35, "price": 30, "repayment": 20, "crop_soil": 10, "farmer_report": 5,
}
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
    domain: str                 # "rainfall" | "price" | "repayment" | "crop_soil" | "farmer_report"
    value: float                # 0..max_value
    max_value: float
    applicable: bool            # False for repayment when not opted in
    stale: bool
    freshness: float            # 0..1
    rule_id: str                # e.g. "rainfall.deficit.severe"
    source: str                 # e.g. "IMD" | "farmer_opt_in" | "farmer_report"
    observed_at: datetime | None
    driver_text: str | None     # human-readable, template-filled

@dataclass(frozen=True)
class Contributor:              # <-- proposed concrete shape for RiskEvent.contributors[]
    rule_id: str
    label: str
    sub_score: float
    max_sub_score: float
    weight_pct: float
    source: str
    observed_at: datetime | None
    confidence: float
    driver_text: str

@dataclass(frozen=True)
class FarmerContext:            # narrowed, read-only view of M1's FarmerProfile
    farmer_token: str
    village_id: str
    crop: str
    sowing_date: date
    irrigation_type: Literal["rainfed", "irrigated"]
    area_band: str | None = None
    soil_context: "SoilContext | None" = None

@dataclass(frozen=True)
class SoilContext:
    poor_soil: bool = False

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
                contributors[], action_ids[], model_version, expires_at }
ConsentContext{ farmer_token, storage, contact, analytics, due_window, consent_scopes[] }
FarmerProfile { farmer_token, village_id, locale, crop, sowing_date,
                irrigation_type, area_band, consent_flags }
```

`Observation.metric` values M4 recognises: `rainfall_deviation_pct`, `mandi_price_deviation_pct`,
`due_window` (value is the `{due_date_band, amount_band}` shape, `source="farmer_opt_in"`),
`farmer_report` (value is the enum event).

---

## 6. Interfaces & APIs

M4 has **no HTTP surface**. It is a library called in-process. All functions are pure and synchronous.

### Inbound — public functions

```python
def compute_risk_event(
    farmer: FarmerContext,
    observations: list[Observation],
    consent: ConsentContext,
    prior_events: list[RiskEvent],       # most-recent-first, caller supplies >= last 3 days of history
    as_of: datetime,
    model_version: str = MODEL_VERSION,
) -> RiskEvent: ...

# Sub-score rule functions — each independently unit-testable
def score_rainfall_shock(observations: list[Observation], irrigation_type: str, as_of: datetime) -> SubScoreResult: ...
def score_price_stress(observations: list[Observation], crop: str, as_of: datetime) -> SubScoreResult: ...
def score_repayment_window(observations: list[Observation], consent: ConsentContext, as_of: datetime) -> SubScoreResult: ...
def score_crop_soil_vulnerability(crop: str, sowing_date: date, soil_context: SoilContext | None, as_of: date) -> SubScoreResult: ...
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
    M4->>M4: 4. run 5 rule functions -> SubScoreResult[]
    M4->>M4: 5. sum -> total score, clamp [0,100]
    M4->>M4: 6. compute_confidence (weight-normalised)
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
4. **Staleness** — `freshness = 1.0` if `age ≤ ttl × 0.5`; linear decay to `0.3` between `ttl×0.5` and
   `ttl`; floor `0.1` beyond `ttl` (data still used, never dropped — "stale lowers confidence, never
   deletes").
5. **Run the 5 rule functions** (rule tables in §4) → `SubScoreResult[]`, each clamped to `[0, domain max]`.
6. **Sum** sub-score values (only `applicable=True` domains) → `total_score`, clamp `[0, 100]`.
7. **Confidence** — `Σ (weight_fraction_i × freshness_i × completeness_i)` re-normalised over applicable
   domains only (repayment excluded from the denominator when not opted in — absence isn't missing data).
8. **`raw_band = band_from_score(total_score)`** via `BAND_CUTOFFS`.
9. **Hysteresis** (`apply_hysteresis`):
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
10. **Stale-feed suppression** — if a domain among the raw top-3 contributors (by point contribution) has
    `freshness < STALE_FRESHNESS_FLOOR`, set `suppressed_escalation = True`: the outgoing `band` is capped
    at `min(raw_band, confirmed_band_before_this_event)`, and `confidence` reflects the staleness. De-escalation
    is never suppressed (dropping risk is always safe to report).
11. **Top-3 drivers** — sort `Contributor[]` by point contribution descending, take top 3, each carrying
    `rule_id` + `source` + `observed_at` (acceptance: "every driver traces to a rule + source").
12. **Expiry** — `expires_at = min(as_of + DEFAULT_EXPIRY_HOURS, as_of + min(ttl of contributing observations))`.
13. **Stamp** `model_version`, assemble and return `RiskEvent`.

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
| 1 | Rainfall — rainfed severe drought | −32% deviation, rainfed | 35 pts, driver "rainfall −32%" |
| 2 | Rainfall — irrigation modulation | Same −32% deviation, irrigated | ≈14 pts (35×0.4), lower driver rank |
| 3 | Rainfall — flood risk | +45% deviation, rainfed | 20 pts, `flood_risk` driver text |
| 4 | Price — linear scaling | −20% deviation | 26 pts, driver "cotton −20%" |
| 5 | Price — no deviation | 0% or positive | 0 pts, no driver text |
| 6 | Repayment — not opted in | `consent.due_window=False`, no `due_window` observation | domain `applicable=False`, absent from `contributors[]`, excluded from confidence denominator |
| 7 | Repayment — opted in, due in 12 days, high amount | consent true | 16×1.15=18.4→18 pts (clamped ≤20), driver "loan due in 12 days" |
| 8 | Crop/soil — flowering stage | 40 days since sowing, cotton | 10 pts (peak vulnerability) |
| 9 | Crop/soil — near harvest | 100 days since sowing | 2 pts |
| 10 | Farmer-reported — single event | 1 `pest_seen` in 7d window | 3 pts |
| 11 | Farmer-reported — multiple events | 2+ events, mixed types | 5 pts (capped) |
| 12 | Band boundary — Green/Amber | score=29 vs score=30 | green vs amber exactly at cutoff |
| 13 | Band boundary — Amber/Red | score=59 vs score=60 | amber vs red exactly at cutoff |
| 14 | Hysteresis — bootstrap | No prior `RiskEvent` for farmer, raw_band=red | `confirmed_band=red` immediately, no delay |
| 15 | Hysteresis — single anomalous observation | Prior confirmed green, one red-qualifying event | band stays green, `pending_band=red`, `pending_observation_count=1` |
| 16 | Hysteresis — confirmed flip | Two red-qualifying events ≥3 days apart (by `observed_at`) | `confirmed_band` flips to red |
| 17 | Hysteresis — de-escalation flip | Two green-qualifying events ≥3 days apart after a confirmed red | `confirmed_band` flips to green (symmetric) |
| 18 | Confidence — full freshness/completeness | All 5 domains fresh + present | confidence ≈1.0 |
| 19 | Confidence — one stale feed | Price observation freshness=0.3 | confidence drops proportionally to price's 0.30 weight fraction |
| 20 | Confidence — domain never reported | No farmer_report ever | completeness=0 for that domain, confidence reduced by its 0.05 weight fraction |
| 21 | Stale-feed suppression | Price stale (freshness<0.3) while otherwise Red-qualifying | `suppressed_escalation=True`, band capped at prior confirmed band, confidence lowered, **no false Red** (masterspec §14 acceptance) |
| 22 | Top-3 drivers traceability | Any qualifying scenario | Exactly 3 contributors returned, each with non-null `rule_id` + `source`; every driver traces to a rule/source (masterspec §14 acceptance) |
| 23 | **Flagship acceptance test** | Drought (rainfall ≤−30%, rainfed) + 20% price crash + opted-in due window (≤14 days) | `total_score ≥ 60`, `band="red"`, `contributors[:3]` = rainfall + price + repayment, all three driver texts present (masterspec §14 acceptance, verbatim) |
| 24 | Expiry — bounded by shortest TTL | Rainfall ttl=48h, price ttl=72h | `expires_at ≤ as_of + 48h` |
| 25 | `model_version` stamping | Default call | `RiskEvent.model_version == "rules-v1.0.0"`; changing `MODEL_VERSION` changes the stamp (regression pin) |
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
| All 5 rule functions with the placeholder tables in §4 | Agronomist-calibrated thresholds per crop, informed by pilot data (§19 KPI: Red precision ≥60% after calibration) |
| Symmetric 2-observation/3-day hysteresis | Asymmetric hysteresis (fast escalate, slow de-escalate) if product decides it's safer |
| Confidence, expiry, stale-feed suppression | Per-domain confidence breakdown surfaced to officer UI (M8) beyond the single scalar |
| Two illustrative MVP crops (cotton, soybean) | Full crop table for all-India coverage (explicitly out of MVP per masterspec §13) |
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
