"""Shadow ML challenger — logged only, never in the safety path.

The rules engine decides. A challenger model may run alongside it so that, once
officer resolutions have produced real labels, we can measure a candidate before
it is ever allowed to act (see design/research_risk_modelling.md, "v1 earns v2").

Isolation contract, asserted by tests:
  * `predict()` never influences `compute_risk_event()`'s output;
  * predictions leave via `sink` only — nothing is returned into the event;
  * the feature flag is **off** by default.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .. import constants
from ..types import FarmerContext, Observation


@dataclass(frozen=True)
class ShadowPrediction:
    """What a challenger thought, recorded for later comparison. Never acted on."""

    farmer_token: str
    predicted_score: float
    challenger_version: str
    predicted_at: datetime
    features: dict[str, Any]


# A sink is any callable that persists a prediction (M1 supplies a real one).
ShadowSink = Callable[[ShadowPrediction], None]


def is_enabled() -> bool:
    """Shadow scoring is opt-in and off by default."""
    return bool(getattr(constants, "SHADOW_ML_ENABLED", False))


def predict(
    farmer: FarmerContext,
    observations: list[Observation],
    as_of: datetime,
    sink: ShadowSink | None = None,
    challenger_version: str = "shadow-none-0.0.0",
) -> ShadowPrediction | None:
    """Record a challenger prediction. Returns None when the flag is off.

    The placeholder challenger has no trained model yet — it emits a null-score
    prediction so the plumbing, isolation tests and sink contract are exercised
    before any real model exists.
    """
    if not is_enabled():
        return None

    features = {
        "observation_count": len(observations),
        "metrics": sorted({item.metric for item in observations}),
        "irrigation_type": farmer.irrigation_type,
        "area_band": farmer.area_band,
    }
    prediction = ShadowPrediction(
        farmer_token=farmer.farmer_token,
        predicted_score=0.0,
        challenger_version=challenger_version,
        predicted_at=as_of,
        features=features,
    )
    if sink is not None:
        sink(prediction)
    return prediction


__all__ = ["ShadowPrediction", "ShadowSink", "is_enabled", "predict"]
