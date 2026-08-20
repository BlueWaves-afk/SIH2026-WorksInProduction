"""Deterministic document chunking for scheme references."""


def chunk_document(text: str, *, source_doc: str, chunk_size: int = 800, overlap: int = 80) -> list[dict]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be larger than overlap")
    chunks = []
    start = 0
    index = 0
    while start < len(text):
        body = text[start : start + chunk_size]
        chunks.append({"source_doc": source_doc, "chunk_id": f"{source_doc}:{index}", "text": body})
        start += chunk_size - overlap
        index += 1
    return chunks
