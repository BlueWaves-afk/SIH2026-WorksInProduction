"""Compatibility note for the pre-FDI v1 module.

Crop-stage and soil-retention effects are now S10 and S12 in
``rules.vulnerability``. This module remains as a named import target for
branches migrating old callers; new code must call ``vulnerability_signals``.
"""

from datetime import datetime

from ..types import FarmerContext, SubScoreResult
from .vulnerability import vulnerability_signals


def score_crop_soil_vulnerability(
    farmer: FarmerContext, as_of: datetime
) -> list[SubScoreResult]:
    """Return the FDI vulnerability signals formerly grouped as crop/soil."""
    return [item for item in vulnerability_signals(farmer, as_of) if item.signal in {"S10", "S12"}]
