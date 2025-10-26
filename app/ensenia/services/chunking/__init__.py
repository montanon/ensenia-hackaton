"""Text chunking strategies for RAG content processing.

This module provides a dependency-injected chunking strategy pattern
that allows different chunking implementations to be swapped out easily.
"""

from app.ensenia.services.chunking.base import ChunkingStrategy, TextChunk
from app.ensenia.services.chunking.simple import SimpleChunkingStrategy

__all__ = ["ChunkingStrategy", "TextChunk", "SimpleChunkingStrategy"]
