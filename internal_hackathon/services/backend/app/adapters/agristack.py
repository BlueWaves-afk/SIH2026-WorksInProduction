"""Compatibility import for the canonical M3 AgriStack adapter."""

from app.integrations.canonical import _ensure_workspace_packages

_ensure_workspace_packages()
from adapters.sources.agristack import AgriStackMockAdapter  # noqa: E402


class AgriStackAdapter:
    """Legacy method shape backed by the shared adapter contract."""

    def __init__(self):
        self._adapter = AgriStackMockAdapter()

    def get_farmer_profile(self, farmer_id: str):
        from types import SimpleNamespace

        profile = self._adapter.fetch_profile(SimpleNamespace(storage=True), farmer_id)
        return profile.model_dump(mode="json")
