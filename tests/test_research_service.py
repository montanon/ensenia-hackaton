"""Unit tests for ResearchService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ensenia.database.models import Session
from app.ensenia.services.research_service import get_research_service


@pytest.mark.asyncio
class TestResearchService:
    """Test suite for ResearchService."""

    async def test_search_curriculum_success(self):
        """Test successful curriculum search."""
        # Updated to match new Worker API schema
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": "test topic",
            "grade": 5,
            "subject": "Mathematics",
            "total_found": 1,
            "content_ids": ["test-id-1"],
            "metadata": [
                {
                    "id": "test-id-1",
                    "score": 0.95,
                    "title": "Test Content",
                    "oa": "TEST.5.OA.1",
                }
            ],
            "cached": False,
            "search_time_ms": 10.0,
        }
        mock_response.raise_for_status = MagicMock()

        with patch(
            "app.ensenia.services.research_service._get_http_client"
        ) as mock_client_fn:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_client_fn.return_value = mock_http

            research_service = get_research_service()
            results = await research_service.search_curriculum(
                query="test topic", grade=5, subject="Mathematics"
            )

            # Now returns SearchResponse Pydantic model
            from app.ensenia.models.curriculum import SearchResponse

            assert isinstance(results, SearchResponse)
            assert results.query == "test topic"
            assert results.total_found == 1
            mock_http.post.assert_called_once()

    async def test_update_session_context(self, db_session: AsyncSession):
        """Test updating session with research context."""
        # Create test session
        session = Session(
            grade=8, subject="Science", mode="learn", research_context=None
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        # Mock search response (new schema)
        mock_search_response = MagicMock()
        mock_search_response.status_code = 200
        mock_search_response.json.return_value = {
            "query": "photosynthesis",
            "grade": 8,
            "subject": "Science",
            "total_found": 2,
            "content_ids": ["photo-1", "photo-2"],
            "metadata": [
                {
                    "id": "photo-1",
                    "score": 0.95,
                    "title": "Photosynthesis",
                    "oa": "SCI.8.OA.1",
                },
                {
                    "id": "photo-2",
                    "score": 0.88,
                    "title": "Light Energy",
                    "oa": "SCI.8.OA.2",
                },
            ],
            "cached": False,
            "search_time_ms": 15.0,
        }
        mock_search_response.raise_for_status = MagicMock()

        # Mock fetch response (new schema)
        mock_fetch_response = MagicMock()
        mock_fetch_response.status_code = 200
        mock_fetch_response.json.return_value = {
            "contents": [
                {
                    "id": "photo-1",
                    "title": "Photosynthesis",
                    "grade": 8,
                    "subject": "Science",
                    "content_text": "Process by which plants convert light to energy",
                    "learning_objectives": ["Understand photosynthesis"],
                    "ministry_standard_ref": "SCI.8.OA.1",
                    "ministry_approved": True,
                    "keywords": "photosynthesis,plants,energy",
                    "difficulty_level": "medium",
                }
            ],
            "fetch_time_ms": 8.0,
        }
        mock_fetch_response.raise_for_status = MagicMock()

        with patch(
            "app.ensenia.services.research_service._get_http_client"
        ) as mock_client_fn:
            mock_http = AsyncMock()
            # Return search response first, then fetch response
            mock_http.post.side_effect = [mock_search_response, mock_fetch_response]
            mock_client_fn.return_value = mock_http

            research_service = get_research_service()
            context = await research_service.update_session_context(
                session.id, "photosynthesis", db_session
            )

            assert len(context) > 0
            assert "photosynthesis" in context.lower() or "topic" in context.lower()

            # Verify session was updated
            await db_session.refresh(session)
            assert session.research_context is not None

        # Cleanup
        await db_session.delete(session)
        await db_session.commit()

    async def test_update_session_context_invalid_session(
        self, db_session: AsyncSession
    ):
        """Test updating context for non-existent session raises error."""
        research_service = get_research_service()

        with pytest.raises(ValueError, match=r"Session .* not found"):
            await research_service.update_session_context(
                99999, "test topic", db_session
            )

    async def test_fetch_content_success(self):
        """Test successful content fetching."""
        # Updated to match new Worker API schema
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "contents": [
                {
                    "id": "content-1",
                    "title": "Test Content",
                    "grade": 5,
                    "subject": "Mathematics",
                    "content_text": "Test description content",
                    "learning_objectives": ["Learn concept"],
                    "ministry_standard_ref": "TEST.5.OA.1",
                    "ministry_approved": True,
                    "keywords": "test,content",
                    "difficulty_level": "medium",
                }
            ],
            "fetch_time_ms": 5.0,
        }
        mock_response.raise_for_status = MagicMock()

        with patch(
            "app.ensenia.services.research_service._get_http_client"
        ) as mock_client_fn:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_client_fn.return_value = mock_http

            research_service = get_research_service()
            result = await research_service.fetch_content(["content-1"])

            # Now returns FetchResponse Pydantic model
            from app.ensenia.models.curriculum import FetchResponse

            assert isinstance(result, FetchResponse)
            assert len(result.contents) == 1
            assert result.contents[0].id == "content-1"
            assert mock_http.post.call_count == 1
