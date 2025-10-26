"""Integration tests for exercise API routes."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.ensenia.database.models import Exercise, Session
from app.ensenia.main import app
from app.ensenia.schemas.exercises import (
    ExerciseType,
    ValidationResult,
)


@pytest.fixture
def client():
    """Create sync test client for simple tests."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client():
    """Create async test client for tests requiring async fixtures."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def sample_api_session(db_session):
    """Create a sample session for API tests."""
    session = Session(
        grade=8,
        subject="Matemáticas",
        mode="practice",
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest.fixture
async def sample_api_exercise(db_session, sample_multiple_choice_exercise):
    """Create a sample exercise for API tests."""
    exercise = Exercise(
        exercise_type=ExerciseType.MULTIPLE_CHOICE.value,
        grade=8,
        subject="Matemáticas",
        topic="Fracciones",
        content=sample_multiple_choice_exercise,
        validation_score=9,
        difficulty_level=3,
        is_public=True,
    )
    db_session.add(exercise)
    await db_session.commit()
    await db_session.refresh(exercise)
    return exercise


class TestGenerateExerciseEndpoint:
    """Tests for POST /exercises/generate endpoint."""

    @patch(
        "app.ensenia.services.generation_service.GenerationService.generate_exercise"
    )
    def test_generate_exercise_success(
        self, mock_generate, client, sample_multiple_choice_exercise
    ):
        """Test successful exercise generation via API."""
        # Mock the generation service
        mock_generate.return_value = (
            sample_multiple_choice_exercise,
            [
                ValidationResult(
                    score=9,
                    breakdown={
                        "curriculum_alignment": 2,
                        "grade_appropriate": 2,
                        "difficulty_match": 2,
                        "pedagogical_quality": 2,
                        "chilean_spanish": 1,
                    },
                    feedback="Excelente",
                    recommendation="APROBAR",
                    is_approved=True,
                    iteration=1,
                )
            ],
            1,
        )

        response = client.post(
            "/exercises/generate",
            json={
                "exercise_type": "multiple_choice",
                "grade": 8,
                "subject": "Matemáticas",
                "topic": "Fracciones",
                "difficulty_level": 3,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "exercise" in data
        assert data["exercise"]["grade"] == 8
        assert data["exercise"]["subject"] == "Matemáticas"
        assert data["iterations_used"] == 1
        assert len(data["validation_history"]) == 1

    def test_generate_exercise_invalid_grade(self, client):
        """Test generation with invalid grade."""
        response = client.post(
            "/exercises/generate",
            json={
                "exercise_type": "multiple_choice",
                "grade": 0,  # Invalid
                "subject": "Matemáticas",
                "topic": "Fracciones",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_generate_exercise_missing_fields(self, client):
        """Test generation with missing required fields."""
        response = client.post(
            "/exercises/generate",
            json={
                "exercise_type": "multiple_choice",
                # Missing grade, subject, topic
            },
        )

        assert response.status_code == 422


class TestSearchExercisesEndpoint:
    """Tests for POST /exercises/search endpoint."""

    async def test_search_all_exercises(self, async_client, sample_api_exercise):
        """Test searching all exercises."""
        response = await async_client.post("/exercises/search", json={})

        assert response.status_code == 200
        data = response.json()
        assert "exercises" in data
        assert "total" in data
        assert data["total"] >= 1

    async def test_search_by_grade(self, async_client, sample_api_exercise):
        """Test searching exercises by grade."""
        response = await async_client.post("/exercises/search", json={"grade": 8})

        assert response.status_code == 200
        data = response.json()
        assert all(ex["grade"] == 8 for ex in data["exercises"])

    async def test_search_by_subject(self, async_client, sample_api_exercise):
        """Test searching exercises by subject."""
        response = await async_client.post(
            "/exercises/search", json={"subject": "Matemáticas"}
        )

        assert response.status_code == 200
        data = response.json()
        assert all(ex["subject"] == "Matemáticas" for ex in data["exercises"])

    async def test_search_with_limit(self, async_client, sample_api_exercise):
        """Test search with limit parameter."""
        response = await async_client.post("/exercises/search", json={"limit": 5})

        assert response.status_code == 200
        data = response.json()
        assert len(data["exercises"]) <= 5

    def test_search_invalid_limit(self, client):
        """Test search with invalid limit."""
        response = client.post("/exercises/search", json={"limit": 100})  # Too high

        assert response.status_code == 422


class TestGetExerciseEndpoint:
    """Tests for GET /exercises/{id} endpoint."""

    async def test_get_existing_exercise(self, async_client, sample_api_exercise):
        """Test retrieving an existing exercise."""
        response = await async_client.get(f"/exercises/{sample_api_exercise.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_api_exercise.id
        assert data["grade"] == 8
        assert "content" in data

    def test_get_nonexistent_exercise(self, client):
        """Test retrieving a non-existent exercise."""
        response = client.get("/exercises/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestLinkExerciseToSessionEndpoint:
    """Tests for POST /exercises/{id}/sessions/{session_id} endpoint."""

    async def test_link_exercise_success(
        self, async_client, sample_api_exercise, sample_api_session
    ):
        """Test successfully linking an exercise to a session."""
        response = await async_client.post(
            f"/exercises/{sample_api_exercise.id}/sessions/{sample_api_session.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["exercise_id"] == sample_api_exercise.id
        assert data["session_id"] == sample_api_session.id
        assert "assigned_at" in data

    async def test_link_nonexistent_exercise(self, async_client, sample_api_session):
        """Test linking a non-existent exercise."""
        response = await async_client.post(
            f"/exercises/99999/sessions/{sample_api_session.id}"
        )

        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    async def test_link_to_nonexistent_session(self, async_client, sample_api_exercise):
        """Test linking to a non-existent session."""
        response = await async_client.post(
            f"/exercises/{sample_api_exercise.id}/sessions/99999"
        )

        assert response.status_code == 400

    async def test_duplicate_link(
        self, async_client, sample_api_exercise, sample_api_session
    ):
        """Test that duplicate links are rejected."""
        # First link
        await async_client.post(
            f"/exercises/{sample_api_exercise.id}/sessions/{sample_api_session.id}"
        )

        # Attempt duplicate
        response = await async_client.post(
            f"/exercises/{sample_api_exercise.id}/sessions/{sample_api_session.id}"
        )

        assert response.status_code == 400
        assert "already linked" in response.json()["detail"].lower()


class TestSubmitAnswerEndpoint:
    """Tests for POST /exercises/sessions/{id}/submit endpoint."""

    async def test_submit_answer_success(
        self, async_client, sample_api_exercise, sample_api_session
    ):
        """Test successfully submitting an answer."""
        # First link the exercise
        link_response = await async_client.post(
            f"/exercises/{sample_api_exercise.id}/sessions/{sample_api_session.id}"
        )
        exercise_session_id = link_response.json()["exercise_session_id"]

        # Submit answer
        response = await async_client.post(
            f"/exercises/sessions/{exercise_session_id}/submit",
            json={"answer": "Santiago"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_completed"] is True
        assert "completed_at" in data

    def test_submit_to_nonexistent_session(self, client):
        """Test submitting to a non-existent exercise session."""
        response = client.post(
            "/exercises/sessions/99999/submit", json={"answer": "Test"}
        )

        assert response.status_code == 404

    async def test_submit_empty_answer(
        self, async_client, sample_api_exercise, sample_api_session
    ):
        """Test submitting an empty answer."""
        # Link exercise
        link_response = await async_client.post(
            f"/exercises/{sample_api_exercise.id}/sessions/{sample_api_session.id}"
        )
        exercise_session_id = link_response.json()["exercise_session_id"]

        # Submit empty answer
        response = await async_client.post(
            f"/exercises/sessions/{exercise_session_id}/submit", json={"answer": ""}
        )

        assert response.status_code == 422  # Validation error


class TestGetSessionExercisesEndpoint:
    """Tests for GET /exercises/sessions/{id}/exercises endpoint."""

    async def test_get_session_exercises(
        self, async_client, sample_api_exercise, sample_api_session
    ):
        """Test getting all exercises for a session."""
        # Link an exercise
        await async_client.post(
            f"/exercises/{sample_api_exercise.id}/sessions/{sample_api_session.id}"
        )

        # Get session exercises
        response = await async_client.get(
            f"/exercises/sessions/{sample_api_session.id}/exercises"
        )

        assert response.status_code == 200
        data = response.json()
        assert "exercises" in data
        assert data["total"] == 1
        assert data["exercises"][0]["id"] == sample_api_exercise.id

    async def test_get_empty_session_exercises(self, async_client, sample_api_session):
        """Test getting exercises for a session with no exercises."""
        response = await async_client.get(
            f"/exercises/sessions/{sample_api_session.id}/exercises"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["exercises"]) == 0


class TestEndToEndWorkflow:
    """End-to-end integration tests."""

    @patch(
        "app.ensenia.services.generation_service.GenerationService.generate_exercise"
    )
    async def test_complete_workflow(
        self,
        mock_generate,
        async_client,
        _db_session,
        sample_api_session,
        sample_multiple_choice_exercise,
    ):
        """Test complete workflow: generate, link, submit."""
        # Mock generation
        mock_generate.return_value = (
            sample_multiple_choice_exercise,
            [
                ValidationResult(
                    score=9,
                    breakdown={
                        "curriculum_alignment": 2,
                        "grade_appropriate": 2,
                        "difficulty_match": 2,
                        "pedagogical_quality": 2,
                        "chilean_spanish": 1,
                    },
                    feedback="Good",
                    recommendation="APROBAR",
                    is_approved=True,
                    iteration=1,
                )
            ],
            1,
        )

        # 1. Generate exercise
        gen_response = await async_client.post(
            "/exercises/generate",
            json={
                "exercise_type": "multiple_choice",
                "grade": 8,
                "subject": "Matemáticas",
                "topic": "Fracciones",
            },
        )
        assert gen_response.status_code == 200
        exercise_id = gen_response.json()["exercise"]["id"]

        # 2. Link to session
        link_response = await async_client.post(
            f"/exercises/{exercise_id}/sessions/{sample_api_session.id}"
        )
        assert link_response.status_code == 200
        exercise_session_id = link_response.json()["exercise_session_id"]

        # 3. Submit answer
        submit_response = await async_client.post(
            f"/exercises/sessions/{exercise_session_id}/submit",
            json={"answer": "Santiago"},
        )
        assert submit_response.status_code == 200
        assert submit_response.json()["is_completed"] is True

        # 4. Verify in session exercises
        session_exercises = await async_client.get(
            f"/exercises/sessions/{sample_api_session.id}/exercises"
        )
        assert session_exercises.status_code == 200
        assert session_exercises.json()["total"] == 1
