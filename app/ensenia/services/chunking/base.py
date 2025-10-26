"""Base chunking strategy interface for dependency injection.

This module defines the abstract base class for text chunking strategies,
enabling different chunking algorithms to be implemented and swapped easily.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata.

    Attributes:
        text: The actual text content of the chunk
        index: Position of this chunk in the sequence (0-based)
        metadata: Additional metadata (e.g., source_file, page_number)
        char_start: Starting character position in original document
        char_end: Ending character position in original document

    """

    text: str
    index: int
    metadata: dict[str, any] | None = None
    char_start: int = 0
    char_end: int = 0


class ChunkingStrategy(ABC):
    """Abstract base class for text chunking strategies.

    Implementations should provide different ways to split text into
    manageable chunks for embedding and retrieval.

    Example usage:
        strategy = SimpleChunkingStrategy(chunk_size=768, overlap=128)
        chunks = strategy.chunk_text(document_text)
    """

    @abstractmethod
    def chunk_text(
        self, text: str, metadata: dict[str, any] | None = None
    ) -> list[TextChunk]:
        """Split text into chunks according to the strategy.

        Args:
            text: The input text to chunk
            metadata: Optional metadata to attach to all chunks

        Returns:
            List of TextChunk objects with appropriate metadata

        """

    @abstractmethod
    def get_chunk_size(self) -> int:
        """Get the target chunk size for this strategy.

        Returns:
            Target size of chunks in characters

        """

    @abstractmethod
    def get_overlap(self) -> int:
        """Get the overlap size between chunks.

        Returns:
            Number of overlapping characters between consecutive chunks

        """
