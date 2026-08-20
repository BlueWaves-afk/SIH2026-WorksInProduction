"""Retrieval + citation assembly boundary."""


def cited_matches(query: str, chunks: list[dict], retrieve) -> list[dict]:
    return [{"scheme": chunk.get("scheme", "scheme"), "why": chunk.get("text", ""), "citation": {"source_doc": chunk.get("source_doc", ""), "chunk_id": chunk.get("chunk_id", ""), "quote": chunk.get("text", "")}} for chunk in retrieve(query, chunks)]
