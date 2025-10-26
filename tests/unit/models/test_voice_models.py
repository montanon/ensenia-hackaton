"""Unit tests for voice-enabled database models.

Tests for:
- InputMode enum with TEXT and VOICE values
- OutputMode enum with TEXT and AUDIO values
- Session model with input_mode and current_mode fields
- Message model with input_mode and output_mode fields
- Backward compatibility with existing models

Test categories:
1. InputMode and OutputMode enums
2. Session model voice fields
3. Message model voice fields
4. Relationships and defaults
5. Data validation
"""

from datetime import UTC, datetime

import pytest

from app.ensenia.database.models import (
    InputMode,
    Message,
    OutputMode,
    Session,
)


class TestInputModeEnum:
    """Tests for InputMode enumeration."""

    def test_input_mode_text_value(self):
        """Test InputMode.TEXT has correct value."""
        assert InputMode.TEXT.value == "text"

    def test_input_mode_voice_value(self):
        """Test InputMode.VOICE has correct value."""
        assert InputMode.VOICE.value == "voice"

    def test_input_mode_enum_members(self):
        """Test InputMode has exactly 2 members."""
        members = list(InputMode)
        assert len(members) == 2
        assert InputMode.TEXT in members
        assert InputMode.VOICE in members

    def test_input_mode_string_conversion(self):
        """Test InputMode can be converted to string."""
        assert str(InputMode.TEXT) == "InputMode.TEXT"
        assert str(InputMode.VOICE) == "InputMode.VOICE"

    def test_input_mode_from_value(self):
        """Test creating InputMode from string value."""
        assert InputMode("text") == InputMode.TEXT
        assert InputMode("voice") == InputMode.VOICE

    def test_input_mode_invalid_value(self):
        """Test InputMode raises error for invalid value."""
        with pytest.raises(ValueError):
            InputMode("invalid")


class TestOutputModeEnum:
    """Tests for OutputMode enumeration."""

    def test_output_mode_text_value(self):
        """Test OutputMode.TEXT has correct value."""
        assert OutputMode.TEXT.value == "text"

    def test_output_mode_audio_value(self):
        """Test OutputMode.AUDIO has correct value."""
        assert OutputMode.AUDIO.value == "audio"

    def test_output_mode_enum_members(self):
        """Test OutputMode has exactly 2 members."""
        members = list(OutputMode)
        assert len(members) == 2
        assert OutputMode.TEXT in members
        assert OutputMode.AUDIO in members

    def test_output_mode_string_conversion(self):
        """Test OutputMode can be converted to string."""
        assert str(OutputMode.TEXT) == "OutputMode.TEXT"
        assert str(OutputMode.AUDIO) == "OutputMode.AUDIO"

    def test_output_mode_from_value(self):
        """Test creating OutputMode from string value."""
        assert OutputMode("text") == OutputMode.TEXT
        assert OutputMode("audio") == OutputMode.AUDIO

    def test_output_mode_invalid_value(self):
        """Test OutputMode raises error for invalid value."""
        with pytest.raises(ValueError):
            OutputMode("invalid")


