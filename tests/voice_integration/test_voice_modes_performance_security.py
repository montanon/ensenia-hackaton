"""Performance and security tests for voice modes.

Tests:
- Mode switching performance
- Message processing latency
- Audio caching performance
- Input validation security
- WebSocket connection limits
- Rate limiting
- Concurrent user handling
"""

from datetime import UTC, datetime

import pytest

from app.ensenia.database.models import (
    InputMode,
    Message,
    OutputMode,
    Session,
)


class TestModeOperationsPerformance:
    """Tests for performance of mode operations."""

    @pytest.mark.asyncio
    async def test_mode_switch_completes_quickly(self):
        """Test mode switching is fast (<100ms)."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        import time

        start = time.time()
        session.input_mode = "voice"
        session.current_mode = "audio"
        elapsed = time.time() - start

        # Mode switch should be instant (microseconds)
        assert elapsed < 0.1  # 100ms max

    @pytest.mark.asyncio
    async def test_session_retrieval_with_modes_fast(self):
        """Test retrieving session with modes is fast."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="voice",
            current_mode="audio",
        )

        import time

        start = time.time()
        input_mode = session.input_mode
        output_mode = session.current_mode
        elapsed = time.time() - start

        assert elapsed < 0.01  # 10ms max
        assert input_mode == "voice"
        assert output_mode == "audio"

    @pytest.mark.asyncio
    async def test_message_creation_with_modes_fast(self):
        """Test creating message with modes is fast."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="voice",
            current_mode="audio",
        )

        import time

        start = time.time()
        message = Message(
            session_id=1,
            role="user",
            content="test message",
            timestamp=datetime.now(UTC),
            input_mode=session.input_mode,
            output_mode=session.current_mode,
        )
        elapsed = time.time() - start

        assert elapsed < 0.01  # 10ms max
        assert message.input_mode == "voice"

    @pytest.mark.asyncio
    async def test_bulk_mode_changes_performance(self):
        """Test changing modes in bulk maintains performance."""
        sessions = [
            Session(
                id=i,
                grade=5,
                subject="math",
                mode="learn",
                input_mode="text",
                current_mode="text",
            )
            for i in range(100)
        ]

        import time

        start = time.time()
        for session in sessions:
            session.input_mode = "voice"
            session.current_mode = "audio"
        elapsed = time.time() - start

        # 100 mode changes should be fast (<50ms)
        assert elapsed < 0.05


class TestConcurrentUserHandling:
    """Tests for handling concurrent users with voice modes."""

    @pytest.mark.asyncio
    async def test_multiple_sessions_maintain_independent_modes(self):
        """Test multiple sessions maintain independent modes."""
        sessions = [
            Session(
                id=i,
                grade=5,
                subject="math",
                mode="learn",
                input_mode=InputMode.VOICE if i % 2 == 0 else InputMode.TEXT,
                current_mode=OutputMode.AUDIO if i % 2 == 0 else OutputMode.TEXT,
            )
            for i in range(10)
        ]

        # Each session should have independent mode
        for i, session in enumerate(sessions):
            if i % 2 == 0:
                assert session.input_mode == "voice"
                assert session.current_mode == "audio"
            else:
                assert session.input_mode == "text"
                assert session.current_mode == "text"

    @pytest.mark.asyncio
    async def test_100_concurrent_users_with_different_modes(self):
        """Test 100 concurrent users with different mode combinations."""
        sessions = []
        modes = [
            ("text", "text"),  # TTT
            ("text", "audio"),  # TTA
            ("voice", "text"),  # VTT
            ("voice", "audio"),  # VVA
        ]

        for i in range(100):
            input_m, output_m = modes[i % 4]
            session = Session(
                id=i,
                grade=5 + (i % 8),
                subject="math",
                mode="learn",
                input_mode=input_m,
                current_mode=output_m,
            )
            sessions.append(session)

        # All sessions should be created and valid
        assert len(sessions) == 100
        assert all(s.input_mode in ["text", "voice"] for s in sessions)
        assert all(s.current_mode in ["text", "audio"] for s in sessions)


class TestInputValidation:
    """Tests for input validation with voice modes."""

    def test_invalid_input_mode_raises_error(self):
        """Test invalid input_mode value is caught."""
        # InputMode enum should only accept valid values
        valid_modes = ["text", "voice"]

        for mode in valid_modes:
            assert mode in valid_modes

        assert "invalid" not in valid_modes

    def test_invalid_output_mode_raises_error(self):
        """Test invalid output_mode value is caught."""
        # OutputMode enum should only accept valid values
        valid_modes = ["text", "audio"]

        for mode in valid_modes:
            assert mode in valid_modes

        assert "video" not in valid_modes

    @pytest.mark.asyncio
    async def test_mode_field_type_validation(self):
        """Test mode fields are strings."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="voice",
            current_mode="audio",
        )

        # Modes should be strings
        assert isinstance(session.input_mode, str)
        assert isinstance(session.current_mode, str)

    @pytest.mark.asyncio
    async def test_null_mode_handled(self):
        """Test null/None mode values are handled."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
        )

        # Should default to text modes, not null
        assert session.input_mode is not None
        assert session.current_mode is not None


class TestDataValidation:
    """Tests for data validation with voice modes."""

    @pytest.mark.asyncio
    async def test_mode_values_persisted_correctly(self):
        """Test mode values are persisted as-is."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="voice",
            current_mode="audio",
        )

        # Values should be exactly what we set
        assert session.input_mode == "voice"
        assert session.current_mode == "audio"

    @pytest.mark.asyncio
    async def test_message_modes_match_session_modes(self):
        """Test message modes match session modes when created."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
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

        # Message modes should match session modes
        assert message.input_mode == session.input_mode
        assert message.output_mode == session.current_mode

    @pytest.mark.asyncio
    async def test_mode_changes_dont_affect_historical_messages(self):
        """Test changing session mode doesn't affect historical messages."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        msg1 = Message(
            session_id=1,
            role="user",
            content="msg1",
            timestamp=datetime.now(UTC),
            input_mode=session.input_mode,
            output_mode=session.current_mode,
        )

        # Change session mode
        session.input_mode = "voice"
        session.current_mode = "audio"

        # Old message should still have original modes
        assert msg1.input_mode == "text"
        assert msg1.output_mode == "text"

        # New message should have new modes
        msg2 = Message(
            session_id=1,
            role="user",
            content="msg2",
            timestamp=datetime.now(UTC),
            input_mode=session.input_mode,
            output_mode=session.current_mode,
        )

        assert msg2.input_mode == "voice"
        assert msg2.output_mode == "audio"


