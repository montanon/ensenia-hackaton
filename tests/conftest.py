"""Pytest configuration and fixtures."""

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ensenia.database.session import close_db, init_db


@pytest.fixture
def event_loop():
    """Create event loop for async tests.

    Creates a new event loop for each test function to ensure isolation.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    # Close any pending tasks
    try:
        loop.run_until_complete(loop.shutdown_asyncgens())
    finally:
        loop.close()


@pytest.fixture
async def setup_database():
    """Initialize database before tests.

    Note: API integration tests don't need this as the TestClient
    handles lifespan events. Only use this for unit tests that need
    direct database access without going through the API.
    """
    await init_db()
    yield
    await close_db()


@pytest.fixture(autouse=True)
async def reset_db_engine():
    """Reset the database engine before and after each test.

    This ensures the engine is not tied to a stale event loop.
    """
    # Dispose before test to ensure clean state
    from app.ensenia.database.session import engine

    await engine.dispose()

    yield

    # Dispose after test to clean up
    await engine.dispose()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for tests.

    This creates a new session for each test to avoid event loop conflicts.
    """
    # Import here to avoid circular dependency issues
    # Ensure database is initialized
    from app.ensenia.database.models import Base
    from app.ensenia.database.session import AsyncSessionLocal, engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create and yield session
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            # Always rollback to ensure test isolation
            # Tests should not persist data between runs
            await session.rollback()
            await session.close()


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Mock settings for all tests to avoid requiring .env file."""
    mock_settings_obj = MagicMock()
    mock_settings_obj.cloudflare_account_id = "test-account-id"
    mock_settings_obj.cloudflare_api_token = "test-api-token"  # noqa: S105
    mock_settings_obj.cloudflare_r2_bucket = "test-bucket"
    mock_settings_obj.cloudflare_r2_access_key = "test-access-key"
    mock_settings_obj.cloudflare_r2_secret_key = "test-secret-key"  # noqa: S105
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
    mock_settings_obj.elevenlabs_model_id = "eleven_turbo_v2_5"
    mock_settings_obj.audio_format = "mp3_44100_128"
    mock_settings_obj.voice_stability_elementary = 0.70
    mock_settings_obj.voice_stability_middle = 0.65
    mock_settings_obj.voice_stability_high = 0.60
    mock_settings_obj.voice_speed_elementary = 0.85
    mock_settings_obj.voice_speed_middle = 0.95
    mock_settings_obj.voice_speed_high = 1.00
    mock_settings_obj.cache_max_size_mb = 500
    mock_settings_obj.cache_ttl_hours = 24

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
    mock_settings_obj.api_host = "0.0.0.0"  # noqa: S104
    mock_settings_obj.api_port = 8000
    mock_settings_obj.api_cors_origins = ["http://localhost:3000"]
    mock_settings_obj.cache_default_ttl = 3600
    mock_settings_obj.cache_tts_ttl = 86400
    mock_settings_obj.rag_top_k = 10
    mock_settings_obj.rag_min_similarity_score = 0.7
    mock_settings_obj.rag_chunk_size = 768
    mock_settings_obj.rag_chunk_overlap = 128
    mock_settings_obj.workers_ai_embedding_model = "@cf/baai/bge-base-en-v1.5"
    mock_settings_obj.workers_ai_embedding_dimensions = 768
    mock_settings_obj.openai_api_key = "test-openai-key"
    mock_settings_obj.openai_model = "gpt-4-turbo-preview"
    mock_settings_obj.generation_max_iterations = 3
    mock_settings_obj.generation_quality_threshold = 8
    mock_settings_obj.generation_model = "gpt-4-turbo-preview"
    mock_settings_obj.database_url = (
        "postgresql+asyncpg://test:test@localhost:5433/test"
    )
    mock_settings_obj.cloudflare_worker_url = "http://localhost:8787"
    mock_settings_obj.cache_dir = "./test_cache"

    # Patch the settings object to return our mock
    monkeypatch.setattr("app.ensenia.core.config.settings", mock_settings_obj)
    monkeypatch.setattr(
        "app.ensenia.services.research_service.settings", mock_settings_obj
    )
    monkeypatch.setattr("app.ensenia.services.chat_service.settings", mock_settings_obj)
    monkeypatch.setattr(
        "app.ensenia.services.elevenlabs_service.settings", mock_settings_obj
    )
    monkeypatch.setattr(
        "app.ensenia.services.stream_orchestrator.settings", mock_settings_obj
    )
    monkeypatch.setattr("app.ensenia.database.session.settings", mock_settings_obj)

    return mock_settings_obj


@pytest.fixture
def sample_multiple_choice_exercise():
    """Sample multiple choice exercise content."""
    return {
        "question": "¿Cuál es la capital de Chile?",
        "learning_objective": "Identificar la capital de Chile según las Bases Curriculares",
        "options": ["Santiago", "Valparaíso", "Concepción", "Antofagasta"],
        "correct_answer": 0,
        "explanation": "Santiago es la capital de Chile desde 1818",
    }


@pytest.fixture
def sample_true_false_exercise():
    """Sample true/false exercise content."""
    return {
        "question": "Chile es un país ubicado en América del Sur",
        "learning_objective": "Reconocer la ubicación geográfica de Chile",
        "correct_answer": True,
        "explanation": "Chile está ubicado en el extremo sudoeste de América del Sur",
    }


@pytest.fixture
def sample_short_answer_exercise():
    """Sample short answer exercise content."""
    return {
        "question": "Explica brevemente qué es la fotosíntesis",
        "learning_objective": "Comprender el proceso de fotosíntesis en las plantas",
        "rubric": [
            "Menciona que es un proceso de las plantas",
            "Explica que convierte luz solar en energía",
            "Menciona el rol del CO2 y agua",
        ],
        "example_answer": "La fotosíntesis es el proceso por el cual las plantas convierten la luz solar, agua y CO2 en glucosa y oxígeno.",
        "max_words": 100,
    }


@pytest.fixture
def sample_essay_exercise():
    """Sample essay exercise content."""
    return {
        "question": "Analiza las causas y consecuencias de la Independencia de Chile",
        "learning_objective": "Analizar el proceso de independencia según Bases Curriculares",
        "rubric": [
            "Identifica causas internas y externas",
            "Menciona personajes clave",
            "Describe consecuencias políticas",
            "Describe consecuencias sociales",
        ],
        "key_points": [
            "Influencia de la Ilustración",
            "Rol de líderes como O'Higgins y San Martín",
            "Formación de la república",
        ],
        "min_words": 150,
        "max_words": 500,
    }
