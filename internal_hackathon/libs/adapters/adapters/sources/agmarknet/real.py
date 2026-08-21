from datetime import datetime, timedelta
from typing import Any

from .._common import ConfiguredRealAdapter, _rows_from_payload, as_number, first_value, parse_datetime
from ...core.interfaces import ObservationPayload, SignalRequest


class AgmarknetRealAdapter(ConfiguredRealAdapter):
    """AGMARKNET/OGD market-price adapter.

    Rows may come from the official OGD catalog (``commodity``, ``market``,
    ``modal_price``) or from a department proxy with an explicit seasonal
    baseline.  We always preserve the modal quote and only emit the FDI price
    shock when a baseline/deviation is actually present; the adapter never
    invents a baseline from a single quote.
    """

    def __init__(
        self,
        endpoint: str | None = None,
        *,
        api_key: str | None = None,
        timeout_seconds: float = 10.0,
        client=None,
    ):
        super().__init__("agmarknet", endpoint, api_key=api_key, timeout_seconds=timeout_seconds, client=client)

    def _request_params(self, req: SignalRequest) -> dict[str, str]:
        """Add the official OGD query contract when pointed at data.gov.in.

        The OGD gateway documents ``api-key``, ``format=json`` and ``limit``
        as query parameters.  Department-owned proxies continue to use the
        generic header-based contract.
        """

        params = super()._request_params(req)
        if self.endpoint and "data.gov.in" in self.endpoint:
            # Keep the request bounded.  The OGD resource is a national
            # catalogue; an unfiltered 1,000-row request can time out before
            # the scorer ever sees a fresh quote.  The adapter is called per
            # farmer, so a small recent window is the safer default.
            params.update({"format": "json", "limit": "100"})
            if self.api_key:
                params["api-key"] = self.api_key
            if req.commodity:
                params["filters[commodity]"] = req.commodity
            if req.district_id:
                params["filters[district]"] = req.district_id
            if req.mandi_id:
                params["filters[market]"] = req.mandi_id
        return params

    def _parse_payload(self, payload: Any, fetched_at: datetime, req: SignalRequest) -> list[ObservationPayload]:
        result: list[ObservationPayload] = []
        for row in _rows_from_payload(payload):
            commodity = str(first_value(row, ("commodity", "Commodity", "Commodity_Name", "crop")) or "").strip()
            if req.commodity and commodity and commodity.casefold() != req.commodity.casefold():
                continue
            mandi_id = str(first_value(row, ("mandi_id", "market_id", "Market", "market")) or "").strip()
            if req.mandi_id and mandi_id and mandi_id.casefold() != req.mandi_id.casefold():
                continue
            observed_at = parse_datetime(
                first_value(row, ("observed_at", "date", "arrival_date", "Arrival_Date", "Date", "price_date")),
                fetched_at,
            )
            modal = as_number(first_value(row, ("modal_price", "Modal Price", "Modal_Price", "modal", "price")))
            if modal is not None:
                result.append(
                    ObservationPayload(
                        source=self.source,
                        observed_at=observed_at,
                        village_id=row.get("village_id") or req.village_id,
                        metric="mandi_modal_price",
                        value=modal,
                        unit="INR/quintal",
                        ttl=timedelta(days=3),
                    )
                )

            deviation = as_number(
                first_value(row, ("deviation_pct", "price_deviation_pct", "seasonal_deviation_pct"))
            )
            baseline = as_number(first_value(row, ("seasonal_median", "baseline_price", "median_price")))
            if deviation is None and modal is not None and baseline not in (None, 0):
                deviation = ((modal - baseline) / baseline) * 100
            if deviation is None:
                continue
            msp = as_number(first_value(row, ("msp", "MSP", "minimum_support_price", "MSP_Price")))
            below_msp = bool(row.get("below_msp", msp is not None and modal is not None and modal < msp))
            result.append(
                ObservationPayload(
                    source=self.source,
                    observed_at=observed_at,
                    village_id=row.get("village_id") or req.village_id,
                    metric="mandi_price_deviation_pct",
                    value={"deviation_pct": deviation, "below_msp": below_msp},
                    unit="percent",
                    ttl=timedelta(days=3),
                )
            )
        return result
