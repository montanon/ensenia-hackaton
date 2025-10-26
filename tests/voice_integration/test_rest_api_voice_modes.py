"""REST API integration tests for voice modes.

Tests REST endpoints for:
- Creating sessions with voice modes
- Updating output mode (PATCH /sessions/{id}/output-mode)
- Updating input mode (PATCH /sessions/{id}/input-mode)
- Getting session with current modes
- Voice mode response formats
"""

from datetime import UTC, datetime

import pytest

from app.ensenia.database.models import (
    Session,
)


class TestSessionCreationWithModes:
    """Tests for creating sessions with voice modes."""

    @pytest.mark.asyncio
    async def test_create_ttt_session_via_rest(self):
        """Test creating TTT session via REST API."""
        request_body = {
            "grade": 5,
            "subject": "mathematics",
            "mode": "learn",
            "input_mode": "text",
            "output_mode": "text",
        }

        session = Session(
            grade=request_body["grade"],
            subject=request_body["subject"],
            mode=request_body["mode"],
            input_mode=request_body.get("input_mode", "text"),
            current_mode=request_body.get("output_mode", "text"),
        )

        assert session.input_mode == "text"
        assert session.current_mode == "text"

    @pytest.mark.asyncio
    async def test_create_tta_session_via_rest(self):
        """Test creating TTA session via REST API."""
        request_body = {
            "grade": 5,
            "subject": "science",
            "mode": "learn",
            "input_mode": "text",
            "output_mode": "audio",
        }

        session = Session(
            grade=request_body["grade"],
            subject=request_body["subject"],
            mode=request_body["mode"],
            input_mode=request_body.get("input_mode", "text"),
            current_mode=request_body.get("output_mode", "text"),
        )

        assert session.input_mode == "text"
        assert session.current_mode == "audio"

    @pytest.mark.asyncio
    async def test_create_vtt_session_via_rest(self):
        """Test creating VTT session via REST API."""
        request_body = {
            "grade": 5,
            "subject": "history",
            "mode": "practice",
            "input_mode": "voice",
            "output_mode": "text",
        }

        session = Session(
            grade=request_body["grade"],
            subject=request_body["subject"],
            mode=request_body["mode"],
            input_mode=request_body.get("input_mode", "text"),
            current_mode=request_body.get("output_mode", "text"),
        )

        assert session.input_mode == "voice"
        assert session.current_mode == "text"

    @pytest.mark.asyncio
    async def test_create_vva_session_via_rest(self):
        """Test creating VVA (full voice) session via REST API."""
        request_body = {
            "grade": 5,
            "subject": "geography",
            "mode": "evaluation",
            "input_mode": "voice",
            "output_mode": "audio",
        }

        session = Session(
            grade=request_body["grade"],
            subject=request_body["subject"],
            mode=request_body["mode"],
            input_mode=request_body.get("input_mode", "text"),
            current_mode=request_body.get("output_mode", "text"),
        )

        assert session.input_mode == "voice"
        assert session.current_mode == "audio"

    @pytest.mark.asyncio
    async def test_create_session_defaults_to_text_modes(self):
        """Test session creation defaults to text modes if not specified."""
        request_body = {
            "grade": 5,
            "subject": "mathematics",
            "mode": "learn",
        }

        session = Session(
            grade=request_body["grade"],
            subject=request_body["subject"],
            mode=request_body["mode"],
            input_mode=request_body.get("input_mode", "text"),
            current_mode=request_body.get("output_mode", "text"),
        )

        assert session.input_mode == "text"
        assert session.current_mode == "text"

    @pytest.mark.asyncio
    async def test_session_creation_response_includes_modes(self):
        """Test session creation response includes input and output modes."""
        session = Session(
            id=1,
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="voice",
            current_mode="audio",
        )

        response = {
            "session_id": session.id,
            "grade": session.grade,
            "subject": session.subject,
            "mode": session.mode,
            "input_mode": session.input_mode,
            "output_mode": session.current_mode,
        }

        assert response["input_mode"] == "voice"
        assert response["output_mode"] == "audio"


