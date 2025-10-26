"""Tests for Exercise Pool Service.

Tests the exercise pool management including:
- Initial pool generation
- Pool status tracking
- Procedural pool maintenance
- Parallel exercise generation
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ensenia.schemas.exercises import DifficultyLevel, ExerciseType
from app.ensenia.services.exercise_pool_service import ExercisePoolService


@pytest.fixture
def mock_generation_service():
    """Mock generation service for testing."""
    service = AsyncMock()
    service.generate_exercise = AsyncMock(
        return_value=(
            {"question": "Test question", "learning_objective": "Test objective"},
            [MagicMock(score=9, feedback="Good", is_approved=True, iteration=1)],
            1,
        )
    )
    return service


@pytest.fixture
def mock_repository():
    """Mock repository for testing."""
    repo = AsyncMock()
    repo.save_exercise = AsyncMock()
    repo.link_exercise_to_session = AsyncMock()
    repo.get_session_exercises = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def pool_service(mock_generation_service, mock_repository):
    """Create pool service with mocked dependencies."""
    return ExercisePoolService(
        generation_service=mock_generation_service,
        repository=mock_repository,
    )


@pytest.mark.asyncio
class TestExercisePoolService:
    """Test suite for ExercisePoolService."""

    async def test_generate_initial_pool_success(
        self, pool_service, mock_generation_service, mock_repository
    ):
        """Test successful initial pool generation."""
        # Mock exercise IDs
        exercise_ids = [1, 2, 3, 4, 5]
        mock_repository.save_exercise.side_effect = [
            MagicMock(id=ex_id) for ex_id in exercise_ids
        ]

        # Mock database session
        mock_db = AsyncMock()

        # Generate initial pool
        result_ids = await pool_service.generate_initial_pool(
            session_id=1,
            grade=5,
            subject="Matemáticas",
            topic="Fracciones",
            db=mock_db,
            pool_size=5,
        )

        # Verify all exercises were generated
        assert len(result_ids) == 5
        assert result_ids == exercise_ids

        # Verify generation service was called 5 times
        assert mock_generation_service.generate_exercise.call_count == 5

        # Verify exercises were saved and linked
        assert mock_repository.save_exercise.call_count == 5
        assert mock_repository.link_exercise_to_session.call_count == 5

    async def test_generate_initial_pool_diverse_types(
        self, pool_service, mock_generation_service
    ):
        """Test that initial pool generates diverse exercise types."""
        mock_db = AsyncMock()

        await pool_service.generate_initial_pool(
            session_id=1,
            grade=5,
            subject="Matemáticas",
            topic="Fracciones",
            db=mock_db,
            pool_size=5,
        )

        # Get all calls to generate_exercise
        calls = mock_generation_service.generate_exercise.call_args_list

        # Verify we have a mix of exercise types
        exercise_types = [call.kwargs["exercise_type"] for call in calls]
        assert ExerciseType.MULTIPLE_CHOICE in exercise_types
        assert ExerciseType.TRUE_FALSE in exercise_types
        assert ExerciseType.SHORT_ANSWER in exercise_types

        # Verify we have different difficulties
        difficulties = [call.kwargs["difficulty_level"] for call in calls]
        assert DifficultyLevel.EASY in difficulties
        assert DifficultyLevel.MEDIUM in difficulties

    async def test_generate_initial_pool_handles_failures(
        self, pool_service, mock_generation_service, mock_repository
    ):
        """Test that partial failures are handled gracefully."""
        # Mock some exercises failing
        mock_repository.save_exercise.side_effect = [
            MagicMock(id=1),
            Exception("Generation failed"),
            MagicMock(id=3),
            Exception("Generation failed"),
            MagicMock(id=5),
        ]

        mock_db = AsyncMock()

        # Generate initial pool
        result_ids = await pool_service.generate_initial_pool(
            session_id=1,
            grade=5,
            subject="Matemáticas",
            topic="Fracciones",
            db=mock_db,
            pool_size=5,
        )

        # Should return only successful IDs
        assert len(result_ids) == 3
        assert result_ids == [1, 3, 5]

    async def test_get_pool_status_healthy(self, pool_service, mock_repository):
        """Test pool status when pool is healthy."""
        # Mock 5 exercises, 2 completed
        mock_exercises = [
            MagicMock(is_completed=False),
            MagicMock(is_completed=False),
            MagicMock(is_completed=False),
            MagicMock(is_completed=True),
            MagicMock(is_completed=True),
        ]
        mock_repository.get_session_exercises.return_value = mock_exercises

        mock_db = AsyncMock()

        status = await pool_service.get_pool_status(session_id=1, db=mock_db)

        assert status["session_id"] == 1
        assert status["total_exercises"] == 5
        assert status["completed_exercises"] == 2
        assert status["pending_exercises"] == 3
        assert status["pool_health"] == "healthy"

    async def test_get_pool_status_low(self, pool_service, mock_repository):
        """Test pool status when pool is low."""
        # Mock 3 exercises, 2 completed
        mock_exercises = [
            MagicMock(is_completed=False),
            MagicMock(is_completed=True),
            MagicMock(is_completed=True),
        ]
        mock_repository.get_session_exercises.return_value = mock_exercises

        mock_db = AsyncMock()

        status = await pool_service.get_pool_status(session_id=1, db=mock_db)

        assert status["pending_exercises"] == 1
        assert status["pool_health"] == "low"

    async def test_get_pool_status_depleted(self, pool_service, mock_repository):
        """Test pool status when pool is depleted."""
        # Mock all completed
        mock_exercises = [
            MagicMock(is_completed=True),
            MagicMock(is_completed=True),
        ]
        mock_repository.get_session_exercises.return_value = mock_exercises

        mock_db = AsyncMock()

        status = await pool_service.get_pool_status(session_id=1, db=mock_db)

        assert status["pending_exercises"] == 0
        assert status["pool_health"] == "depleted"

    @patch("app.ensenia.services.exercise_pool_service.select")
    async def test_maintain_pool_refills_when_low(
        self, mock_select, pool_service, mock_repository, mock_generation_service
    ):
        """Test that pool maintenance refills when low."""
        # Mock pool status - only 1 pending
        mock_exercises = [
            MagicMock(is_completed=False),
            MagicMock(is_completed=True),
            MagicMock(is_completed=True),
        ]
        mock_repository.get_session_exercises.return_value = mock_exercises

        # Mock session
        mock_session = MagicMock(
            id=1,
            grade=5,
            subject="Matemáticas",
            research_context="Test context",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mock successful generation
        mock_repository.save_exercise.side_effect = [
            MagicMock(id=10),
            MagicMock(id=11),
        ]

        # Maintain pool
        new_ids = await pool_service.maintain_pool(
            session_id=1,
            db=mock_db,
            min_pool_size=3,
            refill_count=2,
        )

        # Should have generated 2 new exercises
        assert len(new_ids) == 2
        assert new_ids == [10, 11]
        assert mock_generation_service.generate_exercise.call_count == 2

    @patch("app.ensenia.services.exercise_pool_service.select")
    async def test_maintain_pool_skips_when_healthy(
        self, mock_select, pool_service, mock_repository, mock_generation_service
    ):
        """Test that pool maintenance skips when pool is healthy."""
        # Mock pool status - 5 pending
        mock_exercises = [MagicMock(is_completed=False) for _ in range(5)]
        mock_repository.get_session_exercises.return_value = mock_exercises

        mock_db = AsyncMock()

        # Maintain pool
        new_ids = await pool_service.maintain_pool(
            session_id=1,
            db=mock_db,
            min_pool_size=3,
        )

        # Should not generate any new exercises
        assert len(new_ids) == 0
        assert mock_generation_service.generate_exercise.call_count == 0

    async def test_generate_and_link_exercise_success(
        self, pool_service, mock_generation_service, mock_repository
    ):
        """Test successful exercise generation and linking."""
        mock_db = AsyncMock()
        mock_repository.save_exercise.return_value = MagicMock(id=42)

        exercise_id = await pool_service._generate_and_link_exercise(
            session_id=1,
            grade=5,
            subject="Matemáticas",
            topic="Fracciones",
            exercise_type=ExerciseType.MULTIPLE_CHOICE,
            difficulty_level=DifficultyLevel.MEDIUM,
            curriculum_context="Test context",
            db=mock_db,
        )

        assert exercise_id == 42
        mock_generation_service.generate_exercise.assert_called_once()
        mock_repository.save_exercise.assert_called_once()
        mock_repository.link_exercise_to_session.assert_called_once_with(
            mock_db,
            exercise_id=42,
            session_id=1,
        )

    async def test_generate_and_link_exercise_handles_error(
        self, pool_service, mock_generation_service
    ):
        """Test error handling in exercise generation."""
        mock_db = AsyncMock()
        mock_generation_service.generate_exercise.side_effect = Exception(
            "Generation failed"
        )

        with pytest.raises(Exception, match="Generation failed"):
            await pool_service._generate_and_link_exercise(
                session_id=1,
                grade=5,
                subject="Matemáticas",
                topic="Fracciones",
                exercise_type=ExerciseType.MULTIPLE_CHOICE,
                difficulty_level=DifficultyLevel.MEDIUM,
                curriculum_context=None,
                db=mock_db,
            )
