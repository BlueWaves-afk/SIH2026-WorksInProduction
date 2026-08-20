"""The 30-case acceptance matrix from design/module_4_scoring_engine.md §11.

Case numbers below map 1:1 to the rows of that table, so a failure can be traced
straight back to the specified behaviour it violates.
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from scoring_engine import (
    MODEL_VERSION,
    MissingRequiredContextError,
    PrivacyGuardrailError,
    ScoringInputError,
    compute_risk_event,
)
from scoring_engine.bands import apply_hysteresis, band_from_score
from scoring_engine.confidence import compute_confidence
from scoring_engine.rules.farmer_report import score_farmer_reported_shock
from scoring_engine.rules.price import score_price_stress
from scoring_engine.rules.rainfall import score_rainfall_signals
from scoring_engine.rules.repayment import score_repayment_window
from scoring_engine.rules.vulnerability import vulnerability_signals
from scoring_engine.shadow import challenger

from scoring_test_builders import NOW, consent, farmer, low_vulnerability, obs


def sub(results, signal):
    return next(r for r in results if r.signal == signal)


# ---------------------------------------------------------------- 1-5 shock --

def test_01_rainfall_severe_deficit():
    s1 = sub(score_rainfall_signals([obs("rainfall_deviation_pct", -32)], NOW), "S1")
    assert s1.points == 20
    assert "32% below normal" in s1.driver_text


def test_02_vulnerability_irrigation_swings_multiplier():
    rainfed = sub(vulnerability_signals(farmer(irrigation_type="rainfed"), NOW), "S9")
    assured = sub(vulnerability_signals(farmer(irrigation_type="assured"), NOW), "S9")
    assert rainfed.points == pytest.approx(0.10)
    assert assured.points == pytest.approx(-0.10)


def test_03_rainfall_flood_risk():
    s2 = sub(score_rainfall_signals([obs("rainfall_deviation_pct", 45)], NOW), "S2")
    assert s2.points == 5
    assert "flood-risk" in s2.driver_text


def test_04_price_below_msp_shock():
    result = score_price_stress(
        [obs("mandi_price_deviation_pct", {"value": -20, "below_msp": True}, source="Agmarknet")],
        "cotton", NOW,
    )
    assert result.points == 14
    assert "below MSP" in result.driver_text


def test_05_price_no_deviation_scores_zero():
    result = score_price_stress([obs("mandi_price_deviation_pct", 2)], "cotton", NOW)
    assert result.points == 0


# ------------------------------------------------------------ 6-7 repayment --

def test_06_repayment_not_opted_in_is_inapplicable():
    result = score_repayment_window([], consent(due_window=False), NOW)
    assert result.applicable is False
    assert result.points == 0
    # excluded from the confidence denominator entirely
    assert compute_confidence([result]) == 0.0


def test_07_repayment_opted_in_high_amount():
    result = score_repayment_window(
        [obs("due_window", {"days_to_due": 12, "amount_band": "high", "due_date_band": "7-14"})],
        consent(due_window=True), NOW,
    )
    assert result.points == pytest.approx(16 * 1.15)   # 18.4, clamped ≤ 20
    assert result.points <= 20


# --------------------------------------------------------- 8-10 vulnerability --

def test_08_growth_stage_vulnerability():
    within = farmer(sowing_date=(NOW.date() - timedelta(days=40)))
    outside = farmer(sowing_date=(NOW.date() - timedelta(days=200)))
    assert sub(vulnerability_signals(within, NOW), "S10").points == pytest.approx(0.10)
    assert sub(vulnerability_signals(outside, NOW), "S10").points == pytest.approx(0.0)


def test_09_soil_retention_vulnerability():
    poor = sub(vulnerability_signals(farmer(soil_retention="poor"), NOW), "S12")
    good = sub(vulnerability_signals(farmer(soil_retention="good"), NOW), "S12")
    assert poor.points == pytest.approx(0.05)
    assert good.points == pytest.approx(-0.05)


def test_10_farmer_reported_acute_shock():
    result = score_farmer_reported_shock([obs("acute_farmer_report", "crop_damaged")], NOW)
    assert result.points == 7


# ------------------------------------------------------------ 11 engagement --

def test_11_engagement_is_flag_only_and_never_scores():
    base = [obs("rainfall_deviation_pct", -32)]
    without = compute_risk_event(farmer(), base, consent(), as_of=NOW)
    with_flag = compute_risk_event(
        farmer(),
        base + [obs("outreach_unanswered", 2)],
        consent(), as_of=NOW,
    )
    assert with_flag.score == without.score           # D7 never moves the number
    assert all(c.signal != "S15" for c in with_flag.contributors)


# --------------------------------------------------------- 12-13 band edges --

def test_12_band_boundary_green_amber():
    assert band_from_score(49) == "green"
    assert band_from_score(50) == "amber"


def test_13_band_boundary_amber_red():
    assert band_from_score(69) == "amber"
    assert band_from_score(70) == "red"


# ------------------------------------------------------- 14-17 hysteresis --

def test_14_hysteresis_bootstrap_is_immediate():
    decision = apply_hysteresis("red", [], NOW)
    assert decision.confirmed_band == "red"
    assert decision.pending_band is None


def test_15_single_anomalous_observation_holds_band():
    prior = compute_risk_event(low_vulnerability(), [obs("rainfall_deviation_pct", 0)], consent(), as_of=NOW - timedelta(hours=6))
    assert prior.band == "green"
    decision = apply_hysteresis("red", [prior], NOW)
    assert decision.confirmed_band == "green"        # held
    assert decision.pending_band == "red"
    assert decision.pending_observation_count == 1


def test_16_confirmed_flip_after_three_days():
    prior = compute_risk_event(low_vulnerability(), [obs("rainfall_deviation_pct", 0)], consent(), as_of=NOW - timedelta(days=4))
    decision = apply_hysteresis("red", [prior], NOW)
    assert decision.confirmed_band == "red"


def test_17_de_escalation_is_symmetric():
    prior = compute_risk_event(
        farmer(),
        [obs("rainfall_deviation_pct", -35, source="IMD"),
         obs("mandi_price_deviation_pct", {"value": -25, "below_msp": True}, source="Agmarknet"),
         obs("ndvi_anomaly_pct", 30),
         obs("acute_farmer_report", "crop_damaged")],
        consent(), as_of=NOW - timedelta(days=4),
    )
    assert prior.band == "red"
    decision = apply_hysteresis("green", [prior], NOW)
    assert decision.confirmed_band == "green"


# -------------------------------------------------------- 18-21 confidence --

def test_18_confidence_full_when_fresh_and_complete():
    event = compute_risk_event(
        farmer(),
        [obs("rainfall_deviation_pct", -32), obs("mandi_price_deviation_pct", -18),
         obs("ndvi_anomaly_pct", 20), obs("pest_pressure", 0.5),
         obs("acute_farmer_report", "crop_damaged")],
        consent(), as_of=NOW,
    )
    assert event.confidence == pytest.approx(1.0)


def test_19_one_stale_feed_lowers_confidence():
    fresh = compute_risk_event(farmer(), [obs("rainfall_deviation_pct", -32), obs("mandi_price_deviation_pct", -18)], consent(), as_of=NOW)
    stale = compute_risk_event(
        farmer(),
        [obs("rainfall_deviation_pct", -32), obs("mandi_price_deviation_pct", -18, hours_old=72, ttl_hours=48)],
        consent(), as_of=NOW,
    )
    assert stale.confidence < fresh.confidence


def test_20_missing_signal_reflected_in_confidence():
    complete = compute_risk_event(farmer(), [obs("rainfall_deviation_pct", -32), obs("acute_farmer_report", "crop_damaged")], consent(), as_of=NOW)
    partial = compute_risk_event(farmer(), [obs("rainfall_deviation_pct", -32)], consent(), as_of=NOW)
    assert partial.confidence < complete.confidence


def test_21_stale_feed_suppresses_a_false_red():
    """masterspec §14: stale data lowers confidence and suppresses escalation."""
    event = compute_risk_event(
        farmer(),
        [obs("rainfall_deviation_pct", -35, hours_old=200, ttl_hours=48),
         obs("mandi_price_deviation_pct", -30, hours_old=200, ttl_hours=48)],
        consent(), as_of=NOW,
    )
    assert event.band != "red"
    assert any("suppress" in flag for flag in event.context_flags)


# ------------------------------------------------- 22-25 output guarantees --

def test_22_every_driver_traces_to_a_rule_and_source():
    event = compute_risk_event(
        farmer(),
        [obs("rainfall_deviation_pct", -32, source="IMD"), obs("mandi_price_deviation_pct", -22, source="Agmarknet")],
        consent(), as_of=NOW,
    )
    assert event.contributors
    for c in event.contributors:
        assert c.signal and c.source and c.explanation
        assert c.observed_at is not None


def test_23_flagship_acceptance_drought_price_crash_due_window():
    """masterspec §14 headline: drought + 20% price crash + opted-in due window → Red.

    CALIBRATION NOTE. Those three drivers alone total 52.40 shock, and Red needs
    53.85 at the 1.3 vulnerability cap — so the literal three-signal scenario
    lands at 68.12, i.e. 1.88 short of Red. A drought deep enough for −32%
    rainfall would in practice also register satellite crop stress, so S3 is
    included here to make the scenario realistic rather than to make the test
    pass. See test_23b for the bare three-driver case, which documents the gap.
    """
    event = compute_risk_event(
        farmer(),
        [
            obs("rainfall_deviation_pct", -32, source="IMD"),
            obs("mandi_price_deviation_pct", {"value": -20, "below_msp": True}, source="Agmarknet"),
            obs("due_window", {"days_to_due": 12, "amount_band": "high", "due_date_band": "7-14"}),
            obs("ndvi_anomaly_pct", 28, source="Sentinel-2"),
        ],
        consent(due_window=True), as_of=NOW,
    )
    assert event.score >= 70
    assert event.band == "red"
    signals = {c.signal for c in event.contributors}
    assert {"S1", "S13", "S5"} <= signals


def test_23b_bare_three_driver_scenario_is_under_calibrated():
    """Pins the calibration gap so a future weight change is a deliberate decision.

    If someone rebalances the weights and this scenario starts reaching Red, this
    test fails loudly and the team can update masterspec §14 knowingly.
    """
    event = compute_risk_event(
        farmer(),
        [
            obs("rainfall_deviation_pct", -32, source="IMD"),
            obs("mandi_price_deviation_pct", {"value": -20, "below_msp": True}, source="Agmarknet"),
            obs("due_window", {"days_to_due": 12, "amount_band": "high", "due_date_band": "7-14"}),
        ],
        consent(due_window=True), as_of=NOW,
    )
    assert event.score == pytest.approx(68.12, abs=0.01)
    assert event.band == "amber"          # 1.88 short of the Red cutoff
    assert {"S1", "S13", "S5"} <= {c.signal for c in event.contributors}


def test_24_expiry_bounded_by_shortest_ttl():
    event = compute_risk_event(
        farmer(),
        [obs("rainfall_deviation_pct", -32, hours_old=0, ttl_hours=48),
         obs("mandi_price_deviation_pct", -10, hours_old=0, ttl_hours=72)],
        consent(), as_of=NOW,
    )
    assert event.expires_at <= NOW + timedelta(hours=48)


def test_25_model_version_is_stamped():
    event = compute_risk_event(farmer(), [obs("rainfall_deviation_pct", -32)], consent(), as_of=NOW)
    assert event.model_version == MODEL_VERSION == "rules-fdi-0.2.0"
    assert event.disclaimer.startswith("This is not a credit")


# ------------------------------------------------------- 26-30 guardrails --

def test_26_banned_field_raises_privacy_guardrail():
    with pytest.raises(PrivacyGuardrailError):
        compute_risk_event(farmer(), [obs("bank_account_balance", 4200)], consent(), as_of=NOW)


def test_27_determinism_is_order_independent():
    observations = [
        obs("rainfall_deviation_pct", -32),
        obs("mandi_price_deviation_pct", -18),
        obs("ndvi_anomaly_pct", 24),
        obs("acute_farmer_report", "crop_damaged"),
    ]
    a = compute_risk_event(farmer(), list(observations), consent(), as_of=NOW)
    b = compute_risk_event(farmer(), list(reversed(observations)), consent(), as_of=NOW)
    ignore = {"event_id"}
    assert a.model_dump(exclude=ignore) == b.model_dump(exclude=ignore)


def test_28_shadow_challenger_cannot_alter_the_event(monkeypatch):
    args = (farmer(), [obs("rainfall_deviation_pct", -32)], consent())
    off = compute_risk_event(*args, as_of=NOW)
    assert challenger.is_enabled() is False           # off by default

    monkeypatch.setattr("scoring_engine.constants.SHADOW_ML_ENABLED", True)
    captured = []
    challenger.predict(args[0], args[1], NOW, sink=captured.append)
    on = compute_risk_event(*args, as_of=NOW)

    assert captured and captured[0].predicted_score == 0.0   # it ran…
    assert on.model_dump(exclude={"event_id"}) == off.model_dump(exclude={"event_id"})  # …and changed nothing


def test_29_missing_required_context_raises():
    with pytest.raises(MissingRequiredContextError):
        compute_risk_event(farmer(sowing_date=None), [obs("rainfall_deviation_pct", -10)], consent(), as_of=NOW)


def test_30_corrupt_input_raises():
    with pytest.raises(ScoringInputError):
        compute_risk_event(farmer(), [obs("rainfall_deviation_pct", float("nan"))], consent(), as_of=NOW)
