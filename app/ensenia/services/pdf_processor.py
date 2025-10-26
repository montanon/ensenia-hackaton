"""PDF text extraction service for curriculum content processing.

This module provides functionality to extract text from PDF files,
handling metadata and preparing content for chunking and embedding.
"""

import logging
from pathlib import Path
from typing import Any

import pdfplumber

logger = logging.getLogger(__name__)


class PDFDocument:
    """Represents an extracted PDF document with metadata.

    Attributes:
        text: Full extracted text content
        metadata: Document metadata (title, author, etc.)
        page_count: Number of pages in the document
        source_file: Path to the source PDF file

    """

    def __init__(
        self,
        text: str,
        metadata: dict[str, Any],
        page_count: int,
        source_file: str,
    ):
        """Initialize PDF document.

        Args:
            text: Extracted text content
            metadata: Document metadata
            page_count: Number of pages
            source_file: Source file path

        """
        self.text = text
        self.metadata = metadata
        self.page_count = page_count
        self.source_file = source_file


class PDFProcessor:
    """Service for extracting text from PDF files.

    Uses pdfplumber for robust PDF text extraction with support for
    various PDF formats and layouts.

    Example usage:
        processor = PDFProcessor()
        document = processor.extract_text("path/to/file.pdf")
        print(document.text)
    """

    def __init__(self, *, extract_images: bool = False):
        """Initialize PDF processor.

        Args:
            extract_images: Whether to attempt image extraction (default: False)

        """
        self.extract_images = extract_images

    def extract_text(self, pdf_path: str | Path) -> PDFDocument:
        """Extract text from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            PDFDocument with extracted text and metadata

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If file is not a valid PDF

        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            msg = "PDF file not found: {pdf_path}"
            raise FileNotFoundError(msg)

        if pdf_path.suffix.lower() != ".pdf":
            msg = "File is not a PDF: {pdf_path}"
            raise ValueError(msg)

        msg = "Extracting text from PDF: {pdf_path}"
        logger.info(msg)

        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extract metadata
                metadata = self._extract_metadata(pdf)

                # Extract text from all pages
                text_parts = []
                for page_num, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                    msg = (
                        f"Extracted {len(page_text) if page_text else 0} "
                        f"chars from page {page_num}"
                    )
                    logger.debug(msg)

                # Combine all text
                full_text = "\n\n".join(text_parts)

                msg = (
                    f"Successfully extracted {len(full_text)} characters from "
                    f"{len(pdf.pages)} pages"
                )
                logger.info(msg)

                return PDFDocument(
                    text=full_text,
                    metadata=metadata,
                    page_count=len(pdf.pages),
                    source_file=str(pdf_path),
                )

        except Exception:
            msg = "Failed to extract text from {pdf_path}: {e}"
            logger.exception(msg)
            raise

    def extract_text_batch(self, pdf_paths: list[str | Path]) -> dict[str, PDFDocument]:
        """Extract text from multiple PDF files.

        Args:
            pdf_paths: List of paths to PDF files

        Returns:
            Dictionary mapping file paths to PDFDocument objects
            Failed extractions are logged but not included in results

        """
        results = {}

        for pdf_path in pdf_paths:
            try:
                document = self.extract_text(pdf_path)
                results[str(pdf_path)] = document
            except Exception:
                msg = "Skipping {pdf_path} due to error: {e}"
                logger.exception(msg)
                continue

        msg = f"Successfully extracted {len(results)}/{len(pdf_paths)} PDF files"
        logger.info(msg)

        return results

    def _extract_metadata(self, pdf: pdfplumber.PDF) -> dict[str, Any]:
        """Extract metadata from PDF.

        Args:
            pdf: Opened pdfplumber PDF object

        Returns:
            Dictionary of metadata fields

        """
        metadata = {}

        # Get PDF metadata if available
        if pdf.metadata:
            metadata.update(
                {
                    "title": pdf.metadata.get("Title", ""),
                    "author": pdf.metadata.get("Author", ""),
                    "subject": pdf.metadata.get("Subject", ""),
                    "creator": pdf.metadata.get("Creator", ""),
                    "producer": pdf.metadata.get("Producer", ""),
                    "creation_date": pdf.metadata.get("CreationDate", ""),
                }
            )

        # Add page count
        metadata["page_count"] = len(pdf.pages)

        return metadata

    def extract_by_page(self, pdf_path: str | Path) -> list[tuple[int, str]]:
        """Extract text from PDF, returning individual pages.

        Useful for maintaining page-level granularity in chunks.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of (page_number, page_text) tuples

        Raises:
            FileNotFoundError: If PDF file doesn't exist

        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            msg = "PDF file not found: {pdf_path}"
            raise FileNotFoundError(msg)

        msg = "Extracting text by page from PDF: {pdf_path}"
        logger.info(msg)

        pages_text = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text() or ""
                    pages_text.append((page_num, page_text))

            msg = f"Extracted {len(pages_text)} pages from {pdf_path}"
            logger.info(msg)

            return pages_text

        except Exception:
            msg = "Failed to extract pages from {pdf_path}: {e}"
            logger.exception(msg)
            raise
