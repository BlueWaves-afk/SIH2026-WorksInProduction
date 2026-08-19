"""Band cutoffs and the conservative band-change gate."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from .constants import BAND_AMBER_MIN, BAND_RED_MIN, HYSTERESIS_DAYS, HYSTERESIS_OBSERVATIONS
from .types import BandDecision, RiskEvent

Band = Literal["green", "amber", "red"]


def band_from_score(score: float) -> Band:
    if score < BAND_AMBER_MIN:
        return "green"
    if score < BAND_RED_MIN:
        return "amber"
    return "red"


def apply_hysteresis(
    raw_band: Band,
    prior_events: list[RiskEvent],
    as_of: datetime,
) -> BandDecision:
    """Require corroboration for a band change while allowing first-ever bootstrap.

    A prior event is considered corroborating when it has the same raw/confirmed band and is at
    least the configured span old.  The current observation plus that prior event then satisfies
    the two-observation rule.  If the caller has no history, the first score is authoritative.
    """
    if not prior_events:
        return BandDecision(raw_band, raw_band, None, None, 0, False)

    previous = max(prior_events, key=lambda event: event.evaluated_at or event.expires_at)
    previous_band = previous.band
    if previous_band == raw_band:
        return BandDecision(raw_band, raw_band, None, None, 0, False)

    # The public event carries the evaluation timestamp.  Older persisted events may not have
    # it; in that case we hold the previous band rather than guessing from expiry metadata.
    previous_at = previous.evaluated_at
    min_span = timedelta(days=HYSTERESIS_DAYS)
    if previous_at is not None and as_of - previous_at >= min_span and HYSTERESIS_OBSERVATIONS <= 2:
        return BandDecision(raw_band, raw_band, None, None, 0, False)

    return BandDecision(previous_band, raw_band, raw_band, as_of, 1, False)
