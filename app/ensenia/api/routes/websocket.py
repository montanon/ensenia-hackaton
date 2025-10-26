"""WebSocket routes for real-time chat with text/audio mode switching.

Handles WebSocket connections for chat sessions, enabling:
- Real-time text streaming
- Real-time audio generation
- Dynamic mode switching (text <-> audio)
- Bidirectional communication
- Speech-to-text audio transcription
"""

import base64
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from sqlalchemy.ext.asyncio import AsyncSession

from app.ensenia.database.models import InputMode, OutputMode
from app.ensenia.database.session import get_db
from app.ensenia.services.chat_service import ChatService
from app.ensenia.services.deepgram_service import get_deepgram_service
from app.ensenia.services.stream_orchestrator import (
    process_message_with_dual_stream,
)
from app.ensenia.services.websocket_manager import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/chat/{session_id}")
async def websocket_chat_endpoint(  # noqa: C901, PLR0912, PLR0915
    websocket: WebSocket,
    session_id: int,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> None:
    """WebSocket endpoint for real-time chat with Deepgram streaming STT.

    Handles bidirectional communication including real-time speech-to-text
    transcription via Deepgram and text-to-speech via ElevenLabs.

    Message Types (Client -> Server):
        - {type: "message", content: "text"} - Send chat message
        - {type: "set_mode", mode: "text"|"audio"} - Switch output mode (text or audio) [deprecated: use set_output_mode]
        - {type: "set_output_mode", mode: "text"|"audio"} - Switch how agent responds (text or audio)
        - {type: "set_input_mode", mode: "text"|"voice"} - Switch how user sends messages (text or voice)
        - {type: "toggle_voice"} - Toggle both input/output modes to full voice or full text
        - {type: "audio_chunk", data: "base64_audio"} - Send audio chunk for STT
        - {type: "audio_end"} - Signal end of audio, triggers Deepgram transcription
        - {type: "ping"} - Keep-alive ping

    Message Types (Server -> Client):
        - {type: "connected", ...} - Connection established
        - {type: "text_chunk", content: "..."} - Streaming text response
        - {type: "audio_ready", audio_id: "...", url: "..."} - TTS audio available
        - {type: "stt_partial", transcript: "...", confidence: float} - Interim transcription
        - {type: "stt_result", transcript: "...", confidence: float} - Final transcription
        - {type: "mode_changed", mode: "text"|"audio"} - Output mode changed
        - {type: "message_complete", message_id: int} - Message streaming complete
        - {type: "error", message: "...", code: "..."} - Error occurred
        - {type: "pong"} - Response to ping

    Audio Flow (STT):
        1. Client sends {type: "audio_chunk", data: base64} messages
        2. Server buffers chunks locally
        3. Client sends {type: "audio_end"} when finished speaking
        4. Server sends buffered audio to Deepgram streaming API
        5. Deepgram processes and returns transcription
        6. Server sends stt_result to client with final transcript
        7. Client auto-processes final transcript as chat message

    Args:
        websocket: The WebSocket connection
        session_id: The chat session ID (for routing messages)
        db: Database session for persisting chat and session data

    """
    # Initialize services
    chat_service = ChatService()
    deepgram_service = get_deepgram_service()

    # Buffer for audio chunks during recording
    audio_buffer: list[bytes] = []

    # Verify session exists
    try:
        session = await chat_service.get_session(session_id, db)
        if not session:
            await websocket.close(code=404, reason="Session not found")
            return
    except Exception:
        msg = f"Error fetching session {session_id}."
        logger.exception(msg)
        await websocket.close(code=500, reason="Internal server error")
        return

    # Connect WebSocket
    await connection_manager.connect(websocket, session_id)
    msg = f"WebSocket connected to session {session_id}"
    logger.info(msg)

    # Send initial connection success message
    await connection_manager.send_message(
        session_id,
        {
            "type": "connected",
            "session_id": session_id,
            "input_mode": session.input_mode,
            "output_mode": session.current_mode,
            "grade": session.grade,
            "subject": session.subject,
            "mode": session.mode,
        },
    )

    try:
        while True:
            # Receive message from client
            try:
                data = await websocket.receive_text()
                message_data: dict[str, Any] = json.loads(data)
            except json.JSONDecodeError:
                await connection_manager.send_error(
                    session_id, "Invalid JSON format", "INVALID_JSON"
                )
                continue

            message_type = message_data.get("type")

            msg = f"Received message type '{message_type}' from session {session_id}"
            logger.debug(msg)

            # Handle different message types
            if message_type == "ping":
                await connection_manager.send_message(session_id, {"type": "pong"})

            elif message_type == "set_mode" or message_type == "set_output_mode":
                # Handle output mode switching (text/audio)
                new_mode = message_data.get("mode")
                msg = f"[WebSocket] Output mode change requested for session {session_id}: {new_mode}"
                logger.info(msg)

                if new_mode not in [OutputMode.TEXT.value, OutputMode.AUDIO.value]:
                    msg = f"[WebSocket] Invalid output mode received: {new_mode}"
                    logger.error(msg)
                    await connection_manager.send_error(
                        session_id,
                        f"Invalid output mode: {new_mode}. Must be 'text' or 'audio'",
                        "INVALID_OUTPUT_MODE",
                    )
                    continue

                try:
                    await chat_service.update_session_output_mode(
                        session_id, new_mode, db
                    )
                    await connection_manager.send_output_mode_changed(
                        session_id, new_mode
                    )
                    msg = f"[WebSocket] Session {session_id} output mode successfully changed to {new_mode}"
                    logger.info(msg)
                except Exception:
                    msg = f"[WebSocket] Failed to update session {session_id} output mode to {new_mode}"
                    logger.exception(msg)
                    await connection_manager.send_error(
                        session_id, msg, "OUTPUT_MODE_UPDATE_FAILED"
                    )

            elif message_type == "set_input_mode":
                # Handle input mode switching (text/voice)
                new_mode = message_data.get("mode")
                msg = f"[WebSocket] Input mode change requested for session {session_id}: {new_mode}"
                logger.info(msg)

                if new_mode not in [InputMode.TEXT.value, InputMode.VOICE.value]:
                    msg = f"[WebSocket] Invalid input mode received: {new_mode}"
                    logger.error(msg)
                    await connection_manager.send_error(
                        session_id,
                        f"Invalid input mode: {new_mode}. Must be 'text' or 'voice'",
                        "INVALID_INPUT_MODE",
                    )
                    continue

                try:
                    await chat_service.update_session_input_mode(
                        session_id, new_mode, db
                    )
                    await connection_manager.send_input_mode_changed(
                        session_id, new_mode
                    )
                    msg = f"[WebSocket] Session {session_id} input mode successfully changed to {new_mode}"
                    logger.info(msg)
                except Exception:
                    msg = f"[WebSocket] Failed to update session {session_id} input mode to {new_mode}"
                    logger.exception(msg)
                    await connection_manager.send_error(
                        session_id, msg, "INPUT_MODE_UPDATE_FAILED"
                    )

            elif message_type == "toggle_voice":
                # Handle full voice mode toggle
                msg = f"[WebSocket] Voice toggle requested for session {session_id}"
                logger.info(msg)

                try:
                    # Check current state - toggle to full voice or full text
                    current_input = session.input_mode
                    current_output = session.current_mode

                    # If in text mode, switch to voice. Otherwise, switch back to text.
                    if current_input == InputMode.TEXT.value:
                        new_input = InputMode.VOICE.value
                        new_output = OutputMode.AUDIO.value
                    else:
                        new_input = InputMode.TEXT.value
                        new_output = OutputMode.TEXT.value

                    # Update both modes
                    await chat_service.update_session_input_mode(
                        session_id, new_input, db
                    )
                    await chat_service.update_session_output_mode(
                        session_id, new_output, db
                    )

                    # Notify client of both changes
                    await connection_manager.send_input_mode_changed(
                        session_id, new_input
                    )
                    await connection_manager.send_output_mode_changed(
                        session_id, new_output
                    )

                    msg = f"[WebSocket] Session {session_id} toggled voice mode (input: {new_input}, output: {new_output})"
                    logger.info(msg)
                except Exception:
                    msg = f"[WebSocket] Failed to toggle voice mode for session {session_id}"
                    logger.exception(msg)
                    await connection_manager.send_error(
                        session_id, msg, "VOICE_TOGGLE_FAILED"
                    )

            elif message_type == "audio_chunk":
                # Handle audio chunk from client
                audio_data_b64 = message_data.get("data")
                if not audio_data_b64:
                    await connection_manager.send_error(
                        session_id, "Audio data is required", "MISSING_AUDIO_DATA"
                    )
                    continue

                try:
                    # Decode base64 audio data
                    audio_bytes = base64.b64decode(audio_data_b64)
                    audio_buffer.append(audio_bytes)
                    msg = f"[WebSocket] Audio chunk received for session {session_id}: {len(audio_bytes)} bytes"
                    logger.debug(msg)
                except Exception:
                    msg = f"[WebSocket] Error decoding audio data for session {session_id}"
                    logger.exception(msg)
                    await connection_manager.send_error(
                        session_id,
                        "Failed to decode audio data",
                        "AUDIO_DECODE_ERROR",
                    )

            elif message_type == "audio_end":
                # Handle end of audio stream - transcribe with Deepgram streaming
                if not audio_buffer:
                    await connection_manager.send_error(
                        session_id, "No audio data to transcribe", "NO_AUDIO_DATA"
                    )
                    continue

                try:
                    msg = f"[WebSocket] Starting Deepgram streaming transcription for session {session_id}"
                    logger.info(msg)

                    # Create async generator from audio buffer
                    async def audio_chunk_generator() -> AsyncIterator[bytes]:
                        """Yield audio chunks from buffer."""
                        for chunk in audio_buffer:
                            yield chunk

                    # Track transcription results
                    final_transcript = ""
                    last_partial = ""

                    # Stream transcription results from Deepgram
                    async for result in deepgram_service.transcribe_stream(
                        audio_chunk_generator()
                    ):
                        if result.is_final:
                            final_transcript = result.transcript
                            msg = f"[WebSocket] Final transcript for session {session_id}: {final_transcript}"
                            logger.info(msg)

                            # Send final result
                            await connection_manager.send_message(
                                session_id,
                                {
                                    "type": "stt_result",
                                    "transcript": final_transcript,
                                    "confidence": result.confidence,
                                },
                            )
                        elif result.transcript != last_partial:
                            last_partial = result.transcript
                            msg = f"[WebSocket] Partial transcript for session {session_id}: {result.transcript}"
                            logger.debug(msg)

                            await connection_manager.send_message(
                                session_id,
                                {
                                    "type": "stt_partial",
                                    "transcript": result.transcript,
                                    "confidence": result.confidence,
                                },
                            )

                    # Clear buffer for next recording
                    audio_buffer.clear()

                    # Automatically process the final transcribed message as a chat message
                    if final_transcript:
                        try:
                            await process_message_with_dual_stream(
                                session_id=session_id,
                                user_message=final_transcript,
                                websocket=websocket,
                                db=db,
                            )
                        except Exception:
                            msg = f"Error processing transcribed message for session {session_id}."
                            logger.exception(msg)
                            await connection_manager.send_error(
                                session_id, msg, "PROCESSING_ERROR"
                            )

                except Exception:
                    msg = f"Error transcribing audio for session {session_id}."
                    logger.exception(msg)
                    audio_buffer.clear()  # Clear buffer on error
                    await connection_manager.send_error(
                        session_id,
                        "Failed to transcribe audio with Deepgram",
                        "TRANSCRIPTION_ERROR",
                    )

            elif message_type == "message":
                # Handle chat message - will be processed by stream orchestrator
                content = message_data.get("content")
                if not content:
                    await connection_manager.send_error(
                        session_id, "Message content is required", "MISSING_CONTENT"
                    )
                    continue

                try:
                    await process_message_with_dual_stream(
                        session_id=session_id,
                        user_message=content,
                        websocket=websocket,
                        db=db,
                    )
                except Exception:
                    msg = f"Error processing message for session {session_id}."
                    logger.exception(msg)
                    await connection_manager.send_error(
                        session_id, msg, "PROCESSING_ERROR"
                    )

            else:
                await connection_manager.send_error(
                    session_id,
                    f"Unknown message type: {message_type}",
                    "UNKNOWN_MESSAGE_TYPE",
                )

    except WebSocketDisconnect:
        msg = f"WebSocket disconnected for session {session_id}"
        logger.info(msg)
        connection_manager.disconnect(session_id)
    except Exception:
        msg = f"Unexpected error in WebSocket for session {session_id}."
        logger.exception(msg)
        connection_manager.disconnect(session_id)
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            msg = "Failed to close WebSocket connection after error."
            logger.exception(msg)
