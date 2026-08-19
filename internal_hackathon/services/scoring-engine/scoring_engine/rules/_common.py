"""Small pure helpers shared by FDI signal rules."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from ..confidence import observation_freshness
from ..guardrails import assert_safe_metric
from ..types import Observation, SubScoreResult


def latest(observations: list[Observation], *metrics: str) -> Observation | None:
    candidates = [item for item in observations if item.metric in metrics]
    if not candidates:
        return None
    return max(candidates, key=lambda item: item.observed_at)


def numeric(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        for key in ("deviation_pct", "drop_pct", "value", "score", "pressure"):
            if key in value and isinstance(value[key], (int, float)):
                return float(value[key])
    return default


def result(
    signal: str,
    points: float,
    maximum: float,
    observation: Observation | None,
    as_of: datetime,
    rule_id: str,
    source: str | None = None,
    text: str | None = None,
    applicable: bool = True,
) -> SubScoreResult:
    if observation is not None:
        assert_safe_metric(observation.metric, observation.value)
    return SubScoreResult(
        signal=signal,
        points=max(0.0, min(float(maximum), float(points))),
        max_points=float(maximum),
        applicable=applicable,
        stale=observation.is_stale(as_of) if observation is not None else False,
        freshness=observation_freshness(observation, as_of) if observation is not None else 0.0,
        rule_id=rule_id,
        source=source or (observation.source if observation else "derived"),
        observed_at=observation.observed_at if observation else None,
        driver_text=text,
    )
