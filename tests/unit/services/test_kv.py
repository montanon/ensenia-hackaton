"""Unit tests for KVService."""

import json

import pytest
from pytest_httpx import HTTPXMock

from app.ensenia.services.cloudflare.kv import KVService


class TestKVService:
    """Unit tests for KVService."""

    @pytest.fixture
    def kv_service(self):
        """Create KVService instance."""
        return KVService()

    def test_init(self, kv_service):
        """Test KVService initialization."""
        assert kv_service.account_id is not None
        assert kv_service.namespace_id is not None
        assert kv_service.api_token is not None
        assert kv_service.namespace_prefix == "ensenia"

    def test_make_key(self, kv_service):
        """Test key prefixing."""
        key = kv_service._make_key("test")
        assert key == "ensenia:test"

    @pytest.mark.asyncio
    async def test_set_and_get(self, kv_service, httpx_mock: HTTPXMock):
        """Test setting and getting a value."""
        # Mock set request
        httpx_mock.add_response(json={"success": True})

        # Mock get request
        httpx_mock.add_response(text='"test value"')

        # Set value
        await kv_service.set("key1", "test value")

        # Get value
        value = await kv_service.get("key1")

        assert value == "test value"

    @pytest.mark.asyncio
    async def test_set_json(self, kv_service, httpx_mock: HTTPXMock):
        """Test setting and getting JSON data."""
        test_data = {"name": "test", "value": 123}

        # Mock set request
        httpx_mock.add_response(json={"success": True})

        # Mock get request
        httpx_mock.add_response(text=json.dumps(test_data))

        await kv_service.set("json_key", test_data)
        value = await kv_service.get("json_key")

        assert value == test_data
        assert value["name"] == "test"
        assert value["value"] == 123

    @pytest.mark.asyncio
    async def test_get_not_found(self, kv_service, httpx_mock: HTTPXMock):
        """Test getting non-existent key returns None."""
        httpx_mock.add_response(status_code=404)

        value = await kv_service.get("nonexistent")

        assert value is None

    @pytest.mark.asyncio
    async def test_delete(self, kv_service, httpx_mock: HTTPXMock):
        """Test deleting a key."""
        httpx_mock.add_response(json={"success": True})

        await kv_service.delete("key1")

        # Verify the request was made
        assert len(httpx_mock.get_requests()) == 1

    @pytest.mark.asyncio
    async def test_exists(self, kv_service, httpx_mock: HTTPXMock):
        """Test checking if key exists."""
        # Mock key exists
        httpx_mock.add_response(text="value")

        exists = await kv_service.exists("existing_key")

        assert exists is True

    @pytest.mark.asyncio
    async def test_not_exists(self, kv_service, httpx_mock: HTTPXMock):
        """Test checking if key doesn't exist."""
        httpx_mock.add_response(status_code=404)

        exists = await kv_service.exists("nonexistent")

        assert exists is False

    @pytest.mark.asyncio
    async def test_list_keys(self, kv_service, httpx_mock: HTTPXMock):
        """Test listing keys."""
        httpx_mock.add_response(
            json={
                "success": True,
                "result": [
                    {"name": "ensenia:key1"},
                    {"name": "ensenia:key2"},
                    {"name": "ensenia:key3"},
                ],
            }
        )

        keys = await kv_service.list_keys(prefix="", limit=10)

        assert len(keys) == 3
        assert keys[0]["name"] == "ensenia:key1"

    @pytest.mark.asyncio
    async def test_get_namespace_info(self, kv_service, httpx_mock: HTTPXMock):
        """Test getting namespace info."""
        httpx_mock.add_response(
            json={
                "success": True,
                "result": {"title": "ensenia-cache", "id": "abc123"},
            }
        )

        info = await kv_service.get_namespace_info()

        assert info["title"] == "ensenia-cache"
        assert info["id"] == "abc123"

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, kv_service, httpx_mock: HTTPXMock):
        """Test setting value with TTL."""
        httpx_mock.add_response(json={"success": True})

        await kv_service.set("temp_key", "temp_value", ttl=3600)

        # Verify request includes TTL parameter
        requests = httpx_mock.get_requests()
        assert len(requests) == 1
        assert "expiration_ttl=3600" in str(requests[0].url)