class TestSessionVoiceModes:
    """Tests for Session model voice mode fields."""

    def test_session_input_mode_default_text(self):
        """Test Session input_mode defaults to TEXT."""
        session = Session(grade=5, subject="mathematics", mode="learn")
        assert session.input_mode == InputMode.TEXT.value
        assert session.input_mode == "text"

    def test_session_output_mode_default_text(self):
        """Test Session current_mode defaults to TEXT."""
        session = Session(grade=5, subject="mathematics", mode="learn")
        assert session.current_mode == OutputMode.TEXT.value
        assert session.current_mode == "text"

    def test_session_input_mode_set_voice(self):
        """Test Session input_mode can be set to VOICE."""
        session = Session(
            grade=5, subject="mathematics", mode="learn", input_mode="voice"
        )
        assert session.input_mode == "voice"

    def test_session_output_mode_set_audio(self):
        """Test Session current_mode can be set to AUDIO."""
        session = Session(
            grade=5, subject="mathematics", mode="learn", current_mode="audio"
        )
        assert session.current_mode == "audio"

    def test_session_independent_modes(self):
        """Test input and output modes are independent."""
        session = Session(
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="voice",
            current_mode="audio",
        )
        assert session.input_mode == "voice"
        assert session.current_mode == "audio"

    def test_session_all_voice_modes_combinations(self):
        """Test all 4 voice mode combinations possible."""
        # TTT: text in, text out
        session_ttt = Session(
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )
        assert session_ttt.input_mode == "text"
        assert session_ttt.current_mode == "text"

        # TTA: text in, audio out
        session_tta = Session(
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="text",
            current_mode="audio",
        )
        assert session_tta.input_mode == "text"
        assert session_tta.current_mode == "audio"

        # VTT: voice in, text out
        session_vtt = Session(
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="voice",
            current_mode="text",
        )
        assert session_vtt.input_mode == "voice"
        assert session_vtt.current_mode == "text"

        # VVA: voice in, audio out
        session_vva = Session(
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="voice",
            current_mode="audio",
        )
        assert session_vva.input_mode == "voice"
        assert session_vva.current_mode == "audio"


class TestMessageVoiceModes:
    """Tests for Message model voice mode fields."""

    def test_message_input_mode_default_text(self):
        """Test Message input_mode defaults to TEXT."""
        message = Message(
            session_id=1, role="user", content="Hello", timestamp=datetime.now(UTC)
        )
        assert message.input_mode == InputMode.TEXT.value
        assert message.input_mode == "text"

    def test_message_output_mode_default_text(self):
        """Test Message output_mode defaults to TEXT."""
        message = Message(
            session_id=1, role="assistant", content="Hello", timestamp=datetime.now(UTC)
        )
        assert message.output_mode == OutputMode.TEXT.value
        assert message.output_mode == "text"

    def test_message_input_mode_set_voice(self):
        """Test Message input_mode can be set to VOICE."""
        message = Message(
            session_id=1,
            role="user",
            content="[audio data]",
            timestamp=datetime.now(UTC),
            input_mode="voice",
        )
        assert message.input_mode == "voice"

    def test_message_output_mode_set_audio(self):
        """Test Message output_mode can be set to AUDIO."""
        message = Message(
            session_id=1,
            role="assistant",
            content="Hello",
            timestamp=datetime.now(UTC),
            output_mode="audio",
            audio_id="hash123",
            audio_available=True,
        )
        assert message.output_mode == "audio"
        assert message.audio_id == "hash123"
        assert message.audio_available is True

    def test_message_independent_input_output_modes(self):
        """Test message input and output modes are independent."""
        message = Message(
            session_id=1,
            role="user",
            content="[audio data]",
            timestamp=datetime.now(UTC),
            input_mode="voice",
            output_mode="audio",
        )
        assert message.input_mode == "voice"
        assert message.output_mode == "audio"

    def test_message_audio_fields_with_audio_mode(self):
        """Test message audio fields properly set with audio output."""
        message = Message(
            session_id=1,
            role="assistant",
            content="Test response",
            timestamp=datetime.now(UTC),
            output_mode="audio",
            audio_id="abc123def456",
            audio_url="https://cdn.example.com/audio/abc123def456.mp3",
            audio_available=True,
            audio_duration=5.5,
        )
        assert message.output_mode == "audio"
        assert message.audio_id == "abc123def456"
        assert message.audio_url == "https://cdn.example.com/audio/abc123def456.mp3"
        assert message.audio_available is True
        assert message.audio_duration == 5.5


class TestSessionMessageRelationship:
    """Tests for Session and Message relationship with voice modes."""

    def test_session_has_messages_relationship(self):
        """Test Session has messages relationship."""
        session = Session(grade=5, subject="mathematics", mode="learn")
        assert hasattr(session, "messages")
        assert session.messages == []

    def test_message_references_session(self):
        """Test Message references Session."""
        session = Session(grade=5, subject="mathematics", mode="learn")
        message = Message(
            session_id=1, role="user", content="Hello", timestamp=datetime.now(UTC)
        )
        assert message.session_id == 1
        assert hasattr(message, "session")


