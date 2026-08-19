"""S14 acute farmer-reported shock."""
from __future__ import annotations

from datetime import datetime

from ..types import Observation, SubScoreResult
from ._common import latest, result


def score_farmer_reported_shock(observations: list[Observation], as_of: datetime) -> SubScoreResult:
    observation = latest(observations, "acute_farmer_report", "farmer_report")
    if observation is None:
        return result("S14", 0, 7, None, as_of, "farmer_report.missing", "farmer", "No acute farmer report")
    value = observation.value if isinstance(observation.value, str) else (observation.value or {}).get("intent", "") if isinstance(observation.value, dict) else ""
    acute = value in {"health_expense", "livestock_death", "no_buyer", "crop_damaged", "request_callback"}
    return result("S14", 7 if acute else 0, 7, observation, as_of, "farmer_report.acute", "farmer", f"Farmer-reported shock: {value or 'other'}")