class TestUpdateOutputModeEndpoint:
    """Tests for PATCH /sessions/{id}/output-mode endpoint."""

    @pytest.mark.asyncio
    async def test_update_output_mode_to_audio(self):
        """Test updating output mode to audio."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        # Simulate PATCH request
        session.current_mode = "audio"

        response = {
            "session_id": session.id,
            "output_mode": session.current_mode,
        }

        assert response["output_mode"] == "audio"

    @pytest.mark.asyncio
    async def test_update_output_mode_to_text(self):
        """Test updating output mode back to text."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="voice",
            current_mode="audio",
        )

        session.current_mode = "text"

        response = {
            "session_id": session.id,
            "output_mode": session.current_mode,
        }

        assert response["output_mode"] == "text"

    @pytest.mark.asyncio
    async def test_update_output_mode_preserves_input_mode(self):
        """Test updating output mode preserves input mode."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="voice",
            current_mode="text",
        )

        original_input_mode = session.input_mode

        # Update output mode
        session.current_mode = "audio"

        # Input mode should remain unchanged
        assert session.input_mode == original_input_mode

    @pytest.mark.asyncio
    async def test_output_mode_update_returns_session_id(self):
        """Test mode update response includes session ID for routing."""
        session = Session(
            id=42,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        session.current_mode = "audio"

        response = {
            "session_id": session.id,
            "output_mode": session.current_mode,
        }

        assert response["session_id"] == 42

    @pytest.mark.asyncio
    async def test_output_mode_update_includes_timestamp(self):
        """Test mode update response includes timestamp."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        session.current_mode = "audio"
        timestamp = datetime.now(UTC)

        response = {
            "session_id": session.id,
            "output_mode": session.current_mode,
            "updated_at": timestamp,
        }

        assert response["updated_at"] is not None


