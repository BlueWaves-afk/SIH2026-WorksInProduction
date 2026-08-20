from datetime import datetime
from typing import Any

from .._common import ConfiguredRealAdapter, _rows_from_payload, as_number, first_value, parse_datetime
from ...core.interfaces import ObservationPayload, SignalRequest


class IMDRealAdapter(ConfiguredRealAdapter):
    """IMD rainfall adapter.

    The official IMD rainfall endpoint exposes fields such as ``Daily Actual``,
    ``Daily Normal`` and ``Daily Departure Per``.  A deployment can also point
    this adapter at a small department proxy that returns canonical rows; both
    shapes are accepted so provider field changes do not leak into the scorer.
    """

    def __init__(
        self,
        endpoint: str | None = None,
        *,
        api_key: str | None = None,
        timeout_seconds: float = 10.0,
        client=None,
    ):
        super().__init__("imd", endpoint, api_key=api_key, timeout_seconds=timeout_seconds, client=client)

    def _parse_payload(self, payload: Any, fetched_at: datetime, req: SignalRequest) -> list[ObservationPayload]:
        result: list[ObservationPayload] = []
        for row in _rows_from_payload(payload):
            # Canonical proxy rows are accepted as-is.
            if row.get("metric") in {"rainfall_deviation_pct", "rainfall_actual_mm"} and "value" in row:
                result.append(
                    ObservationPayload(
                        source=self.source,
                        observed_at=parse_datetime(row.get("observed_at") or row.get("date"), fetched_at),
                        village_id=row.get("village_id") or req.village_id,
                        metric=str(row["metric"]),
                        value=row["value"],
                        unit=str(row.get("unit", "percent")),
                    )
                )
                continue

            actual = as_number(
                first_value(
                    row,
                    (
                        "Daily Actual",
                        "Daily Actual (mm)",
                        "daily_actual",
                        "rainfall_actual_mm",
                        "Last 24 hrs Rainfall",
                    ),
                )
            )
            normal = as_number(
                first_value(
                    row,
                    ("Daily Normal", "daily_normal", "rainfall_normal_mm"),
                )
            )
            departure = as_number(
                first_value(
                    row,
                    (
                        "Daily Departure Per",
                        "daily_departure_per",
                        "rainfall_deviation_pct",
                        "departure_pct",
                    ),
                )
            )
            # IMD may return "-100%" or a numeric percentage.  If a provider
            # only supplies actual/normal, derive the departure transparently.
            if departure is None and actual is not None and normal not in (None, 0):
                departure = ((actual - normal) / normal) * 100
            if departure is None:
                continue
            result.append(
                ObservationPayload(
                    source=self.source,
                    observed_at=parse_datetime(
                        first_value(row, ("observed_at", "Date", "date", "Date of Observation")),
                        fetched_at,
                    ),
                    village_id=row.get("village_id") or req.village_id,
                    metric="rainfall_deviation_pct",
                    value=departure,
                    unit="percent",
                )
            )
        return result
