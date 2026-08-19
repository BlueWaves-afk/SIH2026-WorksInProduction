"""Observation — produced by M3 (adapters), consumed by M4 (scoring)."""
from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Quality(str, Enum):
    GOOD = "good"
    DEGRADED = "degraded"
    STALE = "stale"
    MISSING = "missing"


class Observation(BaseModel):
    """A single normalised signal reading from any source.

    TTL rule (masterspec §4.2): a reading past its TTL is *never dropped* — it is
    marked STALE, which lowers confidence downstream and can suppress escalation.
    """
    source: str = Field(..., examples=["imd", "agmarknet", "farmer_report"])
    observed_at: datetime
    village_id: str | None = None
    plot_grid: str | None = None
    metric: str = Field(..., examples=["rainfall_actual", "modal_price"])
    # Source adapters may emit a scalar or a small structured value (for example
    # `{ndvi_anomaly_pct, ndwi_anomaly_pct}` or `{days_to_due, amount_band}`).
    # M4 validates the metric-specific shape; M1 preserves it losslessly.
    value: Any
    unit: str = Field(..., examples=["mm", "inr_per_quintal"])
    quality: Quality = Quality.GOOD
    ttl: timedelta

    def is_stale(self, now: datetime) -> bool:
        return (now - self.observed_at) > self.ttl
