"""Integration test for WebSocket dual-stream functionality.

Tests the text/audio mode switching without requiring a running server.
"""

from unittest.mock import AsyncMock

import pytest

from app.ensenia.services.websocket_manager import ConnectionManager


class TestWebSocketManager:
    """Test WebSocket connection manager."""

    def test_connection_manager_initialization(self):
        """Test that connection manager initializes correctly."""
        manager = ConnectionManager()
        assert manager.active_connections == {}
        assert manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_connect_websocket(self):
        """Test WebSocket connection registration."""
        manager = ConnectionManager()
        mock_websocket = AsyncMock()

        await manager.connect(mock_websocket, session_id=1)

        assert manager.is_connected(1)
        assert manager.get_connection_count() == 1
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_websocket(self):
        """Test WebSocket disconnection."""
        manager = ConnectionManager()
        mock_websocket = AsyncMock()

        await manager.connect(mock_websocket, session_id=1)
        manager.disconnect(1)

        assert not manager.is_connected(1)
        assert manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_send_text_chunk(self):
        """Test sending text chunks via WebSocket."""
        manager = ConnectionManager()
        mock_websocket = AsyncMock()

        await manager.connect(mock_websocket, session_id=1)
        await manager.send_text_chunk(1, "Hello world")

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "text_chunk"
        assert call_args["content"] == "Hello world"

    @pytest.mark.asyncio
    async def test_send_audio_ready(self):
        """Test audio ready notification."""
        manager = ConnectionManager()
        mock_websocket = AsyncMock()

        await manager.connect(mock_websocket, session_id=1)
        await manager.send_audio_ready(
            session_id=1, audio_id="test123", url="/audio/test123.mp3", duration=10.5
        )

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "audio_ready"
        assert call_args["audio_id"] == "test123"
        assert call_args["url"] == "/audio/test123.mp3"
        assert call_args["duration"] == 10.5

    @pytest.mark.asyncio
    async def test_send_mode_changed(self):
        """Test mode change notification."""
        manager = ConnectionManager()
        mock_websocket = AsyncMock()

        await manager.connect(mock_websocket, session_id=1)
        await manager.send_mode_changed(1, "audio")

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "mode_changed"
        assert call_args["mode"] == "audio"

    @pytest.mark.asyncio
    async def test_send_error(self):
        """Test error message sending."""
        manager = ConnectionManager()
        mock_websocket = AsyncMock()

        await manager.connect(mock_websocket, session_id=1)
        await manager.send_error(1, "Something went wrong", "ERROR_CODE")

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["message"] == "Something went wrong"
        assert call_args["code"] == "ERROR_CODE"

    @pytest.mark.asyncio
    async def test_multiple_connections(self):
        """Test managing multiple WebSocket connections."""
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()

        await manager.connect(ws1, session_id=1)
        await manager.connect(ws2, session_id=2)
        await manager.connect(ws3, session_id=3)

        assert manager.get_connection_count() == 3
        assert manager.is_connected(1)
        assert manager.is_connected(2)
        assert manager.is_connected(3)

        manager.disconnect(2)

        assert manager.get_connection_count() == 2
        assert not manager.is_connected(2)

    @pytest.mark.asyncio
    async def test_send_to_disconnected_session_raises_error(self):
        """Test that sending to disconnected session raises KeyError."""
        manager = ConnectionManager()

        with pytest.raises(KeyError):
            await manager.send_text_chunk(999, "This should fail")


class TestDatabaseModels:
    """Test database model changes."""

    def test_session_model_has_audio_fields(self):
        """Verify Session model has new audio/WebSocket fields."""
        from app.ensenia.database.models import Session

        # Check that new fields exist
        assert hasattr(Session, "current_mode")
        assert hasattr(Session, "ws_connection_id")

    def test_message_model_has_audio_fields(self):
        """Verify Message model has new audio fields."""
        from app.ensenia.database.models import Message

        # Check that new fields exist
        assert hasattr(Message, "output_mode")
        assert hasattr(Message, "audio_id")
        assert hasattr(Message, "audio_url")
        assert hasattr(Message, "audio_available")
        assert hasattr(Message, "audio_duration")


def test_imports():
    """Test that all new modules can be imported successfully."""
    # Test WebSocket route import
    from app.ensenia.api.routes import websocket

    assert websocket.router is not None

    # Test WebSocket manager import
    from app.ensenia.services.websocket_manager import connection_manager

    assert connection_manager is not None

    # Test stream orchestrator import
    from app.ensenia.services.stream_orchestrator import (
        process_message_with_dual_stream,
    )

    assert process_message_with_dual_stream is not None

    # Test ChatService has new methods
    from app.ensenia.services.chat_service import ChatService

    service = ChatService()
    assert hasattr(service, "send_message_streaming")
    assert hasattr(service, "update_session_mode")
    assert hasattr(service, "get_session")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
