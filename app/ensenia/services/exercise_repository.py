"""Exercise repository service for database operations.

Provides CRUD operations and search functionality for exercises,
with support for reusable exercise discovery and session tracking.
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ensenia.database.models import Exercise, ExerciseSession, Session
from app.ensenia.schemas.exercises import DifficultyLevel, ExerciseType

logger = logging.getLogger(__name__)


class ExerciseRepository:
    """Repository for exercise database operations."""

    async def search_exercises(
        self,
        db: AsyncSession,
        *,
        grade: int | None = None,
        subject: str | None = None,
        topic: str | None = None,
        exercise_type: ExerciseType | None = None,
        difficulty_level: DifficultyLevel | None = None,
        is_public: bool = True,
        limit: int = 10,
    ) -> list[Exercise]:
        """Search for exercises matching the given criteria.

        Args:
            db: Database session
            grade: Filter by grade level
            subject: Filter by subject
            topic: Filter by topic
            exercise_type: Filter by exercise type
            difficulty_level: Filter by difficulty
            is_public: Only search public (reusable) exercises
            limit: Maximum results to return

        Returns:
            List of matching exercises

        """
        # Build filter conditions
        conditions = []

        if is_public is not None:
            conditions.append(Exercise.is_public == is_public)
        if grade is not None:
            conditions.append(Exercise.grade == grade)
        if subject is not None:
            conditions.append(Exercise.subject == subject)
        if topic is not None:
            conditions.append(Exercise.topic == topic)
        if exercise_type is not None:
            conditions.append(Exercise.exercise_type == exercise_type.value)
        if difficulty_level is not None:
            conditions.append(Exercise.difficulty_level == difficulty_level.value)

        # Build query
        stmt = (
            select(Exercise)
            .where(and_(*conditions))
            .order_by(desc(Exercise.validation_score), desc(Exercise.created_at))
            .limit(limit)
        )

        result = await db.execute(stmt)
        exercises = list(result.scalars().all())

        msg = (
            f"Searched exercises with filters: "
            f"grade={grade}, subject={subject}, topic={topic}, "
            f"type={exercise_type}, difficulty={difficulty_level}, "
            f"found={len(exercises)}"
        )
        logger.info(msg)
        return exercises

    async def save_exercise(
        self,
        db: AsyncSession,
        *,
        exercise_type: ExerciseType,
        grade: int,
        subject: str,
        topic: str,
        content: dict,
        validation_score: int,
        difficulty_level: DifficultyLevel,
        is_public: bool = True,
    ) -> Exercise:
        """Save a new exercise to the database.

        Args:
            db: Database session
            exercise_type: Type of exercise
            grade: Grade level
            subject: Subject area
            topic: Topic
            content: Exercise content (JSONB)
            validation_score: Validation score (0-10)
            difficulty_level: Difficulty level
            is_public: Whether exercise can be reused

        Returns:
            Created exercise

        """
        exercise = Exercise(
            exercise_type=exercise_type.value,
            grade=grade,
            subject=subject,
            topic=topic,
            content=content,
            validation_score=validation_score,
            difficulty_level=difficulty_level.value,
            is_public=is_public,
        )

        db.add(exercise)
        await db.commit()
        await db.refresh(exercise)

        msg = (
            f"Saved exercise: id={exercise.id}, type={exercise_type.value}, "
            f"grade={grade}, subject={subject}, topic={topic}, "
            f"score={validation_score}"
        )
        logger.info(msg)
        return exercise

    async def get_exercise_by_id(
        self, db: AsyncSession, exercise_id: int
    ) -> Exercise | None:
        """Get an exercise by ID.

        Args:
            db: Database session
            exercise_id: Exercise ID

        Returns:
            Exercise or None if not found

        """
        stmt = select(Exercise).where(Exercise.id == exercise_id)
        result = await db.execute(stmt)
        exercise = result.scalar_one_or_none()

        if exercise:
            msg = f"Retrieved exercise: id={exercise_id}"
            logger.info(msg)
        else:
            msg = f"Exercise not found: id={exercise_id}"
            logger.warning(msg)

        return exercise

    async def link_exercise_to_session(
        self, db: AsyncSession, exercise_id: int, session_id: int
    ) -> ExerciseSession:
        """Link an exercise to a session.

        Args:
            db: Database session
            exercise_id: Exercise ID
            session_id: Session ID

        Returns:
            Created ExerciseSession link

        Raises:
            ValueError: If exercise or session not found, or link already exists

        """
        # Check if exercise exists
        exercise = await self.get_exercise_by_id(db, exercise_id)
        if not exercise:
            msg = f"Exercise not found: {exercise_id}"
            raise ValueError(msg)

        # Check if session exists
        session_stmt = select(Session).where(Session.id == session_id)
        session_result = await db.execute(session_stmt)
        session = session_result.scalar_one_or_none()
        if not session:
            msg = f"Session not found: {session_id}"
            raise ValueError(msg)

        # Check if link already exists
        existing_stmt = select(ExerciseSession).where(
            and_(
                ExerciseSession.exercise_id == exercise_id,
                ExerciseSession.session_id == session_id,
            )
        )
        existing_result = await db.execute(existing_stmt)
        if existing_result.scalar_one_or_none():
            msg = f"Exercise {exercise_id} already linked to session {session_id}"
            raise ValueError(msg)

        # Create link
        exercise_session = ExerciseSession(
            exercise_id=exercise_id,
            session_id=session_id,
        )

        db.add(exercise_session)
        await db.commit()
        await db.refresh(exercise_session)

        msg = (
            f"Linked exercise to session: "
            f"exercise_id={exercise_id}, session_id={session_id}, "
            f"link_id={exercise_session.id}"
        )
        logger.info(msg)
        return exercise_session

    async def get_session_exercises(
        self, db: AsyncSession, session_id: int
    ) -> list[ExerciseSession]:
        """Get all exercises linked to a session.

        Args:
            db: Database session
            session_id: Session ID

        Returns:
            List of ExerciseSession links with loaded exercises

        """
        stmt = (
            select(ExerciseSession)
            .where(ExerciseSession.session_id == session_id)
            .options(selectinload(ExerciseSession.exercise))
            .order_by(desc(ExerciseSession.assigned_at))
        )

        result = await db.execute(stmt)
        exercise_sessions = list(result.scalars().all())

        msg = f"Retrieved {len(exercise_sessions)} exercises for session {session_id}"
        logger.info(msg)

        return exercise_sessions

    async def submit_answer(
        self,
        db: AsyncSession,
        exercise_session_id: int,
        answer: str,
    ) -> ExerciseSession:
        """Submit an answer for an exercise.

        Args:
            db: Database session
            exercise_session_id: ExerciseSession ID
            answer: Student's answer

        Returns:
            Updated ExerciseSession

        Raises:
            ValueError: If exercise session not found

        """
        stmt = select(ExerciseSession).where(ExerciseSession.id == exercise_session_id)
        result = await db.execute(stmt)
        exercise_session = result.scalar_one_or_none()

        if not exercise_session:
            msg = f"ExerciseSession not found: {exercise_session_id}"
            raise ValueError(msg)

        # Update with answer and mark as completed
        exercise_session.student_answer = answer
        exercise_session.is_completed = True
        exercise_session.completed_at = datetime.now(UTC)

        await db.commit()
        await db.refresh(exercise_session)

        msg = (
            f"Submitted answer for exercise session: "
            f"id={exercise_session_id}, completed={exercise_session.is_completed}"
        )
        logger.info(msg)
        return exercise_session

    async def get_exercise_session(
        self, db: AsyncSession, exercise_session_id: int
    ) -> ExerciseSession | None:
        """Get an exercise session by ID.

        Args:
            db: Database session
            exercise_session_id: ExerciseSession ID

        Returns:
            ExerciseSession or None if not found

        """
        stmt = (
            select(ExerciseSession)
            .where(ExerciseSession.id == exercise_session_id)
            .options(selectinload(ExerciseSession.exercise))
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_exercise_stats(self, db: AsyncSession, exercise_id: int) -> dict:
        """Get usage statistics for an exercise.

        Args:
            db: Database session
            exercise_id: Exercise ID

        Returns:
            Dictionary with stats: total_uses, completed_count, completion_rate

        """
        stmt = select(ExerciseSession).where(ExerciseSession.exercise_id == exercise_id)
        result = await db.execute(stmt)
        sessions = list(result.scalars().all())

        total_uses = len(sessions)
        completed_count = sum(1 for s in sessions if s.is_completed)
        completion_rate = (
            (completed_count / total_uses * 100) if total_uses > 0 else 0.0
        )

        stats = {
            "total_uses": total_uses,
            "completed_count": completed_count,
            "completion_rate": round(completion_rate, 2),
        }

        msg = f"Exercise stats for id={exercise_id}: {stats}"
        logger.info(msg)

        return stats


# ============================================================================
# Dependency Injection
# ============================================================================


def get_exercise_repository() -> ExerciseRepository:
    """Get a new instance of ExerciseRepository."""
    return ExerciseRepository()
