"""Confidence calculation from source freshness and signal completeness."""
from __future__ import annotations

from datetime import datetime

from .constants import CONFIDENCE_FLOOR
from .types import Observation, SubScoreResult


def observation_freshness(observation: Observation, as_of: datetime) -> float:
    age_seconds = max(0.0, (as_of - observation.observed_at).total_seconds())
    ttl_seconds = max(1.0, observation.ttl.total_seconds())
    if age_seconds <= ttl_seconds * 0.5:
        return 1.0
    if age_seconds >= ttl_seconds:
        return 0.3
    return 1.0 - 0.7 * ((age_seconds - ttl_seconds * 0.5) / (ttl_seconds * 0.5))


def compute_confidence(sub_scores: list[SubScoreResult]) -> float:
    applicable = [score for score in sub_scores if score.applicable]
    if not applicable:
        return 0.0
    freshness = sum(score.freshness for score in applicable) / len(applicable)
    completeness = sum(1.0 for score in applicable if score.observed_at is not None) / len(applicable)
    return max(0.0, min(1.0, freshness * completeness))


def suppress_escalation(confidence: float) -> bool:
    return confidence < CONFIDENCE_FLOOR
