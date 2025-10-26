"""FastAPI routes for ElevenLabs TTS endpoints.

Provides:
- Simple text-to-speech conversion
- Streaming audio
- Batch generation
- Grade-specific audio generation
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from app.ensenia.services.elevenlabs_service import (
    ElevenLabsService,
    get_elevenlabs_service,
)
from app.ensenia.utils.text_processor import preprocess_text, validate_text_for_tts

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tts", tags=["Text-to-Speech"])

# Dependency injection type
ServiceDep = Annotated[ElevenLabsService, Depends(get_elevenlabs_service)]


# Pydantic Models


class TTSRequest(BaseModel):
    """Request model for TTS generation."""

    text: str = Field(..., description="Text to convert to speech", max_length=5000)
    grade_level: int = Field(
        default=5, ge=1, le=12, description="Student grade level (1-12)"
    )
    use_cache: bool = Field(default=True, description="Whether to use cached audio")


class BatchSegment(BaseModel):
    """Model for a single segment in batch TTS."""

    text: str = Field(..., max_length=5000)
    grade_level: int | None = Field(default=None, ge=1, le=12)


class BatchTTSRequest(BaseModel):
    """Request model for batch TTS generation."""

    segments: list[BatchSegment] = Field(..., min_length=1, max_length=10)
    grade_level: int = Field(default=5, ge=1, le=12, description="Default grade level")


class TTSResponse(BaseModel):
    """Response model for TTS operations."""

    success: bool
    message: str
    audio_length: int | None = None


# Routes


@router.get("/speak")
async def text_to_speech_simple(
    service: ServiceDep,
    text: Annotated[
        str, Query(..., description="Text to convert to speech", max_length=5000)
    ],
    grade: Annotated[int, Query(ge=1, le=12, description="Grade level (1-12)")] = 5,
) -> Response:
    """Convert text to speech using Chilean Spanish voice.

    Returns audio file directly.

    Example:
        GET /tts/speak?text=Hola%20estudiantes&grade=5

    """
    try:
        # Validate text
        is_valid, error_msg = validate_text_for_tts(text)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Preprocess text
        processed_text = preprocess_text(text, grade)
        logger.info("TTS request (grade %d): %s...", grade, text[:50])

        # Generate audio using injected service
        audio_bytes = await service.generate_speech(processed_text, grade_level=grade)

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3",
                "Cache-Control": "public, max-age=86400",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("TTS error")
        raise HTTPException(
            status_code=500, detail=f"TTS generation failed: {e!s}"
        ) from e


@router.post("/generate")
async def text_to_speech_advanced(service: ServiceDep, request: TTSRequest) -> Response:
    """Generate text-to-speech with advanced options.

    Provides more control over caching and settings.

    Example:
        POST /tts/generate
        {
            "text": "Hola estudiantes",
            "grade_level": 5,
            "use_cache": true
        }

    """
    try:
        # Validate text
        is_valid, error_msg = validate_text_for_tts(request.text)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Preprocess text
        processed_text = preprocess_text(request.text, request.grade_level)
        logger.info(
            "TTS generate (grade %d, cache=%s)", request.grade_level, request.use_cache
        )

        # Generate audio using injected service
        audio_bytes = await service.generate_speech(
            processed_text, grade_level=request.grade_level, use_cache=request.use_cache
        )

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3",
                "X-Audio-Length": str(len(audio_bytes)),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("TTS generation error")
        raise HTTPException(
            status_code=500, detail=f"TTS generation failed: {e!s}"
        ) from e


@router.get("/stream")
async def text_to_speech_stream(
    service: ServiceDep,
    text: Annotated[
        str, Query(..., description="Text to convert to speech", max_length=5000)
    ],
    grade: Annotated[int, Query(ge=1, le=12, description="Grade level (1-12)")] = 5,
) -> StreamingResponse:
    """Stream text-to-speech audio in real-time chunks.

    Best for long content or real-time applications.

    Example:
        GET /tts/stream?text=Contenido%20largo&grade=5

    """
    try:
        # Validate text
        is_valid, error_msg = validate_text_for_tts(text)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Preprocess text
        processed_text = preprocess_text(text, grade)
        logger.info("TTS streaming request (grade %d)", grade)

        # Create stream using injected service
        return StreamingResponse(
            service.generate_speech_streaming(processed_text, grade),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=speech.mp3"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("TTS streaming error")
        raise HTTPException(
            status_code=500, detail=f"TTS streaming failed: {e!s}"
        ) from e


@router.post("/batch")
async def batch_text_to_speech(
    service: ServiceDep, request: BatchTTSRequest
) -> TTSResponse:
    """Generate audio for multiple text segments.

    Useful for generating multiple exercise questions or lesson sections.

    Example:
        POST /tts/batch
        {
            "segments": [
                {"text": "Pregunta uno"},
                {"text": "Pregunta dos", "grade_level": 6}
            ],
            "grade_level": 5
        }

    """
    try:
        # Preprocess all segments
        processed_segments = []
        for segment in request.segments:
            grade = segment.grade_level or request.grade_level

            # Validate
            is_valid, error_msg = validate_text_for_tts(segment.text)
            if not is_valid:
                raise HTTPException(
                    status_code=400, detail=f"Invalid segment: {error_msg}"
                )

            processed_text = preprocess_text(segment.text, grade)
            processed_segments.append({"text": processed_text, "grade_level": grade})

        logger.info("Batch TTS request: %d segments", len(processed_segments))

        # Generate audio for all segments using injected service
        audio_segments = await service.generate_multiple_segments(
            processed_segments, request.grade_level
        )

        return TTSResponse(
            success=True,
            message=f"Generated audio for {len(audio_segments)} segments",
            audio_length=sum(len(audio) for audio in audio_segments),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Batch TTS error")
        raise HTTPException(status_code=500, detail=f"Batch TTS failed: {e!s}") from e


@router.get("/health")
async def health_check(service: ServiceDep) -> dict[str, Any]:
    """Check TTS service health status."""
    try:
        return {
            "status": "healthy",
            "service": "elevenlabs-tts",
            "voice": "Dorothy (Chilean Spanish)",
            "cache_dir": str(service.cache_dir),
        }
    except Exception as e:
        logger.exception("Health check failed")
        return {"status": "unhealthy", "error": str(e)}
