"""Chat API routes.

Endpoints for managing chat sessions, sending messages,
and triggering research context updates.
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ensenia.database.models import Session as DBSession
from app.ensenia.database.session import AsyncSessionLocal, get_db
from app.ensenia.models import ChatMode
from app.ensenia.services.chat_service import get_chat_service
from app.ensenia.services.exercise_pool_service import (
    get_exercise_pool_service,
)
from app.ensenia.services.exercise_repository import (
    get_exercise_repository,
)
from app.ensenia.services.generation_service import (
    get_generation_service,
)
from app.ensenia.services.research_service import get_research_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

background_tasks: set[asyncio.Task] = set()


# Request/Response Models
class CreateSessionRequest(BaseModel):
    """Request to create a new chat session."""

    grade: int = Field(..., ge=1, le=12, description="Grade level (1-12)")
    subject: str = Field(..., min_length=1, description="Subject area")
    mode: ChatMode = Field(..., description="Chat mode")
    topic: str | None = Field(None, description="Optional topic for initial research")


class CreateSessionResponse(BaseModel):
    """Response after creating a session."""

    session_id: int
    grade: int
    subject: str
    mode: str
    context_loaded: bool
    created_at: datetime


class SendMessageRequest(BaseModel):
    """Request to send a message."""

    message: str = Field(..., min_length=1, description="User message")


class SendMessageResponse(BaseModel):
    """Response after sending a message."""

    response: str


class ResearchRequest(BaseModel):
    """Request to trigger research."""

    topic: str = Field(..., min_length=1, description="Topic to research")


class ResearchResponse(BaseModel):
    """Response after research."""

    context: str


class UpdateModeRequest(BaseModel):
    """Request to update session mode."""

    mode: str = Field(
        ..., description="New mode: 'text' or 'audio'", pattern="^(text|audio)$"
    )


class UpdateModeResponse(BaseModel):
    """Response after updating mode."""

    session_id: int
    mode: str


class MessageResponse(BaseModel):
    """Message in conversation history."""

    id: int
    role: str
    content: str
    timestamp: datetime


class SessionResponse(BaseModel):
    """Detailed session response."""

    id: int
    grade: int
    subject: str
    mode: str
    created_at: datetime
    research_context: str | None
    messages: list[MessageResponse]


# Background task for session initialization
async def initialize_session_background(
    session_id: int,
    grade: int,
    subject: str,
    topic: str | None,
    db_session_maker: Callable[[], AsyncSession],
) -> None:
    """Background task to initialize session with research and exercises.

    Args:
        session_id: Session ID
        grade: Grade level
        subject: Subject area
        topic: Optional topic for research
        db_session_maker: Database session factory

    """
    try:
        # Create a new database session for background task
        async with db_session_maker() as db:
            research_service = get_research_service()
            generation_service = get_generation_service()
            repository = get_exercise_repository()
            pool_service = get_exercise_pool_service(generation_service, repository)

            # Determine research topic
            research_topic = topic or f"{subject} - {grade}° Básico"

            # Step 1: Load research context
            msg = f"[Background] Starting research for session {session_id} on topic: {research_topic}"
            logger.info(msg)
            try:
                context = await research_service.update_session_context(
                    session_id, research_topic, db
                )
                msg = f"[Background] Research completed for session {session_id}"
                logger.info(msg)
            except Exception:
                msg = f"[Background] Research failed for session {session_id}"
                logger.exception(msg)
                context = None

            # Step 2: Generate initial exercise pool
            msg = f"[Background] Generating initial exercise pool for session {session_id}"
            logger.info(msg)
            try:
                exercise_ids = await pool_service.generate_initial_pool(
                    session_id=session_id,
                    grade=grade,
                    subject=subject,
                    topic=research_topic,
                    db=db,
                    pool_size=5,
                    curriculum_context=context,
                )
                msg = f"[Background] Generated {len(exercise_ids)} exercises for session {session_id}"
                logger.info(msg)
            except Exception:
                msg = (
                    f"[Background] Exercise generation failed for session {session_id}"
                )
                logger.exception(msg)

            msg = f"[Background] Session {session_id} initialization complete"
            logger.info(msg)

    except Exception:
        msg = f"[Background] Fatal error in session {session_id} initialization"
        logger.exception(msg)
        # Don't raise - background tasks should fail silently to avoid crashing


# Endpoints
@router.post("/sessions")
async def create_session(
    request: CreateSessionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CreateSessionResponse:
    """Create a new chat session.

    Optionally loads initial research context if topic is provided.

    Args:
        request: Session creation request
        db: Database session

    Returns:
        Created session details

    """
    try:
        # Create session
        session = DBSession(
            grade=request.grade,
            subject=request.subject,
            mode=request.mode.value,  # Convert enum to string
            research_context=None,
        )

        db.add(session)
        await db.commit()
        await db.refresh(session)

        logger.info(
            "Created session %s (grade=%s, subject=%s, mode=%s)",
            session.id,
            session.grade,
            session.subject,
            session.mode,
        )

        # Trigger background initialization (research + exercise generation)
        # This runs asynchronously without blocking the response
        task = asyncio.create_task(
            initialize_session_background(
                session_id=session.id,
                grade=request.grade,
                subject=request.subject,
                topic=request.topic,
                db_session_maker=AsyncSessionLocal,
            )
        )
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
        msg = f"Session {session.id} created, background initialization started"
        logger.info(msg)
        return CreateSessionResponse(
            session_id=session.id,
            grade=session.grade,
            subject=session.subject,
            mode=session.mode,
            context_loaded=False,  # Background task handles this
            created_at=session.created_at,
        )

    except Exception as e:
        logger.exception("Error creating session")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: int,
    request: SendMessageRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SendMessageResponse:
    """Send a message and get AI response.

    Args:
        session_id: Session ID
        request: Message request
        db: Database session

    Returns:
        AI assistant response

    Raises:
        HTTPException: If session not found or error occurs

    """
    try:
        chat_service = get_chat_service()
        response = await chat_service.send_message(session_id, request.message, db)

        return SendMessageResponse(response=response)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error sending message")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/sessions/{session_id}/research")
async def trigger_research(
    session_id: int,
    request: ResearchRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResearchResponse:
    """Trigger Deep Research for a session.

    Updates the session's research context with curriculum-aligned content.

    Args:
        session_id: Session ID
        request: Research request with topic
        db: Database session

    Returns:
        Research context that was loaded

    Raises:
        HTTPException: If session not found or error occurs

    """
    try:
        research_service = get_research_service()
        context = await research_service.update_session_context(
            session_id, request.topic, db
        )
        return ResearchResponse(context=context)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error triggering research")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: int, db: Annotated[AsyncSession, Depends(get_db)]
) -> SessionResponse:
    """Get session details with message history.

    Args:
        session_id: Session ID
        db: Database session

    Returns:
        Session details with all messages

    Raises:
        HTTPException: If session not found

    """
    try:
        # Load session with messages
        stmt = (
            select(DBSession)
            .options(selectinload(DBSession.messages))
            .where(DBSession.id == session_id)
        )

        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Convert messages
        messages = [
            MessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp,
            )
            for msg in session.messages
        ]

        return SessionResponse(
            id=session.id,
            grade=session.grade,
            subject=session.subject,
            mode=session.mode,
            created_at=session.created_at,
            research_context=session.research_context,
            messages=messages,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error getting session")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch("/sessions/{session_id}/mode")
async def update_session_mode(
    session_id: int,
    request: UpdateModeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UpdateModeResponse:
    """Update session's output mode (text/audio).

    REST fallback for mode updates (WebSocket clients can use set_mode message).

    Args:
        session_id: Session ID
        request: Mode update request
        db: Database session

    Returns:
        Updated session mode

    Raises:
        HTTPException: If session not found or invalid mode

    """
    try:
        chat_service = get_chat_service()

        await chat_service.update_session_mode(session_id, request.mode, db)

        return UpdateModeResponse(session_id=session_id, mode=request.mode)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error updating session mode")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/sessions/{session_id}/status")
async def get_session_status(
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Get session initialization status.

    Returns information about whether research context has loaded
    and how many exercises are ready.

    Args:
        session_id: Session ID
        db: Database session

    Returns:
        Session status including research and exercise pool status

    Raises:
        HTTPException: If session not found

    """
    try:
        # Load session
        stmt = select(DBSession).where(DBSession.id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get exercise pool status
        generation_service = get_generation_service()
        repository = get_exercise_repository()
        pool_service = get_exercise_pool_service(generation_service, repository)

        pool_status = await pool_service.get_pool_status(session_id, db)

        return {
            "session_id": session_id,
            "research_loaded": session.research_context is not None,
            "initial_exercises_ready": pool_status["total_exercises"] >= 5,
            "exercise_count": pool_status["total_exercises"],
            "pending_exercises": pool_status["pending_exercises"],
            "pool_health": pool_status["pool_health"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error getting session status")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check for chat service.

    Returns:
        Health status

    """
    return {"status": "healthy", "service": "chat"}
