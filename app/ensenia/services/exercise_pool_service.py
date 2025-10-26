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
from app.ensenia.database.session import AsyncSessionLocal
from app.ensenia.schemas.exercises import DifficultyLevel, ExerciseType
from app.ensenia.services.exercise_repository import ExerciseRepository
from app.ensenia.services.generation_service import GenerationService

logger = logging.getLogger(__name__)

# Constants
MIN_POOL_THRESHOLD = 3


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

    async def generate_initial_pool(  # noqa: PLR0913
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
        logger.info(
            "[ExercisePool] Generating initial pool of %d exercises for session %d",
            pool_size,
            session_id,
        )
        logger.info(
            "[ExercisePool] Parameters: grade=%d, subject=%s, topic=%s, has_context=%s",
            grade,
            subject,
            topic,
            curriculum_context is not None,
        )

        # Define exercise mix (diverse types)
        exercise_mix = [
            (ExerciseType.MULTIPLE_CHOICE, DifficultyLevel.EASY),
            (ExerciseType.TRUE_FALSE, DifficultyLevel.EASY),
            (ExerciseType.MULTIPLE_CHOICE, DifficultyLevel.MEDIUM),
            (ExerciseType.TRUE_FALSE, DifficultyLevel.MEDIUM),
            (ExerciseType.SHORT_ANSWER, DifficultyLevel.MEDIUM),
        ][:pool_size]

        logger.info(
            "[ExercisePool] Exercise mix: %s",
            ", ".join(f"{t.value}/{d.value}" for t, d in exercise_mix),
        )

        # Generate exercises in parallel
        import time

        start_time = time.time()
        tasks = []
        for i, (exercise_type, difficulty) in enumerate(exercise_mix, 1):
            logger.info(
                "[ExercisePool] Task %d/%d: Generating %s (difficulty=%s)...",
                i,
                len(exercise_mix),
                exercise_type.value,
                difficulty.value,
            )
            # Create a separate database session for each concurrent task
            # This avoids SQLAlchemy's "concurrent operations not permitted" error
            task = self._generate_and_link_exercise(
                session_id=session_id,
                grade=grade,
                subject=subject,
                topic=topic,
                exercise_type=exercise_type,
                difficulty_level=difficulty,
                curriculum_context=curriculum_context,
                db=None,  # Pass None to create a new session per task
            )
            tasks.append(task)

        # Execute all generations in parallel
        logger.info(
            "[ExercisePool] Starting parallel generation of %d exercises...", len(tasks)
        )
        exercise_ids = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start_time

        # Filter out errors and LOG THEM
        successful_ids = []
        failed_count = 0
        for i, result in enumerate(exercise_ids, 1):
            exercise_type, difficulty = exercise_mix[i - 1]
            if isinstance(result, Exception):
                failed_count += 1
                logger.error(
                    "[ExercisePool] ✗ Exercise %d/%d FAILED (%s/%s): %s",
                    i,
                    len(exercise_ids),
                    exercise_type.value,
                    difficulty.value,
                    str(result),
                )
                logger.exception(
                    "[ExercisePool] Full error traceback for exercise %d:",
                    i,
                    exc_info=result,
                )
            else:
                successful_ids.append(result)
                logger.info(
                    "[ExercisePool] ✓ Exercise %d/%d SUCCESS (%s/%s) - ID: %d",
                    i,
                    len(exercise_ids),
                    exercise_type.value,
                    difficulty.value,
                    result,
                )

        logger.info(
            "[ExercisePool] ✓ Generated %d/%d exercises for session %d in %.2fs (failed: %d)",
            len(successful_ids),
            pool_size,
            session_id,
            elapsed,
            failed_count,
        )

        if failed_count > 0:
            logger.warning(
                "[ExercisePool] ⚠️ Pool generation incomplete - %d/%d exercises failed!",
                failed_count,
                pool_size,
            )

        return successful_ids

    async def _generate_and_link_exercise(  # noqa: PLR0913
        self,
        session_id: int,
        grade: int,
        subject: str,
        topic: str,
        exercise_type: ExerciseType,
        difficulty_level: DifficultyLevel,
        curriculum_context: str | None,
        db: AsyncSession | None,
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
            db: Database session (if None, creates a new session for this task)

        Returns:
            Exercise ID

        Raises:
            Exception: If generation or linking fails

        """
        logger.debug(
            "[ExercisePool] _generate_and_link_exercise started: type=%s, difficulty=%s, session=%d",
            exercise_type.value,
            difficulty_level.value,
            session_id,
        )

        # If no session provided, create one for this task
        # This avoids concurrent operation issues when running in parallel
        if db is None:
            async with AsyncSessionLocal() as new_db:
                return await self._generate_and_link_exercise(
                    session_id=session_id,
                    grade=grade,
                    subject=subject,
                    topic=topic,
                    exercise_type=exercise_type,
                    difficulty_level=difficulty_level,
                    curriculum_context=curriculum_context,
                    db=new_db,
                )

        try:
            import time

            start_time = time.time()

            # Generate exercise
            logger.debug(
                "[ExercisePool] Calling generation_service.generate_exercise (type=%s, difficulty=%s)...",
                exercise_type.value,
                difficulty_level.value,
            )

            (
                content,
                validation_history,
                iterations,
            ) = await self.generation_service.generate_exercise(
                exercise_type=exercise_type,
                grade=grade,
                subject=subject,
                topic=topic,
                difficulty_level=difficulty_level,
                curriculum_context=curriculum_context,
            )

            gen_elapsed = time.time() - start_time
            logger.debug(
                "[ExercisePool] Exercise generated in %.2fs (%d iterations, %d validation steps)",
                gen_elapsed,
                iterations,
                len(validation_history),
            )

            # Get final validation score
            final_score = validation_history[-1].score if validation_history else 0
            logger.debug("[ExercisePool] Final validation score: %d", final_score)

            # Save to database
            logger.debug("[ExercisePool] Saving exercise to database...")
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
            logger.debug("[ExercisePool] Exercise saved with ID: %d", db_exercise.id)

            # Link to session
            logger.debug(
                "[ExercisePool] Linking exercise %d to session %d...",
                db_exercise.id,
                session_id,
            )
            await self.repository.link_exercise_to_session(
                db,
                exercise_id=db_exercise.id,
                session_id=session_id,
            )

            total_elapsed = time.time() - start_time
            logger.info(
                "[ExercisePool] ✓ Generated and linked exercise %d (type=%s, difficulty=%s) to session %d (%.2fs)",
                db_exercise.id,
                exercise_type.value,
                difficulty_level.value,
                session_id,
                total_elapsed,
            )

            return db_exercise.id

        except Exception as e:
            logger.error(
                "[ExercisePool] ✗ Failed to generate exercise (type=%s, difficulty=%s, session=%d): %s",
                exercise_type.value,
                difficulty_level.value,
                session_id,
                str(e),
            )
            logger.exception("[ExercisePool] Full error traceback:")
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
            if pending_exercises >= MIN_POOL_THRESHOLD
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
            logger.info(
                "Pool for session %s is healthy (%s pending), no refill needed",
                session_id,
                pool_status["pending_exercises"],
            )
            return []

        logger.info(
            "Pool for session %s is low (%s pending), refilling with %s exercises",
            session_id,
            pool_status["pending_exercises"],
            refill_count,
        )

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
                db=None,  # Pass None to create a new session per task to avoid concurrent operations
            )
            tasks.append(task)

        # Execute generations in parallel
        exercise_ids = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out errors
        successful_ids = [
            ex_id for ex_id in exercise_ids if not isinstance(ex_id, Exception)
        ]

        logger.info(
            "Refilled pool for session %s with %s new exercises",
            session_id,
            len(successful_ids),
        )

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
