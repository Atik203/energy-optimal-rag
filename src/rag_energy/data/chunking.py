"""Word-level passage chunking.

The pilot used 70-word passages over SQuAD contexts. Keep chunking deterministic:
the same text, size, and overlap must always produce the same passages, because
retrieval recall and the depth grid depend on it.
"""

from __future__ import annotations


def chunk_words(text: str, size: int = 70, overlap: int = 0) -> list[str]:
    """Split ``text`` into whitespace-delimited chunks of ``size`` words.

    Args:
        text: Input text.
        size: Words per chunk; must be positive.
        overlap: Words shared between adjacent chunks; must satisfy
            ``0 <= overlap < size``.

    Returns:
        A list of chunks. A trailing partial chunk is kept.
    """
    if size <= 0:
        raise ValueError("size must be positive")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must satisfy 0 <= overlap < size")

    words = text.split()
    if not words:
        return []

    step = size - overlap
    chunks: list[str] = []
    start = 0
    while start < len(words):
        chunk = words[start : start + size]
        if chunk:
            chunks.append(" ".join(chunk))
        if start + size >= len(words):
            break
        start += step
    return chunks


def chunk_document(passages: list[str], size: int = 70, overlap: int = 0) -> list[str]:
    """Chunk each upstream passage and concatenate the results in order."""
    out: list[str] = []
    for passage in passages:
        out.extend(chunk_words(passage, size=size, overlap=overlap))
    return out