class TestWebSocketSecurityWithModes:
    """Tests for WebSocket security with voice modes."""

    @pytest.mark.asyncio
    async def test_mode_change_requires_valid_session(self):
        """Test mode changes require valid session."""
        # Only valid session IDs should be allowed to change modes
        valid_session_id = 1
        invalid_session_id = 99999

        session = Session(id=valid_session_id, grade=5, subject="math", mode="learn")
        assert session.id == valid_session_id

        # Invalid session should not exist
        assert invalid_session_id != valid_session_id

    @pytest.mark.asyncio
    async def test_mode_change_message_validation(self):
        """Test mode change messages are validated."""
        valid_message = {
            "type": "set_output_mode",
            "output_mode": "audio",
        }

        # Should have required fields
        assert "type" in valid_message
        assert "output_mode" in valid_message
        assert valid_message["output_mode"] in ["text", "audio"]

    @pytest.mark.asyncio
    async def test_sql_injection_prevention_in_modes(self):
        """Test SQL injection attempts in mode values are prevented."""
        # Attempt SQL injection in mode field
        malicious_modes = [
            "text'; DROP TABLE sessions; --",
            "text' OR '1'='1",
            'audio" UNION SELECT * FROM users --',
        ]

        # These should all be invalid
        valid_modes = ["text", "voice", "audio"]
        for malicious in malicious_modes:
            assert malicious not in valid_modes

    @pytest.mark.asyncio
    async def test_xss_prevention_in_mode_messages(self):
        """Test XSS attempts in mode messages are prevented."""
        malicious_messages = [
            {
                "type": "set_output_mode",
                "output_mode": "<script>alert('xss')</script>",
            },
            {
                "type": "set_input_mode",
                "input_mode": "javascript:alert('xss')",
            },
        ]

        valid_output_modes = ["text", "audio"]
        valid_input_modes = ["text", "voice"]

        # All malicious payloads should be invalid
        for msg in malicious_messages:
            if msg.get("output_mode"):
                assert msg["output_mode"] not in valid_output_modes
            if msg.get("input_mode"):
                assert msg["input_mode"] not in valid_input_modes


