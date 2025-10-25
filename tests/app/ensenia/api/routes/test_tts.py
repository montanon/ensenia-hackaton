"""Unit tests for TTS API endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.ensenia.main import app
from app.ensenia.services.elevenlabs_service import get_elevenlabs_service


@pytest.fixture
def mock_service():
    """Mock ElevenLabsService."""
    service = AsyncMock()
    service.cache_dir = "/tmp/cache"  # noqa: S108
    service.generate_speech = AsyncMock(return_value=b"fake audio data")
    service.generate_multiple_segments = AsyncMock(return_value=[b"audio1", b"audio2"])

    async def mock_stream():
        yield b"chunk1"
        yield b"chunk2"

    service.generate_speech_streaming = mock_stream
    return service


@pytest.fixture
def mock_text_processor():
    """Mock text processing utilities."""
    with (
        patch("app.ensenia.api.routes.tts.validate_text_for_tts") as mock_validate,
        patch("app.ensenia.api.routes.tts.preprocess_text") as mock_preprocess,
    ):
        mock_validate.return_value = (True, "")
        mock_preprocess.side_effect = lambda text, _grade: text  # Return text as-is
        yield {"validate": mock_validate, "preprocess": mock_preprocess}


@pytest.fixture
def client(mock_service, mock_text_processor):  # noqa: ARG001
    """FastAPI test client with dependency overrides."""
    # Override the service dependency
    app.dependency_overrides[get_elevenlabs_service] = lambda: mock_service

    with TestClient(app) as test_client:
        yield test_client

    # Clean up overrides
    app.dependency_overrides.clear()


class TestSimpleTTS:
    """Test GET /tts/speak endpoint."""

    def test_successful_tts_generation(self, client, mock_service, mock_text_processor):  # noqa: ARG002
        """Generate audio successfully."""
        mock_service.generate_speech = AsyncMock(return_value=b"fake audio data")

        response = client.get("/tts/speak?text=Hola estudiantes&grade=5")

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"
        assert response.content == b"fake audio data"
        mock_service.generate_speech.assert_awaited_once()

    def test_validation_error(self, client, mock_service, mock_text_processor):  # noqa: ARG002
        """Reject invalid text."""
        mock_text_processor["validate"].return_value = (False, "Text too long")

        response = client.get("/tts/speak?text=invalid&grade=5")

        assert response.status_code == 400
        assert "Text too long" in response.json()["detail"]

    def test_missing_text_parameter(self, client, mock_service, mock_text_processor):  # noqa: ARG002
        """Reject missing text parameter."""
        response = client.get("/tts/speak?grade=5")

        assert response.status_code == 422  # Validation error

    def test_invalid_grade_level(self, client, mock_service, mock_text_processor):  # noqa: ARG002
        """Reject invalid grade level."""
        response = client.get("/tts/speak?text=Hola&grade=15")

        assert response.status_code == 422

    def test_service_error(self, client, mock_service, mock_text_processor):  # noqa: ARG002
        """Handle service errors gracefully."""
        mock_service.generate_speech.side_effect = Exception("API error")

        response = client.get("/tts/speak?text=Hola&grade=5")

        assert response.status_code == 500
        assert "TTS generation failed" in response.json()["detail"]

    def test_default_grade_level(self, client, mock_service, mock_text_processor):  # noqa: ARG002
        """Use default grade level when not specified."""
        mock_service.generate_speech = AsyncMock(return_value=b"audio")

        response = client.get("/tts/speak?text=Hola")

        assert response.status_code == 200
        # Check that grade 5 (default) was used
        call_args = mock_service.generate_speech.await_args
        assert call_args.kwargs["grade_level"] == 5


class TestAdvancedTTS:
    """Test POST /tts/generate endpoint."""

    def test_successful_generation_with_cache(
        self,
        client,
        mock_service,
        mock_text_processor,  # noqa: ARG002
    ):
        """Generate audio with caching enabled."""
        mock_service.generate_speech = AsyncMock(return_value=b"cached audio")

        response = client.post(
            "/tts/generate",
            json={"text": "Hola estudiantes", "grade_level": 8, "use_cache": True},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"
        assert "X-Audio-Length" in response.headers
        mock_service.generate_speech.assert_awaited_once_with(
            "Hola estudiantes", grade_level=8, use_cache=True
        )

    def test_generation_without_cache(self, client, mock_service, mock_text_processor):  # noqa: ARG002
        """Generate audio with caching disabled."""
        mock_service.generate_speech = AsyncMock(return_value=b"fresh audio")

        response = client.post(
            "/tts/generate",
            json={"text": "Nueva pregunta", "grade_level": 10, "use_cache": False},
        )

        assert response.status_code == 200
        mock_service.generate_speech.assert_awaited_once_with(
            "Nueva pregunta", grade_level=10, use_cache=False
        )

    def test_validation_error_in_body(self, client, mock_service, mock_text_processor):  # noqa: ARG002
        """Reject invalid text in request body."""
        mock_text_processor["validate"].return_value = (False, "Empty text")

        response = client.post(
            "/tts/generate",
            json={"text": "", "grade_level": 5},
        )

        assert response.status_code == 400

    def test_invalid_json_structure(self, client, mock_service, mock_text_processor):  # noqa: ARG002
        """Reject malformed JSON."""
        response = client.post("/tts/generate", json={"invalid": "structure"})

        assert response.status_code == 422

    def test_default_values(self, client, mock_service, mock_text_processor):  # noqa: ARG002
        """Use default values for optional fields."""
        mock_service.generate_speech = AsyncMock(return_value=b"audio")

        response = client.post("/tts/generate", json={"text": "Hola"})

        assert response.status_code == 200
        call_args = mock_service.generate_speech.await_args
        assert call_args.kwargs["grade_level"] == 5
        assert call_args.kwargs["use_cache"] is True


class TestStreamingTTS:
    """Test GET /tts/stream endpoint."""

    def test_successful_streaming(self, client, mock_service, mock_text_processor):  # noqa: ARG002
        """Stream audio successfully."""

        async def mock_stream(text, grade):  # noqa: ARG001
            yield b"chunk1"
            yield b"chunk2"

        mock_service.generate_speech_streaming = mock_stream

        response = client.get("/tts/stream?text=Contenido largo&grade=7")

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"

    def test_validation_error_streaming(
        self,
        client,
        mock_service,
        mock_text_processor,  # noqa: ARG002
    ):
        """Reject invalid text for streaming."""
        mock_text_processor["validate"].return_value = (False, "Invalid")

        response = client.get("/tts/stream?text=invalid&grade=5")

        assert response.status_code == 400

    def test_streaming_service_error(self, client, mock_service, mock_text_processor):  # noqa: ARG002
        """Handle streaming errors."""
        mock_service.generate_speech_streaming.side_effect = Exception("Stream error")

        response = client.get("/tts/stream?text=Hola&grade=5")

        assert response.status_code == 500


class TestBatchTTS:
    """Test POST /tts/batch endpoint."""

    def test_successful_batch_generation(
        self,
        client,
        mock_service,
        mock_text_processor,  # noqa: ARG002
    ):
        """Generate audio for multiple segments."""
        mock_service.generate_multiple_segments.return_value = [
            b"audio1",
            b"audio2",
            b"audio3",
        ]

        response = client.post(
            "/tts/batch",
            json={
                "segments": [
                    {"text": "Pregunta uno"},
                    {"text": "Pregunta dos", "grade_level": 6},
                    {"text": "Pregunta tres"},
                ],
                "grade_level": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Generated audio for 3 segments"
        assert data["audio_length"] > 0

    def test_single_segment_batch(self, client, mock_service, mock_text_processor):  # noqa: ARG002
        """Handle single segment batch."""
        mock_service.generate_multiple_segments.return_value = [b"audio"]

        response = client.post(
            "/tts/batch",
            json={"segments": [{"text": "Solo uno"}], "grade_level": 5},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Generated audio for 1 segments"

    def test_segment_specific_grade_levels(
        self,
        client,
        mock_service,
        mock_text_processor,  # noqa: ARG002
    ):
        """Use segment-specific grade levels."""
        mock_service.generate_multiple_segments = AsyncMock(return_value=[b"a", b"b"])

        response = client.post(
            "/tts/batch",
            json={
                "segments": [
                    {"text": "Elementary", "grade_level": 3},
                    {"text": "High school", "grade_level": 11},
                ],
                "grade_level": 5,
            },
        )

        assert response.status_code == 200
        call_args = mock_service.generate_multiple_segments.await_args
        processed = call_args[0][0]
        assert processed[0]["grade_level"] == 3
        assert processed[1]["grade_level"] == 11

    def test_invalid_segment(self, client, mock_service, mock_text_processor):  # noqa: ARG002
        """Reject batch with invalid segment."""
        mock_text_processor["validate"].side_effect = [
            (True, ""),
            (False, "Invalid segment"),
        ]

        response = client.post(
            "/tts/batch",
            json={
                "segments": [
                    {"text": "Valid"},
                    {"text": "Invalid"},
                ],
                "grade_level": 5,
            },
        )

        assert response.status_code == 400
        assert "Invalid segment" in response.json()["detail"]

    def test_empty_segments_list(self, client, mock_service, mock_text_processor):  # noqa: ARG002
        """Reject empty segments list."""
        response = client.post(
            "/tts/batch",
            json={"segments": [], "grade_level": 5},
        )

        assert response.status_code == 422

    def test_too_many_segments(self, client, mock_service, mock_text_processor):  # noqa: ARG002
        """Reject too many segments."""
        segments = [{"text": f"Segment {i}"} for i in range(11)]
        response = client.post(
            "/tts/batch",
            json={"segments": segments, "grade_level": 5},
        )

        assert response.status_code == 422


class TestHealthCheck:
    """Test GET /tts/health endpoint."""

    def test_healthy_service(self, client, mock_service, mock_text_processor):  # noqa: ARG002
        """Return healthy status."""
        response = client.get("/tts/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "elevenlabs-tts"
        assert "voice" in data
        assert "cache_dir" in data

    def test_unhealthy_service(
        self,
        client,
        mock_service,
        mock_text_processor,  # noqa: ARG002
    ):
        """Handle service errors in health check."""
        # Make cache_dir property raise an exception
        type(mock_service).cache_dir = property(
            lambda _self: (_ for _ in ()).throw(Exception("Cache error"))
        )

        response = client.get("/tts/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
