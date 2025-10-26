"""Tests for exercise repository."""

import pytest

from app.ensenia.database.models import Exercise, Session
from app.ensenia.schemas.exercises import DifficultyLevel, ExerciseType
from app.ensenia.services.exercise_repository import ExerciseRepository


@pytest.fixture
async def repository():
    """Create repository instance."""
    return ExerciseRepository()


@pytest.fixture
async def sample_session(db_session):
    """Create a sample chat session."""
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
async def sample_exercise(db_session, sample_multiple_choice_exercise):
    """Create a sample exercise in database."""
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


class TestSaveExercise:
    """Tests for save_exercise method."""

    async def test_save_exercise(
        self, repository, db_session, sample_multiple_choice_exercise
    ):
        """Test saving a new exercise."""
        exercise = await repository.save_exercise(
            db_session,
            exercise_type=ExerciseType.MULTIPLE_CHOICE,
            grade=8,
            subject="Matemáticas",
            topic="Fracciones",
            content=sample_multiple_choice_exercise,
            validation_score=9,
            difficulty_level=DifficultyLevel.MEDIUM,
            is_public=True,
        )

        assert exercise.id is not None
        assert exercise.exercise_type == ExerciseType.MULTIPLE_CHOICE.value
        assert exercise.grade == 8
        assert exercise.validation_score == 9
        assert exercise.content == sample_multiple_choice_exercise

    async def test_save_private_exercise(
        self, repository, db_session, sample_essay_exercise
    ):
        """Test saving a private (non-reusable) exercise."""
        exercise = await repository.save_exercise(
            db_session,
            exercise_type=ExerciseType.ESSAY,
            grade=12,
            subject="Historia",
            topic="Independencia",
            content=sample_essay_exercise,
            validation_score=7,
            difficulty_level=DifficultyLevel.HARD,
            is_public=False,
        )

        assert exercise.is_public is False


class TestSearchExercises:
    """Tests for search_exercises method."""

    async def test_search_all_public(self, repository, db_session, sample_exercise):
        """Test searching all public exercises."""
        exercises = await repository.search_exercises(db_session)

        assert len(exercises) >= 1
        assert all(ex.is_public for ex in exercises)

    async def test_search_by_grade(self, repository, db_session, sample_exercise):
        """Test searching exercises by grade."""
        exercises = await repository.search_exercises(db_session, grade=8)

        assert len(exercises) >= 1
        assert all(ex.grade == 8 for ex in exercises)

    async def test_search_by_subject(self, repository, db_session, sample_exercise):
        """Test searching exercises by subject."""
        exercises = await repository.search_exercises(db_session, subject="Matemáticas")

        assert len(exercises) >= 1
        assert all(ex.subject == "Matemáticas" for ex in exercises)

    async def test_search_by_topic(self, repository, db_session, sample_exercise):
        """Test searching exercises by topic."""
        exercises = await repository.search_exercises(db_session, topic="Fracciones")

        assert len(exercises) >= 1
        assert all(ex.topic == "Fracciones" for ex in exercises)

    async def test_search_by_type(self, repository, db_session, sample_exercise):
        """Test searching exercises by type."""
        exercises = await repository.search_exercises(
            db_session, exercise_type=ExerciseType.MULTIPLE_CHOICE
        )

        assert len(exercises) >= 1
        assert all(
            ex.exercise_type == ExerciseType.MULTIPLE_CHOICE.value for ex in exercises
        )

    async def test_search_by_difficulty(self, repository, db_session, sample_exercise):
        """Test searching exercises by difficulty level."""
        exercises = await repository.search_exercises(
            db_session, difficulty_level=DifficultyLevel.MEDIUM
        )

        assert len(exercises) >= 1
        assert all(
            ex.difficulty_level == DifficultyLevel.MEDIUM.value for ex in exercises
        )

    async def test_search_with_limit(self, repository, db_session):
        """Test that limit parameter works."""
        # Create 5 exercises
        for i in range(5):
            exercise = Exercise(
                exercise_type=ExerciseType.TRUE_FALSE.value,
                grade=i + 1,
                subject="Test",
                topic=f"Topic {i}",
                content={
                    "question": f"Q{i}",
                    "correct_answer": True,
                    "explanation": "E" * 30,
                    "learning_objective": "O" * 20,
                },
                validation_score=8,
                difficulty_level=2,
                is_public=True,
            )
            db_session.add(exercise)
        await db_session.commit()

        exercises = await repository.search_exercises(db_session, limit=3)
        assert len(exercises) <= 3

    async def test_search_ordered_by_score(self, repository, db_session):
        """Test that results are ordered by validation score."""
        # Create exercises with different scores
        for score in [5, 9, 7]:
            exercise = Exercise(
                exercise_type=ExerciseType.TRUE_FALSE.value,
                grade=8,
                subject="Test",
                topic="Order",
                content={
                    "question": f"Q{score}",
                    "correct_answer": True,
                    "explanation": "E" * 30,
                    "learning_objective": "O" * 20,
                },
                validation_score=score,
                difficulty_level=2,
                is_public=True,
            )
            db_session.add(exercise)
        await db_session.commit()

        exercises = await repository.search_exercises(db_session, topic="Order")
        scores = [ex.validation_score for ex in exercises]
        assert scores == sorted(scores, reverse=True)


