"""S1 rainfall deficit and S2 rainfall excess/flood rules."""
from __future__ import annotations

from datetime import datetime

from ..types import Observation, SubScoreResult
from ._common import latest, numeric, result


def score_rainfall_signals(observations: list[Observation], as_of: datetime) -> list[SubScoreResult]:
    observation = latest(observations, "rainfall_deviation_pct")
    if observation is None:
        return [
            result("S1", 0, 20, None, as_of, "rainfall.missing", "IMD", "Rainfall data unavailable"),
            result("S2", 0, 10, None, as_of, "rainfall.missing", "IMD", "Rainfall data unavailable"),
        ]
    deviation = numeric(observation.value)
    deficit_points = 0 if deviation >= 0 else 3 if deviation > -10 else 9 if deviation > -20 else 14 if deviation > -30 else 20
    excess_points = 10 if deviation >= 50 else 5 if deviation >= 40 else 0
    return [
        result("S1", deficit_points, 20, observation, as_of, "rainfall.deficit", "IMD", f"Rainfall {abs(deviation):g}% below normal" if deviation < 0 else "Rainfall is normal or above normal"),
        result("S2", excess_points, 10, observation, as_of, "rainfall.excess", "IMD", f"Rainfall {deviation:g}% above normal; flood-risk signal" if excess_points else "No flood-risk rainfall signal"),
    ]


def score_rainfall_shock(observations: list[Observation], irrigation_type: str, as_of: datetime) -> SubScoreResult:
    """Compatibility aggregate for callers that still expect one rainfall result."""
    signals = score_rainfall_signals(observations, as_of)
    total = sum(item.points for item in signals)
    observation = latest(observations, "rainfall_deviation_pct")
    return result("rainfall", total, 30, observation, as_of, "rainfall.aggregate", "IMD", "; ".join(item.driver_text or "" for item in signals))
