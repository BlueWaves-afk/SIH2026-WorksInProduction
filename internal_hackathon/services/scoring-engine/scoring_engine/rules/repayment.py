"""S5 coarse, opt-in repayment-window signal."""
from __future__ import annotations

from datetime import datetime

from ..types import ConsentContext, Observation, SubScoreResult
from ._common import latest, result


def score_repayment_window(
    observations: list[Observation], consent: ConsentContext, as_of: datetime
) -> SubScoreResult:
    observation = latest(observations, "due_window")
    if not consent.due_window:
        return result("S5", 0, 20, None, as_of, "repayment.not_opted_in", "farmer_opt_in", None, False)
    if observation is None:
        return result("S5", 0, 20, None, as_of, "repayment.missing", "farmer_opt_in", "Opted-in due window unavailable")
    value = observation.value if isinstance(observation.value, dict) else {}
    days = value.get("days_to_due")
    band = str(value.get("due_date_band", ""))
    if not isinstance(days, (int, float)):
        days = {"0-6": 3, "7-14": 10, "15-30": 22, ">30": 45}.get(band, 45)
    points = 20 if days <= 6 else 16 if days <= 14 else 10 if days <= 30 else 4
    amount = str(value.get("amount_band", "medium"))
    multiplier = {"low": 0.7, "medium": 1.0, "high": 1.15}.get(amount, 1.0)
    points = min(20, points * multiplier)
    return result("S5", points, 20, observation, as_of, "repayment.window", "farmer_opt_in", f"Opted-in due window is {band or f'{days:g} days'}")
