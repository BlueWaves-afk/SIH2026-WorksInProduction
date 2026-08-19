"""S13 market-price shock, including the below-MSP flag."""
from __future__ import annotations

from datetime import datetime

from ..types import Observation, SubScoreResult
from ._common import latest, numeric, result


def score_price_stress(observations: list[Observation], crop: str, as_of: datetime) -> SubScoreResult:
    observation = latest(observations, "mandi_price_deviation_pct")
    if observation is None:
        return result("S13", 0, 20, None, as_of, "price.missing", "Agmarknet", "Market price data unavailable")
    deviation = numeric(observation.value)
    if isinstance(observation.value, dict):
        below_msp = bool(observation.value.get("below_msp", False))
    else:
        below_msp = False
    points = 0 if deviation >= 0 else 4 if deviation > -10 else 9 if deviation > -20 else 14 if deviation > -30 else 20
    if below_msp and points < 4:
        points = 4
    text = f"{crop} price {abs(deviation):g}% below its 90-day median"
    if below_msp:
        text += " and below MSP"
    return result("S13", points, 20, observation, as_of, "price.stress", observation.source, text)
