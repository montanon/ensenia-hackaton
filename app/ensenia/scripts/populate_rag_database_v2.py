#!/usr/bin/env python3
"""Population script for RAG database with grade-folder structure.

This script supports a folder structure like:
    8°/
      Ciencias Naturales/
        - doc1.pdf
        - doc2.pdf
      Matemáticas/
        - doc3.pdf
      doc_general.pdf  ← Grade-level doc (added to ALL subjects)

Usage:
    python -m app.ensenia.scripts.populate_rag_database_v2 --grade-dir ./data/8° --difficulty medium
    python -m app.ensenia.scripts.populate_rag_database_v2 --process-existing
"""

import argparse
import asyncio
import logging
import re
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

logger = logging.getLogger(__name__)

MIN_TEXT_LENGTH = 100


def extract_grade_from_folder(folder_name: str) -> int | None:
    """Extract grade number from folder name like '8°', '7', 'Grade 6', etc.

    Args:
        folder_name: Folder name

    Returns:
        Grade number or None if not found

    """
    # Try patterns: "8°", "8", "Grade 8", "grade-8"
    patterns = [
        r"^(\d+)°?$",  # 8° or 8
        r"(?i)grade[_\s-]?(\d+)",  # Grade 8, grade-8, etc.
        r"(\d+)[°º]",  # 8°, 8º
    ]

    for pattern in patterns:
        match = re.search(pattern, folder_name)
        if match:
            return int(match.group(1))

    return None


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

    async def populate_from_grade_folder(
        self,
        grade_dir: Path,
        difficulty: str = "medium",
    ) -> dict[str, Any]:
        """Populate database from a grade folder with subject subfolders.

        Args:
            grade_dir: Grade directory (e.g., ./data/8°)
            difficulty: Difficulty level (easy, medium, hard)

        Returns:
            Dictionary with processing statistics
        """
        if not grade_dir.exists():
            msg = f"Grade directory not found: {grade_dir}"
            raise FileNotFoundError(msg)

        if not grade_dir.is_dir():
            msg = f"Grade path is not a directory: {grade_dir}"
            raise ValueError(msg)

        # Extract grade from folder name
        grade = extract_grade_from_folder(grade_dir.name)
        if grade is None:
            msg = f"Could not extract grade from folder name: {grade_dir.name}"
            raise ValueError(msg)

        logger.info(f"Processing Grade {grade} from folder: {grade_dir}")

        # Find all PDF files in root (grade-level documents)
        grade_level_pdfs = list(grade_dir.glob("*.pdf"))
        logger.info(f"Found {len(grade_level_pdfs)} grade-level PDFs in root folder")

        # Find all subject subdirectories
        subject_dirs = [d for d in grade_dir.iterdir() if d.is_dir()]
        logger.info(f"Found {len(subject_dirs)} subject folders")

        if not subject_dirs and not grade_level_pdfs:
            msg = "No subject folders or PDFs found in grade directory"
            logger.warning(msg)
            return {"files_processed": 0, "content_created": 0, "subjects_processed": 0}

        overall_stats = {
            "grade": grade,
            "subjects_processed": 0,
            "files_processed": 0,
            "files_failed": 0,
            "content_created": 0,
            "embeddings_generated": 0,
            "errors": [],
        }

        # Process each subject folder
        total_subjects = len(subject_dirs)
        for idx, subject_dir in enumerate(subject_dirs, 1):
            subject_name = subject_dir.name
            progress_pct = (idx / total_subjects) * 100
            logger.info(f"\n{'=' * 60}")
            logger.info(
                f"[{idx}/{total_subjects}] ({progress_pct:.1f}%) Processing Subject: {subject_name} (Grade {grade})"
            )
            logger.info(f"{'=' * 60}")

            # Find subject-specific PDFs
            subject_pdfs = list(subject_dir.glob("*.pdf"))
            logger.info(f"  - Subject-specific PDFs: {len(subject_pdfs)}")
            logger.info(f"  - Grade-level PDFs: {len(grade_level_pdfs)}")
            logger.info(
                f"  - Total PDFs for this subject: {len(subject_pdfs) + len(grade_level_pdfs)}"
            )

            # Combine subject PDFs + grade-level PDFs
            all_pdfs = subject_pdfs + grade_level_pdfs

            if not all_pdfs:
                logger.warning(f"  No PDFs found for subject: {subject_name}")
                continue

            # Process all PDFs for this subject
            subject_stats = await self._process_pdfs_for_subject(
                pdfs=all_pdfs,
                grade=grade,
                subject=subject_name,
                difficulty=difficulty,
            )

            # Update overall stats
            overall_stats["subjects_processed"] += 1
            overall_stats["files_processed"] += subject_stats["files_processed"]
            overall_stats["files_failed"] += subject_stats["files_failed"]
            overall_stats["content_created"] += subject_stats["content_created"]
            overall_stats["embeddings_generated"] += subject_stats[
                "embeddings_generated"
            ]
            overall_stats["errors"].extend(subject_stats["errors"])

        logger.info(f"\n{'=' * 60}")
        logger.info("OVERALL PROCESSING SUMMARY")
        logger.info(f"{'=' * 60}")
        logger.info(f"Grade: {overall_stats['grade']}")
        logger.info(f"Subjects processed: {overall_stats['subjects_processed']}")
        logger.info(f"Total files processed: {overall_stats['files_processed']}")
        logger.info(f"Files failed: {overall_stats['files_failed']}")
        logger.info(f"Content entries created: {overall_stats['content_created']}")
        logger.info(f"Embeddings generated: {overall_stats['embeddings_generated']}")
        logger.info(f"{'=' * 60}")

        return overall_stats

    async def _process_pdfs_for_subject(
        self,
        pdfs: list[Path],
        grade: int,
        subject: str,
        difficulty: str,
    ) -> dict[str, Any]:
        """Process a list of PDFs for a specific subject.

        Args:
            pdfs: List of PDF file paths
            grade: Grade level
            subject: Subject name
            difficulty: Difficulty level

        Returns:
            Processing statistics
        """
        stats = {
            "files_processed": 0,
            "files_failed": 0,
            "content_created": 0,
            "embeddings_generated": 0,
            "errors": [],
        }

        total_pdfs = len(pdfs)
        for pdf_idx, pdf_path in enumerate(pdfs, 1):
            try:
                pdf_progress = (pdf_idx / total_pdfs) * 100
                logger.info(
                    f"  [{pdf_idx}/{total_pdfs}] ({pdf_progress:.1f}%) Processing: {pdf_path.name}"
                )

                # Extract text from PDF
                try:
                    document = self.pdf_processor.extract_text(pdf_path)
                except Exception as pdf_error:
                    msg = f"    ✗ PDF extraction failed: {pdf_path.name} - {pdf_error}"
                    logger.exception(msg)
                    stats["files_failed"] += 1
                    stats["errors"].append(msg)
                    continue

                if not document.text or len(document.text) < MIN_TEXT_LENGTH:
                    msg = f"    ⚠ Skipping (insufficient text): {pdf_path.name}"
                    logger.warning(msg)
                    stats["files_failed"] += 1
                    stats["errors"].append(msg)
                    continue

                # Create content ID
                subject_prefix = "".join(
                    [word[0].upper() for word in subject.split() if word]
                )
                safe_filename = pdf_path.stem.replace(" ", "-")[:50]
                content_id = f"{subject_prefix}-{grade}-{safe_filename}"

                # Check if already exists
                stmt = select(CurriculumContent).where(
                    CurriculumContent.id == content_id
                )
                result = await self.db.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    # Check if embeddings were already generated
                    if existing.embedding_generated:
                        msg = f"    ✓ Already exists with embeddings, skipping: {content_id}"
                        logger.info(msg)
                        stats["files_processed"] += 1
                        continue
                    # Content exists but embeddings missing - regenerate embeddings
                    msg = f"    ⚠ Content exists but missing embeddings, regenerating: {content_id}"
                    logger.info(msg)
                    embedding_result = (
                        await self.embedding_service.process_curriculum_content(
                            content_id
                        )
                    )
                    embeddings_count = embedding_result.get("embeddings_generated", 0)
                    msg = f"    ✓ Generated {embeddings_count} embeddings"
                    logger.info(msg)
                    stats["embeddings_generated"] += embeddings_count
                    stats["files_processed"] += 1
                    continue

                # Create curriculum content entry
                content = CurriculumContent(
                    id=content_id,
                    title=pdf_path.stem,
                    grade=grade,
                    subject=subject,
                    content_text=document.text,
                    learning_objectives=[],
                    ministry_standard_ref="To be determined",
                    ministry_approved=0,
                    keywords="",
                    difficulty_level=difficulty,
                    chunk_index=0,
                    source_file=str(pdf_path),
                    embedding_generated=False,
                )

                self.db.add(content)
                await self.db.commit()
                await self.db.refresh(content)

                msg = f"    ✓ Created content: {content_id}"
                logger.info(msg)
                stats["content_created"] += 1

                # Generate embeddings and store vectors
                embedding_result = (
                    await self.embedding_service.process_curriculum_content(content_id)
                )

                embeddings_count = embedding_result.get("embeddings_generated", 0)
                logger.info(f"    ✓ Generated {embeddings_count} embeddings")
                stats["embeddings_generated"] += embeddings_count
                stats["files_processed"] += 1

            except Exception as e:
                error_msg = f"Failed to process {pdf_path.name}: {e}"
                logger.exception(f"    ✗ {error_msg}")
                stats["files_failed"] += 1
                stats["errors"].append(error_msg)

        return stats

    async def process_existing_content(self) -> dict[str, Any]:
        """Process existing curriculum content that doesn't have embeddings yet.

        Returns:
            Processing statistics
        """
        logger.info("Processing existing curriculum content...")

        # Find all content without embeddings
        stmt = select(CurriculumContent).where(
            CurriculumContent.embedding_generated == False  # noqa: E712
        )
        result = await self.db.execute(stmt)
        content_items = result.scalars().all()

        logger.info(f"Found {len(content_items)} items without embeddings")

        stats = {
            "items_processed": 0,
            "items_failed": 0,
            "embeddings_generated": 0,
            "errors": [],
        }

        total_items = len(content_items)
        for idx, content in enumerate(content_items, 1):
            try:
                progress_pct = (idx / total_items) * 100
                logger.info(
                    f"[{idx}/{total_items}] ({progress_pct:.1f}%) Processing existing content: {content.id}"
                )

                embedding_result = (
                    await self.embedding_service.process_curriculum_content(content.id)
                )

                embeddings_count = embedding_result.get("embeddings_generated", 0)
                logger.info(f"  Generated {embeddings_count} embeddings")
                stats["embeddings_generated"] += embeddings_count
                stats["items_processed"] += 1

            except Exception as e:
                error_msg = f"Failed to process {content.id}: {e}"
                logger.exception(error_msg)
                stats["items_failed"] += 1
                stats["errors"].append(error_msg)

        return stats


