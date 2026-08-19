"""S3 satellite crop-stress signal."""
from __future__ import annotations

from datetime import datetime

from ..types import Observation, SubScoreResult
from ._common import latest, numeric, result


def score_satellite_stress(observations: list[Observation], as_of: datetime) -> SubScoreResult:
    observation = latest(observations, "ndvi_anomaly_pct", "ndwi_anomaly_pct", "satellite_crop_stress")
    if observation is None:
        return result("S3", 0, 15, None, as_of, "satellite.missing", "Sentinel-2", "Satellite crop-stress data unavailable")
    anomaly = numeric(observation.value)
    if isinstance(observation.value, dict):
        anomaly = max(abs(float(observation.value.get("ndvi_anomaly_pct", 0))), abs(float(observation.value.get("ndwi_anomaly_pct", 0))))
    points = min(15, max(0, anomaly) * 0.5)
    return result("S3", points, 15, observation, as_of, "satellite.anomaly", "Sentinel-2", f"Satellite crop-stress anomaly is {anomaly:g}%")
