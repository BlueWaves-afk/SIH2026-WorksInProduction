"""Small, deterministic PII minimisation layer for model context."""

from __future__ import annotations

import re

_PHONE = re.compile(r"(?<!\d)(?:\+?91[-\s]?)?[6-9]\d{9}(?!\d)")
_AADHAAR = re.compile(r"(?<!\d)\d{4}[-\s]?\d{4}[-\s]?\d{4}(?!\d)")
_ACCOUNT = re.compile(r"(?i)(?:account|a/c|acct)[\s:#-]*\d{6,18}")


def redact_pii(text: str) -> str:
    """Replace phone, Aadhaar-like and bank-account-like values with tokens."""

    redacted = _PHONE.sub("[phone redacted]", text)
    redacted = _AADHAAR.sub("[identity number redacted]", redacted)
    return _ACCOUNT.sub("[account reference redacted]", redacted)
