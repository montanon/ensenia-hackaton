"""Unit tests for WorkersAIService."""

import pytest
from pytest_httpx import HTTPXMock

from app.ensenia.core.config import settings
from app.ensenia.services.cloudflare.workers_ai import WorkersAIService


class TestWorkersAIService:
    """Unit tests for WorkersAIService."""

    @pytest.fixture
    def workers_ai_service(self):
        """Create WorkersAIService instance."""
        return WorkersAIService()

    @pytest.fixture
    def sample_embedding(self):
        """Sample embedding response."""
        return [0.1] * settings.workers_ai_embedding_dimensions

    def test_init(self, workers_ai_service):
        """Test WorkersAIService initialization."""
        assert workers_ai_service.account_id is not None
        assert workers_ai_service.api_token is not None
        assert workers_ai_service.embedding_model is not None

    @pytest.mark.asyncio
    async def test_generate_embedding(
        self, workers_ai_service, sample_embedding, httpx_mock: HTTPXMock
    ):
        """Test generating embedding for text."""
        httpx_mock.add_response(
            json={"success": True, "result": {"data": [sample_embedding]}}
        )

        embedding = await workers_ai_service.generate_embedding("Test text")

        assert len(embedding) == settings.workers_ai_embedding_dimensions
        assert isinstance(embedding, list)
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.asyncio
    async def test_generate_embedding_with_custom_model(
        self, workers_ai_service, sample_embedding, httpx_mock: HTTPXMock
    ):
        """Test generating embedding with custom model."""
        httpx_mock.add_response(
            json={"success": True, "result": {"data": [sample_embedding]}}
        )

        embedding = await workers_ai_service.generate_embedding(
            "Test text", model="@cf/baai/bge-large-en-v1.5"
        )

        assert len(embedding) == settings.workers_ai_embedding_dimensions

        # Verify correct model was used
        request = httpx_mock.get_requests()[0]
        assert "@cf/baai/bge-large-en-v1.5" in str(request.url)

    @pytest.mark.asyncio
    async def test_generate_embedding_failure(
        self, workers_ai_service, httpx_mock: HTTPXMock
    ):
        """Test embedding generation failure."""
        httpx_mock.add_response(
            json={"success": False, "errors": [{"message": "Model error"}]}
        )

        with pytest.raises(RuntimeError, match="Workers AI embedding failed"):
            await workers_ai_service.generate_embedding("Test text")

    @pytest.mark.asyncio
    async def test_generate_embedding_no_data(
        self, workers_ai_service, httpx_mock: HTTPXMock
    ):
        """Test handling when no embedding data returned."""
        httpx_mock.add_response(json={"success": True, "result": {"data": None}})

        with pytest.raises(RuntimeError, match="No embedding data"):
            await workers_ai_service.generate_embedding("Test text")

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(
        self, workers_ai_service, sample_embedding, httpx_mock: HTTPXMock
    ):
        """Test generating embeddings for multiple texts."""
        # Mock 3 embedding requests
        for _ in range(3):
            httpx_mock.add_response(
                json={"success": True, "result": {"data": [sample_embedding]}}
            )

        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = await workers_ai_service.generate_embeddings_batch(texts)

        assert len(embeddings) == 3
        assert all(
            len(emb) == settings.workers_ai_embedding_dimensions for emb in embeddings
        )

    @pytest.mark.asyncio
    async def test_run_model(self, workers_ai_service, httpx_mock: HTTPXMock):
        """Test running arbitrary Workers AI model."""
        httpx_mock.add_response(
            json={
                "success": True,
                "result": {"response": "Generated text response"},
            }
        )

        result = await workers_ai_service.run_model(
            "@cf/meta/llama-3.1-8b-instruct",
            {"prompt": "Test prompt", "max_tokens": 100},
        )

        assert result["response"] == "Generated text response"

    @pytest.mark.asyncio
    async def test_run_model_failure(self, workers_ai_service, httpx_mock: HTTPXMock):
        """Test model run failure."""
        httpx_mock.add_response(
            json={"success": False, "errors": [{"message": "Model not found"}]}
        )

        with pytest.raises(RuntimeError, match="Workers AI model run failed"):
            await workers_ai_service.run_model("invalid-model", {})
