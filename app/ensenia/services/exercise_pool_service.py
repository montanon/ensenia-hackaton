"""Exercise Pool Service.

Manages exercise pools for sessions, including:
- Generating initial exercise sets on session creation
- Maintaining a pool of ready-to-use exercises
- Procedurally generating new exercises as the pool depletes
- Adapting difficulty based on student performance
"""

import asyncio
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ensenia.database.models import Session as DBSession
from app.ensenia.schemas.exercises import DifficultyLevel, ExerciseType
from app.ensenia.services.exercise_repository import ExerciseRepository
from app.ensenia.services.generation_service import GenerationService

logger = logging.getLogger(__name__)


class ExercisePoolService:
    """Service for managing exercise pools per session."""

    def __init__(
        self,
        generation_service: GenerationService,
        repository: ExerciseRepository,
    ):
        """Initialize the exercise pool service.

        Args:
            generation_service: Exercise generation service
            repository: Exercise repository

        """
        self.generation_service = generation_service
        self.repository = repository

    async def generate_initial_pool(
        self,
        session_id: int,
        grade: int,
        subject: str,
        topic: str,
        db: AsyncSession,
        pool_size: int = 5,
        curriculum_context: str | None = None,
    ) -> list[int]:
        """Generate initial exercise pool for a new session.

        Creates a diverse set of exercises with different types and difficulties.

        Args:
            session_id: Session ID
            grade: Grade level (1-12)
            subject: Subject area
            topic: Topic for exercises
            db: Database session
            pool_size: Number of exercises to generate (default: 5)
            curriculum_context: Research context from session

        Returns:
            List of generated exercise IDs

        """
        msg = (
            f"Generating initial pool of {pool_size} exercises for session {session_id}"
        )
        logger.info(msg)

        # Define exercise mix (diverse types)
        exercise_mix = [
            (ExerciseType.MULTIPLE_CHOICE, DifficultyLevel.EASY),
            (ExerciseType.TRUE_FALSE, DifficultyLevel.EASY),
            (ExerciseType.MULTIPLE_CHOICE, DifficultyLevel.MEDIUM),
            (ExerciseType.TRUE_FALSE, DifficultyLevel.MEDIUM),
            (ExerciseType.SHORT_ANSWER, DifficultyLevel.MEDIUM),
        ][:pool_size]

        # Generate exercises in parallel
        tasks = []
        for exercise_type, difficulty in exercise_mix:
            task = self._generate_and_link_exercise(
                session_id=session_id,
                grade=grade,
                subject=subject,
                topic=topic,
                exercise_type=exercise_type,
                difficulty_level=difficulty,
                curriculum_context=curriculum_context,
                db=db,
            )
            tasks.append(task)

        # Execute all generations in parallel
        exercise_ids = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out errors and return successful IDs
        successful_ids = [
            ex_id for ex_id in exercise_ids if not isinstance(ex_id, Exception)
        ]
        msg = f"Generated {len(successful_ids)}/{pool_size} exercises for session {session_id}"
        logger.info(msg)

        return successful_ids

    async def _generate_and_link_exercise(
        self,
        session_id: int,
        grade: int,
        subject: str,
        topic: str,
        exercise_type: ExerciseType,
        difficulty_level: DifficultyLevel,
        curriculum_context: str | None,
        db: AsyncSession,
    ) -> int:
        """Generate a single exercise and link it to the session.

        Args:
            session_id: Session ID
            grade: Grade level
            subject: Subject area
            topic: Topic
            exercise_type: Type of exercise
            difficulty_level: Difficulty level
            curriculum_context: Curriculum context
            db: Database session

        Returns:
            Exercise ID

        Raises:
            Exception: If generation or linking fails

        """
        try:
            # Generate exercise
            (
                content,
                validation_history,
                _,
            ) = await self.generation_service.generate_exercise(
                exercise_type=exercise_type,
                grade=grade,
                subject=subject,
                topic=topic,
                difficulty_level=difficulty_level,
                curriculum_context=curriculum_context,
            )

            # Get final validation score
            final_score = validation_history[-1].score if validation_history else 0

            # Save to database
            db_exercise = await self.repository.save_exercise(
                db,
                exercise_type=exercise_type,
                grade=grade,
                subject=subject,
                topic=topic,
                content=content,
                validation_score=final_score,
                difficulty_level=difficulty_level,
                is_public=True,
            )

            # Link to session
            await self.repository.link_exercise_to_session(
                db,
                exercise_id=db_exercise.id,
                session_id=session_id,
            )
            msg = (
                f"Generated and linked exercise {db_exercise.id} "
                f"(type={exercise_type.value}, difficulty={difficulty_level.value}) "
                f"to session {session_id}"
            )
            logger.info(msg)

            return db_exercise.id

        except Exception:
            msg = (
                f"Failed to generate exercise (type={exercise_type.value}, "
                f"difficulty={difficulty_level.value})"
            )
            logger.exception(msg)
            raise

    async def get_pool_status(
        self, session_id: int, db: AsyncSession
    ) -> dict[str, Any]:
        """Get current status of the exercise pool for a session.

        Args:
            session_id: Session ID
            db: Database session

        Returns:
            Dict with pool statistics

        """
        # Get all exercise sessions for this session
        exercise_sessions = await self.repository.get_session_exercises(db, session_id)

        total_exercises = len(exercise_sessions)
        completed_exercises = sum(
            1 for ex_session in exercise_sessions if ex_session.is_completed
        )
        pending_exercises = total_exercises - completed_exercises

        return {
            "session_id": session_id,
            "total_exercises": total_exercises,
            "completed_exercises": completed_exercises,
            "pending_exercises": pending_exercises,
            "pool_health": "healthy"
            if pending_exercises >= 3
            else "low"
            if pending_exercises > 0
            else "depleted",
        }

    async def maintain_pool(
        self,
        session_id: int,
        db: AsyncSession,
        min_pool_size: int = 3,
        refill_count: int = 2,
    ) -> list[int]:
        """Maintain exercise pool by generating new exercises when low.

        Args:
            session_id: Session ID
            db: Database session
            min_pool_size: Minimum pending exercises before refill (default: 3)
            refill_count: Number of exercises to generate on refill (default: 2)

        Returns:
            List of newly generated exercise IDs (empty if no refill needed)

        """
        # Get pool status
        pool_status = await self.get_pool_status(session_id, db)

        if pool_status["pending_exercises"] >= min_pool_size:
            msg = (
                f"Pool for session {session_id} is healthy "
                f"({pool_status['pending_exercises']} pending), no refill needed"
            )
            logger.info(msg)
            return []

        msg = (
            f"Pool for session {session_id} is low "
            f"({pool_status['pending_exercises']} pending), refilling with {refill_count} exercises"
        )
        logger.info(msg)

        # Load session to get parameters
        stmt = select(DBSession).where(DBSession.id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            msg = f"Session {session_id} not found for pool maintenance"
            logger.error(msg)
            return []

        # Determine difficulty based on performance
        # TODO: In future, adapt difficulty based on student performance
        difficulty = DifficultyLevel.MEDIUM

        # Generate new exercises
        exercise_mix = [
            (ExerciseType.MULTIPLE_CHOICE, difficulty),
            (ExerciseType.TRUE_FALSE, difficulty),
        ][:refill_count]

        tasks = []
        for exercise_type, diff in exercise_mix:
            # Use session's subject as topic if no specific topic available
            topic = session.research_context or session.subject

            task = self._generate_and_link_exercise(
                session_id=session_id,
                grade=session.grade,
                subject=session.subject,
                topic=topic,
                exercise_type=exercise_type,
                difficulty_level=diff,
                curriculum_context=session.research_context,
                db=db,
            )
            tasks.append(task)

        # Execute generations in parallel
        exercise_ids = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out errors
        successful_ids = [
            ex_id for ex_id in exercise_ids if not isinstance(ex_id, Exception)
        ]

        msg = f"Refilled pool for session {session_id} with {len(successful_ids)} new exercises"
        logger.info(msg)

        return successful_ids


# Dependency injection
_exercise_pool_service: ExercisePoolService | None = None


def get_exercise_pool_service(
    generation_service: GenerationService,
    repository: ExerciseRepository,
) -> ExercisePoolService:
    """Get or create the singleton ExercisePoolService instance.

    Args:
        generation_service: Exercise generation service
        repository: Exercise repository

    Returns:
        ExercisePoolService instance

    """
    global _exercise_pool_service  # noqa: PLW0603
    if _exercise_pool_service is None:
        _exercise_pool_service = ExercisePoolService(generation_service, repository)
    return _exercise_pool_service
