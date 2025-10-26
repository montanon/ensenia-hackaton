"""Deepgram Streaming Speech-to-Text Service for Chilean Educational Content.

Provides speech-to-text transcription via Deepgram's streaming API.

Features:
- Real-time audio streaming to Deepgram API
- Transcription results (interim + final)
- Chilean Spanish language support (es)
- Async/await for WebSocket integration
- Confidence scores for result quality assessment
- Comprehensive error handling and logging

Note: The streaming in this implementation refers to streaming audio INPUT to
Deepgram, not necessarily streaming transcription results back. Deepgram returns
final transcription after processing the complete audio stream.
"""

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from typing import Any

from deepgram import AsyncDeepgramClient
from deepgram.core.api_error import ApiError

from app.ensenia.core.config import settings

logger = logging.getLogger(__name__)


class TranscriptionResult:
    """Represents a transcription result from Deepgram."""

    def __init__(self, transcript: str, *, is_final: bool, confidence: float = 0.0):
        """Initialize transcription result.

        Args:
            transcript: The transcribed text
            is_final: Whether this is a final result or interim
            confidence: Confidence score (0-1) if available

        """
        self.transcript = transcript
        self.is_final = is_final
        self.confidence = confidence

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "transcript": self.transcript,
            "is_final": self.is_final,
            "confidence": self.confidence,
        }


class DeepgramService:
    """Service for Deepgram streaming speech-to-text operations."""

    def __init__(self):
        """Initialize the Deepgram client."""
        self.api_key = settings.deepgram_api_key
        if not self.api_key:
            logger.warning("Deepgram API key not configured")

        self.client = AsyncDeepgramClient(api_key=self.api_key)
        self.language = getattr(settings, "stt_language", "es")  # Chilean Spanish

        logger.info(
            "Deepgram service initialized (language: %s, model: nova-2)",
            self.language,
        )

    async def transcribe_stream(
        self, audio_stream: AsyncIterator[bytes]
    ) -> AsyncIterator[TranscriptionResult]:
        """Transcribe streaming audio in real-time.

        This method accepts an async iterator of audio chunks and sends them
        to Deepgram's API, yielding transcription results as they become available.

        Args:
            audio_stream: Async iterator of audio chunk bytes

        Yields:
            TranscriptionResult objects with transcript and is_final flag

        """
        try:
            logger.info("Initiating Deepgram streaming connection")

            # Collect all audio chunks first since Deepgram SDK streaming
            # requires a complete buffer or use of the v2 API
            audio_buffer = b""
            chunk_count = 0
            async for chunk in audio_stream:
                if chunk:
                    audio_buffer += chunk
                    chunk_count += 1
                    logger.debug(
                        "Buffered audio chunk %d (%d bytes)", chunk_count, len(chunk)
                    )

            if not audio_buffer:
                logger.warning("No audio data received")
                return

            logger.info("All audio chunks buffered (%d bytes total)", len(audio_buffer))

            # Use Deepgram's prerecorded endpoint for buffered audio
            # This works with the current SDK version
            try:
                response = await self.client.listen.prerecorded.v1(
                    {
                        "buffer": audio_buffer,
                    },
                    options={
                        "model": "nova-2",
                        "language": self.language,
                        "smart_format": True,
                    },
                )

                logger.info("Received response from Deepgram")

                # Parse and yield results
                for result in self._parse_deepgram_results(response):
                    yield result

            except AttributeError:
                # Fallback: try the standard prerecorded method
                logger.info("Attempting standard prerecorded transcription")
                response = await self.client.listen.prerecorded(
                    {"buffer": audio_buffer},
                    options={
                        "model": "nova-2",
                        "language": self.language,
                        "smart_format": True,
                    },
                )

                for result in self._parse_deepgram_results(response):
                    yield result

        except ApiError as e:
            msg = f"Deepgram API error during streaming: {e}"
            logger.exception(msg)
            raise
        except Exception as e:
            msg = f"Unexpected error during streaming transcription: {e}"
            logger.exception(msg)
            raise

    async def transcribe_stream_with_callback(
        self,
        audio_stream: AsyncIterator[bytes],
        on_interim: Callable[[str], Any] | None = None,
        on_final: Callable[[str], Any] | None = None,
    ) -> str:
        """Transcribe streaming audio with callbacks for interim/final results.

        Args:
            audio_stream: Async iterator of audio chunk bytes
            on_interim: Callback for interim results: func(transcript: str)
            on_final: Callback for final results: func(transcript: str)

        Returns:
            Final transcribed text

        """
        final_transcript = ""

        async for result in self.transcribe_stream(audio_stream):
            if result.is_final:
                final_transcript = result.transcript
                if on_final:
                    await self._call_async_or_sync(on_final, result.transcript)
                logger.info("Final transcript: %s", result.transcript)
            else:
                if on_interim:
                    await self._call_async_or_sync(on_interim, result.transcript)
                logger.debug("Interim transcript: %s", result.transcript)

        return final_transcript

    def _parse_deepgram_results(
        self, results: dict
    ) -> AsyncIterator[TranscriptionResult]:
        """Parse Deepgram results and yield TranscriptionResult objects.

        Args:
            results: Raw Deepgram API response

        Yields:
            TranscriptionResult objects

        """
        # Handle different response formats from Deepgram
        if "results" in results:
            for result in results["results"]:
                if "channel" in result and "alternatives" in result["channel"]:
                    for alt in result["channel"]["alternatives"]:
                        transcript = alt.get("transcript", "")
                        confidence = alt.get("confidence", 0.0)

                        # Determine if final based on is_final flag
                        is_final = result.get("is_final", False)

                        if transcript:
                            yield TranscriptionResult(
                                transcript=transcript,
                                is_final=is_final,
                                confidence=confidence,
                            )

        elif "transcript" in results:
            # Single transcript response
            yield TranscriptionResult(
                transcript=results["transcript"],
                is_final=True,
                confidence=results.get("confidence", 1.0),
            )

    @staticmethod
    async def _call_async_or_sync(
        func: Callable[..., Any], *args: object, **kwargs: object
    ) -> object:
        """Call a function that might be async or sync."""
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return func(*args, **kwargs)
        except Exception:
            logger.exception("Error calling callback function")


def get_deepgram_service() -> DeepgramService:
    """Create a new Deepgram service instance.

    Returns:
        DeepgramService instance

    """
    return DeepgramService()
