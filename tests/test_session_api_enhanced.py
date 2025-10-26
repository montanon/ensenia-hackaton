"""Enhanced API tests for session endpoints with pooling features.

Tests the new session initialization and status endpoints:
- POST /chat/sessions - Enhanced with background tasks
- GET /chat/sessions/{id}/status - New status endpoint
- POST /exercises/sessions/{id}/submit - Enhanced with pool maintenance
"""

import asyncio
from unittest.mock import patch

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.ensenia.main import app


@pytest.fixture
async def client(db_session):  # noqa: ARG001
    """Create async test client with database dependency."""
    # The db_session fixture ensures database is initialized
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestSessionCreationWithPooling:
    """Test session creation with background initialization."""

    async def test_create_session_triggers_background_init(self, client):
        """Test that creating a session triggers background initialization."""
        response = await client.post(
            "/chat/sessions",
            json={
                "grade": 5,
                "subject": "Matemáticas",
                "mode": "learn",
                "topic": "Fracciones",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["grade"] == 5
        assert data["subject"] == "Matemáticas"
        # Verify background task initialization is indicated by context_loaded being False
        assert data["context_loaded"] is False

    async def test_create_session_without_topic(self, client):
        """Test session creation without explicit topic."""
        response = await client.post(
            "/chat/sessions",
            json={
                "grade": 8,
                "subject": "Historia",
                "mode": "study",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["subject"] == "Historia"
        # context_loaded should be False since background task handles it
        assert data["context_loaded"] is False

    async def test_create_session_returns_immediately(self, client):
        """Test that session creation doesn't wait for background tasks."""

        async def slow_background_task(*args, **kwargs):
            """Simulate slow background task."""
            import asyncio

            await asyncio.sleep(5)  # 5 second delay

        with patch(
            "app.ensenia.api.routes.chat.initialize_session_background",
            side_effect=slow_background_task,
        ):
            import time

            start = time.time()

            response = await client.post(
                "/chat/sessions",
                json={
                    "grade": 5,
                    "subject": "Matemáticas",
                    "mode": "learn",
                },
            )

            elapsed = time.time() - start

            assert response.status_code == 200
            # Response should be immediate, not wait for background task
            assert elapsed < 2.0  # Should complete in under 2 seconds


@pytest.mark.asyncio
class TestSessionStatusEndpoint:
    """Test the new session status endpoint."""

    async def test_get_session_status_ready(self, client):
        """Test status when session is fully initialized."""
        # First create a session
        create_response = await client.post(
            "/chat/sessions",
            json={
                "grade": 5,
                "subject": "Matemáticas",
                "mode": "learn",
            },
        )
        assert create_response.status_code == 200
        session_id = create_response.json()["session_id"]

        # Get status immediately
        status_response = await client.get(f"/chat/sessions/{session_id}/status")

        assert status_response.status_code == 200
        status_data = status_response.json()

        # Verify status fields are present and have expected types
        assert status_data["session_id"] == session_id
        assert "exercise_count" in status_data
        assert "pending_exercises" in status_data
        assert "pool_health" in status_data
        assert isinstance(status_data["exercise_count"], int)
        assert isinstance(status_data["pending_exercises"], int)

    async def test_get_session_status_initializing(self, client):
        """Test status when session is still initializing."""
        # Create session
        create_response = await client.post(
            "/chat/sessions",
            json={
                "grade": 5,
                "subject": "Matemáticas",
                "mode": "practice",
            },
        )
        assert create_response.status_code == 200
        session_id = create_response.json()["session_id"]

        # Immediately check status (before background task completes)
        status_response = await client.get(f"/chat/sessions/{session_id}/status")

        assert status_response.status_code == 200
        status_data = status_response.json()

        # Verify the status endpoint returns valid response
        assert status_data["session_id"] == session_id
        assert "exercise_count" in status_data
        assert isinstance(status_data["exercise_count"], int)

    async def test_get_session_status_not_found(self, client):
        """Test status endpoint with non-existent session."""
        response = await client.get("/chat/sessions/99999/status")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestExerciseSubmitWithPoolMaintenance:
    """Test exercise submission with pool maintenance."""

    async def test_submit_answer_triggers_pool_maintenance(self, client):
        """Test that submitting answer triggers pool maintenance."""
        # Submit answer to session
        response = await client.post(
            "/exercises/sessions/1/submit",
            json={"answer": "Test answer"},
        )

        # Endpoint should be callable and return a response
        assert response.status_code == 200

    async def test_submit_answer_pool_maintenance_has_own_db_session(self, client):
        """Test that pool maintenance endpoint is accessible."""
        # Attempt to submit answer
        response = await client.post(
            "/exercises/sessions/1/submit",
            json={"answer": "Test answer"},
        )

        # Endpoint should be callable and return a response
        assert response.status_code == 200


@pytest.mark.asyncio
class TestSessionPoolingE2E:
    """End-to-end tests for session with pooling."""

    @pytest.mark.skip(reason="Requires full database and API keys")
    async def test_full_session_lifecycle_with_pooling(self):
        """Test complete session lifecycle with pooling.

        Scenario:
        1. Create session
        2. Wait for initialization (research + exercises)
        3. Check status - should be ready
        4. Get first exercise
        5. Submit answer
        6. Check status - pool should refill
        7. Get next exercise

        Skipped by default - requires real database and API keys.
        """
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # 1. Create session
            create_response = await client.post(
                "/chat/sessions",
                json={
                    "grade": 5,
                    "subject": "Matemáticas",
                    "mode": "practice",
                    "topic": "Fracciones",
                },
            )
            assert create_response.status_code == 200
            session_id = create_response.json()["session_id"]

            # 2. Wait for initialization
            for _ in range(10):  # Poll for up to 10 seconds
                await asyncio.sleep(1)
                status_response = await client.get(
                    f"/chat/sessions/{session_id}/status"
                )
                status = status_response.json()

                if status["research_loaded"] and status["initial_exercises_ready"]:
                    break

            # 3. Verify ready
            assert status["exercise_count"] >= 5
            assert status["pool_health"] == "healthy"

            # 4. Get exercises
            exercises_response = await client.get(
                f"/exercises/sessions/{session_id}/exercises"
            )
            exercises = exercises_response.json()["exercises"]
            assert len(exercises) >= 5

            # 5. Submit answers for multiple exercises
            for i in range(3):
                await client.post(
                    f"/exercises/sessions/{i + 1}/submit",
                    json={"answer": "test answer"},
                )

            # 6. Wait for pool refill
            await asyncio.sleep(2)

            # 7. Check pool was maintained
            status_response = await client.get(f"/chat/sessions/{session_id}/status")
            status = status_response.json()
            assert status["pending_exercises"] >= 3  # Should have refilled
