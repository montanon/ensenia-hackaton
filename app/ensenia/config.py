"""Configuration management using Pydantic Settings.

Loads environment variables for ElevenLabs TTS integration.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ElevenLabs API Configuration
    elevenlabs_api_key: str
    elevenlabs_voice_id: str = "pNInz6obpgDQGcFmaJgB"  # Dorothy - Chilean Spanish
    elevenlabs_model_id: str = "eleven_turbo_v2_5"

    # Cache Configuration
    cache_dir: str = "./cache/audio"
    cache_max_size_mb: int = 500
    cache_ttl_hours: int = 24

    # Audio Configuration
    audio_format: str = "mp3_44100_128"

    # Voice Settings by Grade Level
    voice_stability_elementary: float = 0.70  # Grades 1-4
    voice_stability_middle: float = 0.65  # Grades 5-8
    voice_stability_high: float = 0.60  # Grades 9-12

    voice_speed_elementary: float = 0.85
    voice_speed_middle: float = 0.95
    voice_speed_high: float = 1.00

    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    openai_max_tokens: int = 2000
    openai_temperature: float = 0.4

    # Cloudflare Configuration
    cloudflare_worker_url: str
    cloudflare_api_token: str | None = None
    cloudflare_request_timeout: int = 30  # seconds
    cloudflare_max_retries: int = 3
    cloudflare_cache_ttl: int = 3600  # 1 hour for curriculum content

    # Database Configuration
    database_url: str = "postgresql+asyncpg://ensenia:hackathon@localhost:5433/ensenia"
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Chat Configuration
    chat_context_window: int = 10  # Number of messages to keep in context

    # Application Settings
    environment: Literal["development", "production", "hackathon"] = "development"
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()
