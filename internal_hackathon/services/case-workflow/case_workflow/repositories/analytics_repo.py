"""Aggregate repository protocol; callers enforce cohort suppression."""

from typing import Protocol


class AnalyticsRepository(Protocol):
    def district_counts(self, district_id: str) -> dict[str, int]: ...
