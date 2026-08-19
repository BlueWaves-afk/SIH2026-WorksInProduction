"""Explainable scoring engine — PURE. No I/O, no network, no DB.

    from scoring_engine import compute_risk_event
"""
from .constants import MODEL_VERSION, SCORE_DISCLAIMER
from .engine import compute_risk_event

__all__ = ["MODEL_VERSION", "SCORE_DISCLAIMER", "compute_risk_event"]
