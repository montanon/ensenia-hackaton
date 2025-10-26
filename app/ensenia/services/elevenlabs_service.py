"""ElevenLabs TTS Service for Chilean Educational Content.

Handles:
- Text-to-speech conversion using Dorothy voice
- Grade-specific voice settings
- File-based caching
- Streaming support
"""

import asyncio
import hashlib
import json
import logging
import time
from collections.abc import AsyncIterator
from pathlib import Path

import aiofiles
from elevenlabs import VoiceSettings
from elevenlabs.client import AsyncElevenLabs

from app.ensenia.core.config import settings

logger = logging.getLogger(__name__)

BASIC_LEVEL_THRESHOLD = 4
MEDIUM_LEVEL_THRESHOLD = 8


class ElevenLabsService:
    """Service for ElevenLabs TTS operations."""

    def __init__(self):
        """Initialize the ElevenLabs client and cache directory."""
        self.client = AsyncElevenLabs(api_key=settings.elevenlabs_api_key)
        self.cache_dir = Path(settings.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info("ElevenLabs service initialized with cache at %s", self.cache_dir)

    def _generate_cache_key(
        self, text: str, voice_id: str, model_id: str, voice_settings: dict
    ) -> str:
        """Generate deterministic cache key from parameters.

        Args:
            text: Text content
            voice_id: ElevenLabs voice ID
            model_id: ElevenLabs model ID
            voice_settings: Voice configuration dict

        Returns:
            SHA-256 hash as cache key

        """
        content = (
            f"{text}_{voice_id}_{model_id}_{json.dumps(voice_settings, sort_keys=True)}"
        )
        return hashlib.sha256(content.encode()).hexdigest()

    async def _get_cached_audio(self, cache_key: str) -> bytes | None:
        """Retrieve audio from file cache if available and valid.

        Args:
            cache_key: Cache key to lookup

        Returns:
            Audio bytes if cached, None otherwise

        """
        cache_file = self.cache_dir / f"{cache_key}.mp3"

        if not cache_file.exists():
            return None

        age_hours = (time.time() - cache_file.stat().st_mtime) / 3600
        if age_hours > settings.cache_ttl_hours:
            logger.info("Cache expired: %s (age: %.1fh)", cache_key, age_hours)
            # Delete expired cache asynchronously
            await asyncio.to_thread(cache_file.unlink)
            return None

        logger.info("Cache hit: %s", cache_key)
        async with aiofiles.open(cache_file, "rb") as f:
            return await f.read()

    async def _save_to_cache(self, cache_key: str, audio_data: bytes) -> None:
        """Save audio to file cache.

        Args:
            cache_key: Cache key
            audio_data: Audio bytes to cache

        """
        cache_file = self.cache_dir / f"{cache_key}.mp3"

        async with aiofiles.open(cache_file, "wb") as f:
            await f.write(audio_data)

        logger.info("Cached audio: %s (%s bytes)", cache_key, len(audio_data))

    def get_voice_settings(self, grade_level: int) -> VoiceSettings:
        """Get grade-appropriate voice settings.

        Args:
            grade_level: Student grade (1-12)

        Returns:
            VoiceSettings configured for grade level

        """
        if grade_level <= BASIC_LEVEL_THRESHOLD:
            # Elementary: Slower, more consistent
            return VoiceSettings(
                stability=settings.voice_stability_elementary,
                similarity_boost=0.75,
                style=0.20,
                use_speaker_boost=True,
                speed=settings.voice_speed_elementary,
            )
        if grade_level <= MEDIUM_LEVEL_THRESHOLD:
            # Middle school: Balanced
            return VoiceSettings(
                stability=settings.voice_stability_middle,
                similarity_boost=0.75,
                style=0.25,
                use_speaker_boost=True,
                speed=settings.voice_speed_middle,
            )
        # High school: Natural pace
        return VoiceSettings(
            stability=settings.voice_stability_high,
            similarity_boost=0.75,
            style=0.30,
            use_speaker_boost=True,
            speed=settings.voice_speed_high,
        )

    async def generate_speech(
        self, text: str, grade_level: int = 5, *, use_cache: bool = True
    ) -> bytes:
        """Generate speech from text with caching.

        Args:
            text: Text to convert to speech
            grade_level: Student grade level (1-12)
            use_cache: Whether to use cached audio

        Returns:
            Audio bytes (MP3 format)

        Raises:
            Exception: If TTS generation fails

        """
        # Get voice settings for grade level
        voice_settings = self.get_voice_settings(grade_level)
        voice_settings_dict = {
            "stability": voice_settings.stability,
            "similarity_boost": voice_settings.similarity_boost,
            "style": voice_settings.style,
            "use_speaker_boost": voice_settings.use_speaker_boost,
            "speed": voice_settings.speed,
        }

        # Generate cache key
        cache_key = self._generate_cache_key(
            text,
            settings.elevenlabs_voice_id,
            settings.elevenlabs_model_id,
            voice_settings_dict,
        )

        # Check cache if enabled
        if use_cache:
            cached_audio = await self._get_cached_audio(cache_key)
            if cached_audio:
                return cached_audio

        # Generate audio
        logger.info("Generating audio (grade %s): %s...", grade_level, text[:50])

        try:
            audio_generator = self.client.text_to_speech.convert(
                text=text,
                voice_id=settings.elevenlabs_voice_id,
                model_id=settings.elevenlabs_model_id,
                output_format=settings.audio_format,
                voice_settings=voice_settings,
            )

            # Collect all audio chunks
            audio_chunks = [chunk async for chunk in audio_generator if chunk]
            audio_bytes = b"".join(audio_chunks)

            # Cache the result
            if use_cache:
                await self._save_to_cache(cache_key, audio_bytes)

            logger.info(
                "Audio generated successfully: %s bytes",
                len(audio_bytes),
            )
            return audio_bytes

        except Exception:
            logger.exception("Error generating audio.")
            raise

    async def generate_speech_streaming(
        self, text: str, grade_level: int = 5
    ) -> AsyncIterator[bytes]:
        """Generate speech with streaming for real-time playback.

        Args:
            text: Text to convert
            grade_level: Student grade level

        Yields:
            Audio chunks as they're generated

        """
        voice_settings = self.get_voice_settings(grade_level)

        try:
            audio_stream = self.client.text_to_speech.stream(
                text=text,
                voice_id=settings.elevenlabs_voice_id,
                model_id=settings.elevenlabs_model_id,
                output_format=settings.audio_format,
                voice_settings=voice_settings,
            )

            async for chunk in audio_stream:
                if chunk:
                    yield chunk

        except Exception:
            logger.exception("Error streaming audio.")
            raise

    async def generate_multiple_segments(
        self, segments: list[dict], grade_level: int = 5
    ) -> list[bytes]:
        """Generate audio for multiple text segments.

        Args:
            segments: List of dicts with 'text' and optional 'grade_level'
            grade_level: Default grade level

        Returns:
            List of audio bytes for each segment

        """
        audio_segments = []

        for segment in segments:
            text = segment["text"]
            seg_grade = segment.get("grade_level", grade_level)

            audio = await self.generate_speech(text, seg_grade)
            audio_segments.append(audio)

        logger.info("Generated %s audio segments", len(audio_segments))
        return audio_segments


def get_elevenlabs_service() -> ElevenLabsService:
    """Create a new ElevenLabs service instance.

    Returns:
        ElevenLabsService instance

    """
    return ElevenLabsService()
