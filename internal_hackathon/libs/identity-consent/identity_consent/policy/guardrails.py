"""Privacy and safety guardrails shared by API/application layers."""

import re


def assert_not_scoring_language(text: str) -> None:
    if re.search(r"\b(credit|default|loan)\s+score\b", text, re.IGNORECASE):
        raise ValueError("support output must not be described as a credit/default score")


def enforce_cohort_suppression(count: int, minimum: int = 10) -> None:
    if count < minimum:
        raise PermissionError("aggregate cohort is too small")


def redact_pii_for_role(value: str, role: str) -> str:
    if role in {"admin", "auditor"}:
        return value
    return re.sub(r"(?<!\d)(?:\+?91[-\s]?)?[6-9]\d{9}(?!\d)", "[phone redacted]", value)
