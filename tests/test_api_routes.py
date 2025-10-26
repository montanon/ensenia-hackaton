"""Unit tests for API routes."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.ensenia.main import app


@pytest.fixture
async def client(db_session):  # noqa: ARG001
    """Create async test client with database dependency."""
    # The db_session fixture ensures database is initialized
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestChatRoutes:
    """Test suite for chat API routes."""

    async def test_create_session(self, client):
        """Test creating a new chat session."""
        response = await client.post(
            "/chat/sessions",
            json={"grade": 5, "subject": "Mathematics", "mode": "learn"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["grade"] == 5
        assert data["subject"] == "Mathematics"
        assert data["mode"] == "learn"

    async def test_create_session_with_research(self, client):
        """Test creating session with initial research topic.

        Note: Research context is loaded asynchronously by the Worker AI in background.
        The session creation endpoint returns immediately with context_loaded=False.
        Use the GET /sessions/{id}/status endpoint to poll for initialization completion.
        """
        response = await client.post(
            "/chat/sessions",
            json={
                "grade": 8,
                "subject": "Science",
                "mode": "learn",
                "topic": "photosynthesis",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Context is loaded asynchronously by Worker AI, so initially False
        assert data["context_loaded"] is False
        # Verify session was created with correct params
        assert data["grade"] == 8
        assert data["subject"] == "Science"
        assert data["mode"] == "learn"

    async def test_create_session_invalid_grade(self, client):
        """Test creating session with invalid grade."""
        response = await client.post(
            "/chat/sessions",
            json={"grade": 99, "subject": "Mathematics", "mode": "learn"},
        )

        assert response.status_code == 422  # Validation error

    async def test_send_message(self, client):
        """Test sending a message to a session."""
        # First create a session
        create_response = await client.post(
            "/chat/sessions",
            json={"grade": 5, "subject": "Mathematics", "mode": "learn"},
        )
        session_id = create_response.json()["session_id"]

        # Mock OpenAI response
        mock_choice = MagicMock()
        mock_choice.message.content = "Test response"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage.total_tokens = 100

        with patch(
            "app.ensenia.services.chat_service.AsyncOpenAI"
        ) as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_class.return_value = mock_client

            # Send message
            response = await client.post(
                f"/chat/sessions/{session_id}/messages",
                json={"message": "What is a fraction?"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert data["response"] == "Test response"

    async def test_send_message_invalid_session(self, client):
        """Test sending message to non-existent session."""
        response = await client.post(
            "/chat/sessions/99999/messages", json={"message": "Test"}
        )

        assert response.status_code == 404

    async def test_get_session(self, client):
        """Test retrieving session details."""
        # Create session
        create_response = await client.post(
            "/chat/sessions",
            json={"grade": 6, "subject": "History", "mode": "study"},
        )
        session_id = create_response.json()["session_id"]

        # Get session
        response = await client.get(f"/chat/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["grade"] == 6
        assert data["subject"] == "History"
        assert data["mode"] == "study"
        assert "messages" in data
        assert isinstance(data["messages"], list)

    async def test_get_session_not_found(self, client):
        """Test getting non-existent session."""
        response = await client.get("/chat/sessions/99999")

        assert response.status_code == 404

    async def test_trigger_research(self, client):
        """Test triggering research for a session."""
        # Create session
        create_response = await client.post(
            "/chat/sessions",
            json={"grade": 10, "subject": "Biology", "mode": "learn"},
        )
        session_id = create_response.json()["session_id"]

        # Mock research service
        with patch(
            "app.ensenia.services.research_service._get_http_client"
        ) as mock_client_fn:
            mock_http = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"results": []}
            mock_http.post.return_value = mock_response
            mock_client_fn.return_value = mock_http

            # Trigger research
            response = await client.post(
                f"/chat/sessions/{session_id}/research", json={"topic": "cells"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "context" in data

    async def test_health_check(self, client):
        """Test chat health endpoint."""
        response = await client.get("/chat/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "chat"


class TestMainRoutes:
    """Test suite for main application routes."""

    async def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data

    async def test_health_endpoint(self, client):
        """Test application health check."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