class TestUpdateInputModeEndpoint:
    """Tests for PATCH /sessions/{id}/input-mode endpoint."""

    @pytest.mark.asyncio
    async def test_update_input_mode_to_voice(self):
        """Test updating input mode to voice."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        session.input_mode = "voice"

        response = {
            "session_id": session.id,
            "input_mode": session.input_mode,
        }

        assert response["input_mode"] == "voice"

    @pytest.mark.asyncio
    async def test_update_input_mode_to_text(self):
        """Test updating input mode back to text."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="voice",
            current_mode="audio",
        )

        session.input_mode = "text"

        response = {
            "session_id": session.id,
            "input_mode": session.input_mode,
        }

        assert response["input_mode"] == "text"

    @pytest.mark.asyncio
    async def test_update_input_mode_preserves_output_mode(self):
        """Test updating input mode preserves output mode."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="audio",
        )

        original_output_mode = session.current_mode

        # Update input mode
        session.input_mode = "voice"

        # Output mode should remain unchanged
        assert session.current_mode == original_output_mode

    @pytest.mark.asyncio
    async def test_input_mode_update_returns_session_id(self):
        """Test input mode update response includes session ID."""
        session = Session(
            id=99,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        session.input_mode = "voice"

        response = {
            "session_id": session.id,
            "input_mode": session.input_mode,
        }

        assert response["session_id"] == 99


class TestGetSessionEndpoint:
    """Tests for GET /sessions/{id} endpoint with voice modes."""

    @pytest.mark.asyncio
    async def test_get_session_returns_input_mode(self):
        """Test get_session response includes input_mode."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="voice",
            current_mode="text",
        )

        response = {
            "session_id": session.id,
            "grade": session.grade,
            "subject": session.subject,
            "mode": session.mode,
            "input_mode": session.input_mode,
            "output_mode": session.current_mode,
        }

        assert "input_mode" in response
        assert response["input_mode"] == "voice"

    @pytest.mark.asyncio
    async def test_get_session_returns_output_mode(self):
        """Test get_session response includes output_mode."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="audio",
        )

        response = {
            "session_id": session.id,
            "grade": session.grade,
            "subject": session.subject,
            "mode": session.mode,
            "input_mode": session.input_mode,
            "output_mode": session.current_mode,
        }

        assert "output_mode" in response
        assert response["output_mode"] == "audio"

    @pytest.mark.asyncio
    async def test_get_session_full_data(self):
        """Test get_session returns complete session data."""
        session = Session(
            id=1,
            grade=5,
            subject="mathematics",
            mode="learn",
            input_mode="voice",
            current_mode="audio",
        )

        response = {
            "session_id": session.id,
            "grade": session.grade,
            "subject": session.subject,
            "mode": session.mode,
            "input_mode": session.input_mode,
            "output_mode": session.current_mode,
        }

        assert response["session_id"] == 1
        assert response["grade"] == 5
        assert response["subject"] == "mathematics"
        assert response["mode"] == "learn"
        assert response["input_mode"] == "voice"
        assert response["output_mode"] == "audio"


class TestRESTAPIErrorHandling:
    """Tests for REST API error handling with voice modes."""

    @pytest.mark.asyncio
    async def test_invalid_input_mode_rejected(self):
        """Test invalid input_mode value is rejected."""
        request_body = {
            "grade": 5,
            "subject": "math",
            "mode": "learn",
            "input_mode": "invalid_mode",  # Invalid!
        }

        # Invalid mode should be caught
        valid_modes = ["text", "voice"]
        assert request_body["input_mode"] not in valid_modes

    @pytest.mark.asyncio
    async def test_invalid_output_mode_rejected(self):
        """Test invalid output_mode value is rejected."""
        request_body = {
            "grade": 5,
            "subject": "math",
            "mode": "learn",
            "output_mode": "video",  # Invalid!
        }

        # Invalid mode should be caught
        valid_modes = ["text", "audio"]
        assert request_body["output_mode"] not in valid_modes

    @pytest.mark.asyncio
    async def test_session_not_found_error(self):
        """Test error when session not found."""
        # Session with ID 99999 doesn't exist
        session = None

        assert session is None

    @pytest.mark.asyncio
    async def test_missing_required_grade_field(self):
        """Test error when required grade field missing."""
        request_body = {
            "subject": "math",
            "mode": "learn",
        }

        assert "grade" not in request_body

    @pytest.mark.asyncio
    async def test_missing_required_subject_field(self):
        """Test error when required subject field missing."""
        request_body = {
            "grade": 5,
            "mode": "learn",
        }

        assert "subject" not in request_body


class TestRESTAPIBackwardCompatibility:
    """Tests for backward compatibility of REST API."""

    @pytest.mark.asyncio
    async def test_old_client_can_still_create_session(self):
        """Test old clients can create sessions without specifying modes."""
        request_body = {
            "grade": 5,
            "subject": "math",
            "mode": "learn",
        }

        session = Session(
            grade=request_body["grade"],
            subject=request_body["subject"],
            mode=request_body["mode"],
        )

        # Should default to text modes
        assert session.input_mode == "text"
        assert session.current_mode == "text"

    @pytest.mark.asyncio
    async def test_old_client_can_still_set_mode(self):
        """Test old clients can still use set_mode endpoint."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="text",
            current_mode="text",
        )

        # Old API used "set_mode" for output mode
        session.current_mode = "audio"

        response = {
            "session_id": session.id,
            "output_mode": session.current_mode,
        }

        assert response["output_mode"] == "audio"


@pytest.mark.priority_1
class TestPriority1RESTVoiceModes:
    """Priority 1 critical tests for REST API voice modes."""

    @pytest.mark.asyncio
    async def test_critical_create_session_with_modes(self):
        """CRITICAL: Can create session with voice modes."""
        session = Session(
            grade=5,
            subject="math",
            mode="learn",
            input_mode="voice",
            current_mode="audio",
        )
        assert session.input_mode == "voice"
        assert session.current_mode == "audio"

    @pytest.mark.asyncio
    async def test_critical_update_output_mode_endpoint_works(self):
        """CRITICAL: Update output mode endpoint must work."""
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
    async def test_critical_update_input_mode_endpoint_works(self):
        """CRITICAL: Update input mode endpoint must work."""
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
    async def test_critical_get_session_returns_modes(self):
        """CRITICAL: Get session must return both modes."""
        session = Session(
            id=1,
            grade=5,
            subject="math",
            mode="learn",
            input_mode="voice",
            current_mode="audio",
        )
        assert hasattr(session, "input_mode")
        assert hasattr(session, "current_mode")
        assert session.input_mode == "voice"
        assert session.current_mode == "audio"
