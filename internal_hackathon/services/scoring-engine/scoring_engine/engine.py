"""compute_risk_event() — the single public entrypoint.

PURITY CONTRACT: this package imports nothing from M1/M2/M3/M5/M6/M7 and performs
no I/O. Give it observations, get a RiskEvent back. That is what makes the score
auditable and testable — and what lets us say it is not a black box.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from .bands import apply_hysteresis, band_from_score
from .confidence import compute_confidence, suppress_escalation
from .constants import MODEL_VERSION, SCORE_DISCLAIMER, VULN_BASE, VULN_MAX, VULN_MIN
from .drivers import contributors_from_scores, select_top_drivers
from .guardrails import assert_safe_metric
from .rules.engagement_flag import engagement_context_flags
from .rules.farmer_report import score_farmer_reported_shock
from .rules.pest_pressure import score_pest_pressure
from .rules.price import score_price_stress
from .rules.rainfall import score_rainfall_signals
from .rules.repayment import score_repayment_window
from .rules.satellite_stress import score_satellite_stress
from .rules.vulnerability import vulnerability_signals
from .types import ConsentContext, FarmerContext, Observation, RiskEvent, SubScoreResult


def compute_expiry(observations: list[Observation], as_of: datetime) -> datetime:
    observed = [item.observed_at + item.ttl for item in observations]
    return min(observed, default=as_of + timedelta(hours=48))


def compute_risk_event(
    farmer: FarmerContext,
    observations: list[Observation],
    consent: ConsentContext,
    prior_events: list[RiskEvent] | None = None,
    as_of: datetime | None = None,
    model_version: str = MODEL_VERSION,
) -> RiskEvent:
    """Compute the deterministic FDI-aligned event without I/O or external calls."""
    now = as_of or datetime.now(UTC)
    prior_events = prior_events or []
    for observation in observations:
        assert_safe_metric(observation.metric, observation.value)

    shock_scores: list[SubScoreResult] = [
        *score_rainfall_signals(observations, now),
        score_satellite_stress(observations, now),
        score_pest_pressure(observations, now),
        score_repayment_window(observations, consent, now),
        score_price_stress(observations, farmer.crop, now),
        score_farmer_reported_shock(observations, now),
    ]
    vulnerability = vulnerability_signals(farmer, now)
    shock_score = sum(item.points for item in shock_scores)
    vulnerability_multiplier = max(VULN_MIN, min(VULN_MAX, VULN_BASE + sum(item.points for item in vulnerability)))
    final_score = max(0.0, min(100.0, shock_score * vulnerability_multiplier))
    raw_band = band_from_score(final_score)
    confidence = compute_confidence(shock_scores)
    decision = apply_hysteresis(raw_band, prior_events, now)
    contributors = select_top_drivers(contributors_from_scores(shock_scores), 3)
    flags = engagement_context_flags(observations)
    if suppress_escalation(confidence):
        flags.append("escalation suppressed: low confidence")
        if decision.confirmed_band == "red":
            decision = decision.__class__("amber", decision.raw_band, decision.pending_band, decision.pending_since, decision.pending_observation_count, True)
    return RiskEvent(
        event_id=str(uuid4()),
        farmer_token=farmer.farmer_token,
        village_id=farmer.village_id,
        score=round(final_score, 4),
        band=decision.confirmed_band,
        confidence=round(confidence, 4),
        contributors=contributors,
        action_ids=[],
        model_version=model_version,
        evaluated_at=now,
        expires_at=compute_expiry(observations, now),
        disclaimer=SCORE_DISCLAIMER,
        context_flags=flags,
    )
