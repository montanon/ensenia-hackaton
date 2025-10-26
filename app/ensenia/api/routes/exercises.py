"""API routes for exercise generation and management.

Endpoints:
- POST /exercises/generate: Generate a new exercise using LangGraph
- GET /exercises/search: Search for existing reusable exercises
- GET /exercises/{id}: Get a specific exercise
- POST /exercises/{id}/sessions/{session_id}: Link exercise to session
- POST /exercise-sessions/{id}/submit: Submit answer for an exercise
"""

import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.ensenia.database.models import Exercise as DBExercise
from app.ensenia.database.session import AsyncSessionLocal, get_db
from app.ensenia.schemas.exercises import (
    DifficultyLevel,
    EssayContent,
    ExerciseListResponse,
    ExerciseResponse,
    ExerciseType,
    ExerciseWithSessionInfo,
    GenerateExerciseRequest,
    GenerateExerciseResponse,
    LinkExerciseResponse,
    MultipleChoiceContent,
    SessionExercisesListResponse,
    ShortAnswerContent,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    TrueFalseContent,
)
from app.ensenia.services.exercise_pool_service import (
    get_exercise_pool_service,
)
from app.ensenia.services.exercise_repository import (
    ExerciseRepository,
    get_exercise_repository,
)
from app.ensenia.services.generation_service import (
    GenerationService,
    get_generation_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exercises", tags=["exercises"])

background_tasks: set[asyncio.Task] = set()

# Constants
QUALITY_THRESHOLD = 8


# ============================================================================
# Helper Functions
# ============================================================================


def db_exercise_to_response(exercise: DBExercise) -> ExerciseResponse:
    """Convert database Exercise model to response schema.

    Args:
        exercise: Database exercise model

    Returns:
        ExerciseResponse schema

    """
    # Parse exercise type
    exercise_type = ExerciseType(exercise.exercise_type)

    # Parse content based on type
    if exercise_type == ExerciseType.MULTIPLE_CHOICE:
        content = MultipleChoiceContent(**exercise.content)
    elif exercise_type == ExerciseType.TRUE_FALSE:
        content = TrueFalseContent(**exercise.content)
    elif exercise_type == ExerciseType.SHORT_ANSWER:
        content = ShortAnswerContent(**exercise.content)
    elif exercise_type == ExerciseType.ESSAY:
        content = EssayContent(**exercise.content)
    else:
        msg = f"Unknown exercise type: {exercise.exercise_type}"
        raise ValueError(msg)

    return ExerciseResponse(
        id=exercise.id,
        exercise_type=exercise_type,
        grade=exercise.grade,
        subject=exercise.subject,
        topic=exercise.topic,
        content=content,
        validation_score=exercise.validation_score,
        difficulty_level=exercise.difficulty_level,
        is_public=exercise.is_public,
        created_at=exercise.created_at,
    )


# ============================================================================
# Route Handlers
# ============================================================================


@router.post("/generate")
async def generate_exercise(
    request: GenerateExerciseRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    generation_service: Annotated[GenerationService, Depends(get_generation_service)],
    repository: Annotated[ExerciseRepository, Depends(get_exercise_repository)],
) -> GenerateExerciseResponse:
    """Generate a new exercise using the LangGraph agent-validator loop.

    This endpoint:
    1. Uses LangGraph to generate an exercise with iterative validation
    2. Saves the validated exercise to the database
    3. Returns the exercise with validation history

    Args:
        request: Exercise generation parameters
        db: Database session
        generation_service: Exercise generation service
        repository: Exercise repository

    Returns:
        Generated exercise with validation history

    Raises:
        HTTPException: If generation fails

    """
    try:
        msg = (
            f"Generating exercise: type={request.exercise_type.value}, "
            f"grade={request.grade}, subject={request.subject}, topic={request.topic}"
        )
        logger.info(msg)

        # First, check for existing high-quality exercise to reuse (unless force_new is True)
        if not request.force_new:
            existing_exercises = await repository.search_exercises(
                db,
                grade=request.grade,
                subject=request.subject,
                topic=request.topic,
                exercise_type=request.exercise_type,
                difficulty_level=request.difficulty_level,
                limit=1,
            )

            # Reuse existing exercise if it meets quality threshold
            if existing_exercises and (
                existing_exercises[0].validation_score >= QUALITY_THRESHOLD
            ):
                exercise = existing_exercises[0]
                logger.info(
                    "Reusing existing exercise %s (score: %s)",
                    exercise.id,
                    exercise.validation_score,
                )

                return GenerateExerciseResponse(
                    exercise=db_exercise_to_response(exercise),
                    validation_history=[],
                    iterations_used=0,
                )
        else:
            logger.info("force_new=True, skipping existing exercise search")

        # No suitable exercise found, generate new one
        logger.info("No suitable exercise found in cache, generating new one...")

        # Generate exercise using LangGraph
        (
            content,
            validation_history,
            iterations_used,
        ) = await generation_service.generate_exercise(
            exercise_type=request.exercise_type,
            grade=request.grade,
            subject=request.subject,
            topic=request.topic,
            difficulty_level=request.difficulty_level,
            max_iterations=request.max_iterations,
            quality_threshold=request.quality_threshold,
            curriculum_context=request.curriculum_context,
        )

        # Validate content schema
        if not generation_service.validate_content_schema(
            request.exercise_type, content
        ):
            msg = f"Generated content failed schema validation: {content}"
            logger.error(msg)
            raise HTTPException(
                status_code=500,
                detail="Generated exercise does not match expected schema",
            )

        # Get final validation score
        final_score = validation_history[-1].score if validation_history else 0

        # Save to database
        db_exercise = await repository.save_exercise(
            db,
            exercise_type=request.exercise_type,
            grade=request.grade,
            subject=request.subject,
            topic=request.topic,
            content=content,
            validation_score=final_score,
            difficulty_level=request.difficulty_level,
            is_public=True,  # All generated exercises are public by default
        )

        # Convert to response
        exercise_response = db_exercise_to_response(db_exercise)

        return GenerateExerciseResponse(
            exercise=exercise_response,
            validation_history=validation_history,
            iterations_used=iterations_used,
        )

    except Exception as e:
        msg = "Exercise generation failed"
        logger.exception(msg)
        raise HTTPException(
            status_code=500,
            detail=msg,
        ) from e


@router.get("")
async def search_exercises(  # noqa: PLR0913
    db: Annotated[AsyncSession, Depends(get_db)],
    repository: Annotated[ExerciseRepository, Depends(get_exercise_repository)],
    grade: Annotated[
        int | None, Query(ge=1, le=12, description="Grade level filter")
    ] = None,
    subject: Annotated[
        str | None, Query(max_length=100, description="Subject filter")
    ] = None,
    topic: Annotated[
        str | None, Query(max_length=200, description="Topic filter")
    ] = None,
    exercise_type: Annotated[
        ExerciseType | None, Query(description="Exercise type filter")
    ] = None,
    difficulty_level: Annotated[
        DifficultyLevel | None, Query(description="Difficulty level filter")
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Maximum number of results")
    ] = 10,
) -> ExerciseListResponse:
    """Search for existing reusable exercises.

    This endpoint searches the exercise database for exercises matching
    the given criteria. Useful for finding existing exercises to reuse
    instead of generating new ones.

    Args:
        grade: Grade level filter (1-12)
        subject: Subject filter
        topic: Topic filter
        exercise_type: Exercise type filter
        difficulty_level: Difficulty level filter
        limit: Maximum number of results
        db: Database session
        repository: Exercise repository

    Returns:
        List of matching exercises

    Raises:
        HTTPException: If search fails

    """
    try:
        filters = {
            "grade": grade,
            "subject": subject,
            "topic": topic,
            "exercise_type": exercise_type,
            "difficulty_level": difficulty_level,
            "limit": limit,
        }
        msg = f"Searching exercises with filters: {filters}"
        logger.info(msg)

        exercises = await repository.search_exercises(
            db,
            grade=grade,
            subject=subject,
            topic=topic,
            exercise_type=exercise_type,
            difficulty_level=difficulty_level,
            limit=limit,
        )

        # Convert to responses
        exercise_responses = [db_exercise_to_response(ex) for ex in exercises]

        return ExerciseListResponse(
            exercises=exercise_responses,
            total=len(exercise_responses),
        )

    except Exception as e:
        msg = "Exercise search failed"
        logger.exception(msg)
        raise HTTPException(
            status_code=500,
            detail=msg,
        ) from e


@router.get("/{exercise_id}")
async def get_exercise(
    exercise_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    repository: Annotated[ExerciseRepository, Depends(get_exercise_repository)],
) -> ExerciseResponse:
    """Get a specific exercise by ID.

    Args:
        exercise_id: Exercise ID
        db: Database session
        repository: Exercise repository

    Returns:
        Exercise details

    Raises:
        HTTPException: If exercise not found

    """
    exercise = await repository.get_exercise_by_id(db, exercise_id)

    if not exercise:
        raise HTTPException(
            status_code=404,
            detail=f"Exercise not found: {exercise_id}",
        )

    return db_exercise_to_response(exercise)


@router.post("/{exercise_id}/sessions/{session_id}")
async def link_exercise_to_session(
    exercise_id: int,
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    repository: Annotated[ExerciseRepository, Depends(get_exercise_repository)],
) -> LinkExerciseResponse:
    """Link an exercise to a session.

    This creates a record that tracks which exercises a student
    has been assigned in a particular session.

    Args:
        exercise_id: Exercise ID
        session_id: Session ID
        db: Database session
        repository: Exercise repository

    Returns:
        Link details

    Raises:
        HTTPException: If exercise or session not found, or link already exists

    """
    try:
        exercise_session = await repository.link_exercise_to_session(
            db,
            exercise_id=exercise_id,
            session_id=session_id,
        )

        return LinkExerciseResponse(
            exercise_session_id=exercise_session.id,
            exercise_id=exercise_session.exercise_id,
            session_id=exercise_session.session_id,
            assigned_at=exercise_session.assigned_at,
        )

    except ValueError as e:
        msg = f"Failed to link exercise {exercise_id} to session {session_id}: {str(e)}"
        logger.error(msg)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        msg = f"Failed to link exercise {exercise_id} to session {session_id}: {type(e).__name__}: {str(e)}"
        logger.exception(msg)
        raise HTTPException(
            status_code=500,
            detail="Failed to link exercise to session",
        ) from e


@router.post("/sessions/{exercise_session_id}/submit")
async def submit_answer(
    exercise_session_id: int,
    request: SubmitAnswerRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    repository: Annotated[ExerciseRepository, Depends(get_exercise_repository)],
    generation_service: Annotated[GenerationService, Depends(get_generation_service)],
) -> SubmitAnswerResponse:
    """Submit a student's answer for an exercise.

    This records the student's answer and marks the exercise as completed.
    Also triggers pool maintenance to ensure exercise pool stays healthy.

    Args:
        exercise_session_id: ExerciseSession ID
        request: Answer submission
        db: Database session
        repository: Exercise repository
        generation_service: Exercise generation service

    Returns:
        Submission confirmation

    Raises:
        HTTPException: If exercise session not found

    """
    try:
        exercise_session = await repository.submit_answer(
            db,
            exercise_session_id=exercise_session_id,
            answer=request.answer,
        )

        # Get session_id before triggering background task
        session_id = exercise_session.session_id

        # Trigger pool maintenance in background (non-blocking)
        # Create background task with its own database session
        async def maintain_pool_background() -> None:
            """Background task to maintain exercise pool with separate DB session."""
            async with AsyncSessionLocal() as bg_db:
                try:
                    pool_service = get_exercise_pool_service(
                        generation_service, repository
                    )
                    await pool_service.maintain_pool(
                        session_id=session_id, db=bg_db, min_pool_size=3
                    )
                except Exception:
                    msg = f"Background pool maintenance failed for session {session_id}"
                    logger.exception(msg)

        task = asyncio.create_task(maintain_pool_background())
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

        msg = f"Answer submitted for exercise_session {exercise_session_id}, "
        logger.info(msg)

        return SubmitAnswerResponse(
            is_completed=exercise_session.is_completed,
            completed_at=exercise_session.completed_at,
            feedback="Respuesta registrada exitosamente",
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        msg = "Failed to submit answer"
        logger.exception(msg)
        raise HTTPException(
            status_code=500,
            detail=msg,
        ) from e


@router.get("/sessions/{session_id}/exercises")
async def get_session_exercises(
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    repository: Annotated[ExerciseRepository, Depends(get_exercise_repository)],
) -> SessionExercisesListResponse:
    """Get all exercises linked to a session.

    Args:
        session_id: Session ID
        db: Database session
        repository: Exercise repository

    Returns:
        List of exercises with session link info for the session

    Raises:
        HTTPException: If session exercises not found

    """
    try:
        exercise_sessions = await repository.get_session_exercises(db, session_id)

        # Convert to response format with session info
        exercise_responses = [
            ExerciseWithSessionInfo(
                exercise=db_exercise_to_response(ex_session.exercise),
                exercise_session_id=ex_session.id,
            )
            for ex_session in exercise_sessions
        ]

        return SessionExercisesListResponse(
            exercises=exercise_responses,
            total=len(exercise_responses),
        )

    except Exception as e:
        msg = "Failed to get session exercises"
        logger.exception(msg)
        raise HTTPException(
            status_code=500,
            detail=msg,
        ) from e
