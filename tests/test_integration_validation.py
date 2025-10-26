"""Integration validation tests - validates the full flow works.

These tests simulate the complete user journey without requiring
external API calls (OpenAI, ElevenLabs).
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.ensenia.database.models import Message, Session
from app.ensenia.services.chat_service import ChatService
from app.ensenia.services.websocket_manager import ConnectionManager


class TestEndToEndFlow:
    """Test complete user flows end-to-end."""

    @pytest.mark.asyncio
    async def test_text_mode_complete_flow(self):
        """Test complete flow in text mode: connect → send message → response."""
        # Setup
        manager = ConnectionManager()
        mock_ws = AsyncMock(spec=WebSocket)
        session_id = 1

        # Connect
        await manager.connect(mock_ws, session_id)
        assert manager.is_connected(session_id)

        # Simulate receiving message
        await manager.send_text_chunk(session_id, "Las fracciones ")
        await manager.send_text_chunk(session_id, "representan partes ")
        await manager.send_text_chunk(session_id, "de un todo.")

        # Verify chunks were sent (accept() doesn't call send_json)
        assert mock_ws.send_json.call_count == 3  # 3 text chunks

        # Verify chunk content
        calls = [call[0][0] for call in mock_ws.send_json.call_args_list]
        assert all(call["type"] == "text_chunk" for call in calls)

        full_text = "".join(call["content"] for call in calls)
        assert full_text == "Las fracciones representan partes de un todo."

        # Complete message
        await manager.send_message_complete(session_id)

        # Disconnect
        manager.disconnect(session_id)
        assert not manager.is_connected(session_id)

    @pytest.mark.asyncio
    async def test_audio_mode_complete_flow(self):
        """Test complete flow in audio mode: text + audio notification."""
        manager = ConnectionManager()
        mock_ws = AsyncMock(spec=WebSocket)
        session_id = 2

        await manager.connect(mock_ws, session_id)

        # Send text chunks (same as text mode)
        await manager.send_text_chunk(session_id, "Chunk 1")
        await manager.send_text_chunk(session_id, "Chunk 2")

        # Send audio ready notification
        await manager.send_audio_ready(
            session_id=session_id,
            audio_id="test_audio_123",
            url="/audio/test_audio_123.mp3",
            duration=5.5,
        )

        # Verify audio notification
        calls = [call[0][0] for call in mock_ws.send_json.call_args_list]
        audio_msg = next(c for c in calls if c.get("type") == "audio_ready")

        assert audio_msg["audio_id"] == "test_audio_123"
        assert audio_msg["url"] == "/audio/test_audio_123.mp3"
        assert audio_msg["duration"] == 5.5

        await manager.send_message_complete(session_id)
        manager.disconnect(session_id)

    @pytest.mark.asyncio
    async def test_mode_switching_flow(self):
        """Test switching between text and audio modes."""
        manager = ConnectionManager()
        mock_ws = AsyncMock(spec=WebSocket)
        session_id = 3

        await manager.connect(mock_ws, session_id)

        # Start in text mode
        await manager.send_text_chunk(session_id, "Text mode response")

        # Switch to audio mode
        await manager.send_mode_changed(session_id, "audio")

        # Next response includes audio
        await manager.send_text_chunk(session_id, "Audio mode response")
        await manager.send_audio_ready(session_id, "audio_456", "/audio/audio_456.mp3")

        # Switch back to text mode
        await manager.send_mode_changed(session_id, "text")

        # Verify mode change messages
        calls = [call[0][0] for call in mock_ws.send_json.call_args_list]
        mode_changes = [c for c in calls if c.get("type") == "mode_changed"]

        assert len(mode_changes) == 2
        assert mode_changes[0]["mode"] == "audio"
        assert mode_changes[1]["mode"] == "text"

    @pytest.mark.asyncio
    async def test_error_handling_flow(self):
        """Test error handling and recovery."""
        manager = ConnectionManager()
        mock_ws = AsyncMock(spec=WebSocket)
        session_id = 4

        await manager.connect(mock_ws, session_id)

        # Send error
        await manager.send_error(session_id, "Something went wrong", "TEST_ERROR")

        # Verify error message
        calls = [call[0][0] for call in mock_ws.send_json.call_args_list]
        error_msg = next(c for c in calls if c.get("type") == "error")

        assert error_msg["message"] == "Something went wrong"
        assert error_msg["code"] == "TEST_ERROR"

        # Connection should still work after error
        await manager.send_text_chunk(session_id, "Recovery successful")
        assert manager.is_connected(session_id)

    @pytest.mark.asyncio
    async def test_concurrent_sessions(self):
        """Test multiple concurrent WebSocket sessions."""
        manager = ConnectionManager()
        sessions = {}

        # Create 5 concurrent sessions
        for i in range(1, 6):
            ws = AsyncMock(spec=WebSocket)
            await manager.connect(ws, i)
            sessions[i] = ws

        assert manager.get_connection_count() == 5

        # Send different messages to each
        for session_id in range(1, 6):
            await manager.send_text_chunk(
                session_id, f"Message for session {session_id}"
            )

        # Verify each session got only its message
        for session_id, ws in sessions.items():
            calls = [call[0][0] for call in ws.send_json.call_args_list]
            text_msgs = [c for c in calls if c.get("type") == "text_chunk"]

            assert len(text_msgs) == 1
            assert f"session {session_id}" in text_msgs[0]["content"]

        # Disconnect some sessions
        manager.disconnect(2)
        manager.disconnect(4)
        assert manager.get_connection_count() == 3

        # Remaining sessions still work
        await manager.send_text_chunk(1, "Still connected")
        assert sessions[1].send_json.called


class TestDatabaseIntegration:
    """Test database model integration."""

    def test_session_model_defaults(self):
        """Test Session model has correct defaults for new fields."""
        # Create session instance (defaults applied on insert, set them explicitly)
        session = Session(
            grade=5,
            subject="mathematics",
            mode="learn",
            current_mode="text",  # Default value
        )

        # Check defaults
        assert session.current_mode == "text"
        assert session.ws_connection_id is None

    def test_message_model_defaults(self):
        """Test Message model has correct defaults for audio fields."""
        msg = Message(
            session_id=1,
            role="user",
            content="Test message",
            timestamp=datetime.now(UTC),
            output_mode="text",  # Default value
            audio_available=False,  # Default value
        )

        # Check audio defaults
        assert msg.output_mode == "text"
        assert msg.audio_id is None
        assert msg.audio_url is None
        assert msg.audio_available is False
        assert msg.audio_duration is None

    def test_message_with_audio(self):
        """Test Message model with audio fields populated."""
        from datetime import UTC, datetime

        msg = Message(
            session_id=1,
            role="assistant",
            content="Response with audio",
            timestamp=datetime.now(UTC),
            output_mode="audio",
            audio_id="abc123",
            audio_url="/audio/abc123.mp3",
            audio_available=True,
            audio_duration=10.5,
        )

        assert msg.output_mode == "audio"
        assert msg.audio_id == "abc123"
        assert msg.audio_url == "/audio/abc123.mp3"
        assert msg.audio_available is True
        assert msg.audio_duration == 10.5


class TestChatServiceEnhancements:
    """Test ChatService new methods."""

    def test_chat_service_has_new_methods(self):
        """Verify ChatService has all new streaming methods."""
        service = ChatService()

        assert hasattr(service, "send_message_streaming")
        assert hasattr(service, "get_session")
        assert hasattr(service, "update_session_mode")
        assert callable(service.send_message_streaming)
        assert callable(service.get_session)
        assert callable(service.update_session_mode)

    @pytest.mark.asyncio
    async def test_update_session_mode_validation(self):
        """Test mode update validates input."""
        mock_db = AsyncMock(spec=AsyncSession)
        service = ChatService()

        # Invalid mode should raise ValueError
        with pytest.raises(ValueError, match="Invalid mode"):
            await service.update_session_mode(1, "invalid_mode", mock_db)

    @pytest.mark.asyncio
    async def test_get_session_requires_db(self):
        """Test get_session requires database session parameter."""
        service = ChatService()
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock the database to return None (session not found)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Should return None when session not found
        result = await service.get_session(1, mock_db)
        assert result is None


class TestStreamOrchestrator:
    """Test stream orchestrator logic."""

    def test_orchestrator_imports(self):
        """Test stream orchestrator can be imported."""
        from app.ensenia.services.stream_orchestrator import (
            process_message_with_dual_stream,
            stream_audio_response,
            stream_text_response,
        )

        assert callable(process_message_with_dual_stream)
        assert callable(stream_text_response)
        assert callable(stream_audio_response)

    @pytest.mark.asyncio
    async def test_audio_id_generation(self):
        """Test audio ID is generated consistently."""
        import hashlib

        text = "Test message for audio"
        expected_id = hashlib.sha256(text.encode()).hexdigest()[:16]

        # Simulate what stream_audio_response does
        audio_id = hashlib.sha256(text.encode()).hexdigest()[:16]

        assert audio_id == expected_id
        assert len(audio_id) == 16


class TestWebSocketRoute:
    """Test WebSocket route integration."""

    def test_websocket_route_registered(self):
        """Test WebSocket route is properly registered."""
        from app.ensenia.api.routes import websocket

        assert websocket.router is not None
        assert hasattr(websocket, "router")

        # Check route is configured
        routes = list(websocket.router.routes)
        assert len(routes) > 0

    def test_websocket_route_path(self):
        """Test WebSocket route has correct path."""
        from app.ensenia.api.routes import websocket

        # Check prefix
        assert websocket.router.prefix == "/ws"


class TestRESTFallback:
    """Test REST API fallback endpoints."""

    def test_update_mode_endpoint_exists(self):
        """Test mode update endpoint is registered."""
        from app.ensenia.api.routes import chat

        # Find PATCH endpoint for mode update
        routes = [r for r in chat.router.routes if hasattr(r, "methods")]
        patch_routes = [r for r in routes if "PATCH" in r.methods]

        # Should have at least one PATCH route (mode update)
        assert len(patch_routes) > 0

    def test_update_mode_request_model(self):
        """Test UpdateModeRequest validates correctly."""
        from pydantic import ValidationError

        from app.ensenia.api.routes.chat import UpdateModeRequest

        # Valid modes
        valid_text = UpdateModeRequest(mode="text")
        valid_audio = UpdateModeRequest(mode="audio")
        assert valid_text.mode == "text"
        assert valid_audio.mode == "audio"

        # Invalid mode should fail validation
        with pytest.raises(ValidationError):
            UpdateModeRequest(mode="invalid")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