class TestVoiceModeAuditTrail:
    """Tests for voice mode audit trail functionality."""

    def test_message_input_mode_tracks_user_input_method(self):
        """Test message input_mode tracks how user sent message."""
        text_message = Message(
            session_id=1,
            role="user",
            content="What is photosynthesis?",
            timestamp=datetime.now(UTC),
            input_mode="text",
        )
        assert text_message.input_mode == "text"

        voice_message = Message(
            session_id=1,
            role="user",
            content="[transcribed voice]",
            timestamp=datetime.now(UTC),
            input_mode="voice",
        )
        assert voice_message.input_mode == "voice"

    def test_message_output_mode_tracks_response_delivery(self):
        """Test message output_mode tracks how response was delivered."""
        text_response = Message(
            session_id=1,
            role="assistant",
            content="Photosynthesis is...",
            timestamp=datetime.now(UTC),
            output_mode="text",
        )
        assert text_response.output_mode == "text"
        assert text_response.audio_available is False

        audio_response = Message(
            session_id=1,
            role="assistant",
            content="Photosynthesis is...",
            timestamp=datetime.now(UTC),
            output_mode="audio",
            audio_id="response123",
            audio_available=True,
            audio_duration=4.2,
        )
        assert audio_response.output_mode == "audio"
        assert audio_response.audio_available is True


class TestVoiceModeRepresentations:
    """Tests for string representations with voice modes."""

    def test_session_repr_includes_mode_info(self):
        """Test Session __repr__ includes basic mode info."""
        session = Session(id=1, grade=5, subject="mathematics", mode="learn")
        repr_str = repr(session)
        assert "Session" in repr_str
        assert "id=1" in repr_str
        assert "mode=learn" in repr_str

    def test_message_repr_includes_basic_info(self):
        """Test Message __repr__ includes basic info."""
        message = Message(
            id=1,
            session_id=1,
            role="user",
            content="Hello",
            timestamp=datetime.now(UTC),
        )
        repr_str = repr(message)
        assert "Message" in repr_str
        assert "id=1" in repr_str
        assert "session_id=1" in repr_str


@pytest.mark.priority_1
class TestPriority1VoiceModels:
    """Priority 1 critical tests for voice models."""

    async def test_critical_input_mode_enum_exists(self):
        """CRITICAL: InputMode enum must exist and be accessible."""
        assert InputMode is not None
        assert hasattr(InputMode, "TEXT")
        assert hasattr(InputMode, "VOICE")

    async def test_critical_output_mode_enum_exists(self):
        """CRITICAL: OutputMode enum must exist and be accessible."""
        assert OutputMode is not None
        assert hasattr(OutputMode, "TEXT")
        assert hasattr(OutputMode, "AUDIO")

    async def test_critical_session_has_input_mode_field(self):
        """CRITICAL: Session must have input_mode field."""
        session = Session(grade=5, subject="mathematics", mode="learn")
        assert hasattr(session, "input_mode")

    async def test_critical_session_has_output_mode_field(self):
        """CRITICAL: Session must have current_mode field."""
        session = Session(grade=5, subject="mathematics", mode="learn")
        assert hasattr(session, "current_mode")

    async def test_critical_message_has_input_mode_field(self):
        """CRITICAL: Message must have input_mode field."""
        message = Message(
            session_id=1, role="user", content="test", timestamp=datetime.now(UTC)
        )
        assert hasattr(message, "input_mode")

    async def test_critical_message_has_output_mode_field(self):
        """CRITICAL: Message must have output_mode field."""
        message = Message(
            session_id=1,
            role="assistant",
            content="test",
            timestamp=datetime.now(UTC),
        )
        assert hasattr(message, "output_mode")
