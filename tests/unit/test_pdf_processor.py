"""Unit tests for PDF text extraction."""

from pathlib import Path

import pytest

from app.ensenia.services.pdf_processor import PDFProcessor


class TestPDFProcessor:
    """Test the PDF processor service."""

    def test_extract_text_from_real_pdf(self):
        """Test extraction from a real PDF file."""
        # Use an actual PDF from the data directory
        pdf_path = Path("data/CIENCIAS-NATURALES-ACTIVIDADES-TOMO-II.pdf")

        if not pdf_path.exists():
            pytest.skip(f"Test PDF not found: {pdf_path}")

        processor = PDFProcessor()
        document = processor.extract_text(pdf_path)

        assert document is not None
        assert document.text is not None
        assert len(document.text) > 0
        assert document.page_count > 0
        assert document.source_file == str(pdf_path)

    def test_extract_metadata(self):
        """Test that metadata is extracted."""
        pdf_path = Path("data/CIENCIAS-NATURALES-ACTIVIDADES-TOMO-II.pdf")

        if not pdf_path.exists():
            pytest.skip(f"Test PDF not found: {pdf_path}")

        processor = PDFProcessor()
        document = processor.extract_text(pdf_path)

        assert document.metadata is not None
        assert isinstance(document.metadata, dict)

    def test_page_count_accuracy(self):
        """Test that page count is accurate."""
        pdf_path = Path("data/CIENCIAS-NATURALES-ACTIVIDADES-TOMO-II.pdf")

        if not pdf_path.exists():
            pytest.skip(f"Test PDF not found: {pdf_path}")

        processor = PDFProcessor()
        document = processor.extract_text(pdf_path)

        # Known page count for this PDF
        assert document.page_count == 241

    def test_missing_file(self):
        """Test handling of missing PDF file."""
        processor = PDFProcessor()

        with pytest.raises(FileNotFoundError):
            processor.extract_text("nonexistent.pdf")

    def test_invalid_pdf_path(self):
        """Test handling of invalid path."""
        processor = PDFProcessor()

        with pytest.raises((FileNotFoundError, ValueError)):
            processor.extract_text("")

    def test_text_content_quality(self):
        """Test that extracted text has reasonable quality."""
        pdf_path = Path("data/CIENCIAS-NATURALES-ACTIVIDADES-TOMO-II.pdf")

        if not pdf_path.exists():
            pytest.skip(f"Test PDF not found: {pdf_path}")

        processor = PDFProcessor()
        document = processor.extract_text(pdf_path)

        # Should have substantial text
        assert len(document.text) > 10000

        # Should contain expected keywords for this curriculum document
        text_lower = document.text.lower()
        assert "ciencias" in text_lower or "naturales" in text_lower
