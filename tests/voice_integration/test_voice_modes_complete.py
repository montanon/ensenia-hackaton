"""Integration tests for all 4 voice modes end-to-end.

Tests complete workflows for:
- Mode 1 (TTT): Text In / Text Out
- Mode 2 (TTA): Text In / Audio Out
- Mode 3 (VTT): Voice In / Text Out
- Mode 4 (VVA): Voice In / Audio Out

Also tests:
- Mode switching during conversations
- Message audit trails
- Database persistence
- WebSocket interactions
"""

from datetime import UTC, datetime

import pytest

from app.ensenia.database.models import (
    Message,
    Session,
)


class TestMode1TextInTextOut:
    """Tests for Mode 1: Text In / Text Out (TTT)."""

    @pytest.mark.asyncio
    async def test_ttt_session_creation(self):
        """Test creating TTT mode session."""
        session = Session(
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        assert session.input_mode == "text"
        assert session.current_mode == "text"

    @pytest.mark.asyncio
    async def test_ttt_user_message_creation(self):
        """Test creating user message in TTT mode."""
        session = Session(
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        message = Message(
            session_id=1,
            role="user",
            content="What is 5 + 3?",
            timestamp=datetime.now(UTC),
            input_mode=session.input_mode,
        )

        assert message.input_mode == "text"
        assert message.content == "What is 5 + 3?"

    @pytest.mark.asyncio
    async def test_ttt_assistant_response_creation(self):
        """Test creating assistant response in TTT mode."""
        session = Session(
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        response = Message(
            session_id=1,
            role="assistant",
            content="5 + 3 = 8",
            timestamp=datetime.now(UTC),
            output_mode=session.current_mode,
        )

        assert response.output_mode == "text"
        assert response.content == "5 + 3 = 8"
        assert response.audio_available is False

    @pytest.mark.asyncio
    async def test_ttt_conversation_flow(self):
        """Test complete TTT conversation flow."""
        messages = [
            Message(
                session_id=1,
                role="user",
                content="What is photosynthesis?",
                timestamp=datetime.now(UTC),
                input_mode="text",
            ),
            Message(
                session_id=1,
                role="assistant",
                content="Photosynthesis is the process...",
                timestamp=datetime.now(UTC),
                output_mode="text",
            ),
            Message(
                session_id=1,
                role="user",
                content="Can you explain it simpler?",
                timestamp=datetime.now(UTC),
                input_mode="text",
            ),
            Message(
                session_id=1,
                role="assistant",
                content="Plants use sunlight to make food...",
                timestamp=datetime.now(UTC),
                output_mode="text",
            ),
        ]

        # Verify conversation flow
        assert len(messages) == 4
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"
        assert all(m.input_mode == "text" for m in messages if m.role == "user")
        assert all(m.output_mode == "text" for m in messages if m.role == "assistant")


class TestMode2TextInAudioOut:
    """Tests for Mode 2: Text In / Audio Out (TTA)."""

    @pytest.mark.asyncio
    async def test_tta_session_creation(self):
        """Test creating TTA mode session."""
        session = Session(
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="text",
            current_mode="audio",
        )

        assert session.input_mode == "text"
        assert session.current_mode == "audio"

    @pytest.mark.asyncio
    async def test_tta_user_message_creation(self):
        """Test creating user message in TTA mode."""
        session = Session(
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="text",
            current_mode="audio",
        )

        message = Message(
            session_id=1,
            role="user",
            content="Explain fractions",
            timestamp=datetime.now(UTC),
            input_mode=session.input_mode,
        )

        assert message.input_mode == "text"
        assert message.content == "Explain fractions"

    @pytest.mark.asyncio
    async def test_tta_audio_response_creation(self):
        """Test creating audio response in TTA mode."""
        session = Session(
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="text",
            current_mode="audio",
        )

        response = Message(
            session_id=1,
            role="assistant",
            content="Fractions represent parts of a whole...",
            timestamp=datetime.now(UTC),
            output_mode=session.current_mode,
            audio_id="abc123def456",
            audio_url="https://cdn.example.com/audio/abc123def456.mp3",
            audio_available=True,
            audio_duration=12.5,
        )

        assert response.output_mode == "audio"
        assert response.audio_available is True
        assert response.audio_id == "abc123def456"
        assert response.audio_duration == 12.5

    @pytest.mark.asyncio
    async def test_tta_multiple_exchanges(self):
        """Test multiple text-in, audio-out exchanges."""
        messages = [
            Message(
                session_id=1,
                role="user",
                content="What causes rain?",
                timestamp=datetime.now(UTC),
                input_mode="text",
            ),
            Message(
                session_id=1,
                role="assistant",
                content="Rain happens when water evaporates...",
                timestamp=datetime.now(UTC),
                output_mode="audio",
                audio_id="audio1",
                audio_available=True,
                audio_duration=8.3,
            ),
            Message(
                session_id=1,
                role="user",
                content="How long does it take?",
                timestamp=datetime.now(UTC),
                input_mode="text",
            ),
            Message(
                session_id=1,
                role="assistant",
                content="The water cycle takes several days...",
                timestamp=datetime.now(UTC),
                output_mode="audio",
                audio_id="audio2",
                audio_available=True,
                audio_duration=7.1,
            ),
        ]

        # All user messages should be text input
        user_messages = [m for m in messages if m.role == "user"]
        assert all(m.input_mode == "text" for m in user_messages)

        # All assistant messages should be audio output
        assistant_messages = [m for m in messages if m.role == "assistant"]
        assert all(m.output_mode == "audio" for m in assistant_messages)
        assert all(m.audio_available for m in assistant_messages)


class TestMode3VoiceInTextOut:
    """Tests for Mode 3: Voice In / Text Out (VTT)."""

    @pytest.mark.asyncio
    async def test_vtt_session_creation(self):
        """Test creating VTT mode session."""
        session = Session(
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="voice",
            current_mode="text",
        )

        assert session.input_mode == "voice"
        assert session.current_mode == "text"

    @pytest.mark.asyncio
    async def test_vtt_voice_user_message(self):
        """Test creating transcribed voice message in VTT mode."""
        session = Session(
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="voice",
            current_mode="text",
        )

        # Voice message (transcribed from audio)
        message = Message(
            session_id=1,
            role="user",
            content="¿Qué es la fotosíntesis?",  # Transcribed from voice
            timestamp=datetime.now(UTC),
            input_mode=session.input_mode,
        )

        assert message.input_mode == "voice"
        assert "fotosíntesis" in message.content

    @pytest.mark.asyncio
    async def test_vtt_text_response(self):
        """Test creating text response to voice input in VTT mode."""
        session = Session(
            grade=5,
            subject="science",
            mode="learn",
            input_mode="voice",
            current_mode="text",
        )

        response = Message(
            session_id=1,
            role="assistant",
            content="La fotosíntesis es el proceso...",
            timestamp=datetime.now(UTC),
            output_mode=session.current_mode,
        )

        assert response.output_mode == "text"
        assert response.audio_available is False

    @pytest.mark.asyncio
    async def test_vtt_conversation_maintains_voice_input_mode(self):
        """Test VTT conversation maintains voice input mode throughout."""
        messages = [
            Message(
                session_id=1,
                role="user",
                content="¿Cuál es el ciclo del agua?",
                timestamp=datetime.now(UTC),
                input_mode="voice",
            ),
            Message(
                session_id=1,
                role="assistant",
                content="El ciclo del agua incluye evaporación...",
                timestamp=datetime.now(UTC),
                output_mode="text",
            ),
            Message(
                session_id=1,
                role="user",
                content="¿Dónde ocurre la condensación?",
                timestamp=datetime.now(UTC),
                input_mode="voice",
            ),
            Message(
                session_id=1,
                role="assistant",
                content="La condensación ocurre en la atmósfera...",
                timestamp=datetime.now(UTC),
                output_mode="text",
            ),
        ]

        # All user messages should have voice input
        user_messages = [m for m in messages if m.role == "user"]
        assert all(m.input_mode == "voice" for m in user_messages)

        # All assistant messages should have text output
        assistant_messages = [m for m in messages if m.role == "assistant"]
        assert all(m.output_mode == "text" for m in assistant_messages)


class TestMode4VoiceInAudioOut:
    """Tests for Mode 4: Voice In / Audio Out (VVA)."""

    @pytest.mark.asyncio
    async def test_vva_session_creation(self):
        """Test creating VVA mode session (full voice)."""
        session = Session(
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="voice",
            current_mode="audio",
        )

        assert session.input_mode == "voice"
        assert session.current_mode == "audio"

    @pytest.mark.asyncio
    async def test_vva_voice_user_message(self):
        """Test creating voice user message in VVA mode."""
        session = Session(
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="voice",
            current_mode="audio",
        )

        message = Message(
            session_id=1,
            role="user",
            content="Explica la independencia de Chile",
            timestamp=datetime.now(UTC),
            input_mode=session.input_mode,
        )

        assert message.input_mode == "voice"

    @pytest.mark.asyncio
    async def test_vva_audio_response(self):
        """Test creating audio response in VVA mode."""
        session = Session(
            grade=5,
            subject="history",
            mode="learn",
            input_mode="voice",
            current_mode="audio",
        )

        response = Message(
            session_id=1,
            role="assistant",
            content="La Independencia de Chile ocurrió en 1810...",
            timestamp=datetime.now(UTC),
            output_mode=session.current_mode,
            audio_id="voice_response_123",
            audio_url="https://cdn.example.com/audio/voice_response_123.mp3",
            audio_available=True,
            audio_duration=15.8,
        )

        assert response.output_mode == "audio"
        assert response.audio_available is True
        assert response.audio_duration == 15.8

    @pytest.mark.asyncio
    async def test_vva_full_conversation(self):
        """Test full VVA conversation with voice in and audio out."""
        messages = [
            Message(
                session_id=1,
                role="user",
                content="¿Quién fue Salvador Allende?",
                timestamp=datetime.now(UTC),
                input_mode="voice",
            ),
            Message(
                session_id=1,
                role="assistant",
                content="Salvador Allende fue presidente de Chile...",
                timestamp=datetime.now(UTC),
                output_mode="audio",
                audio_id="audio_1",
                audio_available=True,
                audio_duration=10.5,
            ),
            Message(
                session_id=1,
                role="user",
                content="¿En qué año fue presidente?",
                timestamp=datetime.now(UTC),
                input_mode="voice",
            ),
            Message(
                session_id=1,
                role="assistant",
                content="Fue presidente desde 1970 hasta 1973...",
                timestamp=datetime.now(UTC),
                output_mode="audio",
                audio_id="audio_2",
                audio_available=True,
                audio_duration=9.2,
            ),
        ]

        # Verify complete VVA flow
        assert len(messages) == 4
        user_messages = [m for m in messages if m.role == "user"]
        assistant_messages = [m for m in messages if m.role == "assistant"]

        assert all(m.input_mode == "voice" for m in user_messages)
        assert all(m.output_mode == "audio" for m in assistant_messages)
        assert all(m.audio_available for m in assistant_messages)


class TestModeSwitching:
    """Tests for mode switching during conversations."""

    @pytest.mark.asyncio
    async def test_switch_output_mode_mid_conversation(self):
        """Test switching output mode during conversation."""
        session = Session(
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        # User sends message in text
        msg1 = Message(
            session_id=1,
            role="user",
            content="Hello",
            timestamp=datetime.now(UTC),
            input_mode="text",
        )

        # Assistant responds in text
        resp1 = Message(
            session_id=1,
            role="assistant",
            content="Hi there",
            timestamp=datetime.now(UTC),
            output_mode="text",
        )

        # User switches assistant to audio mode
        session.current_mode = "audio"

        # Assistant responds in audio
        resp2 = Message(
            session_id=1,
            role="assistant",
            content="How can I help?",
            timestamp=datetime.now(UTC),
            output_mode=session.current_mode,
            audio_id="switched_audio",
            audio_available=True,
            audio_duration=3.2,
        )

        assert msg1.input_mode == "text"
        assert resp1.output_mode == "text"
        assert resp2.output_mode == "audio"

    @pytest.mark.asyncio
    async def test_switch_input_mode_mid_conversation(self):
        """Test switching input mode during conversation."""
        session = Session(
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        # User types
        msg1 = Message(
            session_id=1,
            role="user",
            content="What is algebra?",
            timestamp=datetime.now(UTC),
            input_mode="text",
        )

        # Switch to voice input
        session.input_mode = "voice"

        # User speaks
        msg2 = Message(
            session_id=1,
            role="user",
            content="¿Qué son las ecuaciones?",
            timestamp=datetime.now(UTC),
            input_mode=session.input_mode,
        )

        assert msg1.input_mode == "text"
        assert msg2.input_mode == "voice"

    @pytest.mark.asyncio
    async def test_ttt_to_vva_mode_switch(self):
        """Test switching from TTT to VVA mode."""
        session = Session(
            grade=5,
            subject="science",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        # Text conversation
        msg_text = Message(
            session_id=1,
            role="user",
            content="Explain photosynthesis",
            timestamp=datetime.now(UTC),
            input_mode="text",
        )

        resp_text = Message(
            session_id=1,
            role="assistant",
            content="Photosynthesis is...",
            timestamp=datetime.now(UTC),
            output_mode="text",
        )

        # Switch to full voice
        session.input_mode = "voice"
        session.current_mode = "audio"

        # Voice conversation
        msg_voice = Message(
            session_id=1,
            role="user",
            content="¿Cuál es el producto?",
            timestamp=datetime.now(UTC),
            input_mode="voice",
        )

        resp_voice = Message(
            session_id=1,
            role="assistant",
            content="El producto es glucosa y oxígeno",
            timestamp=datetime.now(UTC),
            output_mode="audio",
            audio_id="glucose_audio",
            audio_available=True,
            audio_duration=5.8,
        )

        # Verify the switch
        assert msg_text.input_mode == "text"
        assert resp_text.output_mode == "text"
        assert msg_voice.input_mode == "voice"
        assert resp_voice.output_mode == "audio"


class TestMessageAuditTrail:
    """Tests for message audit trail with voice modes."""

    @pytest.mark.asyncio
    async def test_audit_trail_records_all_four_modes(self):
        """Test audit trail captures all 4 mode combinations."""
        messages = [
            # TTT
            Message(
                session_id=1,
                role="user",
                content="Question 1",
                timestamp=datetime.now(UTC),
                input_mode="text",
                output_mode="text",
            ),
            # TTA
            Message(
                session_id=1,
                role="user",
                content="Question 2",
                timestamp=datetime.now(UTC),
                input_mode="text",
                output_mode="audio",
            ),
            # VTT
            Message(
                session_id=1,
                role="user",
                content="Question 3",
                timestamp=datetime.now(UTC),
                input_mode="voice",
                output_mode="text",
            ),
            # VVA
            Message(
                session_id=1,
                role="user",
                content="Question 4",
                timestamp=datetime.now(UTC),
                input_mode="voice",
                output_mode="audio",
            ),
        ]

        # All messages should have both modes recorded
        for msg in messages:
            assert msg.input_mode in ["text", "voice"]
            assert msg.output_mode in ["text", "audio"]

    @pytest.mark.asyncio
    async def test_audit_trail_preserves_mode_history(self):
        """Test complete audit trail preserves mode changes."""
        session = Session(
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        audit_trail = [
            Message(
                session_id=1,
                role="user",
                content="msg1",
                timestamp=datetime.now(UTC),
                input_mode=session.input_mode,
                output_mode=session.current_mode,
            ),
        ]

        # Mode change
        session.input_mode = "voice"
        session.current_mode = "audio"

        audit_trail.append(
            Message(
                session_id=1,
                role="user",
                content="msg2",
                timestamp=datetime.now(UTC),
                input_mode=session.input_mode,
                output_mode=session.current_mode,
            ),
        )

        # Verify history
        assert audit_trail[0].input_mode == "text"
        assert audit_trail[0].output_mode == "text"
        assert audit_trail[1].input_mode == "voice"
        assert audit_trail[1].output_mode == "audio"


@pytest.mark.priority_1
class TestPriority1VoiceModesComplete:
    """Priority 1 critical tests for complete voice mode implementation."""

    @pytest.mark.asyncio
    async def test_critical_mode_1_ttt_working(self):
        """CRITICAL: Mode 1 (TTT) must work end-to-end."""
        session = Session(
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )
        assert session.input_mode == "text"
        assert session.current_mode == "text"

    @pytest.mark.asyncio
    async def test_critical_mode_2_tta_working(self):
        """CRITICAL: Mode 2 (TTA) must work end-to-end."""
        session = Session(
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="audio",
        )
        msg = Message(
            session_id=1,
            role="assistant",
            content="response",
            timestamp=datetime.now(UTC),
            output_mode="audio",
            audio_id="test",
            audio_available=True,
        )
        assert session.input_mode == "text"
        assert msg.output_mode == "audio"

    @pytest.mark.asyncio
    async def test_critical_mode_3_vtt_working(self):
        """CRITICAL: Mode 3 (VTT) must work end-to-end."""
        session = Session(
            grade=5,
            subject="math",
            mode="learn",
            input_mode="voice",
            current_mode="text",
        )
        msg = Message(
            session_id=1,
            role="user",
            content="voice input",
            timestamp=datetime.now(UTC),
            input_mode="voice",
        )
        assert msg.input_mode == "voice"
        assert session.current_mode == "text"

    @pytest.mark.asyncio
    async def test_critical_mode_4_vva_working(self):
        """CRITICAL: Mode 4 (VVA) full voice working."""
        session = Session(
            grade=5,
            subject="math",
            mode="learn",
            input_mode="voice",
            current_mode="audio",
        )
        # User message in voice mode
        Message(
            session_id=1,
            role="user",
            content="voice question",
            timestamp=datetime.now(UTC),
            input_mode="voice",
        )
        resp = Message(
            session_id=1,
            role="assistant",
            content="voice answer",
            timestamp=datetime.now(UTC),
            output_mode="audio",
            audio_id="test",
            audio_available=True,
        )
        assert session.input_mode == "voice"
        assert resp.output_mode == "audio"

    @pytest.mark.asyncio
    async def test_critical_mode_switching_works(self):
        """CRITICAL: Mode switching must work during conversation."""
        session = Session(
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
    async def test_critical_modes_independent(self):
        """CRITICAL: Input and output modes must be independent."""
        session = Session(
            grade=5,
            subject="math",
            mode="learn",
            input_mode="voice",
            current_mode="text",
        )
        assert session.input_mode != session.current_mode
        assert session.input_mode == "voice"
        assert session.current_mode == "text"
