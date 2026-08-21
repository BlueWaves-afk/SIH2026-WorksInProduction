"""Minimum Support Price reference-table adapter."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .._common import ConfiguredRealAdapter, _rows_from_payload, as_number, first_value, parse_datetime
from ...core.interfaces import ObservationPayload, SignalRequest


class MSPRealAdapter(ConfiguredRealAdapter):
    def __init__(
        self,
        endpoint: str | None = None,
        *,
        api_key: str | None = None,
        timeout_seconds: float = 10.0,
        client=None,
    ):
        super().__init__("msp", endpoint, api_key=api_key, timeout_seconds=timeout_seconds, client=client)

    def _parse_payload(self, payload: Any, fetched_at: datetime, req: SignalRequest) -> list[ObservationPayload]:
        result: list[ObservationPayload] = []
        for row in _rows_from_payload(payload):
            commodity = str(first_value(row, ("commodity", "Commodity", "crop", "Crops", "name")) or "").strip()
            if req.commodity and commodity and commodity.casefold() != req.commodity.casefold():
                continue
            value = as_number(
                first_value(
                    row,
                    (
                        "msp_price",
                        "msp",
                        "MSP",
                        "minimum_support_price",
                        "MSP 2026-27",
                        "MSP 2025-26",
                        "price",
                    ),
                )
            )
            if value is None:
                continue
            season = str(first_value(row, ("season", "marketing_season", "season_year", "year")) or "").strip()
            result.append(
                ObservationPayload(
                    source=self.source,
                    observed_at=parse_datetime(first_value(row, ("observed_at", "effective_from", "date")), fetched_at),
                    village_id=row.get("village_id") or req.village_id,
                    metric="msp_price",
                    value={"commodity": commodity or req.commodity, "price": value, "season": season or None},
                    unit="INR/quintal",
                    ttl=timedelta(days=365),
                )
            )
        return result
