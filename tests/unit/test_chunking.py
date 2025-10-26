"""Unit tests for text chunking strategies."""

from app.ensenia.services.chunking import SimpleChunkingStrategy


class TestSimpleChunkingStrategy:
    """Test the simple chunking strategy."""

    def test_basic_chunking(self, sample_text):
        """Test that text is chunked correctly."""
        chunker = SimpleChunkingStrategy(chunk_size=200, overlap=50)
        chunks = chunker.chunk_text(sample_text)

        assert len(chunks) > 0
        assert all(hasattr(chunk, "text") for chunk in chunks)
        assert all(hasattr(chunk, "index") for chunk in chunks)
        assert all(hasattr(chunk, "metadata") for chunk in chunks)

    def test_chunk_size_respected(self):
        """Test that chunks don't exceed max size."""
        text = "word " * 200  # 200 words
        chunker = SimpleChunkingStrategy(chunk_size=100, overlap=20)
        chunks = chunker.chunk_text(text)

        for chunk in chunks:
            assert len(chunk.text) <= 100

    def test_overlap_works(self):
        """Test that chunks have overlap."""
        text = "This is a test sentence. " * 20
        chunker = SimpleChunkingStrategy(chunk_size=100, overlap=30)
        chunks = chunker.chunk_text(text)

        if len(chunks) > 1:
            # Check that consecutive chunks share some text
            for i in range(len(chunks) - 1):
                chunk1 = chunks[i].text
                chunk2 = chunks[i + 1].text
                # At least some overlap should exist
                assert any(word in chunk2 for word in chunk1.split()[-10:])

    def test_metadata_preserved(self):
        """Test that metadata is added to chunks."""
        text = "Test text for chunking."
        metadata = {"source": "test", "grade": 7}
        chunker = SimpleChunkingStrategy(chunk_size=200, overlap=50)
        chunks = chunker.chunk_text(text, metadata=metadata)

        for chunk in chunks:
            assert chunk.metadata["source"] == "test"
            assert chunk.metadata["grade"] == 7

    def test_empty_text(self):
        """Test handling of empty text."""
        chunker = SimpleChunkingStrategy()
        chunks = chunker.chunk_text("")

        assert len(chunks) == 0

    def test_short_text(self):
        """Test that short text creates one chunk."""
        text = "Short text."
        chunker = SimpleChunkingStrategy(chunk_size=200)
        chunks = chunker.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_chunk_indices(self):
        """Test that chunk indices are sequential."""
        text = "word " * 500
        chunker = SimpleChunkingStrategy(chunk_size=100, overlap=20)
        chunks = chunker.chunk_text(text)

        for i, chunk in enumerate(chunks):
            assert chunk.index == i
