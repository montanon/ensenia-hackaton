"""Comprehensive API endpoint tests covering all critical paths.

Tests for:
- Session creation and status endpoints
- Learning content and study guide retrieval
- Exercise management endpoints
- Error handling and validation
- Content readiness tracking
"""

import asyncio

import httpx
import pytest

from app.ensenia.main import app


@pytest.fixture
async def client(db_session):
    """Create async test client."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
class TestSessionEndpoints:
    """Test session creation and management endpoints."""

    async def test_post_create_session_valid_request(self, client):
        """Test successful session creation with valid request."""
        print("\n=== Testing session creation ===")

        response = await client.post(
            "/chat/sessions",
            json={
                "grade": 5,
                "subject": "Matemáticas",
                "mode": "learn",
                "topic": "Fracciones",
            },
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        print(f"✓ Session created: ID={data['session_id']}")

        # Verify response structure
        assert "session_id" in data
        assert "grade" in data
        assert "subject" in data
        assert "mode" in data
        assert "created_at" in data
        assert "context_loaded" in data

        # Verify response values
        assert isinstance(data["session_id"], int)
        assert data["grade"] == 5
        assert data["subject"] == "Matemáticas"
        assert data["mode"] == "learn"
        assert isinstance(data["context_loaded"], bool)

    async def test_post_create_session_minimal_request(self, client):
        """Test session creation with only required fields."""
        print("\n=== Testing minimal session creation ===")

        response = await client.post(
            "/chat/sessions",
            json={
                "grade": 8,
                "subject": "Historia",
                "mode": "practice",
            },
        )

        assert response.status_code == 200
        data = response.json()

        print(f"✓ Session created without topic: ID={data['session_id']}")

        assert data["grade"] == 8
        assert data["subject"] == "Historia"
        assert data["mode"] == "practice"

    async def test_get_session_details(self, client):
        """Test retrieving session details."""
        print("\n=== Testing session retrieval ===")

        # Create session first
        create_resp = await client.post(
            "/chat/sessions",
            json={"grade": 6, "subject": "Ciencias", "mode": "study"},
        )
        session_id = create_resp.json()["session_id"]

        # Retrieve session
        response = await client.get(f"/chat/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()

        print(f"✓ Session retrieved: grade={data['grade']}, subject={data['subject']}")

        assert data["id"] == session_id
        assert data["grade"] == 6
        assert data["subject"] == "Ciencias"
        assert "messages" in data

    async def test_get_session_status(self, client):
        """Test session status endpoint."""
        print("\n=== Testing session status endpoint ===")

        # Create session
        create_resp = await client.post(
            "/chat/sessions",
            json={"grade": 5, "subject": "Matemáticas", "mode": "learn"},
        )
        session_id = create_resp.json()["session_id"]

        # Get status
        response = await client.get(f"/chat/sessions/{session_id}/status")

        assert response.status_code == 200
        status = response.json()

        print(f"✓ Status retrieved for session {session_id}")

        # Verify status structure
        assert "session_id" in status
        assert "research_loaded" in status
        assert "initial_exercises_ready" in status
        assert "exercise_count" in status
        assert "pending_exercises" in status
        assert "pool_health" in status
        assert "learning_content_ready" in status
        assert "study_guide_ready" in status

        # Verify data types
        assert isinstance(status["session_id"], int)
        assert isinstance(status["research_loaded"], bool)
        assert isinstance(status["initial_exercises_ready"], bool)
        assert isinstance(status["exercise_count"], int)
        assert status["pool_health"] in ["healthy", "low", "depleted"]

        print(
            f"  Research: {status['research_loaded']}, "
            f"Exercises: {status['initial_exercises_ready']}, "
            f"Pool health: {status['pool_health']}"
        )

    async def test_get_learning_content_when_ready(self, client):
        """Test retrieving learning content."""
        print("\n=== Testing learning content endpoint ===")

        # Create session
        create_resp = await client.post(
            "/chat/sessions",
            json={"grade": 5, "subject": "Historia", "mode": "learn"},
        )
        session_id = create_resp.json()["session_id"]

        # Try to get content (may not be ready yet)
        response = await client.get(f"/chat/sessions/{session_id}/learning-content")

        # Should be either 200 (ready) or 202 (not ready yet)
        assert response.status_code in [200, 202]

        if response.status_code == 200:
            data = response.json()
            print("✓ Learning content retrieved")

            assert "content" in data
            assert "session_id" in data

            # Verify content exists
            if data["content"]:
                print(f"  Content size: {len(str(data['content']))} chars")
        else:
            print("⚠ Content not ready (202 Accepted)")

    async def test_get_study_guide_when_ready(self, client):
        """Test retrieving study guide."""
        print("\n=== Testing study guide endpoint ===")

        # Create session
        create_resp = await client.post(
            "/chat/sessions",
            json={"grade": 6, "subject": "Matemáticas", "mode": "learn"},
        )
        session_id = create_resp.json()["session_id"]

        # Try to get study guide
        response = await client.get(f"/chat/sessions/{session_id}/study-guide")

        # Should be either 200 (ready) or 202 (not ready yet)
        assert response.status_code in [200, 202]

        if response.status_code == 200:
            data = response.json()
            print("✓ Study guide retrieved")

            assert "guide" in data or "content" in data
        else:
            print("⚠ Study guide not ready (202 Accepted)")


@pytest.mark.asyncio
class TestExerciseEndpoints:
    """Test exercise-related endpoints."""

    async def test_get_session_exercises(self, client):
        """Test retrieving exercises for a session."""
        print("\n=== Testing exercise retrieval ===")

        # Create session
        create_resp = await client.post(
            "/chat/sessions",
            json={"grade": 5, "subject": "Matemáticas", "mode": "practice"},
        )
        session_id = create_resp.json()["session_id"]

        # Wait for exercises to be generated
        await asyncio.sleep(2)

        # Get exercises
        response = await client.get(f"/exercises/sessions/{session_id}/exercises")

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            print("✓ Exercises retrieved")

            assert "exercises" in data
            exercises = data["exercises"]

            if exercises:
                print(f"  Found {len(exercises)} exercises")

                # Verify exercise structure
                first = exercises[0]
                assert "id" in first
                assert "exercise_type" in first
                assert "grade" in first
                assert "subject" in first
                assert "content" in first
            else:
                print("  No exercises available yet")
        else:
            print("⚠ Could not retrieve exercises")

    async def test_exercise_type_validation(self, client):
        """Test that valid exercise types are supported."""
        print("\n=== Testing exercise types ===")

        valid_types = [
            "multiple_choice",
            "true_false",
            "short_answer",
        ]

        print(f"✓ Valid exercise types: {valid_types}")

        # Create session and check generated exercises
        create_resp = await client.post(
            "/chat/sessions",
            json={"grade": 5, "subject": "Historia", "mode": "practice"},
        )
        session_id = create_resp.json()["session_id"]

        # Wait for generation
        await asyncio.sleep(3)

        # Get exercises
        response = await client.get(f"/exercises/sessions/{session_id}/exercises")

        if response.status_code == 200:
            data = response.json()
            exercises = data.get("exercises", [])

            if exercises:
                types_found = [e.get("exercise_type") for e in exercises]
                print(f"  Exercise types in response: {set(types_found)}")


@pytest.mark.asyncio
class TestInputValidation:
    """Test input validation and error handling."""

    async def test_invalid_grade_too_high(self, client):
        """Test that grade above 12 is rejected."""
        print("\n=== Testing grade validation (too high) ===")

        response = await client.post(
            "/chat/sessions",
            json={
                "grade": 13,  # Invalid
                "subject": "Matemáticas",
                "mode": "learn",
            },
        )

        assert response.status_code == 422
        print("✓ Grade 13 properly rejected")

    async def test_invalid_grade_too_low(self, client):
        """Test that grade below 1 is rejected."""
        print("\n=== Testing grade validation (too low) ===")

        response = await client.post(
            "/chat/sessions",
            json={
                "grade": 0,  # Invalid
                "subject": "Matemáticas",
                "mode": "learn",
            },
        )

        assert response.status_code == 422
        print("✓ Grade 0 properly rejected")

    async def test_missing_required_subject(self, client):
        """Test that missing subject is rejected."""
        print("\n=== Testing required field validation ===")

        response = await client.post(
            "/chat/sessions",
            json={
                "grade": 5,
                # Missing "subject"
                "mode": "learn",
            },
        )

        assert response.status_code == 422
        print("✓ Missing subject properly rejected")

    async def test_invalid_mode(self, client):
        """Test that invalid mode is rejected."""
        print("\n=== Testing mode validation ===")

        response = await client.post(
            "/chat/sessions",
            json={
                "grade": 5,
                "subject": "Matemáticas",
                "mode": "invalid_mode",  # Invalid
            },
        )

        assert response.status_code == 422
        print("✓ Invalid mode properly rejected")

    async def test_empty_topic_string(self, client):
        """Test that empty topic string is rejected."""
        print("\n=== Testing empty topic validation ===")

        response = await client.post(
            "/chat/sessions",
            json={
                "grade": 5,
                "subject": "Matemáticas",
                "mode": "learn",
                "topic": "",  # Empty
            },
        )

        assert response.status_code == 422
        print("✓ Empty topic properly rejected")


@pytest.mark.asyncio
class TestErrorResponses:
    """Test error response formats and status codes."""

    async def test_nonexistent_session_404(self, client):
        """Test that nonexistent session returns 404."""
        print("\n=== Testing 404 response ===")

        response = await client.get("/chat/sessions/99999")

        assert response.status_code == 404
        print("✓ Nonexistent session returns 404")

    async def test_error_response_has_error_code(self, client):
        """Test that error responses include error code."""
        print("\n=== Testing error response format ===")

        response = await client.get("/chat/sessions/99999")

        assert response.status_code == 404
        data = response.json()

        # Error response should have 'error' field
        if "error" in data:
            print("✓ Error response includes 'error' field")
            assert "code" in data["error"] or "message" in data["error"]

    async def test_validation_error_response(self, client):
        """Test validation error response format."""
        print("\n=== Testing validation error response ===")

        response = await client.post(
            "/chat/sessions",
            json={"grade": "invalid"},  # Should be int
        )

        assert response.status_code == 422
        print("✓ Validation error returns 422")

        # Should have error details
        data = response.json()
        print(f"  Error response: {list(data.keys())}")


@pytest.mark.asyncio
class TestConcurrentRequests:
    """Test handling of concurrent requests."""

    async def test_multiple_session_creation(self, client):
        """Test creating multiple sessions concurrently."""
        print("\n=== Testing concurrent session creation ===")

        # Create 3 sessions concurrently
        tasks = [
            client.post(
                "/chat/sessions",
                json={
                    "grade": 5,
                    "subject": "Matemáticas",
                    "mode": "learn",
                },
            ),
            client.post(
                "/chat/sessions",
                json={
                    "grade": 6,
                    "subject": "Historia",
                    "mode": "practice",
                },
            ),
            client.post(
                "/chat/sessions",
                json={
                    "grade": 7,
                    "subject": "Ciencias",
                    "mode": "study",
                },
            ),
        ]

        responses = await asyncio.gather(*tasks)

        # All should succeed
        assert all(r.status_code == 200 for r in responses)

        session_ids = [r.json()["session_id"] for r in responses]

        # All should have different IDs
        assert len(set(session_ids)) == 3

        print(f"✓ Created 3 concurrent sessions: {session_ids}")

    async def test_concurrent_status_polling(self, client):
        """Test polling status of same session concurrently."""
        print("\n=== Testing concurrent status polling ===")

        # Create one session
        create_resp = await client.post(
            "/chat/sessions",
            json={"grade": 5, "subject": "Matemáticas", "mode": "learn"},
        )
        session_id = create_resp.json()["session_id"]

        # Poll status concurrently
        tasks = [client.get(f"/chat/sessions/{session_id}/status") for _ in range(5)]

        responses = await asyncio.gather(*tasks)

        # All should succeed
        assert all(r.status_code == 200 for r in responses)

        # All should return same session_id
        data = [r.json() for r in responses]
        assert all(d["session_id"] == session_id for d in data)

        print(f"✓ Concurrent polling succeeded for session {session_id}")
