"""Sanitise untrusted text before it reaches a model or a prompt template."""

from __future__ import annotations

import re

_INSTRUCTION_PATTERNS = (
    re.compile(r"ignore\s+(?:all\s+)?previous\s+instructions?", re.IGNORECASE),
    re.compile(r"system\s*prompt\s*[:=]", re.IGNORECASE),
    re.compile(r"(?:call|invoke|run)\s+(?:the\s+)?(?:tool|function)", re.IGNORECASE),
    re.compile(r"reveal\s+(?:the\s+)?(?:prompt|secrets?|credentials?)", re.IGNORECASE),
)


def sanitize_untrusted_text(text: str) -> str:
    """Remove instruction-like spans while preserving useful source text."""

    cleaned = text
    for pattern in _INSTRUCTION_PATTERNS:
        cleaned = pattern.sub("[removed unsafe instruction]", cleaned)
    return cleaned.strip()


def contains_prompt_injection(text: str) -> bool:
    return any(pattern.search(text) for pattern in _INSTRUCTION_PATTERNS)
