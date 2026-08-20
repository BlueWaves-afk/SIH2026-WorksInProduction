"""Dependency-free deterministic embedding for fixture retrieval."""

import hashlib


def embed(text: str, dimensions: int = 32) -> list[float]:
    digest = hashlib.sha256(text.lower().encode("utf-8")).digest()
    return [((digest[index % len(digest)] / 255) * 2) - 1 for index in range(dimensions)]
