"""Driver conversion and deterministic top-three selection."""
from __future__ import annotations

from .types import Contributor, SubScoreResult


def contributors_from_scores(scores: list[SubScoreResult]) -> list[Contributor]:
    contributors = [
        Contributor(
            signal=score.signal,
            points=score.points,
            max_points=score.max_points,
            explanation=score.driver_text or score.signal,
            source=score.source,
            observed_at=score.observed_at,
        )
        for score in scores
        if score.applicable and score.points > 0 and score.observed_at is not None
    ]
    return sorted(contributors, key=lambda item: (-item.points, item.signal))


def select_top_drivers(contributors: list[Contributor], n: int = 3) -> list[Contributor]:
    return sorted(contributors, key=lambda item: (-item.points, item.signal))[:n]
