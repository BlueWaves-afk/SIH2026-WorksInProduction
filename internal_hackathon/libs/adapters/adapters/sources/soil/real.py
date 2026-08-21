"""Soil Health Card / department soil-observation adapter."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .._common import ConfiguredRealAdapter, _rows_from_payload, as_number, first_value, parse_datetime
from ...core.interfaces import ObservationPayload, SignalRequest


class SoilRealAdapter(ConfiguredRealAdapter):
    def __init__(
        self,
        endpoint: str | None = None,
        *,
        api_key: str | None = None,
        timeout_seconds: float = 10.0,
        client=None,
    ):
        super().__init__("soil", endpoint, api_key=api_key, timeout_seconds=timeout_seconds, client=client)

    def _parse_payload(self, payload: Any, fetched_at: datetime, req: SignalRequest) -> list[ObservationPayload]:
        result: list[ObservationPayload] = []
        for row in _soil_rows(payload):
            observed_at = parse_datetime(first_value(row, ("observed_at", "sample_date", "date", "timestamp")), fetched_at)
            village_id = row.get("village_id") or req.village_id
            values: list[tuple[str, Any, str]] = []

            retention = first_value(row, ("soil_retention", "retention_class", "water_holding_capacity", "available_water_capacity_class"))
            if retention is not None:
                values.append(("soil_retention", str(retention).strip().lower(), "class"))
            water_capacity = as_number(first_value(row, ("soil_water_holding_capacity", "available_water_capacity", "awc")))
            if water_capacity is not None:
                values.append(("soil_water_holding_capacity", water_capacity, "percent"))
            for metric, keys, unit in (
                ("soil_ph", ("soil_ph", "ph", "pH"), "pH"),
                ("soil_electrical_conductivity", ("electrical_conductivity", "ec", "EC"), "dS/m"),
                ("soil_organic_carbon_pct", ("organic_carbon_pct", "organic_carbon", "OC"), "percent"),
                ("soil_nitrogen_kg_ha", ("nitrogen_kg_ha", "available_nitrogen", "N"), "kg/ha"),
                ("soil_phosphorus_kg_ha", ("phosphorus_kg_ha", "available_phosphorus", "P"), "kg/ha"),
                ("soil_potassium_kg_ha", ("potassium_kg_ha", "available_potassium", "K"), "kg/ha"),
            ):
                number = as_number(first_value(row, keys))
                if number is not None:
                    values.append((metric, number, unit))

            for metric, value, unit in values:
                result.append(
                    ObservationPayload(
                        source=self.source,
                        observed_at=observed_at,
                        village_id=village_id,
                        plot_grid=row.get("plot_grid") or row.get("sample_id"),
                        metric=metric,
                        value=value,
                        unit=unit,
                        ttl=timedelta(days=365),
                    )
                )
        return result


def _soil_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        direct = {
            "soil_retention",
            "retention_class",
            "water_holding_capacity",
            "soil_water_holding_capacity",
            "ph",
            "pH",
            "organic_carbon",
            "available_nitrogen",
        }
        if direct.intersection(payload):
            return [payload]
    return _rows_from_payload(payload)
