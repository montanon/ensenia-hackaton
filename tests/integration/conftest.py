"""Pytest fixtures for integration tests."""

import pytest

from app.ensenia.services.cloudflare import (
    D1Service,
    KVService,
    R2Service,
    VectorizeService,
    WorkersAIService,
)


@pytest.fixture
def r2_service():
    """Provide R2 service instance."""
    return R2Service()


@pytest.fixture
def d1_service():
    """Provide D1 service instance."""
    return D1Service()


@pytest.fixture
def vectorize_service():
    """Provide Vectorize service instance."""
    return VectorizeService()


@pytest.fixture
def kv_service():
    """Provide KV service instance."""
    return KVService()


@pytest.fixture
def workers_ai_service():
    """Provide Workers AI service instance."""
    return WorkersAIService()
