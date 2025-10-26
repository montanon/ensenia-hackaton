"""Stream Orchestrator for dual text/audio streaming.

Coordinates parallel streaming of text and audio responses, enabling
real-time mode switching between text and audio output.
"""

import asyncio
import logging
from datetime import UTC, datetime

from fastapi import WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ensenia.core.config import settings
from app.ensenia.database.models import Message as DBMessage
from app.ensenia.database.models import OutputMode
from app.ensenia.database.models import Session as DBSession
from app.ensenia.services.chat_service import ChatService
from app.ensenia.services.elevenlabs_service import ElevenLabsService
from app.ensenia.services.websocket_manager import connection_manager

logger = logging.getLogger(__name__)


async def process_message_with_dual_stream(
    session_id: int,
    user_message: str,
    websocket: WebSocket,  # noqa: ARG001 - passed from route but not used
    db: AsyncSession,
) -> None:
    """Orchestration for streaming text and audio responses.

    This function coordinates two parallel tasks:
    1. Stream text chunks from OpenAI to the WebSocket
    2. Generate audio from complete text and stream/deliver it

    Args:
        session_id: The chat session ID
        user_message: The user's message content
        websocket: The WebSocket connection
        db: Database session

    Raises:
        Exception: If critical errors occur during processing

    """
    msg = f"Starting dual stream processing for session {session_id}"
    logger.info(msg)

    # Initialize services
    chat_service = ChatService()
    tts_service = ElevenLabsService()

    # Get session with messages
    session = await chat_service.get_session(session_id, db)
    if not session:
        msg = f"Session {session_id} not found"
        logger.error(msg)
        await connection_manager.send_error(session_id, msg, "SESSION_NOT_FOUND")
        return

    # Buffer to accumulate text for TTS
    text_buffer: list[str] = []

    # Save user message to database
    user_msg = DBMessage(
        session_id=session_id,
        role="user",
        content=user_message,
        timestamp=datetime.now(UTC),
        input_mode=session.input_mode,  # Track how user sent this message
        output_mode=OutputMode.TEXT.value,  # User messages are always stored as text
    )
    db.add(user_msg)
    try:
        await db.commit()
    except Exception:
        msg = "Failed to save user message."
        logger.exception(msg)
        await db.rollback()

    # Create tasks for parallel execution
    text_task = asyncio.create_task(
        stream_text_response(
            session=session,
            user_message=user_message,
            text_buffer=text_buffer,
            chat_service=chat_service,
            db=db,
        )
    )

    # Wait for text streaming to complete and get full response
    try:
        full_text = await text_task
    except Exception:
        msg = "Text streaming failed."
        logger.exception(msg)
        await connection_manager.send_error(session_id, msg, "TEXT_STREAM_ERROR")
        return

    # Check if session is in audio mode
    # Refresh session to get latest mode (might have changed during streaming)
    await db.refresh(session)

    # Generate and stream audio if in audio mode
    if session.current_mode == OutputMode.AUDIO.value and full_text:
        audio_task = asyncio.create_task(
            stream_audio_response(
                text_content=full_text,
                grade=session.grade,
                session_id=session_id,
                tts_service=tts_service,
            )
        )

        try:
            audio_info = await audio_task
            # Update the assistant message with audio info
            if audio_info:
                # Find the most recent assistant message
                stmt = (
                    select(DBMessage)
                    .where(DBMessage.session_id == session_id)
                    .where(DBMessage.role == "assistant")
                    .order_by(DBMessage.timestamp.desc())
                    .limit(1)
                )
                result = await db.execute(stmt)
                assistant_msg = result.scalar_one_or_none()

                if assistant_msg:
                    assistant_msg.audio_id = audio_info["audio_id"]
                    assistant_msg.audio_url = audio_info["audio_url"]
                    assistant_msg.audio_available = True
                    assistant_msg.audio_duration = audio_info.get("duration")
                    assistant_msg.output_mode = OutputMode.AUDIO.value
                    await db.commit()

        except ValueError as ve:
            # API key not configured
            msg = f"Audio generation failed - TTS not configured: {ve}"
            logger.error(msg)
            await connection_manager.send_error(
                session_id,
                "Text-to-speech service not configured. Using text mode only.",
                "TTS_NOT_CONFIGURED",
            )
        except Exception as e:
            msg = f"Audio streaming failed: {e}"
            logger.exception(msg)
            # Don't fail the whole request if audio fails - graceful degradation
            await connection_manager.send_error(
                session_id,
                f"Audio generation failed: {e!s}. Text response is available.",
                "AUDIO_STREAM_ERROR",
            )

    # Send completion signal
    try:
        await connection_manager.send_message_complete(session_id)
    except Exception as e:
        # Log but don't fail - connection may have been closed
        msg = f"Failed to send completion signal for session {session_id}: {e}"
        logger.warning(msg)

    msg = f"Dual stream processing complete for session {session_id}"
    logger.info(msg)


