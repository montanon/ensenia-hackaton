"""Simple character-based chunking strategy with overlap.

This is a straightforward chunking implementation that splits text
based on character count with configurable overlap between chunks.
"""

import re

from app.ensenia.services.chunking.base import ChunkingStrategy, TextChunk


class SimpleChunkingStrategy(ChunkingStrategy):
    """Simple character-based chunking with overlap.

    Splits text into fixed-size chunks with overlap, attempting to break
    at sentence boundaries when possible to maintain coherence.

    Args:
        chunk_size: Target size of each chunk in characters
        overlap: Number of overlapping characters between chunks
        respect_sentences: If True, try to break at sentence boundaries

    """

    def __init__(
        self,
        chunk_size: int = 768,
        overlap: int = 128,
        *,
        respect_sentences: bool = True,
    ):
        """Initialize the simple chunking strategy.

        Args:
            chunk_size: Target chunk size in characters
            overlap: Overlap between chunks in characters
            respect_sentences: Try to break at sentence boundaries

        """
        if chunk_size <= 0:
            msg = "chunk_size must be positive, got {chunk_size}"
            raise ValueError(msg)
        if overlap < 0:
            msg = "overlap cannot be negative, got {overlap}"
            raise ValueError(msg)
        if overlap >= chunk_size:
            msg = "overlap must be less than chunk_size, got {overlap}"
            raise ValueError(msg)

        self._chunk_size = chunk_size
        self._overlap = overlap
        self._respect_sentences = respect_sentences

    def chunk_text(
        self, text: str, metadata: dict[str, any] | None = None
    ) -> list[TextChunk]:
        """Split text into chunks with overlap.

        Args:
            text: Input text to chunk
            metadata: Optional metadata to attach to all chunks

        Returns:
            List of TextChunk objects

        """
        if not text or not text.strip():
            return []

        chunks = []
        start = 0
        index = 0

        while start < len(text):
            # Calculate end position
            end = min(start + self._chunk_size, len(text))

            # If respecting sentences and not at document end, try to break at sentence
            if self._respect_sentences and end < len(text):
                end = self._find_sentence_boundary(text, start, end)

            # Extract chunk text
            chunk_text = text[start:end].strip()

            # Only create chunk if it has content
            if chunk_text:
                chunk = TextChunk(
                    text=chunk_text,
                    index=index,
                    metadata=metadata or {},
                    char_start=start,
                    char_end=end,
                )
                chunks.append(chunk)
                index += 1

            # Move start position forward (with overlap)
            start = end - self._overlap

            # Prevent infinite loop if overlap causes no progress
            if start <= chunks[-1].char_start if chunks else False:
                start = end

        return chunks

    def _find_sentence_boundary(self, text: str, start: int, end: int) -> int:
        """Find the best sentence boundary near the end position.

        Looks for sentence-ending punctuation (., !, ?) within a reasonable
        distance from the target end position.

        Args:
            text: Full text
            start: Start position of current chunk
            end: Target end position

        Returns:
            Adjusted end position at sentence boundary

        """
        # Look backwards from end position for sentence endings
        search_start = max(start, end - 100)  # Don't look too far back
        search_text = text[search_start:end]

        # Find all sentence-ending punctuation
        sentence_endings = [m.end() for m in re.finditer(r"[.!?]\s+", search_text)]

        if sentence_endings:
            # Use the last sentence ending found
            return search_start + sentence_endings[-1]

        # If no sentence boundary found, also check for paragraph breaks
        paragraph_breaks = [m.end() for m in re.finditer(r"\n\n+", search_text)]
        if paragraph_breaks:
            return search_start + paragraph_breaks[-1]

        # If still no good boundary, return original end
        return end

    def get_chunk_size(self) -> int:
        """Get the target chunk size.

        Returns:
            Chunk size in characters

        """
        return self._chunk_size

    def get_overlap(self) -> int:
        """Get the overlap size.

        Returns:
            Overlap in characters

        """
        return self._overlap
