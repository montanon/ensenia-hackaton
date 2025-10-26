"""WebSocket routes for real-time chat with text/audio mode switching.

Handles WebSocket connections for chat sessions, enabling:
- Real-time text streaming
- Real-time audio generation
- Dynamic mode switching (text <-> audio)
- Bidirectional communication
"""

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from sqlalchemy.ext.asyncio import AsyncSession

from app.ensenia.database.models import OutputMode
from app.ensenia.database.session import get_db
from app.ensenia.services.chat_service import ChatService
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
    """WebSocket endpoint for real-time chat with audio support.

    Message Types (Client -> Server):
        - {type: "message", content: "text"} - Send chat message
        - {type: "set_mode", mode: "text"|"audio"} - Switch output mode
        - {type: "ping"} - Keep-alive ping

    Message Types (Server -> Client):
        - {type: "text_chunk", content: "..."} - Streaming text response
        - {type: "audio_chunk", audio_id: "...", chunk_data: base64} - Audio stream
        - {type: "audio_ready", audio_id: "...", url: "..."} - Full audio available
        - {type: "mode_changed", mode: "text"|"audio"} - Confirm mode switch
        - {type: "message_complete", message_id: int} - Message streaming done
        - {type: "error", message: "...", code: "..."} - Error occurred
        - {type: "pong"} - Response to ping

    Args:
        websocket: The WebSocket connection
        session_id: The chat session ID
        db: Database session (injected)

    """
    # Initialize services
    chat_service = ChatService()

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
            "current_mode": session.current_mode,
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

            elif message_type == "set_mode":
                # Handle mode switching
                new_mode = message_data.get("mode")
                msg = f"[WebSocket] Mode change requested for session {session_id}: {new_mode}"
                logger.info(msg)

                if new_mode not in [OutputMode.TEXT.value, OutputMode.AUDIO.value]:
                    msg = f"[WebSocket] Invalid mode received: {new_mode}"
                    logger.error(msg)
                    await connection_manager.send_error(
                        session_id,
                        f"Invalid mode: {new_mode}. Must be 'text' or 'audio'",
                        "INVALID_MODE",
                    )
                    continue

                try:
                    await chat_service.update_session_mode(session_id, new_mode, db)
                    await connection_manager.send_mode_changed(session_id, new_mode)
                    msg = f"[WebSocket] Session {session_id} mode successfully changed to {new_mode}"
                    logger.info(msg)
                except Exception:
                    msg = f"[WebSocket] Failed to update session {session_id} mode to {new_mode}"
                    logger.exception(msg)
                    await connection_manager.send_error(
                        session_id, msg, "MODE_UPDATE_FAILED"
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
