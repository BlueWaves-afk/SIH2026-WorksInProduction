"""Boundary validation for canonical observations.

The scoring engine remains deliberately pure, but the HTTP/adapter boundary
must reject malformed or privacy-sensitive payloads before they are persisted.
Unknown metrics are allowed for forward-compatible adapters; known metrics get
strict shape/range checks so a provider cannot silently turn a bad value into a
high-confidence support event.
"""

from __future__ import annotations

import math
import re
from typing import Any

from fastapi import HTTPException


_BANNED = re.compile(r"aadhaar|bank[_ -]?account|lender|credit[_ -]?score", re.IGNORECASE)
_NUMERIC_RANGES: dict[str, tuple[float, float]] = {
    "rainfall_deviation_pct": (-100.0, 500.0),
    "rainfall_actual_mm": (0.0, 2000.0),
    "rainfall_excess_pct": (0.0, 500.0),
    "ndvi_anomaly_pct": (-200.0, 200.0),
    "ndwi_anomaly_pct": (-200.0, 200.0),
    "satellite_crop_stress": (0.0, 100.0),
    "pest_pressure": (0.0, 100.0),
    "mandi_modal_price": (0.0, 1_000_000.0),
}
_SOURCES = {
    "imd",
    "agmarknet",
    "agristack",
    "bhashini",
    "bhuvan",
    "msp",
    "sentinel2",
    "soil",
    "farmer",
    "farmer_report",
    "outreach_inbound",
    "replay",
}


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise HTTPException(status_code=422, detail=f"{field} must be a finite number")
    return float(value)


def _check_numeric(metric: str, value: Any) -> None:
    bounds = _NUMERIC_RANGES.get(metric)
    if bounds is None:
        return
    if metric == "pest_pressure" and value in {"pest_seen", "disease_seen", "none", "unknown"}:
        return
    number = value
    if isinstance(value, dict):
        number = value.get("deviation_pct", value.get("value", value.get("score")))
    parsed = _finite_number(number, metric)
    if not bounds[0] <= parsed <= bounds[1]:
        raise HTTPException(status_code=422, detail=f"{metric} must be between {bounds[0]:g} and {bounds[1]:g}")


def validate_observation(*, source: str, metric: str, value: Any, ttl_seconds: int) -> None:
    source = source.strip().lower()
    metric = metric.strip().lower()
    if source not in _SOURCES:
        raise HTTPException(status_code=422, detail=f"unsupported observation source: {source}")
    if not metric or len(metric) > 96:
        raise HTTPException(status_code=422, detail="metric must be non-empty and at most 96 characters")
    if ttl_seconds < 1 or ttl_seconds > 31_536_000:
        raise HTTPException(status_code=422, detail="ttl_seconds must be between 1 second and 365 days")
    if _BANNED.search(metric):
        raise HTTPException(status_code=422, detail="privacy-sensitive fields cannot be scored")
    if isinstance(value, dict):
        for key, child in value.items():
            if _BANNED.search(str(key)):
                raise HTTPException(status_code=422, detail="privacy-sensitive fields cannot be scored")
            if isinstance(child, float) and not math.isfinite(child):
                raise HTTPException(status_code=422, detail="observation contains a non-finite number")
    _check_numeric(metric, value)
    if metric == "mandi_price_deviation_pct":
        if not isinstance(value, (int, float, dict)):
            raise HTTPException(status_code=422, detail="mandi_price_deviation_pct must be numeric or an object")
        if isinstance(value, dict) and "below_msp" in value and not isinstance(value["below_msp"], bool):
            raise HTTPException(status_code=422, detail="below_msp must be boolean")
    if metric == "mandi_below_msp" and not isinstance(value, bool):
        raise HTTPException(status_code=422, detail="mandi_below_msp must be boolean")
    if metric == "due_window":
        if not isinstance(value, dict):
            raise HTTPException(status_code=422, detail="due_window must be an object")
        days = value.get("days_to_due")
        if days is not None and (isinstance(days, bool) or not isinstance(days, (int, float)) or not 0 <= days <= 365):
            raise HTTPException(status_code=422, detail="days_to_due must be between 0 and 365")
        if not days and not value.get("due_date_band"):
            raise HTTPException(status_code=422, detail="due_window needs days_to_due or due_date_band")
    if metric in {"acute_farmer_report", "farmer_report"} and (not isinstance(value, str) or not value.strip() or len(value) > 2000):
        raise HTTPException(status_code=422, detail="farmer report must be a short non-empty string")
    if metric == "outreach_unanswered" and not isinstance(value, (str, int, float, bool)):
        raise HTTPException(status_code=422, detail="outreach_unanswered must be a scalar context value")


__all__ = ["validate_observation"]
