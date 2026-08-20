"""Input privacy and numeric safety guardrails."""
from __future__ import annotations

import math
import re
from typing import Any

from .constants import BANNED_FIELDS, SCORE_DISCLAIMER
from .errors import PrivacyGuardrailError, ScoringInputError


def assert_safe_metric(metric: str, value: Any) -> None:
    lowered = metric.lower()
    if any(field in lowered for field in BANNED_FIELDS):
        raise PrivacyGuardrailError(f"banned scoring field: {metric}")
    _scan_value(value)


def _scan_value(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ScoringInputError("non-finite scoring input")
    if isinstance(value, dict):
        for key, child in value.items():
            if re.search(r"aadhaar|bank|lender|credit", str(key), re.IGNORECASE):
                raise PrivacyGuardrailError(f"banned scoring field: {key}")
            _scan_value(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _scan_value(child)


__all__ = ["SCORE_DISCLAIMER", "PrivacyGuardrailError", "ScoringInputError", "assert_safe_metric"]
