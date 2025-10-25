"""Pytest configuration and fixtures."""

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ensenia.database.session import close_db, get_db, init_db


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_database():
    """Initialize database before tests."""
    await init_db()
    yield
    await close_db()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for tests."""
    async for session in get_db():
        yield session
        break


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Mock settings for all tests to avoid requiring .env file."""
    mock_settings_obj = MagicMock()
    mock_settings_obj.cloudflare_account_id = "test-account-id"
    mock_settings_obj.cloudflare_api_token = "test-api-token"
    mock_settings_obj.cloudflare_r2_bucket = "test-bucket"
    mock_settings_obj.cloudflare_r2_access_key = "test-access-key"
    mock_settings_obj.cloudflare_r2_secret_key = "test-secret-key"
    mock_settings_obj.cloudflare_r2_endpoint = "https://test.r2.cloudflarestorage.com"
    mock_settings_obj.cloudflare_d1_database_id = "test-db-id"
    mock_settings_obj.cloudflare_vectorize_index = "test-index"
    mock_settings_obj.cloudflare_kv_namespace_id = "test-kv-id"

    # New Worker integration settings
    mock_settings_obj.cloudflare_worker_url = "https://test-worker.workers.dev"
    mock_settings_obj.cloudflare_request_timeout = 30
    mock_settings_obj.cloudflare_max_retries = 3
    mock_settings_obj.cloudflare_cache_ttl = 3600

    # OpenAI settings
    mock_settings_obj.openai_api_key = "test-openai-key"
    mock_settings_obj.openai_model = "gpt-4-turbo-preview"
    mock_settings_obj.openai_max_tokens = 2000
    mock_settings_obj.openai_temperature = 0.4

    # ElevenLabs settings
    mock_settings_obj.elevenlabs_api_key = "test-elevenlabs-key"
    mock_settings_obj.elevenlabs_voice_id = "test-voice-id"

    # Database settings
    mock_settings_obj.database_url = (
        "postgresql+asyncpg://test:test@localhost:5433/test"
    )
    mock_settings_obj.database_pool_size = 5
    mock_settings_obj.database_max_overflow = 10

    # Chat settings
    mock_settings_obj.chat_context_window = 10

    # App settings
    mock_settings_obj.environment = "test"
    mock_settings_obj.debug = True
    mock_settings_obj.log_level = "INFO"
    mock_settings_obj.api_host = "0.0.0.0"
    mock_settings_obj.api_port = 8000
    mock_settings_obj.api_cors_origins = ["http://localhost:3000"]
    mock_settings_obj.cache_default_ttl = 3600
    mock_settings_obj.cache_tts_ttl = 86400
    mock_settings_obj.rag_top_k = 10
    mock_settings_obj.rag_min_similarity_score = 0.7
    mock_settings_obj.rag_chunk_size = 768
    mock_settings_obj.rag_chunk_overlap = 128
    mock_settings_obj.workers_ai_embedding_model = "@cf/baai/bge-large-en-v1.5"
    mock_settings_obj.workers_ai_embedding_dimensions = 1024

    # Patch the get_settings function to return our mock
    monkeypatch.setattr("app.ensenia.config.get_settings", lambda: mock_settings_obj)
    monkeypatch.setattr(
        "app.ensenia.services.research_service.settings", mock_settings_obj
    )

    return mock_settings_obj
