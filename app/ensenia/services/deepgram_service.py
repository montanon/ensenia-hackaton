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
from collections.abc import AsyncIterator

import aiofiles
from deepgram import DeepgramClient, PrerecordedOptions
from deepgram.types import DeepgramError

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

        self.client = DeepgramClient(api_key=self.api_key)
        self.language = getattr(settings, "stt_language", "es")  # Chilean Spanish

        logger.info(
            "Deepgram service initialized (language: %s, model: nova-2)",
            self.language,
        )

    async def transcribe_stream(
        self, audio_stream: AsyncIterator[bytes]
    ) -> AsyncIterator[TranscriptionResult]:
        """Transcribe streaming audio in real-time.

        This method accepts an async iterator of audio chunks and yields
        transcription results as they become available from Deepgram.
        Uses event callbacks for true streaming results.

        Args:
            audio_stream: Async iterator of audio chunk bytes

        Yields:
            TranscriptionResult objects with transcript and is_final flag

        """
        try:
            logger.info("Initiating Deepgram streaming connection")

            # Create connection with streaming options
            with self.client.listen.live(
                options={
                    "model": "nova-2",
                    "language": self.language,
                    "smart_format": True,
                    "interim_results": True,
                }
            ) as connection:
                logger.info("Deepgram streaming connection established")

                # Track results to stream them as they arrive
                results_received = []

                # Define event handlers for results
                def handle_result(message: dict) -> None:
                    """Handle transcription result from Deepgram."""
                    try:
                        if message:
                            results_received.append(message)
                            msg = f"Deepgram result received: {message}"
                            logger.debug(msg)
                    except Exception:
                        logger.exception("Error handling Deepgram result")

                # Attach handler to connection if supported
                if hasattr(connection, "on_message"):
                    connection.on_message(handle_result)

                # Send all audio chunks
                chunk_count = 0
                async for chunk in audio_stream:
                    if chunk:
                        try:
                            connection.send(chunk)
                            chunk_count += 1
                            msg = f"Sent audio chunk {chunk_count} ({len(chunk)} bytes)"
                            logger.debug(msg)
                        except Exception:
                            logger.exception("Error sending chunk to Deepgram")
                            raise

                msg = (
                    f"All audio chunks sent ({chunk_count} total). Finalizing stream..."
                )
                logger.info(msg)

                # Finish the stream
                connection.finish()

                # Collect final results
                final_message = connection.get_close_message()

                if final_message:
                    logger.info("Deepgram final results received")
                    # Parse final results
                    for result in self._parse_deepgram_results(final_message):
                        yield result
                else:
                    # Also yield any results collected during streaming
                    for msg in results_received:
                        for result in self._parse_deepgram_results(msg):
                            yield result

        except DeepgramError:
            msg = "Deepgram API error during streaming."
            logger.exception(msg)
            raise
        except Exception:
            msg = "Unexpected error during streaming transcription."
            logger.exception(msg)
            raise

    async def transcribe_stream_with_callback(
        self,
        audio_stream: AsyncIterator[bytes],
        on_interim: callable | None = None,
        on_final: callable | None = None,
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
        func: callable, *args: object, **kwargs: object
    ) -> object:
        """Call a function that might be async or sync."""
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return func(*args, **kwargs)
        except Exception:
            logger.exception("Error calling callback function")

    async def transcribe_file(self, audio_bytes: bytes) -> str:
        """Transcribe a complete audio file (non-streaming fallback).

        Args:
            audio_bytes: Complete audio file bytes

        Returns:
            Transcribed text

        """
        try:
            logger.info(
                "Transcribing audio file (%s bytes) with Deepgram", len(audio_bytes)
            )

            async with aiofiles.open("/tmp/deepgram_audio.webm", "wb") as f:
                await f.write(audio_bytes)

            async with aiofiles.open("/tmp/deepgram_audio.webm", "rb") as f:
                audio_data = await f.read()
                response = self.client.listen.prerecorded(
                    {"buffer": audio_data},
                    PrerecordedOptions(
                        model="nova-2",
                        language=self.language,
                        smart_format=True,
                    ),
                )

            transcript = response.results.channels[0].alternatives[0].transcript
            logger.info("File transcription completed: %s...", transcript[:100])
            return transcript

        except Exception:
            logger.exception("Error transcribing audio file")
            raise


def get_deepgram_service() -> DeepgramService:
    """Create a new Deepgram service instance.

    Returns:
        DeepgramService instance

    """
    return DeepgramService()
