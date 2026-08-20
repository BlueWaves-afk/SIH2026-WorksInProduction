"""Small repository protocol for backend persistence adapters."""

from typing import Protocol


class CaseRepository(Protocol):
    def list_open(self) -> list[dict]: ...

    def save(self, case: dict) -> dict: ...
