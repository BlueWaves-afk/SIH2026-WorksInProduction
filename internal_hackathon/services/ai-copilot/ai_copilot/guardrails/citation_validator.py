"""Citation checks for the officer-facing brief."""

from __future__ import annotations

from collections.abc import Iterable

from app.schemas import Citation, SchemeMatch


def citation_is_complete(citation: Citation) -> bool:
    return bool(citation.source_doc.strip() and citation.chunk_id.strip() and citation.quote.strip())


def validate_scheme_matches(matches: Iterable[SchemeMatch]) -> None:
    """Raise when a scheme claim cannot be traced to a source chunk."""

    for match in matches:
        if not match.scheme.strip() or not match.why.strip() or not match.citations:
            raise ValueError(f"scheme match {match.scheme!r} is missing a citation")
        if not all(citation_is_complete(citation) for citation in match.citations):
            raise ValueError(f"scheme match {match.scheme!r} contains an incomplete citation")
