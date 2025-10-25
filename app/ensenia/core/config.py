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
    cloudflare_api_token: str = "test-token"
    cloudflare_account_id: str = "test-account"

    # Cloudflare R2 (Object Storage)
    cloudflare_r2_bucket: str = "test-bucket"
    cloudflare_r2_access_key: str = "test-key"
    cloudflare_r2_secret_key: str = "test-secret"
    cloudflare_r2_endpoint: str = "https://test.r2.cloudflarestorage.com"

    # Cloudflare D1 (SQL Database)
    cloudflare_d1_database_id: str = "test-db-id"

    # Cloudflare Vectorize (Vector Database)
    cloudflare_vectorize_index: str = "test-index"

    # Cloudflare KV (Key-Value Cache)
    cloudflare_kv_namespace_id: str = "test-kv-id"

    # ElevenLabs Text-to-Speech
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    # Application Settings
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # API Settings
    api_host: str = "0.0.0.0"
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

    @field_validator("api_cors_origins", mode="after")
    @classmethod
    def parse_cors_origins(cls, v: str) -> list[str]:
        """Parse CORS origins from comma-separated string to list."""
        if not v or not v.strip():
            return ["http://localhost:3000", "http://localhost:5173"]
        return [origin.strip() for origin in v.split(",") if origin.strip()]


# Global settings instance
settings = Settings()
