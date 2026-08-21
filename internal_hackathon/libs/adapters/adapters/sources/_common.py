"""Small interchangeable source-adapter implementations used by the MVP."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
import math
from typing import Any, Iterable

import httpx

from ..core.health import AdapterHealth, HealthTracker
from ..core.interfaces import (
    ASRResult,
    AdapterMode,
    ObservationPayload,
    ProfilePrefill,
    SignalRequest,
)


class MockSignalAdapter:
    def __init__(self, source: str, rows: list[dict[str, Any]] | None = None):
        self.source = source
        self.mode = AdapterMode.MOCK
        self._rows = rows or []
        self._health = HealthTracker(source, self.mode)

    def fetch(self, req: SignalRequest) -> list[ObservationPayload]:
        now = datetime.now(UTC)
        result = [
            ObservationPayload(
                source=self.source,
                observed_at=row.get("observed_at", now),
                village_id=row.get("village_id") or req.village_id,
                metric=row["metric"],
                value=row.get("value"),
                unit=row.get("unit", ""),
                ttl=row.get("ttl", timedelta(days=2)),
            )
            for row in self._rows
            if not req.village_id or not row.get("village_id") or row.get("village_id") == req.village_id
        ]
        self._health.success(now)
        return result

    def health(self) -> AdapterHealth:
        return self._health.snapshot()


class MockProfileAdapter:
    source = "agristack"
    mode = AdapterMode.MOCK

    def __init__(self):
        self._health = HealthTracker(self.source, self.mode)

    def fetch_profile(self, consent: Any, farmer_ref: str) -> ProfilePrefill:
        if not getattr(consent, "storage", False):
            raise PermissionError("storage consent is required for AgriStack prefill")
        now = datetime.now(UTC)
        self._health.success(now)
        return ProfilePrefill(
            farmer_ref=farmer_ref,
            village_id="demo-village",
            crop="cotton",
            land_area_band="<1",
            irrigation_type="rainfed",
            fetched_at=now,
        )

    def health(self) -> AdapterHealth:
        return self._health.snapshot()


class MockVoiceAdapter:
    source = "bhashini"
    mode = AdapterMode.MOCK

    def __init__(self):
        self._health = HealthTracker(self.source, self.mode)

    def transcribe(self, audio: bytes, lang: str) -> ASRResult:
        del audio
        self._health.success(datetime.now(UTC))
        return ASRResult(text="", lang=lang, confidence=0.0)

    def synthesize(self, text: str, lang: str) -> bytes:
        del lang
        self._health.success(datetime.now(UTC))
        return text.encode("utf-8")

    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        del src_lang, tgt_lang
        self._health.success(datetime.now(UTC))
        return text

    def health(self) -> AdapterHealth:
        return self._health.snapshot()


class ConfiguredRealAdapter(MockSignalAdapter):
    """HTTP-backed adapter with a deliberately small, testable contract.

    Source adapters are configured with an endpoint rather than hard-coding
    provider credentials.  This lets local development use a mock transport,
    while a deployment can point at an official provider or a department-owned
    normalisation proxy.  Failures are recorded in the adapter health tracker
    and raised to the caller: live data must never silently become fixture data.
    """

    def __init__(
        self,
        source: str,
        endpoint: str | None = None,
        *,
        api_key: str | None = None,
        timeout_seconds: float = 10.0,
        client: httpx.Client | None = None,
    ):
        super().__init__(source)
        self.mode = AdapterMode.REAL
        self.endpoint = endpoint.strip() if endpoint else None
        self.api_key = api_key.strip() if api_key else None
        self.timeout_seconds = timeout_seconds
        self._client = client

    @property
    def configured(self) -> bool:
        return bool(self.endpoint)

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            return {"accept": "application/json"}
        # The official IMD and OGD deployments have used different gateway
        # conventions over time.  Supplying both headers is harmless for a
        # normalising proxy and keeps the key out of query strings/logs.
        return {
            "accept": "application/json",
            "authorization": f"Bearer {self.api_key}",
            "x-api-key": self.api_key,
        }

    def _request_params(self, req: SignalRequest) -> dict[str, str]:
        params: dict[str, str] = {
            "start_date": req.date_range[0].isoformat(),
            "end_date": req.date_range[1].isoformat(),
        }
        for key in ("village_id", "district_id", "mandi_id", "commodity"):
            value = getattr(req, key, None)
            if value:
                params[key] = str(value)
        if req.latitude is not None:
            params["latitude"] = str(req.latitude)
        if req.longitude is not None:
            params["longitude"] = str(req.longitude)
        if req.bbox is not None:
            params["bbox"] = ",".join(str(value) for value in req.bbox)
        return params

    def _fetch_json(self, req: SignalRequest) -> tuple[Any, datetime]:
        if not self.endpoint:
            raise RuntimeError(f"{self.source} real adapter requires a configured endpoint")
        if not self.endpoint.startswith(("https://", "http://")):
            raise RuntimeError(f"{self.source} endpoint must use http:// or https://")
        client = self._client
        close_client = client is None
        if client is None:
            client = httpx.Client(timeout=self.timeout_seconds)
        try:
            response = client.get(self.endpoint, params=self._request_params(req), headers=self._headers())
            response.raise_for_status()
            return response.json(), datetime.now(UTC)
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"{self.source} provider returned HTTP {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"{self.source} provider request failed: {exc.__class__.__name__}") from exc
        except ValueError as exc:
            raise RuntimeError(f"{self.source} provider returned invalid JSON") from exc
        finally:
            if close_client:
                client.close()

    def _parse_payload(self, payload: Any, fetched_at: datetime, req: SignalRequest) -> list[ObservationPayload]:
        """Parse a provider response shaped as ``data``/``observations`` rows.

        Concrete adapters override this method when a provider's native field
        names need interpretation.  The generic parser remains useful for a
        department-owned endpoint that already follows our canonical rows.
        """
        body: dict[str, Any]
        if isinstance(payload, list):
            body = {"data": payload}
        elif isinstance(payload, dict):
            body = payload
        else:
            raise TypeError(f"{self.source} provider payload must be an object or array")
        rows = _rows_from_payload(body)
        result: list[ObservationPayload] = []
        for row in rows:
            metric = str(row.get("metric") or row.get("field") or "").strip()
            if not metric or "value" not in row:
                continue
            observed_at = parse_datetime(row.get("observed_at") or row.get("date"), fetched_at)
            result.append(
                ObservationPayload(
                    source=self.source,
                    observed_at=observed_at,
                    village_id=row.get("village_id") or req.village_id,
                    plot_grid=row.get("plot_grid"),
                    metric=metric,
                    value=row.get("value"),
                    unit=str(row.get("unit", "")),
                )
            )
        return result

    def fetch(self, req: SignalRequest) -> list[ObservationPayload]:
        try:
            payload, fetched_at = self._fetch_json(req)
            rows = self._parse_payload(payload, fetched_at, req)
            self._health.success(fetched_at)
            return rows
        except Exception as exc:
            # Do not include URLs or response bodies in health state: endpoint
            # strings can contain query parameters and provider errors can echo
            # sensitive request details.
            self._health.failure(str(exc).split("?", 1)[0][:240])
            raise


def _rows_from_payload(payload: Any) -> list[dict[str, Any]]:
    """Extract rows from common OGD/provider envelopes without guessing values."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("observations", "data", "records", "results", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            nested = _rows_from_payload(value)
            if nested:
                return nested
    return [payload] if any(key in payload for key in ("metric", "field", "value")) else []


def parse_datetime(value: Any, fallback: datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, datetime.min.time())
    elif isinstance(value, str) and value.strip():
        text = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d"):
                try:
                    parsed = datetime.strptime(text[:10], fmt).replace(tzinfo=UTC)
                    break
                except ValueError:
                    continue
            else:
                parsed = fallback
    else:
        parsed = fallback
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def as_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        cleaned = value.strip().replace(",", "").replace("%", "")
        try:
            number = float(cleaned)
        except ValueError:
            return None
    else:
        return None
    return number if math.isfinite(number) else None


def first_value(row: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, "", "NA", "N/A", "ND"):
            return row[key]
    return None
