"""One-time scheme-document ingestion into a caller-owned store."""

from .chunker import chunk_document


def ingest_document(text: str, source_doc: str, store: list[dict]) -> int:
    chunks = chunk_document(text, source_doc=source_doc)
    store.extend(chunks)
    return len(chunks)
