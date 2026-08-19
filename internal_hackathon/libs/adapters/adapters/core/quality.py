"""Schema/range validation, de-duplication and quality classification."""
from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from .interfaces import ObservationPayload
from .ttl import TTLPolicy


class QualityGate:
    def __init__(self, ttl_policy: TTLPolicy | None = None):
        self.ttl_policy = ttl_policy or TTLPolicy()
        self._seen: set[tuple[str, str, str | None, datetime]] = set()

    def accept(self, observations: Iterable[ObservationPayload], as_of: datetime) -> list[ObservationPayload]:
        accepted: list[ObservationPayload] = []
        for observation in observations:
            if not observation.source or not observation.metric:
                raise ValueError("source and metric are required")
            key = (observation.source, observation.metric, observation.village_id, observation.observed_at)
            if key in self._seen:
                continue
            self._seen.add(key)
            accepted.append(self.ttl_policy.classify(observation, as_of))
        return accepted
