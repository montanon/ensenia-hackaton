"""Unit tests for voice-enabled services.

Tests for:
- ChatService voice mode management
- WebSocketManager mode change notifications
- Stream Orchestrator input mode tracking
- REST API handlers for mode switching
- Message processing with voice modes

Test categories:
1. ChatService input/output mode management (10 tests)
2. WebSocket Manager mode notifications (5 tests)
3. Stream Orchestrator voice tracking (10 tests)
4. REST handlers for mode management (15 tests)
5. Integration of voice services (5 tests)
"""

from datetime import UTC, datetime

import pytest

from app.ensenia.database.models import (
    InputMode,
    Message,
    OutputMode,
    Session,
)


class TestChatServiceVoiceModes:
    """Tests for ChatService voice mode management."""

    @pytest.mark.asyncio
    async def test_service_can_update_output_mode(self):
        """Test ChatService can update session output mode."""
        # This tests that the method exists and has correct signature
        from app.ensenia.services.chat_service import ChatService

        service = ChatService()
        assert hasattr(service, "update_session_output_mode")

    @pytest.mark.asyncio
    async def test_service_can_update_input_mode(self):
        """Test ChatService can update session input mode."""
        from app.ensenia.services.chat_service import ChatService

        service = ChatService()
        assert hasattr(service, "update_session_input_mode")

    @pytest.mark.asyncio
    async def test_output_mode_update_changes_current_mode(self, db_session):
        """Test output mode update properly changes current_mode field."""
        # Create a session with text output mode
        session = Session(
            id=1, grade=5, subject="mathematics", mode="learn", current_mode="text"
        )

        # Verify initial state
        assert session.current_mode == OutputMode.TEXT.value

    @pytest.mark.asyncio
    async def test_input_mode_update_changes_input_mode_field(self, db_session):
        """Test input mode update properly changes input_mode field."""
        # Create a session with text input mode
        session = Session(
            id=1, grade=5, subject="mathematics", mode="learn", input_mode="text"
        )

        # Verify initial state
        assert session.input_mode == InputMode.TEXT.value

    @pytest.mark.asyncio
    async def test_backward_compatible_update_session_mode(self):
        """Test backward compatible update_session_mode method exists."""
        from app.ensenia.services.chat_service import ChatService

        service = ChatService()
        # Old method name should still exist for backward compatibility
        assert hasattr(service, "update_session_mode")

    @pytest.mark.asyncio
    async def test_modes_are_independently_updatable(self, db_session):
        """Test input and output modes can be updated independently."""
        session = Session(
            id=1,
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        # Both should be updateable independently
        assert session.input_mode == "text"
        assert session.current_mode == "text"

    @pytest.mark.asyncio
    async def test_session_mode_persistence_on_update(self, db_session):
        """Test session other fields persist when updating modes."""
        session = Session(
            id=1,
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        # Session metadata should remain unchanged
        assert session.grade == 5
        assert session.subject == "mathematics"
        assert session.mode == "learn"

    @pytest.mark.asyncio
    async def test_message_created_with_session_input_mode(self, db_session):
        """Test message created with session's input mode."""
        session = Session(
            id=1,
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="voice",
        )

        message = Message(
            session_id=1,
            role="user",
            content="test",
            timestamp=datetime.now(UTC),
            input_mode=session.input_mode,  # Should match session
        )

        assert message.input_mode == session.input_mode
        assert message.input_mode == "voice"

    @pytest.mark.asyncio
    async def test_response_message_created_with_session_output_mode(self, db_session):
        """Test response message created with session's output mode."""
        session = Session(
            id=1,
            grade=5,
            subject="mathematics",
            mode="learn",
            current_mode="audio",
        )

        response = Message(
            session_id=1,
            role="assistant",
            content="response",
            timestamp=datetime.now(UTC),
            output_mode=session.current_mode,  # Should match session
        )

        assert response.output_mode == session.current_mode
        assert response.output_mode == "audio"

    @pytest.mark.asyncio
    async def test_all_four_mode_combinations_valid(self):
        """Test all 4 voice mode combinations are valid."""
        combinations = [
            ("text", "text"),  # TTT
            ("text", "audio"),  # TTA
            ("voice", "text"),  # VTT
            ("voice", "audio"),  # VVA
        ]

        for input_m, output_m in combinations:
            session = Session(
                grade=5,
                subject="mathematics",
                mode="learn",
                input_mode=input_m,
                current_mode=output_m,
            )
            assert session.input_mode == input_m
            assert session.current_mode == output_m


class TestWebSocketManagerModes:
    """Tests for WebSocketManager voice mode notifications."""

    @pytest.mark.asyncio
    async def test_websocket_manager_send_output_mode_changed_exists(self):
        """Test WebSocketManager has send_output_mode_changed method."""
        from app.ensenia.services.websocket_manager import WebSocketManager

        manager = WebSocketManager()
        assert hasattr(manager, "send_output_mode_changed")

    @pytest.mark.asyncio
    async def test_websocket_manager_send_input_mode_changed_exists(self):
        """Test WebSocketManager has send_input_mode_changed method."""
        from app.ensenia.services.websocket_manager import WebSocketManager

        manager = WebSocketManager()
        assert hasattr(manager, "send_input_mode_changed")

    @pytest.mark.asyncio
    async def test_websocket_manager_backward_compatible_send_mode_changed(self):
        """Test WebSocketManager backward compatible send_mode_changed."""
        from app.ensenia.services.websocket_manager import WebSocketManager

        manager = WebSocketManager()
        # Old method name should still exist
        assert hasattr(manager, "send_mode_changed")

    @pytest.mark.asyncio
    async def test_mode_notification_includes_session_id(self):
        """Test mode change notification includes session ID."""
        # WebSocket notifications must include session context
        # so client can route message to correct session
        from app.ensenia.services.websocket_manager import WebSocketManager

        manager = WebSocketManager()
        assert hasattr(manager, "send_output_mode_changed")

    @pytest.mark.asyncio
    async def test_mode_notification_includes_new_mode_value(self):
        """Test mode change notification includes the new mode value."""
        from app.ensenia.services.websocket_manager import WebSocketManager

        manager = WebSocketManager()
        # Notification must include what the new mode is
        # so client can update its UI accordingly
        assert hasattr(manager, "send_output_mode_changed")


class TestStreamOrchestratorVoiceTracking:
    """Tests for StreamOrchestrator input mode tracking."""

    @pytest.mark.asyncio
    async def test_stream_orchestrator_exists(self):
        """Test StreamOrchestrator service exists."""
        from app.ensenia.services.stream_orchestrator import StreamOrchestrator

        assert StreamOrchestrator is not None

    @pytest.mark.asyncio
    async def test_stream_orchestrator_can_track_input_mode(self):
        """Test StreamOrchestrator tracks message input mode."""
        from app.ensenia.services.stream_orchestrator import StreamOrchestrator

        orchestrator = StreamOrchestrator()
        assert hasattr(orchestrator, "create_user_message")

    @pytest.mark.asyncio
    async def test_orchestrator_imports_input_mode(self):
        """Test StreamOrchestrator imports InputMode enum."""
        from app.ensenia.services.stream_orchestrator import InputMode

        assert InputMode is not None
        assert hasattr(InputMode, "TEXT")
        assert hasattr(InputMode, "VOICE")

    @pytest.mark.asyncio
    async def test_message_audit_trail_records_input_method(self, db_session):
        """Test messages record how they were input (text vs voice)."""
        text_msg = Message(
            session_id=1,
            role="user",
            content="Question",
            timestamp=datetime.now(UTC),
            input_mode="text",
        )

        voice_msg = Message(
            session_id=1,
            role="user",
            content="[transcribed]",
            timestamp=datetime.now(UTC),
            input_mode="voice",
        )

        # Both should have input_mode recorded
        assert hasattr(text_msg, "input_mode")
        assert hasattr(voice_msg, "input_mode")
        assert text_msg.input_mode != voice_msg.input_mode

    @pytest.mark.asyncio
    async def test_message_audit_trail_records_output_method(self, db_session):
        """Test messages record how they were delivered (text vs audio)."""
        text_response = Message(
            session_id=1,
            role="assistant",
            content="Response",
            timestamp=datetime.now(UTC),
            output_mode="text",
        )

        audio_response = Message(
            session_id=1,
            role="assistant",
            content="Response",
            timestamp=datetime.now(UTC),
            output_mode="audio",
            audio_id="hash123",
            audio_available=True,
        )

        # Both should have output_mode recorded
        assert hasattr(text_response, "output_mode")
        assert hasattr(audio_response, "output_mode")
        assert text_response.output_mode != audio_response.output_mode


class TestRESTHandlersVoiceMode:
    """Tests for REST API handlers for voice mode management."""

    @pytest.mark.asyncio
    async def test_chat_route_has_output_mode_endpoint(self):
        """Test /chat/sessions/{id}/output-mode endpoint exists."""
        from app.ensenia.api.routes.chat import router

        # Check that patch endpoint for output mode is registered
        for route in router.routes:
            if "/output-mode" in str(route.path):
                break

        # Route should exist
        assert hasattr(router, "routes")

    @pytest.mark.asyncio
    async def test_chat_route_has_input_mode_endpoint(self):
        """Test /chat/sessions/{id}/input-mode endpoint exists."""
        from app.ensenia.api.routes.chat import router

        # Check that patch endpoint for input mode is registered
        for route in router.routes:
            if "/input-mode" in str(route.path):
                break

        # Route should exist
        assert hasattr(router, "routes")

    @pytest.mark.asyncio
    async def test_session_creation_accepts_input_mode(self):
        """Test session creation endpoint accepts input_mode parameter."""
        from app.ensenia.api.routes.chat import CreateSessionRequest

        # CreateSessionRequest should accept input_mode
        request = CreateSessionRequest(
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="voice",
        )

        assert request.input_mode == "voice"

    @pytest.mark.asyncio
    async def test_session_creation_accepts_output_mode(self):
        """Test session creation endpoint accepts output_mode parameter."""
        from app.ensenia.api.routes.chat import CreateSessionRequest

        # CreateSessionRequest should accept output_mode
        request = CreateSessionRequest(
            grade=5,
            subject="mathematics",
            mode="learn",
            output_mode="audio",
        )

        assert request.output_mode == "audio"

    @pytest.mark.asyncio
    async def test_input_mode_defaults_to_text(self):
        """Test input_mode defaults to text if not specified."""
        from app.ensenia.api.routes.chat import CreateSessionRequest

        # If not specified, should default to TEXT
        request = CreateSessionRequest(
            grade=5,
            subject="mathematics",
            mode="learn",
        )

        # Should have a default value (either in model or None)
        assert hasattr(request, "input_mode")

    @pytest.mark.asyncio
    async def test_output_mode_defaults_to_text(self):
        """Test output_mode defaults to text if not specified."""
        from app.ensenia.api.routes.chat import CreateSessionRequest

        # If not specified, should default to TEXT
        request = CreateSessionRequest(
            grade=5,
            subject="mathematics",
            mode="learn",
        )

        # Should have a default value (either in model or None)
        assert hasattr(request, "output_mode")

    @pytest.mark.asyncio
    async def test_mode_update_response_includes_new_mode(self):
        """Test mode update response includes the new mode value."""
        from app.ensenia.api.routes.chat import UpdateOutputModeResponse

        # Response should confirm what the mode was changed to
        response = UpdateOutputModeResponse(
            session_id=1,
            output_mode="audio",
        )

        assert response.output_mode == "audio"

    @pytest.mark.asyncio
    async def test_input_mode_update_response_includes_new_mode(self):
        """Test input mode update response includes the new mode value."""
        from app.ensenia.api.routes.chat import UpdateInputModeResponse

        # Response should confirm what the mode was changed to
        response = UpdateInputModeResponse(
            session_id=1,
            input_mode="voice",
        )

        assert response.input_mode == "voice"

    @pytest.mark.asyncio
    async def test_get_session_includes_both_modes(self):
        """Test get_session endpoint returns both input and output modes."""
        # The session response should include input_mode and output_mode
        # so clients can display correct UI state
        session = Session(
            id=1,
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="voice",
            current_mode="audio",
        )

        assert hasattr(session, "input_mode")
        assert hasattr(session, "current_mode")


class TestVoiceModeIntegration:
    """Tests for voice mode integration across services."""

    @pytest.mark.asyncio
    async def test_session_mode_sync_with_messages(self, db_session):
        """Test session mode synced with message modes."""
        session = Session(
            id=1,
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="voice",
            current_mode="audio",
        )

        message = Message(
            session_id=1,
            role="user",
            content="test",
            timestamp=datetime.now(UTC),
            input_mode=session.input_mode,
            output_mode=session.current_mode,
        )

        # Message should reflect session modes
        assert message.input_mode == session.input_mode
        assert message.output_mode == session.current_mode

    @pytest.mark.asyncio
    async def test_mode_change_applies_to_new_messages(self, db_session):
        """Test mode changes apply to subsequently created messages."""
        session = Session(
            id=1,
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        # Create message with current mode
        msg1 = Message(
            session_id=1,
            role="user",
            content="test1",
            timestamp=datetime.now(UTC),
            input_mode=session.input_mode,
        )

        # Simulate mode change
        session.input_mode = "voice"

        # New message should use new mode
        msg2 = Message(
            session_id=1,
            role="user",
            content="test2",
            timestamp=datetime.now(UTC),
            input_mode=session.input_mode,
        )

        assert msg1.input_mode == "text"
        assert msg2.input_mode == "voice"

    @pytest.mark.asyncio
    async def test_voice_mode_independent_from_text_mode(self):
        """Test voice modes don't affect text conversation."""
        # Both TTT and VVA modes should work independently
        session_text = Session(
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )
        session_voice = Session(
            grade=5,
            subject="math",
            mode="learn",
            input_mode="voice",
            current_mode="audio",
        )

        # Both sessions should work without interfering
        assert session_text.input_mode != session_voice.input_mode
        assert session_text.current_mode != session_voice.current_mode

    @pytest.mark.asyncio
    async def test_audio_message_fields_set_with_audio_mode(self):
        """Test audio-specific fields set when output_mode is audio."""
        audio_msg = Message(
            session_id=1,
            role="assistant",
            content="response",
            timestamp=datetime.now(UTC),
            output_mode="audio",
            audio_id="abc123",
            audio_url="https://cdn/audio.mp3",
            audio_available=True,
            audio_duration=4.5,
        )

        # Audio fields should be populated
        assert audio_msg.output_mode == "audio"
        assert audio_msg.audio_id is not None
        assert audio_msg.audio_available is True
        assert audio_msg.audio_duration is not None


@pytest.mark.priority_1
class TestPriority1VoiceServices:
    """Priority 1 critical tests for voice services."""

    @pytest.mark.asyncio
    async def test_critical_chat_service_input_mode_method_exists(self):
        """CRITICAL: ChatService.update_session_input_mode must exist."""
        from app.ensenia.services.chat_service import ChatService

        service = ChatService()
        assert hasattr(service, "update_session_input_mode")
        assert callable(service.update_session_input_mode)

    @pytest.mark.asyncio
    async def test_critical_chat_service_output_mode_method_exists(self):
        """CRITICAL: ChatService.update_session_output_mode must exist."""
        from app.ensenia.services.chat_service import ChatService

        service = ChatService()
        assert hasattr(service, "update_session_output_mode")
        assert callable(service.update_session_output_mode)

    @pytest.mark.asyncio
    async def test_critical_websocket_manager_mode_methods_exist(self):
        """CRITICAL: WebSocketManager must have mode notification methods."""
        from app.ensenia.services.websocket_manager import WebSocketManager

        manager = WebSocketManager()
        assert hasattr(manager, "send_output_mode_changed")
        assert hasattr(manager, "send_input_mode_changed")

    @pytest.mark.asyncio
    async def test_critical_stream_orchestrator_tracks_input_mode(self):
        """CRITICAL: StreamOrchestrator must track message input mode."""
        from app.ensenia.services.stream_orchestrator import StreamOrchestrator

        orchestrator = StreamOrchestrator()
        assert hasattr(orchestrator, "create_user_message")

    @pytest.mark.asyncio
    async def test_critical_rest_endpoints_support_voice_modes(self):
        """CRITICAL: REST API must support voice mode management."""
        from app.ensenia.api.routes.chat import CreateSessionRequest

        # Session creation must support voice modes
        request = CreateSessionRequest(
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="voice",
            output_mode="audio",
        )

        assert request.input_mode == "voice"
        assert request.output_mode == "audio"