async def stream_text_response(
    session: DBSession,
    user_message: str,
    text_buffer: list[str],
    chat_service: ChatService,
    db: AsyncSession,
) -> str:
    """Stream text response chunks from OpenAI to WebSocket.

    Args:
        session: The database session object
        user_message: The user's message
        text_buffer: List to accumulate text chunks
        chat_service: ChatService instance
        db: Database session

    Returns:
        Complete text response

    """
    full_text = ""
    chunk_count = 0

    try:
        logger.info(f"[StreamOrchestrator] Starting to stream from OpenAI for session {session.id}")
        generator = chat_service.send_message_streaming(session, user_message, db)
        logger.info(f"[StreamOrchestrator] Created async generator for session {session.id}")

        async for chunk in generator:
            chunk_count += 1
            full_text += chunk
            text_buffer.append(chunk)

            # Send chunk to WebSocket
            logger.info(f"[StreamOrchestrator] Chunk {chunk_count}: {len(chunk)} chars - Sending to WebSocket for session {session.id}")
            try:
                await connection_manager.send_text_chunk(session.id, chunk)
                logger.info(f"[StreamOrchestrator] Chunk {chunk_count} sent successfully to WebSocket")
            except Exception as e:
                logger.error(f"[StreamOrchestrator] Failed to send text chunk {chunk_count}: {e}", exc_info=True)
                raise

        logger.info(f"[StreamOrchestrator] Finished streaming {chunk_count} chunks for session {session.id}")

        # Save assistant message to database
        assistant_msg = DBMessage(
            session_id=session.id,
            role="assistant",
            content=full_text,
            timestamp=datetime.now(UTC),
            output_mode=session.current_mode,
        )
        db.add(assistant_msg)
        await db.commit()

        msg = (
            f"Text streaming complete for session {session.id}: {len(full_text)} chars"
        )
        logger.info(msg)
        return full_text

    except Exception:
        msg = "Error in text streaming."
        logger.exception(msg)
        raise


async def stream_audio_response(
    text_content: str,
    grade: int,
    session_id: int,
    tts_service: ElevenLabsService,
) -> dict:
    """Generate and deliver audio for text response.

    Args:
        text_content: The complete text to convert to audio
        grade: Grade level for voice settings
        session_id: Session ID for WebSocket delivery
        tts_service: ElevenLabsService instance

    Returns:
        Dict with audio_id, audio_url, and optional duration

    """
    # Generate cache key using the same method as ElevenLabsService
    voice_settings = tts_service.get_voice_settings(grade)
    voice_settings_dict = {
        "stability": voice_settings.stability,
        "similarity_boost": voice_settings.similarity_boost,
        "style": voice_settings.style,
        "use_speaker_boost": voice_settings.use_speaker_boost,
        "speed": voice_settings.speed,
    }

    audio_id = tts_service._generate_cache_key(  # noqa: SLF001
        text_content,
        settings.elevenlabs_voice_id,
        settings.elevenlabs_model_id,
        voice_settings_dict,
    )

    try:
        msg = f"Generating audio for session {session_id}, audio_id={audio_id}"
        logger.info(msg)

        # Generate audio (uses caching internally)
        audio_bytes = await tts_service.generate_speech(
            text=text_content, grade=grade, use_cache=True
        )

        # Audio is cached as file, construct URL
        # Assuming audio is served from /audio/{audio_id}.mp3
        audio_url = f"/audio/{audio_id}.mp3"

        # Notify client that audio is ready
        await connection_manager.send_audio_ready(
            session_id=session_id, audio_id=audio_id, url=audio_url
        )

        msg = f"Audio ready for session {session_id}: {audio_url} ({len(audio_bytes)} bytes)"
        logger.info(msg)

        return {
            "audio_id": audio_id,
            "audio_url": audio_url,
            "duration": None,  # Could calculate from audio_bytes if needed
        }

    except ValueError as ve:
        # API key not configured - re-raise with clear message
        logger.error("TTS API key not configured: %s", ve)
        raise
    except Exception as e:
        msg = f"Error generating audio: {e}"
        logger.exception(msg)
        raise RuntimeError(msg) from e
