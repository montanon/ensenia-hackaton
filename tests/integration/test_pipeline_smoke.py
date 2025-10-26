"""Integration smoke tests for the RAG pipeline."""

import logging
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.ensenia.core.config import settings
from app.ensenia.database.models import CurriculumContent
from app.ensenia.services.embedding_service import EmbeddingService
from app.ensenia.services.pdf_processor import PDFProcessor

logger = logging.getLogger(__name__)


@pytest.mark.skip(reason="Requires real Cloudflare API credentials and PDF file")
@pytest.mark.asyncio
async def test_rag_pipeline_end_to_end():
    """Test the complete RAG pipeline with a real PDF.

    This test:
    1. Extracts text from a PDF
    2. Stores content in PostgreSQL
    3. Generates embeddings
    4. Stores vectors in Vectorize
    5. Verifies data in database
    6. Cleans up test data

    Note: This test requires a PDF file at data/CUADERNILLO3.pdf
    It will be skipped if the PDF is not available.
    """
    # Setup
    pdf_path = Path("data/CUADERNILLO3.pdf")  # Small PDF for faster testing

    if not pdf_path.exists():
        pytest.skip(
            f"Test PDF not found at {pdf_path.absolute()} - skipping integration test"
        )

    # Use a unique ID each time to avoid duplicate key constraint violations
    import time

    test_content_id = f"TEST-PIPELINE-INTEGRATION-{int(time.time() * 1000)}"

    # Initialize database
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            # Step 1: Extract text from PDF
            processor = PDFProcessor()
            document = processor.extract_text(pdf_path)

            assert document.text is not None
            assert len(document.text) > 100
            msg = f"✓ Extracted {len(document.text)} characters from PDF"
            logger.info(msg)

            # Step 2: Store in PostgreSQL
            content = CurriculumContent(
                id=test_content_id,
                title="Test Pipeline PDF",
                grade=7,
                subject="Test Subject",
                content_text=document.text,
                learning_objectives=[],
                ministry_standard_ref="Test",
                ministry_approved=0,
                keywords="test pipeline",
                difficulty_level="medium",
                chunk_index=0,
                source_file=str(pdf_path),
                embedding_generated=False,
            )

            session.add(content)
            await session.commit()
            await session.refresh(content)

            msg = f"✓ Stored content in PostgreSQL: {test_content_id}"
            logger.info(msg)

            # Step 3 & 4: Generate embeddings and store in Vectorize
            embedding_service = EmbeddingService(session)
            result = await embedding_service.process_curriculum_content(test_content_id)

            embeddings_count = result.get("embeddings_generated", 0)
            assert embeddings_count > 0
            msg = f"✓ Generated {embeddings_count} embeddings and stored in Vectorize"
            logger.info(msg)

            # Step 5: Verify data in database
            stmt = select(CurriculumContent).where(
                CurriculumContent.id == test_content_id
            )
            result = await session.execute(stmt)
            stored_content = result.scalar_one_or_none()

            assert stored_content is not None
            assert stored_content.embedding_generated is True
            msg = "✓ Verified content in database with embeddings flag set"
            logger.info(msg)

            # Cleanup
            await session.delete(stored_content)
            await session.commit()
            msg = "✓ Cleaned up test data"
            logger.info(msg)

    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_chunking_integration():
    """Test that chunking works correctly with PDF content."""
    from app.ensenia.services.chunking import SimpleChunkingStrategy

    pdf_path = Path("data/CUADERNILLO3.pdf")

    if not pdf_path.exists():
        pytest.skip(f"Test PDF not found: {pdf_path}")

    # Extract text
    processor = PDFProcessor()
    document = processor.extract_text(pdf_path)

    # Chunk text
    chunker = SimpleChunkingStrategy(chunk_size=768, overlap=128)
    chunks = chunker.chunk_text(document.text)

    assert len(chunks) > 0
    assert all(len(chunk.text) <= 768 for chunk in chunks)
    assert all(chunk.index == i for i, chunk in enumerate(chunks))

    msg = f"✓ Created {len(chunks)} chunks from PDF content"
    logger.info(msg)
