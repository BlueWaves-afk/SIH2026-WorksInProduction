"""Deterministic replay driver; no network or database dependency.

The JSON files under ``fixtures/scenarios`` document the same recipes for reviewers;
the built-in values below keep this installable package self-contained when fixtures
are not packaged into a wheel.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pydantic import BaseModel

from ..core.interfaces import ObservationPayload
from .scenarios import SCENARIO_IDS


class ScenarioNotFound(ValueError):
    pass


class DayOffsetOutOfRange(ValueError):
    pass


class DueWindow(BaseModel):
    days_to_due: int
    amount_band: str = "medium"
    consent_required: bool = True


class ReplayBundle(BaseModel):
    scenario_id: str
    day_offset: int
    observations: list[ObservationPayload]
    due_window: DueWindow | None = None


class ReplayDriver:
    def list_scenarios(self) -> list[str]:
        return sorted(SCENARIO_IDS)

    def generate(self, scenario_id: str, day_offset: int) -> ReplayBundle:
        if scenario_id not in SCENARIO_IDS:
            raise ScenarioNotFound(scenario_id)
        if not 0 <= day_offset < 90:
            raise DayOffsetOutOfRange("day_offset must be between 0 and 89")
        as_of = datetime(2026, 6, 1, tzinfo=UTC) + timedelta(days=day_offset)
        stale = scenario_id == "stale_data"
        observed_at = as_of - timedelta(days=20 if stale else 0)
        rainfall = {
            "normal": 2,
            "rainfall_shock": -30,
            "price_crash": 2,
            "due_window": 2,
            "stale_data": -30,
        }[scenario_id]
        price = {
            "normal": 2,
            "rainfall_shock": -25,
            "price_crash": -25,
            "due_window": 2,
            "stale_data": -25,
        }[scenario_id]
        satellite_stress = {
            "normal": 0,
            "rainfall_shock": 12,
            "price_crash": 8,
            "due_window": 0,
            "stale_data": 12,
        }[scenario_id]
        pest_pressure = {
            "normal": 0,
            "rainfall_shock": 0,
            "price_crash": 0,
            "due_window": 0,
            "stale_data": 0,
        }[scenario_id]
        due = scenario_id in {"rainfall_shock", "due_window", "stale_data"}
        due_days = 5 if scenario_id == "rainfall_shock" else 14
        observations = [
            ObservationPayload(
                source="imd",
                observed_at=observed_at,
                village_id="demo-village",
                metric="rainfall_deviation_pct",
                value=rainfall,
                unit="percent",
                ttl=timedelta(days=2),
            ),
            ObservationPayload(
                source="agmarknet",
                observed_at=observed_at,
                village_id="demo-village",
                metric="mandi_price_deviation_pct",
                value={"deviation_pct": price, "below_msp": price < -10},
                unit="percent",
                ttl=timedelta(days=3),
            ),
            # MSP, soil and Bhuvan are intentionally replayed as ordinary
            # observations so the demo exercises every restricted provider
            # without depending on credentials or network availability.
            ObservationPayload(
                source="msp",
                observed_at=observed_at,
                village_id="demo-village",
                metric="msp_price",
                value=7121,
                unit="inr_per_quintal",
                ttl=timedelta(days=365),
            ),
            ObservationPayload(
                source="bhuvan",
                observed_at=observed_at,
                village_id="demo-village",
                metric="village_coordinates",
                value={"lat": 20.0, "lon": 73.8},
                unit="geojson",
                ttl=timedelta(days=30),
            ),
            ObservationPayload(
                source="soil",
                observed_at=observed_at,
                village_id="demo-village",
                metric="soil_water_holding_capacity",
                value="medium",
                unit="class",
                ttl=timedelta(days=365),
            ),
        ]
        bundle_due = DueWindow(days_to_due=due_days) if due else None
        if due:
            observations.append(
                ObservationPayload(
                    source="farmer_opt_in",
                    observed_at=observed_at,
                    village_id="demo-village",
                    metric="due_window",
                    value={"days_to_due": due_days, "amount_band": "medium"},
                    unit="days",
                    ttl=timedelta(days=7),
                )
            )
        observations.extend(
            [
                ObservationPayload(
                    source="sentinel2",
                    observed_at=observed_at,
                    village_id="demo-village",
                    metric="satellite_crop_stress",
                    value=satellite_stress,
                    unit="percent",
                    ttl=timedelta(days=10),
                ),
                ObservationPayload(
                    source="advisory",
                    observed_at=observed_at,
                    village_id="demo-village",
                    metric="pest_pressure",
                    value=pest_pressure,
                    unit="ratio",
                    ttl=timedelta(days=2),
                ),
                ObservationPayload(
                    source="farmer",
                    observed_at=observed_at,
                    village_id="demo-village",
                    metric="acute_farmer_report",
                    value="none",
                    ttl=timedelta(days=2),
                ),
            ]
        )
        return ReplayBundle(
            scenario_id=scenario_id,
            day_offset=day_offset,
            observations=observations,
            due_window=bundle_due,
        )
