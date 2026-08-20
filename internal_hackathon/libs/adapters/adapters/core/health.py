"""Small in-memory adapter health tracker.

The platform can persist or export this snapshot; the adapter package itself never
writes to the database.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from .interfaces import AdapterMode


class AdapterHealth(BaseModel):
    source: str
    mode: AdapterMode
    ok: bool = True
    last_success_at: datetime | None = None
    last_error: str | None = None
    consecutive_failures: int = 0
    circuit_open: bool = False


class HealthTracker:
    def __init__(self, source: str, mode: AdapterMode, failure_threshold: int = 3):
        self._state = AdapterHealth(source=source, mode=mode)
        self._failure_threshold = failure_threshold

    def success(self, at: datetime) -> AdapterHealth:
        self._state = self._state.model_copy(
            update={
                "ok": True,
                "last_success_at": at,
                "last_error": None,
                "consecutive_failures": 0,
                "circuit_open": False,
            }
        )
        return self.snapshot()

    def failure(self, error: str) -> AdapterHealth:
        failures = self._state.consecutive_failures + 1
        opened = failures >= self._failure_threshold
        self._state = self._state.model_copy(
            update={
                "ok": False,
                "last_error": error,
                "consecutive_failures": failures,
                "circuit_open": opened,
            }
        )
        return self.snapshot()

    def snapshot(self) -> AdapterHealth:
        return self._state.model_copy(deep=True)
