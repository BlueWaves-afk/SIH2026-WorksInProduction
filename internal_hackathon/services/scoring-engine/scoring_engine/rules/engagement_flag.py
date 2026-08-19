"""S15 engagement/withdrawal context; never scored (FDI D7)."""
from __future__ import annotations

from ..types import Observation


def engagement_context_flags(observations: list[Observation]) -> list[str]:
    unanswered = sum(item.metric == "outreach_unanswered" for item in observations)
    return [f"{unanswered} outreach attempts unanswered"] if unanswered else []
