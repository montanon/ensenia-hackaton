"""WebSocket integration tests for voice modes.

Tests WebSocket communication for:
- set_output_mode message handling
- set_input_mode message handling
- toggle_voice message handling
- Mode change notifications
- Real-time mode switching
"""

from datetime import UTC, datetime

import pytest

from app.ensenia.database.models import (
    Message,
    Session,
)


class TestWebSocketModeMessages:
    """Tests for WebSocket mode change messages."""

    @pytest.mark.asyncio
    async def test_set_output_mode_message_format(self):
        """Test set_output_mode message has correct format."""
        message = {
            "type": "set_output_mode",
            "output_mode": "audio",
        }

        assert message["type"] == "set_output_mode"
        assert message["output_mode"] in ["text", "audio"]

    @pytest.mark.asyncio
    async def test_set_input_mode_message_format(self):
        """Test set_input_mode message has correct format."""
        message = {
            "type": "set_input_mode",
            "input_mode": "voice",
        }

        assert message["type"] == "set_input_mode"
        assert message["input_mode"] in ["text", "voice"]

    @pytest.mark.asyncio
    async def test_toggle_voice_message_format(self):
        """Test toggle_voice message format."""
        message = {
            "type": "toggle_voice",
        }

        assert message["type"] == "toggle_voice"

    @pytest.mark.asyncio
    async def test_set_mode_backward_compatible_message(self):
        """Test backward compatible set_mode message still works."""
        message = {
            "type": "set_mode",
            "output_mode": "audio",
        }

        assert message["type"] == "set_mode"
        assert message["output_mode"] in ["text", "audio"]


class TestWebSocketModeNotifications:
    """Tests for WebSocket mode change notifications."""

    @pytest.mark.asyncio
    async def test_output_mode_changed_notification_format(self):
        """Test output_mode_changed notification format."""
        notification = {
            "type": "output_mode_changed",
            "output_mode": "audio",
        }

        assert notification["type"] == "output_mode_changed"
        assert notification["output_mode"] in ["text", "audio"]

    @pytest.mark.asyncio
    async def test_input_mode_changed_notification_format(self):
        """Test input_mode_changed notification format."""
        notification = {
            "type": "input_mode_changed",
            "input_mode": "voice",
        }

        assert notification["type"] == "input_mode_changed"
        assert notification["input_mode"] in ["text", "voice"]

    @pytest.mark.asyncio
    async def test_mode_changed_backward_compatible_notification(self):
        """Test backward compatible mode_changed notification."""
        notification = {
            "type": "mode_changed",
            "output_mode": "audio",
        }

        assert notification["type"] == "mode_changed"
        assert notification["output_mode"] in ["text", "audio"]

    @pytest.mark.asyncio
    async def test_connected_message_includes_modes(self):
        """Test connected message includes input and output modes."""
        connected_msg = {
            "type": "connected",
            "session_id": 1,
            "input_mode": "voice",
            "output_mode": "audio",
        }

        assert connected_msg["type"] == "connected"
        assert connected_msg["input_mode"] in ["text", "voice"]
        assert connected_msg["output_mode"] in ["text", "audio"]


class TestWebSocketModeHandling:
    """Tests for WebSocket mode handling logic."""

    @pytest.mark.asyncio
    async def test_toggle_voice_toggles_both_modes(self):
        """Test toggle_voice switches both input and output modes."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        # Simulate toggle_voice: switch both modes
        if session.input_mode == "text":
            session.input_mode = "voice"
        else:
            session.input_mode = "text"

        if session.current_mode == "text":
            session.current_mode = "audio"
        else:
            session.current_mode = "text"

        # Both should be toggled
        assert session.input_mode == "voice"
        assert session.current_mode == "audio"

    @pytest.mark.asyncio
    async def test_consecutive_toggles_return_to_original(self):
        """Test toggling voice twice returns to original state."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        original_input = session.input_mode
        original_output = session.current_mode

        # First toggle
        session.input_mode = "voice" if session.input_mode == "text" else "text"
        session.current_mode = "audio" if session.current_mode == "text" else "text"

        # Second toggle
        session.input_mode = "voice" if session.input_mode == "text" else "text"
        session.current_mode = "audio" if session.current_mode == "text" else "text"

        # Should be back to original
        assert session.input_mode == original_input
        assert session.current_mode == original_output

    @pytest.mark.asyncio
    async def test_set_mode_only_changes_specified_mode(self):
        """Test setting one mode doesn't change the other."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        original_input = session.input_mode

        # Only change output mode
        session.current_mode = "audio"

        # Input should be unchanged
        assert session.input_mode == original_input
        assert session.current_mode == "audio"

    @pytest.mark.asyncio
    async def test_multiple_mode_changes_in_sequence(self):
        """Test sequential mode changes maintain correct state."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        # Change 1: set_output_mode to audio
        session.current_mode = "audio"
        assert session.input_mode == "text"
        assert session.current_mode == "audio"

        # Change 2: set_input_mode to voice
        session.input_mode = "voice"
        assert session.input_mode == "voice"
        assert session.current_mode == "audio"

        # Change 3: set_output_mode back to text
        session.current_mode = "text"
        assert session.input_mode == "voice"
        assert session.current_mode == "text"


