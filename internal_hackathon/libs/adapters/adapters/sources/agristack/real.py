"""AgriStack/API Setu profile prefill adapter."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

from .._common import MockProfileAdapter, _rows_from_payload, first_value, parse_datetime
from ...core import AdapterMode
from ...core.interfaces import ProfilePrefill


class AgriStackRealAdapter(MockProfileAdapter):
    mode = AdapterMode.REAL

    def __init__(
        self,
        endpoint: str | None = None,
        *,
        api_key: str | None = None,
        timeout_seconds: float = 10.0,
        client: httpx.Client | None = None,
    ):
        super().__init__()
        self.endpoint = endpoint.strip() if endpoint else None
        self.api_key = api_key.strip() if api_key else None
        self.timeout_seconds = timeout_seconds
        self._client = client

    @property
    def configured(self) -> bool:
        return bool(self.endpoint and self.api_key)

    def fetch_profile(self, consent, farmer_ref):
        if not getattr(consent, "storage", False):
            raise PermissionError("storage consent is required for AgriStack prefill")
        if not self.configured:
            raise RuntimeError("AgriStack real adapter requires an API Setu endpoint and credential")
        client = self._client or httpx.Client(timeout=self.timeout_seconds)
        close_client = self._client is None
        fetched_at = datetime.now(UTC)
        try:
            response = client.get(
                self.endpoint or "",
                params={"farmer_ref": farmer_ref},
                headers={"authorization": f"Bearer {self.api_key}", "x-api-key": self.api_key or "", "accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"AgriStack provider returned HTTP {exc.response.status_code}") from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError("AgriStack provider request failed") from exc
        finally:
            if close_client:
                client.close()
        rows = _rows_from_payload(payload)
        if rows:
            row = rows[0]
        elif isinstance(payload, dict) and isinstance(payload.get("data"), dict):
            # API Setu connectors commonly return one profile under ``data``
            # rather than a list of observations.
            row = payload["data"]
        else:
            row = payload if isinstance(payload, dict) else {}
        if not isinstance(row, dict):
            raise TypeError("AgriStack provider returned an invalid profile")
        return ProfilePrefill(
            farmer_ref=farmer_ref,
            village_id=str(first_value(row, ("village_id", "village", "village_code")) or ""),
            crop=str(first_value(row, ("crop", "crop_name", "primary_crop")) or "") or None,
            land_area_band=str(first_value(row, ("land_area_band", "area_band")) or "") or None,
            irrigation_type=str(first_value(row, ("irrigation_type", "irrigation")) or "") or None,
            fetched_at=parse_datetime(first_value(row, ("fetched_at", "updated_at", "observed_at")), fetched_at),
        )
