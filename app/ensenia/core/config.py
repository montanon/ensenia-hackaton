"""Application configuration using Pydantic Settings."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Cloudflare API
    cloudflare_api_token: str = "test-token"  # noqa: S105
    cloudflare_account_id: str = "test-account"

    # Cloudflare R2 (Object Storage)
    cloudflare_r2_bucket: str = "test-bucket"
    cloudflare_r2_access_key: str = "test-key"
    cloudflare_r2_secret_key: str = "test-secret"  # noqa: S105
    cloudflare_r2_endpoint: str = "https://test.r2.cloudflarestorage.com"

    # Cloudflare D1 (SQL Database)
    cloudflare_d1_database_id: str = "test-db-id"

    # Cloudflare Vectorize (Vector Database)
    cloudflare_vectorize_index: str = "test-index"

    # Cloudflare KV (Key-Value Cache)
    cloudflare_kv_namespace_id: str = "test-kv-id"

    # Cloudflare Worker URL
    cloudflare_worker_url: str = "http://localhost:8787"
    cloudflare_request_timeout: int = 30  # seconds
    cloudflare_max_retries: int = 3
    cloudflare_cache_ttl: int = 3600  # 1 hour for curriculum content

    # Database
    database_url: str = "postgresql+asyncpg://ensenia:hackathon@localhost:5433/ensenia"
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Chat Configuration
    chat_context_window: int = 10  # Number of messages to keep in context

    # ElevenLabs Text-to-Speech
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "pNInz6obpgDQGcFmaJgB"  # Dorothy - Chilean Spanish
    elevenlabs_model_id: str = "eleven_turbo_v2_5"

    # Audio Configuration
    audio_format: str = "mp3_44100_128"

    # Voice Settings by Grade Level
    voice_stability_elementary: float = 0.70  # Grades 1-4
    voice_stability_middle: float = 0.65  # Grades 5-8
    voice_stability_high: float = 0.60  # Grades 9-12

    voice_speed_elementary: float = 0.85
    voice_speed_middle: float = 0.95
    voice_speed_high: float = 1.00

    # Cache Configuration
    cache_max_size_mb: int = 500
    cache_ttl_hours: int = 24

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    openai_max_tokens: int = 2000
    openai_temperature: float = 0.4

    # Exercise Generation Settings
    generation_max_iterations: int = (
        1  # Reduced for performance (30s → 10s per exercise)
    )
    generation_quality_threshold: int = 6
    generation_model: str = "gpt-4-turbo-preview"

    # Cache Directory
    cache_dir: str = "./cache"

    # Application Settings
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # API Settings
    api_host: str = "0.0.0.0"  # noqa: S104
    api_port: int = 8000
    api_cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Cache Settings
    cache_default_ttl: int = 3600  # 1 hour
    cache_tts_ttl: int = 86400  # 24 hours

    # RAG Settings
    rag_top_k: int = 10
    rag_min_similarity_score: float = 0.7
    rag_chunk_size: int = 768
    rag_chunk_overlap: int = 128

    # Workers AI
    workers_ai_embedding_model: str = "@cf/baai/bge-base-en-v1.5"
    workers_ai_embedding_dimensions: int = 768
    workers_ai_timeout_connect: int = 10  # seconds to establish connection
    workers_ai_timeout_read: int = 60  # seconds to read response
    workers_ai_timeout_write: int = 120  # seconds to send request (large text chunks)
    workers_ai_timeout_pool: int = 10  # seconds to acquire connection from pool

    @field_validator("api_cors_origins", mode="after")
    @classmethod
    def parse_cors_origins(cls, v: str) -> list[str]:
        """Parse CORS origins from comma-separated string to list."""
        if not v or not v.strip():
            return ["http://localhost:3000", "http://localhost:5173"]
        return [origin.strip() for origin in v.split(",") if origin.strip()]


# Global settings instance
settings = Settings()