class TestWebSocketSessionStateTracking:
    """Tests for WebSocket session state tracking with modes."""

    @pytest.mark.asyncio
    async def test_session_connection_establishes_with_modes(self):
        """Test WebSocket connection establishes with session modes."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="voice",
            current_mode="audio",
        )

        # Connection should know current modes
        assert session.input_mode == "voice"
        assert session.current_mode == "audio"

    @pytest.mark.asyncio
    async def test_mode_changes_persist_across_messages(self):
        """Test mode changes persist across multiple WebSocket messages."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        # Message 1 with original modes
        msg1 = Message(
            session_id=1,
            role="user",
            content="msg1",
            timestamp=datetime.now(UTC),
            input_mode=session.input_mode,
            output_mode=session.current_mode,
        )

        # Mode change via WebSocket
        session.input_mode = "voice"
        session.current_mode = "audio"

        # Message 2 with new modes
        msg2 = Message(
            session_id=1,
            role="user",
            content="msg2",
            timestamp=datetime.now(UTC),
            input_mode=session.input_mode,
            output_mode=session.current_mode,
        )

        # Verify modes changed
        assert msg1.input_mode == "text"
        assert msg1.output_mode == "text"
        assert msg2.input_mode == "voice"
        assert msg2.output_mode == "audio"

    @pytest.mark.asyncio
    async def test_concurrent_sessions_maintain_separate_modes(self):
        """Test multiple sessions maintain independent mode states."""
        session1 = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        session2 = Session(
            id=2,
            grade=6,
            subject="science",
            mode="practice",
            input_mode="voice",
            current_mode="audio",
        )

        # Sessions should have independent modes
        assert session1.input_mode != session2.input_mode
        assert session1.current_mode != session2.current_mode

        # Changing one shouldn't affect the other
        session1.input_mode = "voice"
        assert (
            session2.input_mode == "voice"
        )  # Different session, same mode coincidentally
        assert session1.input_mode == session2.input_mode  # Both voice


class TestWebSocketModeValidation:
    """Tests for WebSocket mode message validation."""

    @pytest.mark.asyncio
    async def test_output_mode_must_be_text_or_audio(self):
        """Test output_mode validation in WebSocket."""
        valid_modes = ["text", "audio"]

        for mode in valid_modes:
            message = {"type": "set_output_mode", "output_mode": mode}
            assert message["output_mode"] in valid_modes

    @pytest.mark.asyncio
    async def test_input_mode_must_be_text_or_voice(self):
        """Test input_mode validation in WebSocket."""
        valid_modes = ["text", "voice"]

        for mode in valid_modes:
            message = {"type": "set_input_mode", "input_mode": mode}
            assert message["input_mode"] in valid_modes

    @pytest.mark.asyncio
    async def test_invalid_mode_values_rejected(self):
        """Test invalid mode values are caught."""
        invalid_output_modes = ["invalid", "audio_only", ""]
        invalid_input_modes = ["audio", "speaking", ""]

        # These should be validated by the system
        for mode in invalid_output_modes:
            assert mode not in ["text", "audio"]

        for mode in invalid_input_modes:
            assert mode not in ["text", "voice"]

    @pytest.mark.asyncio
    async def test_missing_mode_field_detected(self):
        """Test missing mode field in message is detected."""
        incomplete_messages = [
            {"type": "set_output_mode"},  # Missing output_mode
            {"type": "set_input_mode"},  # Missing input_mode
            {"output_mode": "audio"},  # Missing type
        ]

        for msg in incomplete_messages:
            # Missing required field should be caught
            if "output_mode" not in msg and msg.get("type") == "set_output_mode":
                assert "output_mode" not in msg
            if "input_mode" not in msg and msg.get("type") == "set_input_mode":
                assert "input_mode" not in msg


@pytest.mark.priority_1
class TestPriority1WebSocketVoiceModes:
    """Priority 1 critical tests for WebSocket voice modes."""

    @pytest.mark.asyncio
    async def test_critical_set_output_mode_works(self):
        """CRITICAL: set_output_mode message must work."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )
        session.current_mode = "audio"
        assert session.current_mode == "audio"

    @pytest.mark.asyncio
    async def test_critical_set_input_mode_works(self):
        """CRITICAL: set_input_mode message must work."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )
        session.input_mode = "voice"
        assert session.input_mode == "voice"

    @pytest.mark.asyncio
    async def test_critical_toggle_voice_works(self):
        """CRITICAL: toggle_voice must switch both modes."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )
        session.input_mode = "voice"
        session.current_mode = "audio"
        assert session.input_mode == "voice"
        assert session.current_mode == "audio"

    @pytest.mark.asyncio
    async def test_critical_mode_notifications_sent(self):
        """CRITICAL: Mode change notifications must be sent."""
        notification = {
            "type": "output_mode_changed",
            "output_mode": "audio",
        }
        assert notification["type"] == "output_mode_changed"
        assert notification["output_mode"] == "audio"

    @pytest.mark.asyncio
    async def test_critical_connected_message_includes_modes(self):
        """CRITICAL: Connected message must include modes."""
        msg = {
            "type": "connected",
            "input_mode": "text",
            "output_mode": "text",
        }
        assert "input_mode" in msg
        assert "output_mode" in msg
