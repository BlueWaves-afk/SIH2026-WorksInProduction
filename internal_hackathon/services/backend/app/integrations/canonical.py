from __future__ import annotations

import sys
from pathlib import Path


def _ensure_workspace_packages() -> None:
    try:
        import adapters  # noqa: F401
        import scoring_engine  # noqa: F401
        return
    except ModuleNotFoundError:
        root = Path(__file__).resolve().parents[4]
        for package in (root / "libs" / "adapters", root / "services" / "scoring-engine"):
            if str(package) not in sys.path:
                sys.path.insert(0, str(package))


_ensure_workspace_packages()

from adapters.replay import ReplayDriver  # noqa: E402
from scoring_engine.engine import compute_risk_event  # noqa: E402
from scoring_engine.types import (  # noqa: E402
    ConsentContext as ScoringConsentContext,
    FarmerContext as ScoringFarmerContext,
    Observation as ScoringObservation,
)

__all__ = [
    "ReplayDriver",
    "ScoringConsentContext",
    "ScoringFarmerContext",
    "ScoringObservation",
    "compute_risk_event",
]