async def main() -> None:
    """Entry point."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

    parser = argparse.ArgumentParser(
        description="Populate RAG database from grade folder structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a grade folder
  python -m app.ensenia.scripts.populate_rag_database_v2 --grade-dir ./data/8° --difficulty medium

  # Process existing content without embeddings
  python -m app.ensenia.scripts.populate_rag_database_v2 --process-existing

Folder Structure:
  8°/
    Ciencias Naturales/
      - doc1.pdf
      - doc2.pdf
    Matemáticas/
      - doc3.pdf
    doc_general.pdf  ← Grade-level doc (added to ALL subjects)
        """,
    )

    parser.add_argument(
        "--grade-dir",
        type=Path,
        help="Grade directory containing subject folders and PDFs (e.g., ./data/8°)",
    )
    parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard"],
        default="medium",
        help="Content difficulty level (default: medium)",
    )
    parser.add_argument(
        "--process-existing",
        action="store_true",
        help="Process existing content that doesn't have embeddings yet",
    )

    args = parser.parse_args()

    if not args.grade_dir and not args.process_existing:
        parser.error("Either --grade-dir or --process-existing is required")

    if args.grade_dir and args.process_existing:
        parser.error("Cannot use both --grade-dir and --process-existing")

    # Initialize database
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        populator = RAGDatabasePopulator(session)

        if args.process_existing:
            logger.info("Processing existing content without embeddings...")
            stats = await populator.process_existing_content()
            logger.info(f"\nProcessed {stats['items_processed']} items")
            logger.info(f"Generated {stats['embeddings_generated']} embeddings")
            if stats["items_failed"] > 0:
                logger.error(f"Failed: {stats['items_failed']} items")

        elif args.grade_dir:
            logger.info(f"Populating from grade folder: {args.grade_dir}")
            stats = await populator.populate_from_grade_folder(
                grade_dir=args.grade_dir,
                difficulty=args.difficulty,
            )

            if stats["errors"]:
                logger.error("\nErrors encountered:")
                for error in stats["errors"]:
                    logger.error(f"  - {error}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
