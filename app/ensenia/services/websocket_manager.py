"""WebSocket connection manager for real-time chat communication.

Manages active WebSocket connections, message broadcasting, and connection lifecycle.
"""

import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for chat sessions."""

    def __init__(self):
        """Initialize connection manager with empty connection registry."""
        # Map session_id -> WebSocket connection
        self.active_connections: dict[int, WebSocket] = {}
        logger.info("WebSocket Connection Manager initialized")

    async def connect(self, websocket: WebSocket, session_id: int) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection to register
            session_id: The chat session ID this connection belongs to

        """
        await websocket.accept()
        self.active_connections[session_id] = websocket
        msg = (
            f"WebSocket connected for session {session_id}."
            f"Active connections: {len(self.active_connections)}"
        )
        logger.info(msg)

    def disconnect(self, session_id: int) -> None:
        """Unregister a WebSocket connection.

        Args:
            session_id: The chat session ID to disconnect

        """
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            msg = (
                f"WebSocket disconnected for session {session_id}."
                f"Active connections: {len(self.active_connections)}"
            )
            logger.info(msg)

    async def send_message(self, session_id: int, message: dict) -> None:
        """Send a message to a specific session's WebSocket.

        Args:
            session_id: The session to send the message to
            message: The message dictionary to send (will be JSON-encoded)

        Raises:
            KeyError: If session_id is not connected

        """
        if session_id not in self.active_connections:
            msg = f"Attempted to send message to disconnected session {session_id}"
            logger.warning(msg)
            raise KeyError(msg)

        websocket = self.active_connections[session_id]
        try:
            await websocket.send_json(message)
            msg = (
                f"Message sent to session {session_id}: "
                f"{message.get('type', 'unknown')}"
            )
            logger.debug(msg)
        except Exception:
            msg = f"Failed to send message to session {session_id}."
            logger.exception(msg)
            # Clean up broken connection
            self.disconnect(session_id)
            raise

    async def send_text_chunk(self, session_id: int, content: str) -> None:
        """Send a text chunk to the client.

        Args:
            session_id: The session to send to
            content: The text content chunk

        """
        await self.send_message(session_id, {"type": "text_chunk", "content": content})

    async def send_audio_chunk(
        self, session_id: int, audio_id: str, chunk_data: str
    ) -> None:
        """Send an audio chunk to the client.

        Args:
            session_id: The session to send to
            audio_id: Unique ID for this audio generation
            chunk_data: Base64-encoded audio data

        """
        await self.send_message(
            session_id,
            {"type": "audio_chunk", "audio_id": audio_id, "chunk_data": chunk_data},
        )

    async def send_audio_ready(
        self, session_id: int, audio_id: str, url: str, duration: float | None = None
    ) -> None:
        """Notify client that complete audio is ready.

        Args:
            session_id: The session to send to
            audio_id: Unique ID for this audio
            url: URL where audio can be accessed
            duration: Optional audio duration in seconds

        """
        message = {"type": "audio_ready", "audio_id": audio_id, "url": url}
        if duration is not None:
            message["duration"] = duration

        await self.send_message(session_id, message)

    async def send_output_mode_changed(self, session_id: int, mode: str) -> None:
        """Notify client that output mode has changed.

        Args:
            session_id: The session to send to
            mode: The new output mode ('text' or 'audio')

        """
        await self.send_message(
            session_id, {"type": "output_mode_changed", "mode": mode}
        )

    async def send_mode_changed(self, session_id: int, mode: str) -> None:
        """Notify client that output mode has changed (backward compatibility).

        Args:
            session_id: The session to send to
            mode: The new mode ('text' or 'audio')

        """
        await self.send_output_mode_changed(session_id, mode)

    async def send_input_mode_changed(self, session_id: int, mode: str) -> None:
        """Notify client that input mode has changed.

        Args:
            session_id: The session to send to
            mode: The new input mode ('text' or 'voice')

        """
        await self.send_message(
            session_id, {"type": "input_mode_changed", "mode": mode}
        )

    async def send_error(
        self, session_id: int, error_message: str, error_code: str | None = None
    ) -> None:
        """Send an error message to the client.

        Args:
            session_id: The session to send to
            error_message: Human-readable error description
            error_code: Optional machine-readable error code

        """
        message = {"type": "error", "message": error_message}
        if error_code:
            message["code"] = error_code

        await self.send_message(session_id, message)

    async def send_message_complete(
        self, session_id: int, message_id: int | None = None
    ) -> None:
        """Signal that message streaming is complete.

        Args:
            session_id: The session to send to
            message_id: Optional database message ID

        """
        message = {"type": "message_complete"}
        if message_id is not None:
            message["message_id"] = message_id

        await self.send_message(session_id, message)

    def is_connected(self, session_id: int) -> bool:
        """Check if a session has an active WebSocket connection.

        Args:
            session_id: The session ID to check

        Returns:
            True if connected, False otherwise

        """
        return session_id in self.active_connections

    def get_connection_count(self) -> int:
        """Get the number of active connections.

        Returns:
            Number of active WebSocket connections

        """
        return len(self.active_connections)


# Global connection manager instance
connection_manager = ConnectionManager()
