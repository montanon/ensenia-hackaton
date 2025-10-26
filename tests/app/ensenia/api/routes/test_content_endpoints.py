"""Integration tests for content generation endpoints."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.ensenia.database.models import Session
from app.ensenia.main import app


@pytest.fixture
def client():
    """Create sync test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def sample_session_with_content(db_session):
    """Create a session with content already generated."""
    learning_content = {
        "title": "Test Learning",
        "overview": "Test overview",
        "learning_objectives": ["Objective 1"],
        "sections": [
            {
                "title": "Section 1",
                "content": "Content",
                "key_points": ["Point 1"],
                "examples": [{"description": "Example", "explanation": "Explanation"}],
            }
        ],
        "vocabulary": [{"term": "Term", "definition": "Definition"}],
        "summary": "Summary",
    }

    study_guide = {
        "title": "Test Guide",
        "subject": "Matemáticas",
        "grade": 8,
        "key_concepts": [
            {
                "concept": "Concept",
                "explanation": "Explanation",
                "importance": "Important",
            }
        ],
        "summary_sections": [
            {"title": "Summary", "summary": "Text", "remember": ["Remember"]}
        ],
        "common_mistakes": [
            {"mistake": "Mistake", "correction": "Correction", "explanation": "Why"}
        ],
        "practice_tips": ["Tip 1"],
        "review_questions": ["Question 1"],
    }

    session = Session(
        grade=8,
        subject="Matemáticas",
        mode="learn",
        research_context="Test context",
        learning_content=learning_content,
        study_guide=study_guide,
    )

    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest.fixture
async def sample_session_without_content(db_session):
    """Create a session without content."""
    session = Session(
        grade=8,
        subject="Matemáticas",
        mode="learn",
        research_context="Test context",
        learning_content=None,
        study_guide=None,
    )

    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


class TestGetLearningContent:
    """Tests for GET /sessions/{session_id}/learning-content endpoint."""

    @pytest.mark.asyncio
    async def test_get_learning_content_success(
        self, async_client, sample_session_with_content
    ):
        """Test successful retrieval of learning content."""
        response = await async_client.get(
            f"/chat/sessions/{sample_session_with_content.id}/learning-content"
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "content" in data
        assert data["content"]["title"] == "Test Learning"
        assert len(data["content"]["sections"]) == 1

    @pytest.mark.asyncio
    async def test_get_learning_content_not_ready(
        self, async_client, sample_session_without_content
    ):
        """Test getting content when not yet generated (returns 202)."""
        response = await async_client.get(
            f"/chat/sessions/{sample_session_without_content.id}/learning-content"
        )

        assert response.status_code == 202
        # Check for error message in custom error format
        response_data = response.json()
        assert "error" in response_data
        assert "not yet generated" in response_data["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_get_learning_content_session_not_found(self, async_client):
        """Test getting content for non-existent session."""
        response = await async_client.get("/chat/sessions/99999/learning-content")

        assert response.status_code == 404
        # Check for error message in custom error format
        response_data = response.json()
        assert "error" in response_data
        assert "not found" in response_data["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_get_learning_content_structure(
        self, async_client, sample_session_with_content
    ):
        """Test that returned learning content has correct structure."""
        response = await async_client.get(
            f"/chat/sessions/{sample_session_with_content.id}/learning-content"
        )

        assert response.status_code == 200
        content = response.json()["content"]

        # Verify structure
        assert isinstance(content["title"], str)
        assert isinstance(content["overview"], str)
        assert isinstance(content["learning_objectives"], list)
        assert isinstance(content["sections"], list)
        assert isinstance(content["vocabulary"], list)
        assert isinstance(content["summary"], str)


class TestGetStudyGuide:
    """Tests for GET /sessions/{session_id}/study-guide endpoint."""

    @pytest.mark.asyncio
    async def test_get_study_guide_success(
        self, async_client, sample_session_with_content
    ):
        """Test successful retrieval of study guide."""
        response = await async_client.get(
            f"/chat/sessions/{sample_session_with_content.id}/study-guide"
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "guide" in data
        assert data["guide"]["title"] == "Test Guide"
        assert data["guide"]["subject"] == "Matemáticas"

    @pytest.mark.asyncio
    async def test_get_study_guide_not_ready(
        self, async_client, sample_session_without_content
    ):
        """Test getting guide when not yet generated (returns 202)."""
        response = await async_client.get(
            f"/chat/sessions/{sample_session_without_content.id}/study-guide"
        )

        assert response.status_code == 202
        # Check for error message in custom error format
        response_data = response.json()
        assert "error" in response_data
        assert "not yet generated" in response_data["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_get_study_guide_session_not_found(self, async_client):
        """Test getting guide for non-existent session."""
        response = await async_client.get("/chat/sessions/99999/study-guide")

        assert response.status_code == 404
        # Check for error message in custom error format
        response_data = response.json()
        assert "error" in response_data
        assert "not found" in response_data["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_get_study_guide_structure(
        self, async_client, sample_session_with_content
    ):
        """Test that returned study guide has correct structure."""
        response = await async_client.get(
            f"/chat/sessions/{sample_session_with_content.id}/study-guide"
        )

        assert response.status_code == 200
        guide = response.json()["guide"]

        # Verify structure
        assert isinstance(guide["title"], str)
        assert isinstance(guide["subject"], str)
        assert isinstance(guide["grade"], int)
        assert isinstance(guide["key_concepts"], list)
        assert isinstance(guide["summary_sections"], list)
        assert isinstance(guide["common_mistakes"], list)
        assert isinstance(guide["practice_tips"], list)
        assert isinstance(guide["review_questions"], list)


class TestSessionStatusWithContent:
    """Tests for updated session status endpoint with content fields."""

    @pytest.mark.asyncio
    async def test_status_includes_content_ready_flags(
        self, async_client, sample_session_with_content
    ):
        """Test that status endpoint returns content readiness flags."""
        response = await async_client.get(
            f"/chat/sessions/{sample_session_with_content.id}/status"
        )

        assert response.status_code == 200
        data = response.json()
        assert "learning_content_ready" in data
        assert "study_guide_ready" in data
        assert data["learning_content_ready"] is True
        assert data["study_guide_ready"] is True

    @pytest.mark.asyncio
    async def test_status_content_not_ready(
        self, async_client, sample_session_without_content
    ):
        """Test that status shows content as not ready."""
        response = await async_client.get(
            f"/chat/sessions/{sample_session_without_content.id}/status"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["learning_content_ready"] is False
        assert data["study_guide_ready"] is False
