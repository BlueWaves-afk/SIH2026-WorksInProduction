"""Stable idempotency keys for outbox writes."""

import hashlib


def idempotency_key(*parts: str) -> str:
    return hashlib.sha256(":".join(parts).encode("utf-8")).hexdigest()
