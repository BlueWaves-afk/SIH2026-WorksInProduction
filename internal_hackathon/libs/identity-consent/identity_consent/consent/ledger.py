"""Pure consent ledger operations; persistence is supplied by the platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class ConsentEntry:
    farmer_token: str
    purpose: str
    granted: bool
    version: str
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class ConsentLedger:
    def __init__(self):
        self._entries: list[ConsentEntry] = []

    def record(self, farmer_token: str, purpose: str, granted: bool, version: str = "1") -> ConsentEntry:
        entry = ConsentEntry(farmer_token, purpose, granted, version)
        self._entries.append(entry)
        return entry

    def current(self, farmer_token: str) -> dict[str, bool]:
        result: dict[str, bool] = {}
        for entry in self._entries:
            if entry.farmer_token == farmer_token:
                result[entry.purpose] = entry.granted
        return result

    def may(self, farmer_token: str, purpose: str) -> bool:
        return self.current(farmer_token).get(purpose, False)
