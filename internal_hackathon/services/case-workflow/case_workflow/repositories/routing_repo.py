"""Routing repository protocol."""

from typing import Protocol


class RoutingRepository(Protocol):
    def officer_for_village(self, village_id: str) -> str | None: ...
