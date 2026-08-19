"""S4 pest/disease pressure from a bounded advisory/report signal."""
from __future__ import annotations

from datetime import datetime

from ..types import Observation, SubScoreResult
from ._common import latest, numeric, result


def score_pest_pressure(observations: list[Observation], as_of: datetime) -> SubScoreResult:
    observation = latest(observations, "pest_pressure", "pest_seen")
    if observation is None:
        return result("S4", 0, 8, None, as_of, "pest.missing", "advisory", "No pest-pressure signal")
    pressure = numeric(observation.value)
    if isinstance(observation.value, str):
        pressure = 1.0 if observation.value in {"pest_seen", "disease_seen"} else 0.0
    points = min(8, max(0, pressure * 8 if pressure <= 1 else pressure))
    return result("S4", points, 8, observation, as_of, "pest.pressure", observation.source, "Pest or disease pressure reported")
