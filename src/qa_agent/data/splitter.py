"""Text splitter: split documents into chunks with overlap."""

from ..infra.logging import logger


def split_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: float = 0.15,
) -> list[str]:
    """Split text into overlapping chunks.

    Args:
        text: Input text to split.
        chunk_size: Target chunk size in characters.
        chunk_overlap: Overlap ratio (0.0-1.0).

    Returns:
        List of text chunks.
    """
    if not text or not text.strip():
        return []

    overlap_chars = int(chunk_size * chunk_overlap)
    step = max(chunk_size - overlap_chars, 1)
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        if end < len(text):
            last_newline = chunk.rfind("\n")
            if last_newline > chunk_size * 0.5:
                chunk = chunk[:last_newline]

        chunk = chunk.strip()
        if chunk:
            chunks.append(chunk)

        start += step

    logger.debug("Split text into %d chunks (size=%d, overlap=%.0f%%)", len(chunks), chunk_size, chunk_overlap * 100)
    return chunks


class TextSplitter:
    """Configurable text splitter."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: float = 0.15):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> list[str]:
        return split_text(text, self.chunk_size, self.chunk_overlap)
