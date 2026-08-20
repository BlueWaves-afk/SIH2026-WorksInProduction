"""Validate and reject unsafe copilot output before it reaches M8."""

from __future__ import annotations

from app.schemas import CopilotBrief

from .citation_validator import validate_scheme_matches

_UNSAFE_TERMS = ("kg/acre", "ml/acre", "pesticide dosage", "diagnosed", "guaranteed eligible")


def validate_brief(brief: CopilotBrief) -> CopilotBrief:
    validate_scheme_matches(brief.scheme_matches)
    searchable = " ".join([brief.summary, *brief.drivers, brief.draft_message or ""]).lower()
    if any(term in searchable for term in _UNSAFE_TERMS):
        raise ValueError("brief contains dosage, diagnosis or guaranteed-eligibility language")
    return brief
