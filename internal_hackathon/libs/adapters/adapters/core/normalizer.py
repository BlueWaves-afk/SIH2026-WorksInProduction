"""Conservative raw-payload normalisation.

Source-specific adapters should validate their payload first. This helper only maps
known field names and never invents a value for a missing field.
"""
from __future__ import annotations

from datetime import UTC, datetime

from .interfaces import ObservationPayload, RawPayload
from .ttl import TTLPolicy

METRIC_ALIASES = {
    "rainfall": "rainfall_actual",
    "rainfall_actual_mm": "rainfall_actual",
    "rainfall_deviation": "rainfall_deviation_pct",
    "modal_price": "mandi_modal_price",
    "price_deviation_pct": "mandi_price_deviation_pct",
    "ndvi": "ndvi_anomaly_pct",
    "ndwi": "ndwi_anomaly_pct",
    "soil_water_holding": "soil_water_holding_capacity",
}


def normalize(payload: RawPayload, ttl_policy: TTLPolicy | None = None) -> list[ObservationPayload]:
    policy = ttl_policy or TTLPolicy()
    rows = payload.body.get("observations", payload.body.get("data", []))
    if isinstance(rows, dict):
        rows = [rows]
    if not isinstance(rows, list):
        raise TypeError("raw payload must contain a list under observations or data")
    result: list[ObservationPayload] = []
    for row in rows:
        if not isinstance(row, dict):
            raise TypeError("observation row must be an object")
        metric = str(row.get("metric") or row.get("field") or "").strip()
        if not metric:
            raise ValueError("observation row is missing metric")
        metric = METRIC_ALIASES.get(metric, metric)
        observed_at = row.get("observed_at") or payload.fetched_at
        if isinstance(observed_at, str):
            observed_at = datetime.fromisoformat(observed_at)
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=UTC)
        result.append(
            ObservationPayload(
                source=payload.source,
                observed_at=observed_at,
                village_id=row.get("village_id"),
                plot_grid=row.get("plot_grid"),
                metric=metric,
                value=row.get("value"),
                unit=str(row.get("unit", "")),
                ttl=policy.ttl_for(payload.source, metric),
            )
        )
    return result
