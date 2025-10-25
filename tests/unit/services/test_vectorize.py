"""Unit tests for VectorizeService."""

import pytest
from pytest_httpx import HTTPXMock

from app.ensenia.core.config import settings
from app.ensenia.services.cloudflare.vectorize import VectorizeService


class TestVectorizeService:
    """Unit tests for VectorizeService."""

    @pytest.fixture
    def vectorize_service(self):
        """Create VectorizeService instance."""
        return VectorizeService()

    @pytest.fixture
    def sample_vector(self):
        """Sample 768-dim vector."""
        return [0.1] * settings.workers_ai_embedding_dimensions

    def test_init(self, vectorize_service):
        """Test VectorizeService initialization."""
        assert vectorize_service.account_id is not None
        assert vectorize_service.index_name is not None
        assert vectorize_service.api_token is not None

    @pytest.mark.asyncio
    async def test_insert_vectors(
        self, vectorize_service, sample_vector, httpx_mock: HTTPXMock
    ):
        """Test inserting vectors."""
        httpx_mock.add_response(
            json={"success": True, "result": {"ids": ["vec-1"], "count": 1}}
        )

        vectors = [
            {"id": "vec-1", "values": sample_vector, "metadata": {"test": "true"}}
        ]

        result = await vectorize_service.insert_vectors(vectors)

        assert result["count"] == 1
        assert "vec-1" in result["ids"]

    @pytest.mark.asyncio
    async def test_upsert_vectors(
        self, vectorize_service, sample_vector, httpx_mock: HTTPXMock
    ):
        """Test upserting vectors."""
        httpx_mock.add_response(
            json={"success": True, "result": {"ids": ["vec-1"], "count": 1}}
        )

        vectors = [{"id": "vec-1", "values": sample_vector}]

        result = await vectorize_service.upsert_vectors(vectors)

        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_query(self, vectorize_service, sample_vector, httpx_mock: HTTPXMock):
        """Test querying similar vectors."""
        httpx_mock.add_response(
            json={
                "success": True,
                "result": {
                    "matches": [
                        {
                            "id": "vec-1",
                            "score": 0.95,
                            "metadata": {"grade": 5, "subject": "math"},
                        },
                        {"id": "vec-2", "score": 0.87, "metadata": {"grade": 5}},
                    ]
                },
            }
        )

        matches = await vectorize_service.query(sample_vector, top_k=2)

        assert len(matches) == 2
        assert matches[0]["score"] > matches[1]["score"]
        assert matches[0]["id"] == "vec-1"

    @pytest.mark.asyncio
    async def test_query_with_filter(
        self, vectorize_service, sample_vector, httpx_mock: HTTPXMock
    ):
        """Test querying with metadata filter."""
        httpx_mock.add_response(
            json={
                "success": True,
                "result": {
                    "matches": [
                        {"id": "vec-1", "score": 0.95, "metadata": {"grade": 5}}
                    ]
                },
            }
        )

        matches = await vectorize_service.query(
            sample_vector, top_k=10, filter_metadata={"grade": 5}
        )

        assert len(matches) == 1
        assert matches[0]["metadata"]["grade"] == 5

    @pytest.mark.asyncio
    async def test_delete_by_ids(self, vectorize_service, httpx_mock: HTTPXMock):
        """Test deleting vectors by IDs."""
        httpx_mock.add_response(
            json={"success": True, "result": {"deleted": 2, "ids": ["vec-1", "vec-2"]}}
        )

        result = await vectorize_service.delete_by_ids(["vec-1", "vec-2"])

        assert result["deleted"] == 2

    @pytest.mark.asyncio
    async def test_get_index_info(self, vectorize_service, httpx_mock: HTTPXMock):
        """Test getting index information."""
        httpx_mock.add_response(
            json={
                "success": True,
                "result": {
                    "name": "ensenia-curriculum-embeddings",
                    "config": {"dimensions": 768, "metric": "cosine"},
                },
            }
        )

        info = await vectorize_service.get_index_info()

        assert info["name"] == "ensenia-curriculum-embeddings"
        assert info["config"]["dimensions"] == 768
        assert info["config"]["metric"] == "cosine"

    @pytest.mark.asyncio
    async def test_insert_failure(
        self, vectorize_service, sample_vector, httpx_mock: HTTPXMock
    ):
        """Test insert failure handling."""
        httpx_mock.add_response(
            json={"success": False, "errors": [{"message": "Invalid vector"}]}
        )

        vectors = [{"id": "vec-1", "values": sample_vector}]

        with pytest.raises(RuntimeError, match="Vectorize insert failed"):
            await vectorize_service.insert_vectors(vectors)
