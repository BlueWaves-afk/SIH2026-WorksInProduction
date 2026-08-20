"""Typed failures raised by the scoring engine.

The engine refuses to score rather than guess. Each error names the class of
problem so callers (M1) can map it to the right HTTP response and so the
privacy guardrail is distinguishable from ordinary bad input.
"""
from __future__ import annotations


class ScoringError(Exception):
    """Base class for every refusal raised by the scoring engine."""


class PrivacyGuardrailError(ScoringError):
    """A banned field reached the scoring boundary.

    Aadhaar, bank, lender or credit-derived fields must never influence the
    score (masterspec §4.5). Reaching this means an upstream module leaked a
    field the platform promises never to use.
    """


class MissingRequiredContextError(ScoringError):
    """The minimum farmer context for a score is absent.

    masterspec §4.1: village_id + crop + irrigation_type + sowing_date.
    """


class ScoringInputError(ScoringError):
    """An observation value is unusable (NaN, infinite, or wrong shape)."""


__all__ = [
    "MissingRequiredContextError",
    "PrivacyGuardrailError",
    "ScoringError",
    "ScoringInputError",
]
