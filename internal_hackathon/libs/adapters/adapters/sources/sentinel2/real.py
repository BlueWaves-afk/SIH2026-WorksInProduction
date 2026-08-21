"""Sentinel-2 / Copernicus Data Space crop-stress adapter."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from .._common import ConfiguredRealAdapter, _rows_from_payload, as_number, first_value, parse_datetime
from ...core.interfaces import ObservationPayload, SignalRequest


class Sentinel2RealAdapter(ConfiguredRealAdapter):
    """Fetch pre-computed Sentinel-2 indices from a provider or proxy.

    Copernicus Data Space uses OAuth client credentials rather than a single
    API key.  The adapter also accepts a bearer-style ``api_key`` for a
    department-owned proxy, which keeps local integration tests simple.
    """

    DEFAULT_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

    def __init__(
        self,
        endpoint: str | None = None,
        *,
        api_key: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        token_url: str | None = None,
        timeout_seconds: float = 20.0,
        client: httpx.Client | None = None,
    ):
        super().__init__("sentinel2", endpoint, api_key=api_key, timeout_seconds=timeout_seconds, client=client)
        self.client_id = client_id.strip() if client_id else None
        self.client_secret = client_secret.strip() if client_secret else None
        self.token_url = (token_url or self.DEFAULT_TOKEN_URL).strip()
        self._access_token: str | None = None
        self._access_token_expires_at: datetime | None = None

    @property
    def configured(self) -> bool:
        return bool(self.endpoint and (self.api_key or (self.client_id and self.client_secret)))

    def _token(self, client: httpx.Client) -> str:
        now = datetime.now(UTC)
        if self._access_token and self._access_token_expires_at and now < self._access_token_expires_at:
            return self._access_token
        if not self.client_id or not self.client_secret:
            raise RuntimeError("sentinel2 OAuth client credentials are not configured")
        try:
            response = client.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError("sentinel2 OAuth token request failed") from exc
        token = payload.get("access_token") if isinstance(payload, dict) else None
        if not isinstance(token, str) or not token:
            raise RuntimeError("sentinel2 OAuth response did not contain an access token")
        expires_in = payload.get("expires_in", 300) if isinstance(payload, dict) else 300
        try:
            ttl = max(30, int(expires_in) - 30)
        except (TypeError, ValueError):
            ttl = 270
        self._access_token = token
        self._access_token_expires_at = now + timedelta(seconds=ttl)
        return token

    def _fetch_json(self, req: SignalRequest) -> tuple[Any, datetime]:
        if not self.endpoint:
            raise RuntimeError("sentinel2 real adapter requires a configured endpoint")
        if not self.endpoint.startswith(("https://", "http://")):
            raise RuntimeError("sentinel2 endpoint must use http:// or https://")
        client = self._client
        close_client = client is None
        if client is None:
            client = httpx.Client(timeout=self.timeout_seconds)
        try:
            headers = {"accept": "application/json"}
            if self.api_key:
                headers["authorization"] = f"Bearer {self.api_key}"
                headers["x-api-key"] = self.api_key
            else:
                headers["authorization"] = f"Bearer {self._token(client)}"
            response = client.get(self.endpoint, params=self._request_params(req), headers=headers)
            response.raise_for_status()
            return response.json(), datetime.now(UTC)
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"sentinel2 provider returned HTTP {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"sentinel2 provider request failed: {exc.__class__.__name__}") from exc
        except ValueError as exc:
            raise RuntimeError("sentinel2 provider returned invalid JSON") from exc
        finally:
            if close_client:
                client.close()

    def _parse_payload(self, payload: Any, fetched_at: datetime, req: SignalRequest) -> list[ObservationPayload]:
        result: list[ObservationPayload] = []
        for row in _sentinel_rows(payload):
            observed_at = parse_datetime(first_value(row, ("observed_at", "date", "datetime", "timestamp")), fetched_at)
            village_id = row.get("village_id") or req.village_id
            quality = "degraded" if as_number(first_value(row, ("cloud_cover_pct", "cloud_cover"))) not in (None, 0) else "good"

            direct = str(row.get("metric") or row.get("field") or "").strip().lower()
            if direct and "value" in row and direct in {"ndvi_anomaly_pct", "ndwi_anomaly_pct", "satellite_crop_stress"}:
                result.append(self._observation(direct, row["value"], observed_at, village_id, quality))
                continue

            ndvi_anomaly = as_number(first_value(row, ("ndvi_anomaly_pct", "NDVI_anomaly_pct", "ndvi_departure_pct")))
            ndwi_anomaly = as_number(first_value(row, ("ndwi_anomaly_pct", "NDWI_anomaly_pct", "ndwi_departure_pct")))
            if ndvi_anomaly is None:
                ndvi = as_number(first_value(row, ("ndvi", "NDVI")))
                baseline = as_number(first_value(row, ("ndvi_baseline", "NDVI_baseline", "ndvi_seasonal_median")))
                if ndvi is not None and baseline not in (None, 0):
                    ndvi_anomaly = ((baseline - ndvi) / abs(baseline)) * 100
            if ndwi_anomaly is None:
                ndwi = as_number(first_value(row, ("ndwi", "NDWI")))
                baseline = as_number(first_value(row, ("ndwi_baseline", "NDWI_baseline", "ndwi_seasonal_median")))
                if ndwi is not None and baseline not in (None, 0):
                    ndwi_anomaly = ((baseline - ndwi) / abs(baseline)) * 100
            stress = as_number(first_value(row, ("satellite_crop_stress", "crop_stress", "stress_pct")))
            if ndvi_anomaly is not None:
                result.append(self._observation("ndvi_anomaly_pct", ndvi_anomaly, observed_at, village_id, quality))
            if ndwi_anomaly is not None:
                result.append(self._observation("ndwi_anomaly_pct", ndwi_anomaly, observed_at, village_id, quality))
            if stress is not None:
                result.append(self._observation("satellite_crop_stress", stress, observed_at, village_id, quality))
        return result

    def _observation(self, metric: str, value: Any, observed_at: datetime, village_id: str | None, quality: str) -> ObservationPayload:
        return ObservationPayload(
            source=self.source,
            observed_at=observed_at,
            village_id=village_id,
            metric=metric,
            value=value,
            unit="percent",
            quality=quality,
            ttl=timedelta(days=7),
        )


def _sentinel_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and payload.get("type") == "FeatureCollection":
        rows: list[dict[str, Any]] = []
        for feature in payload.get("features", []):
            if not isinstance(feature, dict):
                continue
            props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
            rows.append({**props, "geometry": feature.get("geometry")})
        return rows
    if isinstance(payload, dict):
        direct_keys = {"ndvi", "NDVI", "ndvi_anomaly_pct", "ndwi_anomaly_pct", "satellite_crop_stress", "crop_stress"}
        if direct_keys.intersection(payload):
            return [payload]
    return _rows_from_payload(payload)
