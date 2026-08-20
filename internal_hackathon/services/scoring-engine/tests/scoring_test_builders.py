"""Explicit builders shared by the scoring acceptance tests."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from scoring_engine.types import ConsentContext, FarmerContext, Observation

NOW = datetime(2026, 8, 21, 6, 0, tzinfo=UTC)


def obs(metric: str, value, *, source="test", hours_old: float = 1, ttl_hours: float = 48, **kw) -> Observation:
    return Observation(
        source=source,
        observed_at=NOW - timedelta(hours=hours_old),
        metric=metric,
        value=value,
        ttl=timedelta(hours=ttl_hours),
        **kw,
    )


def farmer(**overrides) -> FarmerContext:
    base = {
        "farmer_token": "tok-1",
        "village_id": "Nashik / Dindori",
        "crop": "cotton",
        "sowing_date": date(2026, 7, 1),
        "irrigation_type": "rainfed",
        "area_band": "<1",
        "secondary_crop": None,
        "schemes_enrolled": [],
        "institutional_access": "limited",
        "soil_retention": "poor",
    }
    base.update(overrides)
    return FarmerContext(**base)


def consent(**overrides) -> ConsentContext:
    base = {"farmer_token": "tok-1", "storage": True, "contact": True, "due_window": False}
    base.update(overrides)
    return ConsentContext(**base)


def low_vulnerability(**overrides) -> FarmerContext:
    return farmer(
        irrigation_type="assured",
        area_band=">2",
        secondary_crop="soybean",
        schemes_enrolled=["pm-kisan"],
        institutional_access="good",
        soil_retention="good",
        sowing_date=date(2026, 1, 1),
        **overrides,
    )
