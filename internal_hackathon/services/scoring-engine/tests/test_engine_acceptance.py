"""Acceptance tests from masterspec §14.

These intentionally use only deterministic fixtures and the pure M4 entrypoint;
no database, API key or external feed is required.
"""
from datetime import UTC, date, datetime, timedelta

from scoring_engine.engine import compute_risk_event
from scoring_engine.types import ConsentContext, FarmerContext, Observation

NOW = datetime(2026, 6, 1, tzinfo=UTC)


def farmer() -> FarmerContext:
    return FarmerContext(
        farmer_token="farmer-demo",
        village_id="village-demo",
        crop="cotton",
        sowing_date=date(2026, 4, 20),
        irrigation_type="rainfed",
        area_band="<1",
        institutional_access="limited",
        soil_retention="poor",
    )


def observation(metric: str, value, source: str, ttl_days: int = 2) -> Observation:
    return Observation(
        source=source,
        observed_at=NOW,
        village_id="village-demo",
        metric=metric,
        value=value,
        unit="percent" if "pct" in metric else "",
        ttl=timedelta(days=ttl_days),
    )


def test_drought_price_crash_and_due_window_produces_red_with_three_drivers():
    """Drought + 20% price crash + opted-in due window -> Red with a complete feed snapshot."""
    event = compute_risk_event(
        farmer(),
        [
            observation("rainfall_deviation_pct", -30, "imd"),
            observation(
                "mandi_price_deviation_pct",
                {"deviation_pct": -20, "below_msp": True},
                "agmarknet",
                3,
            ),
            observation(
                "due_window",
                {"days_to_due": 5, "amount_band": "medium"},
                "farmer_opt_in",
                7,
            ),
            observation("satellite_crop_stress", 0, "sentinel2", 10),
            observation("pest_pressure", 0, "advisory", 2),
            observation("acute_farmer_report", "none", "farmer", 2),
        ],
        ConsentContext(farmer_token="farmer-demo", storage=True, due_window=True),
        as_of=NOW,
    )

    assert event.band == "red"
    assert event.score >= 70
    assert {driver.signal for driver in event.contributors} >= {"S1", "S5", "S13"}


def test_stale_data_lowers_confidence_and_suppresses_escalation():
    """A feed past its TTL lowers confidence and cannot manufacture Red."""
    stale = Observation(
        source="imd",
        observed_at=NOW - timedelta(days=10),
        village_id="village-demo",
        metric="rainfall_deviation_pct",
        value=-30,
        unit="percent",
        ttl=timedelta(days=2),
    )
    event = compute_risk_event(
        farmer(),
        [stale],
        ConsentContext(farmer_token="farmer-demo"),
        as_of=NOW,
    )

    assert event.confidence < 0.45
    assert event.band != "red"
    assert any("suppressed" in flag for flag in event.context_flags)


def test_every_driver_traces_to_a_rule_and_source():
    """Each returned contributor carries an explanation, source and timestamp."""
    event = compute_risk_event(
        farmer(),
        [observation("rainfall_deviation_pct", -30, "imd")],
        ConsentContext(farmer_token="farmer-demo"),
        as_of=NOW,
    )

    assert event.contributors
    assert event.confidence < 1
    for driver in event.contributors:
        assert driver.explanation
        assert driver.source
        assert driver.observed_at is not None