class TestGetExerciseById:
    """Tests for get_exercise_by_id method."""

    async def test_get_existing_exercise(self, repository, db_session, sample_exercise):
        """Test retrieving an existing exercise."""
        exercise = await repository.get_exercise_by_id(db_session, sample_exercise.id)

        assert exercise is not None
        assert exercise.id == sample_exercise.id

    async def test_get_nonexistent_exercise(self, repository, db_session):
        """Test retrieving a non-existent exercise."""
        exercise = await repository.get_exercise_by_id(db_session, 99999)

        assert exercise is None


class TestLinkExerciseToSession:
    """Tests for link_exercise_to_session method."""

    async def test_link_exercise(
        self, repository, db_session, sample_exercise, sample_session
    ):
        """Test linking an exercise to a session."""
        link = await repository.link_exercise_to_session(
            db_session, sample_exercise.id, sample_session.id
        )

        assert link.exercise_id == sample_exercise.id
        assert link.session_id == sample_session.id
        assert link.is_completed is False

    async def test_link_nonexistent_exercise(
        self, repository, db_session, sample_session
    ):
        """Test linking a non-existent exercise."""
        with pytest.raises(ValueError, match="Exercise not found"):
            await repository.link_exercise_to_session(
                db_session, 99999, sample_session.id
            )

    async def test_link_to_nonexistent_session(
        self, repository, db_session, sample_exercise
    ):
        """Test linking to a non-existent session."""
        with pytest.raises(ValueError, match="Session not found"):
            await repository.link_exercise_to_session(
                db_session, sample_exercise.id, 99999
            )

    async def test_duplicate_link(
        self, repository, db_session, sample_exercise, sample_session
    ):
        """Test that duplicate links are prevented."""
        # Create first link
        await repository.link_exercise_to_session(
            db_session, sample_exercise.id, sample_session.id
        )

        # Attempt duplicate link
        with pytest.raises(ValueError, match="already linked"):
            await repository.link_exercise_to_session(
                db_session, sample_exercise.id, sample_session.id
            )


class TestGetSessionExercises:
    """Tests for get_session_exercises method."""

    async def test_get_session_exercises(
        self, repository, db_session, sample_exercise, sample_session
    ):
        """Test getting all exercises for a session."""
        # Link exercise to session
        await repository.link_exercise_to_session(
            db_session, sample_exercise.id, sample_session.id
        )

        exercises = await repository.get_session_exercises(
            db_session, sample_session.id
        )

        assert len(exercises) == 1
        assert exercises[0].exercise_id == sample_exercise.id
        assert exercises[0].exercise is not None

    async def test_get_empty_session_exercises(
        self, repository, db_session, sample_session
    ):
        """Test getting exercises for a session with no exercises."""
        exercises = await repository.get_session_exercises(
            db_session, sample_session.id
        )

        assert len(exercises) == 0


class TestSubmitAnswer:
    """Tests for submit_answer method."""

    async def test_submit_answer(
        self, repository, db_session, sample_exercise, sample_session
    ):
        """Test submitting an answer."""
        # Link exercise to session
        link = await repository.link_exercise_to_session(
            db_session, sample_exercise.id, sample_session.id
        )

        # Submit answer
        updated_link = await repository.submit_answer(db_session, link.id, "Santiago")

        assert updated_link.student_answer == "Santiago"
        assert updated_link.is_completed is True
        assert updated_link.completed_at is not None

    async def test_submit_to_nonexistent_link(self, repository, db_session):
        """Test submitting answer to non-existent exercise session."""
        with pytest.raises(ValueError, match="ExerciseSession not found"):
            await repository.submit_answer(db_session, 99999, "Answer")


class TestGetExerciseStats:
    """Tests for get_exercise_stats method."""

    async def test_stats_no_uses(self, repository, db_session, sample_exercise):
        """Test stats for unused exercise."""
        stats = await repository.get_exercise_stats(db_session, sample_exercise.id)

        assert stats["total_uses"] == 0
        assert stats["completed_count"] == 0
        assert stats["completion_rate"] == 0.0

    async def test_stats_with_uses(
        self, repository, db_session, sample_exercise, sample_session
    ):
        """Test stats with usage."""
        # Link and complete
        link = await repository.link_exercise_to_session(
            db_session, sample_exercise.id, sample_session.id
        )
        await repository.submit_answer(db_session, link.id, "Answer")

        stats = await repository.get_exercise_stats(db_session, sample_exercise.id)

        assert stats["total_uses"] == 1
        assert stats["completed_count"] == 1
        assert stats["completion_rate"] == 100.0

    async def test_stats_partial_completion(
        self, repository, db_session, sample_exercise
    ):
        """Test stats with partial completion."""
        # Create 3 sessions
        for i in range(3):
            session = Session(grade=8, subject="Test", mode="practice")
            db_session.add(session)
            await db_session.commit()
            await db_session.refresh(session)

            link = await repository.link_exercise_to_session(
                db_session, sample_exercise.id, session.id
            )

            # Complete only first one
            if i == 0:
                await repository.submit_answer(db_session, link.id, "Answer")

        stats = await repository.get_exercise_stats(db_session, sample_exercise.id)

        assert stats["total_uses"] == 3
        assert stats["completed_count"] == 1
        assert stats["completion_rate"] == pytest.approx(33.33, rel=0.01)
