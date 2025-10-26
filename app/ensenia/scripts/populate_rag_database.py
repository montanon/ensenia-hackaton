#!/usr/bin/env python3
"""Population script for RAG database.

This script orchestrates the complete pipeline:
1. Extract text from PDF files
2. Chunk the text
3. Store chunks in PostgreSQL as curriculum_content
4. Generate embeddings
5. Store vectors in Cloudflare Vectorize

Usage:
    python -m app.ensenia.scripts.populate_rag_database --pdf-dir ./data/pdfs
    python -m app.ensenia.scripts.populate_rag_database --process-existing
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.ensenia.core.config import settings
from app.ensenia.database.models import CurriculumContent
from app.ensenia.services.embedding_service import EmbeddingService
from app.ensenia.services.pdf_processor import PDFProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class RAGDatabasePopulator:
    """Orchestrates the RAG database population pipeline."""

    def __init__(self, db_session: AsyncSession):
        """Initialize populator.

        Args:
            db_session: Database session

        """
        self.db = db_session
        self.pdf_processor = PDFProcessor()
        self.embedding_service = EmbeddingService(db_session)

    async def populate_from_pdfs(
        self,
        pdf_dir: Path,
        grade: int,
        subject: str,
        difficulty: str = "medium",
    ) -> dict[str, Any]:
        """Populate database from PDF files in a directory.

        Args:
            pdf_dir: Directory containing PDF files
            grade: Grade level for the content
            subject: Subject name
            difficulty: Difficulty level (easy, medium, hard)

        Returns:
            Dictionary with processing statistics

        """
        if not pdf_dir.exists():
            msg = "PDF directory not found: {pdf_dir}"
            raise FileNotFoundError(msg)

        # Find all PDF files
        pdf_files = list(pdf_dir.glob("*.pdf"))
        msg = "Found {len(pdf_files)} PDF files in {pdf_dir}"
        logger.info(msg)

        if not pdf_files:
            msg = "No PDF files found in {pdf_dir}"
            logger.warning(msg)
            return {"files_processed": 0, "content_created": 0}

        stats = {
            "files_processed": 0,
            "files_failed": 0,
            "content_created": 0,
            "embeddings_generated": 0,
            "errors": [],
        }

        # Process each PDF
        for pdf_path in pdf_files:
            try:
                msg = "Processing PDF: {pdf_path.name}"
                logger.info(msg)

                # Extract text from PDF
                document = self.pdf_processor.extract_text(pdf_path)

                # Create curriculum content entry
                content_id = await self._create_curriculum_content(
                    document=document,
                    grade=grade,
                    subject=subject,
                    difficulty=difficulty,
                )

                stats["content_created"] += 1
                stats["files_processed"] += 1

                msg = "Created curriculum content: {content_id}"
                logger.info(msg)

                # Generate embeddings
                embedding_result = (
                    await self.embedding_service.process_curriculum_content(content_id)
                )

                stats["embeddings_generated"] += embedding_result[
                    "embeddings_generated"
                ]
                msg = (
                    f"Generated {embedding_result['embeddings_generated']} "
                    f"embeddings for {content_id}"
                )
                logger.info(msg)

            except Exception as e:
                msg = "Failed to process {pdf_path.name}: {e}"
                logger.exception(msg)
                stats["files_failed"] += 1
                stats["errors"].append({"file": pdf_path.name, "error": str(e)})

        msg = (
            f"Population complete: {stats['files_processed']} files, "
            f"{stats['content_created']} content items, "
            f"{stats['embeddings_generated']} embeddings"
        )
        logger.info(msg)

        return stats

    async def process_existing_content(self) -> dict[str, Any]:
        """Process existing curriculum content to generate embeddings.

        Useful for regenerating embeddings or processing content added manually.

        Returns:
            Dictionary with processing statistics

        """
        msg = "Processing existing curriculum content for embeddings"
        logger.info(msg)

        result = await self.embedding_service.process_all_curriculum_content()

        msg = (
            f"Processed {result['total_processed']} content items, "
            f"generated {result['total_embeddings']} embeddings"
        )
        logger.info(msg)

        return result

    async def _create_curriculum_content(
        self,
        document: object,
        grade: int,
        subject: str,
        difficulty: str,
    ) -> str:
        """Create a curriculum content entry in the database.

        Args:
            document: PDFDocument with extracted text
            grade: Grade level
            subject: Subject name
            difficulty: Difficulty level

        Returns:
            Content ID

        """
        # Generate content ID from filename
        source_path = Path(document.source_file)
        base_name = source_path.stem.replace(" ", "-").replace("_", "-")
        content_id = f"{subject[:3].upper()}-{grade}-{base_name}"[:50]

        # Check if content already exists
        stmt = select(CurriculumContent).where(CurriculumContent.id == content_id)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            msg = "Content {content_id} already exists, skipping"
            logger.warning(msg)
            return content_id

        # Extract title from metadata or filename
        title = document.metadata.get("title") or source_path.stem
        title = title[:255]  # Truncate to fit column

        # Create content entry
        content = CurriculumContent(
            id=content_id,
            title=title,
            grade=grade,
            subject=subject,
            content_text=document.text,
            learning_objectives=[],  # Can be populated later
            ministry_standard_ref="To be determined",
            ministry_approved=0,
            keywords="",  # Can be extracted/generated later
            difficulty_level=difficulty,
            source_file=str(document.source_file),
            chunk_index=0,
            embedding_generated=False,
        )

        self.db.add(content)
        await self.db.commit()
        await self.db.refresh(content)

        msg = "Created database entry for {content_id}"
        logger.debug(msg)

        return content.id


async def main() -> None:
    """Entry point for the population script."""
    parser = argparse.ArgumentParser(
        description="Populate RAG database from PDFs or process existing content"
    )

    parser.add_argument(
        "--pdf-dir",
        type=Path,
        help="Directory containing PDF files to process",
    )
    parser.add_argument(
        "--grade",
        type=int,
        default=5,
        help="Grade level for the content (default: 5)",
    )
    parser.add_argument(
        "--subject",
        type=str,
        default="General",
        help="Subject name (default: General)",
    )
    parser.add_argument(
        "--difficulty",
        type=str,
        choices=["easy", "medium", "hard"],
        default="medium",
        help="Difficulty level (default: medium)",
    )
    parser.add_argument(
        "--process-existing",
        action="store_true",
        help="Process existing curriculum content to generate embeddings",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.process_existing and not args.pdf_dir:
        parser.error("Either --pdf-dir or --process-existing must be specified")

    # Create database engine and session
    engine = create_async_engine(
        settings.database_url,
        echo=settings.environment == "development",
    )

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        populator = RAGDatabasePopulator(session)

        try:
            if args.process_existing:
                msg = "Processing existing curriculum content"
                logger.info(msg)
                result = await populator.process_existing_content()
            else:
                msg = "Populating from PDFs in {args.pdf_dir}"
                logger.info(msg)
                result = await populator.populate_from_pdfs(
                    pdf_dir=args.pdf_dir,
                    grade=args.grade,
                    subject=args.subject,
                    difficulty=args.difficulty,
                )

            # Print summary
            msg = "=" * 60
            logger.info(msg)
            msg = "POPULATION SUMMARY"
            logger.info(msg)
            msg = "=" * 60
            logger.info(msg)
            for key in result:
                if key != "errors":
                    msg = "{key}: {value}"
                    logger.info(msg)

            if result.get("errors"):
                msg = "Errors encountered: {len(result['errors'])}"
                logger.warning(msg)
                for error in result["errors"]:
                    msg = f"  - {error}"
                    logger.warning(msg)

            logger.info("=" * 60)

        except Exception:
            msg = "Population failed: {e}"
            logger.exception(msg)
            sys.exit(1)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
