"""Per-source TTL policy and stale-at-read classification."""
from __future__ import annotations

from datetime import datetime, timedelta

from .interfaces import ObservationPayload

DEFAULT_TTL = timedelta(days=2)
SOURCE_TTL: dict[str, timedelta] = {
    "imd": timedelta(days=2),
    "agmarknet": timedelta(days=3),
    "sentinel2": timedelta(days=10),
    "msp": timedelta(days=365),
    "soil": timedelta(days=365),
    "bhuvan": timedelta(days=30),
    "agristack": timedelta(days=30),
    "bhashini": timedelta(minutes=5),
    "farmer": timedelta(days=2),
}


class TTLPolicy:
    def ttl_for(self, source: str, metric: str | None = None) -> timedelta:
        del metric
        return SOURCE_TTL.get(source.lower(), DEFAULT_TTL)

    def classify(self, observation: ObservationPayload, as_of: datetime) -> ObservationPayload:
        ttl = observation.ttl if observation.ttl != DEFAULT_TTL else self.ttl_for(observation.source, observation.metric)
        stale = as_of - observation.observed_at > ttl
        quality = "stale" if stale else observation.quality
        return observation.model_copy(update={"ttl": ttl, "quality": quality})