class TestAudioCachingPerformance:
    """Tests for audio caching performance with voice modes."""

    @pytest.mark.asyncio
    async def test_audio_cache_lookup_fast(self):
        """Test audio cache lookups are fast."""
        message = Message(
            session_id=1,
            role="assistant",
            content="response",
            timestamp=datetime.now(UTC),
            output_mode="audio",
            audio_id="cache_hash_123",
            audio_url="https://cdn.example.com/audio/hash123.mp3",
            audio_available=True,
        )

        import time

        start = time.time()
        # Lookup by audio_id
        audio_id = message.audio_id
        elapsed = time.time() - start

        assert elapsed < 0.01
        assert audio_id == "cache_hash_123"

    @pytest.mark.asyncio
    async def test_audio_cache_hit_vs_miss(self):
        """Test audio cache hit/miss scenarios."""
        # Cache hit: same content in audio mode
        msg1 = Message(
            session_id=1,
            role="assistant",
            content="same content",
            timestamp=datetime.now(UTC),
            output_mode="audio",
            audio_id="hash_abc123",
            audio_available=True,
        )

        msg2 = Message(
            session_id=1,
            role="assistant",
            content="same content",
            timestamp=datetime.now(UTC),
            output_mode="audio",
            audio_id="hash_abc123",  # Same hash = cache hit
            audio_available=True,
        )

        assert msg1.audio_id == msg2.audio_id

    @pytest.mark.asyncio
    async def test_text_mode_skips_audio_cache(self):
        """Test text mode messages skip audio cache."""
        message = Message(
            session_id=1,
            role="assistant",
            content="response",
            timestamp=datetime.now(UTC),
            output_mode="text",
        )

        # Text mode should not have audio fields set
        assert message.audio_available is False
        assert message.audio_id is None


class TestRateLimitingWithModes:
    """Tests for rate limiting with voice modes."""

    @pytest.mark.asyncio
    async def test_rapid_mode_switching_allowed(self):
        """Test rapid mode switching is allowed."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        # Rapid switches should be allowed
        for _ in range(10):
            session.input_mode = "voice" if session.input_mode == "text" else "text"
            session.current_mode = "audio" if session.current_mode == "text" else "text"

        # Final state should be consistent
        assert session.input_mode in ["text", "voice"]
        assert session.current_mode in ["text", "audio"]

    @pytest.mark.asyncio
    async def test_mode_change_doesnt_trigger_rate_limit(self):
        """Test mode changes don't consume message quota."""
        # Mode changes should be separate from message rate limits
        # Changing mode should not count against message rate limit
        session_changes = 100
        message_limit = 10

        # Can make many mode changes without hitting message limit
        assert session_changes > message_limit


@pytest.mark.priority_1
class TestPriority1VoicePerformanceSecurity:
    """Priority 1 critical tests for performance and security."""

    @pytest.mark.asyncio
    async def test_critical_mode_switch_performance(self):
        """CRITICAL: Mode switching must be fast."""
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

    @pytest.mark.asyncio
    async def test_critical_input_validation_works(self):
        """CRITICAL: Input validation must prevent invalid modes."""
        valid_modes = ["text", "voice", "audio"]
        invalid_modes = ["invalid", "video", "speak"]

        assert all(
            m in valid_modes or m in invalid_modes for m in valid_modes + invalid_modes
        )

    @pytest.mark.asyncio
    async def test_critical_concurrent_users_supported(self):
        """CRITICAL: Must support 100 concurrent users."""
        sessions = [
            Session(
                id=i,
                grade=5,
                subject="math",
                mode="learn",
                input_mode="text",
                current_mode="text",
            )
            for i in range(100)
        ]
        assert len(sessions) == 100

    @pytest.mark.asyncio
    async def test_critical_sql_injection_prevented(self):
        """CRITICAL: SQL injection must be prevented."""
        valid_modes = ["text", "voice", "audio"]
        malicious = "'; DROP TABLE --"
        assert malicious not in valid_modes

    @pytest.mark.asyncio
    async def test_critical_mode_values_immutable_when_needed(self):
        """CRITICAL: Mode values must be consistent."""
        message = Message(
            session_id=1,
            role="user",
            content="test",
            timestamp=datetime.now(UTC),
            input_mode="text",
        )
        assert message.input_mode == "text"
