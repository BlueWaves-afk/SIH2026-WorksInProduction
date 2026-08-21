"""Bhuvan/NRSC geospatial adapter.

Bhuvan exposes several products (JSON search services, GeoJSON endpoints and
OGC WMS/WMTS layers).  The scoring pipeline consumes observations, not map
tiles, so this adapter intentionally accepts JSON/GeoJSON responses from a
department proxy or Bhuvan search endpoint.  WMS URLs can still be used by the
frontend map, but they are not parsed as score observations here.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .._common import ConfiguredRealAdapter, _rows_from_payload, as_number, first_value, parse_datetime
from ...core.interfaces import ObservationPayload, SignalRequest


class BhuvanRealAdapter(ConfiguredRealAdapter):
    def __init__(
        self,
        endpoint: str | None = None,
        *,
        api_key: str | None = None,
        timeout_seconds: float = 10.0,
        client=None,
    ):
        super().__init__("bhuvan", endpoint, api_key=api_key, timeout_seconds=timeout_seconds, client=client)

    def _parse_payload(self, payload: Any, fetched_at: datetime, req: SignalRequest) -> list[ObservationPayload]:
        result: list[ObservationPayload] = []
        for row in _geo_rows(payload):
            observed_at = parse_datetime(first_value(row, ("observed_at", "date", "timestamp")), fetched_at)
            village_id = row.get("village_id") or req.village_id

            lat = as_number(first_value(row, ("latitude", "lat", "y")))
            lon = as_number(first_value(row, ("longitude", "lon", "lng", "x")))
            geometry = row.get("geometry")
            if (lat is None or lon is None) and isinstance(geometry, dict):
                coords = geometry.get("coordinates")
                if isinstance(coords, (list, tuple)) and len(coords) >= 2 and geometry.get("type") == "Point":
                    lon = as_number(coords[0])
                    lat = as_number(coords[1])
            if lat is not None and lon is not None and -90 <= lat <= 90 and -180 <= lon <= 180:
                result.append(
                    ObservationPayload(
                        source=self.source,
                        observed_at=observed_at,
                        village_id=village_id,
                        metric="village_coordinates",
                        value={"lat": lat, "lon": lon},
                        unit="geojson",
                        ttl=timedelta(days=30),
                    )
                )

            # Preserve useful Bhuvan/NRSC layers when the endpoint returns a
            # tabular feature response.  These are reference observations; no
            # Bhuvan field is silently converted into a risk score.
            for metric, keys, unit in (
                ("elevation_m", ("elevation_m", "elevation", "altitude"), "m"),
                ("land_use_class", ("land_use_class", "lulc", "landuse", "class"), "class"),
                ("flood_depth_mm", ("flood_depth_mm", "flood_depth", "depth"), "mm"),
                ("soil_moisture_pct", ("soil_moisture_pct", "soil_moisture"), "percent"),
            ):
                value = first_value(row, keys)
                if value is None or value == "":
                    continue
                numeric = as_number(value)
                result.append(
                    ObservationPayload(
                        source=self.source,
                        observed_at=observed_at,
                        village_id=village_id,
                        metric=metric,
                        value=numeric if numeric is not None else str(value),
                        unit=unit,
                        ttl=timedelta(days=7),
                    )
                )
        return result


def _geo_rows(payload: Any) -> list[dict[str, Any]]:
    """Flatten common JSON and GeoJSON response envelopes."""

    if isinstance(payload, dict) and payload.get("type") == "FeatureCollection":
        features = payload.get("features")
        rows: list[dict[str, Any]] = []
        if isinstance(features, list):
            for feature in features:
                if not isinstance(feature, dict):
                    continue
                properties = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
                rows.append({**properties, "geometry": feature.get("geometry")})
        return rows
    if isinstance(payload, dict) and payload.get("type") == "Feature":
        properties = payload.get("properties") if isinstance(payload.get("properties"), dict) else {}
        return [{**properties, "geometry": payload.get("geometry")}]
    return _rows_from_payload(payload)
