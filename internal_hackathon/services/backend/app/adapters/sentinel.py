"""Compatibility import for the canonical Sentinel-2 adapter."""

from datetime import date

from app.integrations.canonical import _ensure_workspace_packages

_ensure_workspace_packages()
from adapters.core.interfaces import SignalRequest  # noqa: E402
from adapters.sources.sentinel2 import Sentinel2MockAdapter  # noqa: E402


class SentinelNDVIAdapter:
    def __init__(self):
        self._adapter = Sentinel2MockAdapter()

    def get_ndvi_stress(self, village_id: str):
        rows = self._adapter.fetch(SignalRequest(village_id=village_id, date_range=(date.today(), date.today())))
        return rows[0].model_dump(mode="json") if rows else None
