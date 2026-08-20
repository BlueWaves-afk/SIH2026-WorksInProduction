"""Small lexical retrieval fallback; production may swap in pgvector."""


def retrieve(query: str, chunks: list[dict], *, limit: int = 3) -> list[dict]:
    terms = {term for term in query.lower().split() if term}
    ranked = sorted(chunks, key=lambda chunk: len(terms & set(chunk.get("text", "").lower().split())), reverse=True)
    return ranked[:limit]
