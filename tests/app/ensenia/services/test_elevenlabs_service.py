"""Unit tests for ElevenLabsService - Core functionality."""

import time
from unittest.mock import Mock, patch

import pytest

from app.ensenia.services.elevenlabs_service import (
    ElevenLabsService,
    get_elevenlabs_service,
)


@pytest.fixture
def mock_settings():
    """Mock settings."""
    with patch("app.ensenia.services.elevenlabs_service.settings") as mock:
        mock.elevenlabs_api_key = "test-key"
        mock.cache_dir = "./test_cache"
        mock.cache_ttl_hours = 24
        mock.elevenlabs_voice_id = "test-voice"
        mock.elevenlabs_model_id = "test-model"
        mock.audio_format = "mp3_44100_128"
        mock.voice_stability_elementary = 0.70
        mock.voice_stability_middle = 0.65
        mock.voice_stability_high = 0.60
        mock.voice_speed_elementary = 0.85
        mock.voice_speed_middle = 0.95
        mock.voice_speed_high = 1.00
        yield mock


@pytest.fixture
def mock_client():
    """Mock ElevenLabs client."""
    with patch("app.ensenia.services.elevenlabs_service.AsyncElevenLabs"):
        yield


@pytest.fixture
def service(mock_settings, mock_client, tmp_path):  # noqa: ARG001
    """Create service with temp cache."""
    mock_settings.cache_dir = str(tmp_path / "cache")
    return ElevenLabsService()


class TestCacheKeyGeneration:
    """Test cache key generation logic."""

    def test_cache_key_is_deterministic(self, service):
        """Same inputs produce same cache key."""
        key1 = service._generate_cache_key("test", "v1", "m1", {"s": 0.5})
        key2 = service._generate_cache_key("test", "v1", "m1", {"s": 0.5})
        assert key1 == key2
        assert len(key1) == 64

    def test_cache_key_differs_for_different_inputs(self, service):
        """Different inputs produce different keys."""
        key1 = service._generate_cache_key("text1", "v", "m", {})
        key2 = service._generate_cache_key("text2", "v", "m", {})
        assert key1 != key2


class TestVoiceSettings:
    """Test grade-level voice settings."""

    def test_elementary_settings(self, service, mock_settings):
        """Elementary grades get appropriate settings."""
        for grade in [1, 2, 3, 4]:
            vs = service.get_voice_settings(grade)
            assert vs.speed == mock_settings.voice_speed_elementary
            assert vs.stability == mock_settings.voice_stability_elementary

    def test_middle_school_settings(self, service, mock_settings):
        """Middle school grades get appropriate settings."""
        for grade in [5, 6, 7, 8]:
            vs = service.get_voice_settings(grade)
            assert vs.speed == mock_settings.voice_speed_middle
            assert vs.stability == mock_settings.voice_stability_middle

    def test_high_school_settings(self, service, mock_settings):
        """High school grades get appropriate settings."""
        for grade in [9, 10, 11, 12]:
            vs = service.get_voice_settings(grade)
            assert vs.speed == mock_settings.voice_speed_high
            assert vs.stability == mock_settings.voice_stability_high


class TestCacheOperations:
    """Test cache save/retrieve operations."""

    @pytest.mark.asyncio
    async def test_save_and_get_cache(self, service):
        """Can save and retrieve from cache."""
        key = "test-key"
        data = b"test audio data"

        await service._save_to_cache(key, data)
        result = await service._get_cached_audio(key)

        assert result == data

    @pytest.mark.asyncio
    async def test_nonexistent_cache_returns_none(self, service):
        """Getting nonexistent cache returns None."""
        result = await service._get_cached_audio("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_expired_cache_deleted(self, service, mock_settings):
        """Expired cache is deleted."""
        key = "old-key"
        cache_file = service.cache_dir / f"{key}.mp3"
        cache_file.write_bytes(b"old")

        # Make it old
        old_time = time.time() - (mock_settings.cache_ttl_hours + 1) * 3600
        import os

        os.utime(cache_file, (old_time, old_time))

        result = await service._get_cached_audio(key)

        assert result is None
        assert not cache_file.exists()


class TestFactoryFunction:
    """Test service factory."""

    def test_factory_creates_instance(self, mock_settings, mock_client):
        """Factory returns service instance."""
        service = get_elevenlabs_service()
        assert isinstance(service, ElevenLabsService)

    def test_factory_creates_new_instance_each_time(self, mock_settings, mock_client):
        """Each call creates a new instance."""
        s1 = get_elevenlabs_service()
        s2 = get_elevenlabs_service()
        assert s1 is not s2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
