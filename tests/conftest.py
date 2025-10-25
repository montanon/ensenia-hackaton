"""Global pytest fixtures."""

from unittest.mock import MagicMock

import pytest


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
    mock_settings_obj.elevenlabs_api_key = "test-elevenlabs-key"
    mock_settings_obj.elevenlabs_voice_id = "test-voice-id"
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
    mock_settings_obj.workers_ai_embedding_model = "@cf/baai/bge-base-en-v1.5"
    mock_settings_obj.workers_ai_embedding_dimensions = 768

    # Patch the settings object
    monkeypatch.setattr("app.ensenia.core.config.settings", mock_settings_obj)

    return mock_settings_obj
