"""Compatibility import for the canonical soil adapter."""

from datetime import date

from app.integrations.canonical import _ensure_workspace_packages

_ensure_workspace_packages()
from adapters.core.interfaces import SignalRequest  # noqa: E402
from adapters.sources.soil import SoilMockAdapter  # noqa: E402


class SoilDataAdapter:
    def __init__(self):
        self._adapter = SoilMockAdapter()

    def get_soil_health(self, village_id: str):
        rows = self._adapter.fetch(SignalRequest(village_id=village_id, date_range=(date.today(), date.today())))
        return rows[0].model_dump(mode="json") if rows else None
