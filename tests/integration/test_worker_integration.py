"""Integration tests for ResearchService <-> Cloudflare Worker communication.

Tests the new Worker integration methods with proper Pydantic model validation.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.ensenia.models.curriculum import (
    FetchResponse,
    GenerateResponse,
    SearchResponse,
    ValidateResponse,
)
from app.ensenia.services.research_service import get_research_service


@pytest.mark.asyncio
class TestWorkerIntegration:
    """Test suite for Worker API integration."""

    async def test_search_curriculum_success(self):
        """Test successful curriculum search with valid response."""
        # Mock Worker response matching actual schema
        mock_response_data = {
            "query": "fracciones",
            "grade": 5,
            "subject": "matemáticas",
            "total_found": 3,
            "content_ids": ["id1", "id2", "id3"],
            "metadata": [
                {
                    "id": "id1",
                    "score": 0.95,
                    "title": "Suma de Fracciones",
                    "oa": "MAT.5.OA.1",
                },
                {
                    "id": "id2",
                    "score": 0.88,
                    "title": "Resta de Fracciones",
                    "oa": "MAT.5.OA.2",
                },
                {
                    "id": "id3",
                    "score": 0.75,
                    "title": "Fracciones Equivalentes",
                    "oa": "MAT.5.OA.3",
                },
            ],
            "cached": False,
            "search_time_ms": 45.2,
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = MagicMock()

        with patch(
            "app.ensenia.services.research_service._get_http_client"
        ) as mock_client_fn:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_client_fn.return_value = mock_http

            service = get_research_service()
            result = await service.search_curriculum(
                query="fracciones", grade=5, subject="matemáticas", limit=10
            )

            # Verify result is proper Pydantic model
            assert isinstance(result, SearchResponse)
            assert result.query == "fracciones"
            assert result.grade == 5
            assert result.total_found == 3
            assert len(result.content_ids) == 3
            assert len(result.metadata) == 3
            assert result.metadata[0].score == 0.95

            # Verify HTTP call
            mock_http.post.assert_called_once()
            call_args = mock_http.post.call_args
            # Should call the /search endpoint (URL comes from config)
            assert "/search" in str(call_args)

    async def test_search_curriculum_validation_error(self):
        """Test search with invalid response schema raises error."""
        # Invalid response - missing required fields
        invalid_response_data = {
            "query": "test",
            # Missing grade, subject, total_found, etc.
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = invalid_response_data
        mock_response.raise_for_status = MagicMock()

        with patch(
            "app.ensenia.services.research_service._get_http_client"
        ) as mock_client_fn:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_client_fn.return_value = mock_http

            service = get_research_service()

            # Should raise validation error
            with pytest.raises(Exception, match=r".*"):
                await service.search_curriculum(
                    query="test", grade=5, subject="matemáticas"
                )

    async def test_fetch_content_success(self):
        """Test successful content fetching with valid response."""
        mock_response_data = {
            "contents": [
                {
                    "id": "id1",
                    "title": "Suma de Fracciones",
                    "grade": 5,
                    "subject": "matemáticas",
                    "content_text": "Las fracciones son...",
                    "learning_objectives": [
                        "Comprender fracciones",
                        "Sumar fracciones",
                    ],
                    "ministry_standard_ref": "MAT.5.OA.1",
                    "ministry_approved": True,
                    "keywords": "fracciones,suma,matemáticas",
                    "difficulty_level": "medium",
                }
            ],
            "fetch_time_ms": 12.5,
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = MagicMock()

        with patch(
            "app.ensenia.services.research_service._get_http_client"
        ) as mock_client_fn:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_client_fn.return_value = mock_http

            service = get_research_service()
            result = await service.fetch_content(["id1"])

            # Verify Pydantic model
            assert isinstance(result, FetchResponse)
            assert len(result.contents) == 1
            assert result.contents[0].id == "id1"
            assert result.contents[0].ministry_approved is True
            assert result.fetch_time_ms == 12.5

    async def test_generate_explanation_success(self):
        """Test successful content generation with valid response."""
        mock_response_data = {
            "generated_text": "Para sumar fracciones con igual denominador...",
            "oa_codes": ["MAT.5.OA.1"],
            "model_used": "@cf/meta/llama-3.1-8b-instruct",
            "generation_time_ms": 234.5,
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = MagicMock()

        with patch(
            "app.ensenia.services.research_service._get_http_client"
        ) as mock_client_fn:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_client_fn.return_value = mock_http

            service = get_research_service()
            result = await service.generate_explanation(
                context="Matemáticas 5to básico",
                query="¿Cómo sumar fracciones?",
                grade=5,
                subject="matemáticas",
                oa_codes=["MAT.5.OA.1"],
                style="explanation",
            )

            # Verify Pydantic model
            assert isinstance(result, GenerateResponse)
            assert "fracciones" in result.generated_text.lower()
            assert result.oa_codes == ["MAT.5.OA.1"]
            assert result.generation_time_ms > 0

    async def test_validate_content_success(self):
        """Test successful content validation with valid response."""
        mock_response_data = {
            "is_valid": True,
            "score": 87,
            "validation_details": {
                "oa_alignment_score": 90,
                "grade_appropriate_score": 85,
                "chilean_terminology_score": 92,
                "learning_coverage_score": 83,
                "issues": [],
                "recommendations": ["Agregar más ejemplos"],
            },
            "validation_time_ms": 156.3,
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = MagicMock()

        with patch(
            "app.ensenia.services.research_service._get_http_client"
        ) as mock_client_fn:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_client_fn.return_value = mock_http

            service = get_research_service()
            result = await service.validate_content(
                content="Una fracción representa...",
                grade=5,
                subject="matemáticas",
                expected_oa=["MAT.5.OA.1"],
            )

            # Verify Pydantic model
            assert isinstance(result, ValidateResponse)
            assert result.is_valid is True
            assert result.score == 87
            assert result.validation_details.oa_alignment_score == 90
            assert len(result.validation_details.recommendations) > 0

    async def test_worker_timeout_error(self):
        """Test handling of Worker timeout."""
        with patch(
            "app.ensenia.services.research_service._get_http_client"
        ) as mock_client_fn:
            mock_http = AsyncMock()
            mock_http.post.side_effect = httpx.TimeoutException("Request timeout")
            mock_client_fn.return_value = mock_http

            service = get_research_service()

            with pytest.raises(httpx.TimeoutException):
                await service.search_curriculum(
                    query="test", grade=5, subject="matemáticas"
                )

    async def test_worker_500_error(self):
        """Test handling of Worker 500 error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 error", request=MagicMock(), response=mock_response
        )

        with patch(
            "app.ensenia.services.research_service._get_http_client"
        ) as mock_client_fn:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_client_fn.return_value = mock_http

            service = get_research_service()

            with pytest.raises(httpx.HTTPStatusError):
                await service.search_curriculum(
                    query="test", grade=5, subject="matemáticas"
                )

    async def test_worker_network_error(self):
        """Test handling of network connection error."""
        with patch(
            "app.ensenia.services.research_service._get_http_client"
        ) as mock_client_fn:
            mock_http = AsyncMock()
            mock_http.post.side_effect = httpx.ConnectError("Connection refused")
            mock_client_fn.return_value = mock_http

            service = get_research_service()

            with pytest.raises(httpx.ConnectError):
                await service.search_curriculum(
                    query="test", grade=5, subject="matemáticas"
                )

    async def test_get_context_integration(self):
        """Test get_context method using new typed methods."""
        # Mock search response
        search_response_data = {
            "query": "fracciones",
            "grade": 5,
            "subject": "matemáticas",
            "total_found": 2,
            "content_ids": ["id1", "id2"],
            "metadata": [
                {"id": "id1", "score": 0.95, "title": "Suma", "oa": "MAT.5.OA.1"},
                {"id": "id2", "score": 0.88, "title": "Resta", "oa": "MAT.5.OA.2"},
            ],
            "cached": False,
            "search_time_ms": 45.2,
        }

        # Mock fetch response
        fetch_response_data = {
            "contents": [
                {
                    "id": "id1",
                    "title": "Suma de Fracciones",
                    "grade": 5,
                    "subject": "matemáticas",
                    "content_text": "Para sumar fracciones...",
                    "learning_objectives": ["Sumar fracciones"],
                    "ministry_standard_ref": "MAT.5.OA.1",
                    "ministry_approved": True,
                    "keywords": "fracciones,suma",
                    "difficulty_level": "medium",
                }
            ],
            "fetch_time_ms": 12.5,
        }

        mock_search_response = MagicMock()
        mock_search_response.status_code = 200
        mock_search_response.json.return_value = search_response_data
        mock_search_response.raise_for_status = MagicMock()

        mock_fetch_response = MagicMock()
        mock_fetch_response.status_code = 200
        mock_fetch_response.json.return_value = fetch_response_data
        mock_fetch_response.raise_for_status = MagicMock()

        with patch(
            "app.ensenia.services.research_service._get_http_client"
        ) as mock_client_fn:
            mock_http = AsyncMock()
            # Return different responses for search and fetch
            mock_http.post.side_effect = [mock_search_response, mock_fetch_response]
            mock_client_fn.return_value = mock_http

            service = get_research_service()
            context = await service.get_context(
                topic="fracciones", grade=5, subject="matemáticas"
            )

            # Verify context string contains expected information
            assert isinstance(context, str)
            assert "fracciones" in context.lower()
            assert "5" in context or "grade" in context.lower()
            assert len(context) > 0

            # Verify both endpoints were called
            assert mock_http.post.call_count == 2
