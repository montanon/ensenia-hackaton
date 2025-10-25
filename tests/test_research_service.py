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
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "title": "Test Content",
                    "content": "Test description",
                    "url": "https://example.com",
                }
            ]
        }

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

            assert isinstance(results, dict)
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

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "title": "Photosynthesis",
                    "content": "Process by which plants convert light to energy",
                    "url": "https://example.com/photosynthesis",
                }
            ]
        }

        with patch(
            "app.ensenia.services.research_service._get_http_client"
        ) as mock_client_fn:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
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
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "contents": [
                {
                    "id": "content-1",
                    "title": "Test Content",
                    "description": "Test description",
                }
            ]
        }

        with patch(
            "app.ensenia.services.research_service._get_http_client"
        ) as mock_client_fn:
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_client_fn.return_value = mock_http

            research_service = get_research_service()
            result = await research_service.fetch_content(["content-1"])

            assert result == mock_response.json.return_value
            assert mock_http.post.call_count == 1
