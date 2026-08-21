"""S13 market-price shock, including the below-MSP flag."""
from __future__ import annotations

from datetime import datetime

from ..types import Observation, SubScoreResult
from ._common import latest, numeric, result


def score_price_stress(observations: list[Observation], crop: str, as_of: datetime) -> SubScoreResult:
    observation = latest(observations, "mandi_price_deviation_pct")
    msp_flag = latest(observations, "mandi_below_msp")
    if observation is None and msp_flag is None:
        return result("S13", 0, 20, None, as_of, "price.missing", "Agmarknet", "Market price data unavailable")
    deviation = numeric(observation.value) if observation is not None else 0.0
    if isinstance(observation.value if observation is not None else None, dict):
        below_msp = bool(observation.value.get("below_msp", False))
    else:
        below_msp = bool(msp_flag.value) if msp_flag is not None else False
    points = 0 if deviation >= 0 else 4 if deviation > -10 else 9 if deviation > -20 else 14 if deviation > -30 else 20
    if below_msp and points < 4:
        points = 4
    text = f"{crop} price {abs(deviation):g}% below its 90-day median" if observation is not None else f"{crop} market quote is available"
    if below_msp:
        text += " and below MSP"
    source = observation.source if observation is not None else msp_flag.source if msp_flag is not None else "Agmarknet"
    evidence = observation if observation is not None else msp_flag
    return result("S13", points, 20, evidence, as_of, "price.stress", source, text)
