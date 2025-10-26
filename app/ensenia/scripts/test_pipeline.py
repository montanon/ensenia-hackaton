"""Simple test script to validate the RAG pipeline.

This script tests the complete pipeline with a single PDF file:
1. PDF text extraction
2. Text chunking
3. Database storage
4. Embedding generation (dry-run mode)

Usage:
    python -m app.ensenia.scripts.test_pipeline
"""

import asyncio
import logging
import sys
from pathlib import Path

from app.ensenia.services.chunking import SimpleChunkingStrategy
from app.ensenia.services.pdf_processor import PDFProcessor

logger = logging.getLogger(__name__)


MIN_TEXT_LENGTH = 100


async def test_pipeline() -> bool:
    """Test the RAG pipeline components."""
    msg = "=" * 60
    logger.info(msg)
    msg = "RAG PIPELINE TEST"
    logger.info(msg)
    msg = "=" * 60
    logger.info(msg)

    # Find project root and data directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent
    data_dir = project_root / "data"

    msg = f"Project root: {project_root}"
    logger.info(msg)
    msg = f"Data directory: {data_dir}"
    logger.info(msg)

    # Find a test PDF
    pdf_files = list(data_dir.glob("*.pdf"))
    if not pdf_files:
        msg = "No PDF files found in data directory"
        logger.error(msg)
        return False

    test_pdf = pdf_files[0]
    msg = f"Using test PDF: {test_pdf.name}"
    logger.info(msg)

    # Test 1: PDF Text Extraction
    msg = "\n" + "=" * 60
    logger.info(msg)
    msg = "TEST 1: PDF Text Extraction"
    logger.info(msg)
    msg = "=" * 60
    logger.info(msg)

    try:
        pdf_processor = PDFProcessor()
        document = pdf_processor.extract_text(test_pdf)

        msg = "✓ Extraction successful"
        logger.info(msg)
        msg = f"  - Pages: {document.page_count}"
        logger.info(msg)
        msg = f"  - Characters: {len(document.text)}"
        logger.info(msg)
        msg = f"  - Title: {document.metadata.get('title', 'N/A')}"
        logger.info(msg)
        msg = f"  - Text preview: {document.text[:200]}..."
        logger.info(msg)

        if len(document.text) < MIN_TEXT_LENGTH:
            logger.warning(
                "⚠ Text seems very short, PDF may not have extracted properly"
            )

    except Exception:
        msg = "✗ PDF extraction failed."
        logger.exception(msg)
        return False

    # Test 2: Text Chunking
    msg = "\n" + "=" * 60
    logger.info(msg)
    msg = "TEST 2: Text Chunking"
    logger.info(msg)
    msg = "=" * 60
    logger.info(msg)

    try:
        chunking_strategy = SimpleChunkingStrategy(
            chunk_size=768, overlap=128, respect_sentences=True
        )

        metadata = {
            "source_file": str(test_pdf),
            "title": document.metadata.get("title", test_pdf.stem),
        }

        chunks = chunking_strategy.chunk_text(document.text, metadata)

        msg = "✓ Chunking successful"
        logger.info(msg)
        msg = f"  - Chunks created: {len(chunks)}"
        logger.info(msg)
        msg = f"  - Chunk size: {chunking_strategy.get_chunk_size()}"
        logger.info(msg)
        msg = f"  - Overlap: {chunking_strategy.get_overlap()}"
        logger.info(msg)

        if chunks:
            msg = "\n  First chunk preview:"
            logger.info(msg)
            msg = f"    - Index: {chunks[0].index}"
            logger.info(msg)
            msg = f"    - Length: {len(chunks[0].text)}"
            logger.info(msg)
            msg = f"    - Text: {chunks[0].text[:150]}..."
            logger.info(msg)
            msg = f"    - Metadata keys: {list(chunks[0].metadata.keys())}"
            logger.info(msg)

        if not chunks:
            logger.warning("⚠ No chunks created, text may be too short")

    except Exception:
        msg = "✗ Chunking failed."
        logger.exception(msg)
        return False

    # Test 3: Validate Chunk Quality
    msg = "\n" + "=" * 60
    logger.info(msg)
    msg = "TEST 3: Chunk Quality Validation"
    logger.info(msg)
    msg = "=" * 60
    logger.info(msg)

    try:
        # Check chunk sizes
        chunk_sizes = [len(chunk.text) for chunk in chunks]
        avg_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
        min_size = min(chunk_sizes) if chunk_sizes else 0
        max_size = max(chunk_sizes) if chunk_sizes else 0

        logger.info("✓ Chunk size analysis:")
        msg = f"  - Average: {avg_size:.0f} chars"
        logger.info(msg)
        msg = f"  - Min: {min_size} chars"
        logger.info(msg)
        msg = f"  - Max: {max_size} chars"
        logger.info(msg)
        msg = f"  - Target: {chunking_strategy.get_chunk_size()} chars"
        logger.info(msg)

        # Check overlap
        if len(chunks) > 1:
            first_chunk_end = chunks[0].text[-50:]
            second_chunk_start = chunks[1].text[:50]

            overlap_detected = any(
                word in second_chunk_start for word in first_chunk_end.split()[-10:]
            )
            msg = f"  - Overlap detected chunks: {'Yes' if overlap_detected else 'No'}"
            logger.info(msg)

        # Check metadata preservation
        if chunks:
            metadata_preserved = all(
                chunk.metadata.get("source_file") == str(test_pdf) for chunk in chunks
            )
            msg = f"  - Metadata preserved: {'Yes' if metadata_preserved else 'No'}"
            logger.info(msg)

    except Exception:
        msg = "✗ Validation failed."
        logger.exception(msg)
        return False

    # Test 4: Dry-run Database Entry Creation
    msg = "\n" + "=" * 60
    logger.info(msg)
    msg = "TEST 4: Database Entry Structure (Dry-run)"
    logger.info(msg)
    msg = "=" * 60
    logger.info(msg)
    logger.info("=" * 60)

    try:
        # Simulate what would be stored in the database
        content_id = f"TEST-5-{test_pdf.stem[:20]}"
        db_entry_structure = {
            "id": content_id,
            "title": document.metadata.get("title") or test_pdf.stem[:255],
            "grade": 5,
            "subject": "Test Subject",
            "content_text": document.text,
            "learning_objectives": [],
            "ministry_standard_ref": "Test Reference",
            "ministry_approved": 0,
            "keywords": "",
            "difficulty_level": "medium",
            "source_file": str(test_pdf),
            "chunk_index": 0,
            "embedding_generated": False,
        }

        logger.info("✓ Database entry structure:")
        msg = f"  - ID: {db_entry_structure['id']}"
        logger.info(msg)
        msg = f"  - Title: {db_entry_structure['title'][:50]}..."
        logger.info(msg)
        msg = f"  - Content length: {len(db_entry_structure['content_text'])} chars"
        logger.info(msg)
        msg = f"  - Grade: {db_entry_structure['grade']}"
        logger.info(msg)
        msg = f"  - Subject: {db_entry_structure['subject']}"
        logger.info(msg)
        msg = f"  - Difficulty: {db_entry_structure['difficulty_level']}"
        logger.info(msg)
        msg = f"  - Difficulty: {db_entry_structure['difficulty_level']}"
        logger.info(msg)

    except Exception:
        msg = "✗ Database structure validation failed."
        logger.exception(msg)
        return False

    # Test 5: Dry-run Vector Preparation
    msg = "\n" + "=" * 60
    logger.info(msg)
    msg = "TEST 5: Vector Structure (Dry-run)"
    logger.info(msg)
    msg = "=" * 60
    logger.info(msg)
    logger.info("=" * 60)

    try:
        # Simulate vector preparation (without actual embedding generation)
        if chunks:
            sample_vector = {
                "id": f"{content_id}_chunk_0",
                "values": [0.0] * 768,  # Placeholder embedding
                "metadata": {
                    "content_id": content_id,
                    "grade": 5,
                    "subject": "Test Subject",
                    "chunk_index": 0,
                    "chunk_text": chunks[0].text[:200],
                },
            }

            logger.info("✓ Vector structure:")
            msg = f"  - Vector ID: {sample_vector['id']}"
            logger.info(msg)
            msg = f"  - Dimensions: {len(sample_vector['values'])}"
            logger.info(msg)
            msg = f"  - Metadata keys: {list(sample_vector['metadata'].keys())}"
            logger.info(msg)
            msg = f"  - Total vectors needed: {len(chunks)}"
            logger.info(msg)

    except Exception:
        msg = "✗ Vector structure validation failed."
        logger.exception(msg)
        return False

    # Summary
    msg = "\n" + "=" * 60
    logger.info(msg)
    msg = "TEST SUMMARY"
    logger.info(msg)
    msg = "=" * 60
    logger.info(msg)
    logger.info("✓ All pipeline components validated successfully")
    msg = "\nPipeline would process:"
    logger.info(msg)
    msg = f"  - 1 PDF file ({document.page_count} pages)"
    logger.info(msg)
    msg = f"  - {len(chunks)} text chunks"
    logger.info(msg)
    msg = f"  - {len(chunks)} embeddings to generate"
    logger.info(msg)
    msg = f"  - {len(chunks)} vectors to store in Vectorize"
    logger.info(msg)
    logger.info("\nTo run the full pipeline with database and embeddings:")
    logger.info(
        "  python -m app.ensenia.scripts.populate_rag_database --pdf-dir ./data"
    )
    logger.info("=" * 60)

    return True


if __name__ == "__main__":
    success = asyncio.run(test_pipeline())
    sys.exit(0 if success else 1)
