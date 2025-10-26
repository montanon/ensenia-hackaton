"""Embedding generation and storage service for RAG pipeline.

This module orchestrates the process of generating embeddings for text chunks
and storing them in Cloudflare Vectorize for semantic search.
"""

import asyncio
import logging
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.ensenia.core.config import settings
from app.ensenia.database.models import CurriculumContent
from app.ensenia.services.chunking import (
    ChunkingStrategy,
    SimpleChunkingStrategy,
    TextChunk,
)
from app.ensenia.services.cloudflare.vectorize import VectorizeService
from app.ensenia.services.cloudflare.workers_ai import WorkersAIService

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and storing embeddings.

    Coordinates chunking text, generating embeddings via Workers AI,
    and storing vectors in Vectorize with appropriate metadata.

    Example usage:
        service = EmbeddingService(db_session)
        await service.process_curriculum_content(content_id)
    """

    def __init__(
        self,
        db_session: AsyncSession,
        chunking_strategy: ChunkingStrategy | None = None,
        batch_size: int = 10,
    ):
        """Initialize embedding service.

        Args:
            db_session: Database session for accessing content
            chunking_strategy: Strategy chunking text (default: SimpleChunkingStrategy)
            batch_size: Number of embeddings to process in parallel (default: 10)

        """
        self.db = db_session
        self.workers_ai = WorkersAIService()
        self.vectorize = VectorizeService()
        self.chunking_strategy = chunking_strategy or SimpleChunkingStrategy(
            chunk_size=settings.rag_chunk_size,
            overlap=settings.rag_chunk_overlap,
        )
        self.batch_size = batch_size

    async def process_curriculum_content(self, content_id: str) -> dict[str, Any]:
        """Process a single curriculum content item.

        Chunks the content, generates embeddings, and stores in Vectorize.

        Args:
            content_id: ID of curriculum content to process

        Returns:
            Dictionary with processing results:
                - chunks_created: Number of chunks created
                - embeddings_generated: Number of embeddings generated
                - vectors_stored: Number of vectors stored in Vectorize

        Raises:
            ValueError: If content not found

        """
        # Fetch content from database
        stmt = select(CurriculumContent).where(CurriculumContent.id == content_id)
        result = await self.db.execute(stmt)
        content = result.scalar_one_or_none()

        if not content:
            msg = "Curriculum content not found: {content_id}"
            raise ValueError(msg)

        msg = "Processing curriculum content: {content_id}"
        logger.info(msg)

        # Chunk the text
        metadata = {
            "content_id": content.id,
            "grade": content.grade,
            "subject": content.subject,
            "title": content.title,
            "difficulty": content.difficulty_level,
            "learning_objectives": content.learning_objectives,
        }

        chunks = self.chunking_strategy.chunk_text(content.content_text, metadata)
        msg = f"Created {len(chunks)} chunks from content {content_id}"
        logger.info(msg)

        if not chunks:
            msg = "No chunks created for content {content_id}"
            logger.warning(msg)
            return {"chunks_created": 0, "embeddings_generated": 0, "vectors_stored": 0}

        # Generate embeddings for chunks
        embeddings = await self._generate_embeddings_for_chunks(chunks)
        msg = f"Generated {len(embeddings)} embeddings for content {content_id}"
        logger.info(msg)

        # Prepare vectors for Vectorize
        vectors = self._prepare_vectors(chunks, embeddings, content_id)

        # Store in Vectorize
        result = await self.vectorize.upsert_vectors(vectors)
        msg = f"Stored {len(vectors)} vectors in Vectorize for content {content_id}"
        logger.info(msg)

        # Mark content as having embeddings generated
        await self._mark_embedding_generated(content_id)

        return {
            "chunks_created": len(chunks),
            "embeddings_generated": len(embeddings),
            "vectors_stored": len(vectors),
            "vectorize_result": result,
        }

    async def process_curriculum_content_batch(
        self, content_ids: list[str]
    ) -> dict[str, Any]:
        """Process multiple curriculum content items.

        Args:
            content_ids: List of content IDs to process

        Returns:
            Dictionary with batch processing results

        """
        msg = f"Processing batch of {len(content_ids)} curriculum contents"
        logger.info(msg)

        results = {
            "total_processed": 0,
            "total_chunks": 0,
            "total_embeddings": 0,
            "total_vectors": 0,
            "errors": [],
        }

        for content_id in content_ids:
            try:
                result = await self.process_curriculum_content(content_id)
                results["total_processed"] += 1
                results["total_chunks"] += result["chunks_created"]
                results["total_embeddings"] += result["embeddings_generated"]
                results["total_vectors"] += result["vectors_stored"]
            except Exception:
                msg = f"Failed to process content {content_id}"
                logger.exception(msg)
                results["errors"].append({"content_id": content_id, "error": msg})

        msg = f"Batch complete: {results['total_processed']}/{len(content_ids)} success"
        logger.info(msg)

        return results

    async def process_all_curriculum_content(self) -> dict[str, Any]:
        """Process all curriculum content that doesn't have embeddings yet.

        Returns:
            Dictionary with processing results

        """
        # Get all content without embeddings
        stmt = select(CurriculumContent).where(
            CurriculumContent.embedding_generated == False  # noqa: E712
        )
        result = await self.db.execute(stmt)
        contents = result.scalars().all()

        content_ids = [content.id for content in contents]
        msg = f"Found {len(content_ids)} curriculum contents without embeddings"
        logger.info(msg)

        if not content_ids:
            msg = "No content to process"
            logger.info(msg)
            return {
                "total_processed": 0,
                "total_chunks": 0,
                "total_embeddings": 0,
                "total_vectors": 0,
                "errors": [],
            }

        return await self.process_curriculum_content_batch(content_ids)

    async def _generate_embeddings_for_chunks(
        self, chunks: list[TextChunk]
    ) -> list[list[float]]:
        """Generate embeddings for a list of text chunks.

        Processes chunks in batches to avoid overwhelming the API.

        Args:
            chunks: List of text chunks

        Returns:
            List of embedding vectors

        """
        all_embeddings = []

        # Process in batches
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i : i + self.batch_size]
            texts = [chunk.text for chunk in batch]

            msg = f"Generating embeddings for batch {i // self.batch_size + 1}"
            logger.debug(msg)

            # Generate embeddings (Workers AI doesn't support true batching yet)
            embeddings = []
            for text in texts:
                embedding = await self.workers_ai.generate_embedding(text)
                embeddings.append(embedding)

            all_embeddings.extend(embeddings)

            # Small delay to avoid rate limiting
            if i + self.batch_size < len(chunks):
                await asyncio.sleep(0.1)

        return all_embeddings

    def _prepare_vectors(
        self, chunks: list[TextChunk], embeddings: list[list[float]], content_id: str
    ) -> list[dict[str, Any]]:
        """Prepare vector objects for Vectorize storage.

        Args:
            chunks: Text chunks
            embeddings: Corresponding embeddings
            content_id: ID of the source content

        Returns:
            List of vector dictionaries ready for Vectorize

        """
        vectors = []

        for chunk, embedding in zip(chunks, embeddings, strict=True):
            vector_id = f"{content_id}_chunk_{chunk.index}"

            # Combine chunk metadata with additional info
            metadata = {
                **(chunk.metadata or {}),
                "chunk_index": chunk.index,
                "char_start": chunk.char_start,
                "char_end": chunk.char_end,
                "chunk_text": chunk.text[:200],  # Store preview for debugging
            }

            vector = {"id": vector_id, "values": embedding, "metadata": metadata}

            vectors.append(vector)

        return vectors

    async def _mark_embedding_generated(self, content_id: str) -> None:
        """Mark curriculum content as having embeddings generated.

        Args:
            content_id: ID of the content to mark

        """
        stmt = (
            update(CurriculumContent)
            .where(CurriculumContent.id == content_id)
            .values(embedding_generated=True)
        )
        await self.db.execute(stmt)
        await self.db.commit()
        msg = f"Marked content {content_id} as embedding_generated=True"
        logger.debug(msg)
