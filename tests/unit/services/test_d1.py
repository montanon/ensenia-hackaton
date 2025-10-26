"""Unit tests for D1Service."""

import pytest
from pytest_httpx import HTTPXMock

from app.ensenia.services.cloudflare.d1 import D1Service


class TestD1Service:
    """Unit tests for D1Service."""

    @pytest.fixture
    def d1_service(self):
        """Create D1Service instance."""
        return D1Service()

    def test_init(self, d1_service):
        """Test D1Service initialization."""
        assert d1_service.account_id is not None
        assert d1_service.database_id is not None
        assert d1_service.api_token is not None
        assert "cloudflare.com" in d1_service.base_url

    @pytest.mark.asyncio
    async def test_execute_success(self, d1_service, httpx_mock: HTTPXMock):
        """Test successful query execution."""
        # Mock successful response
        httpx_mock.add_response(
            json={
                "success": True,
                "result": [{"results": [{"id": 1, "name": "test"}], "meta": {}}],
            }
        )

        result = await d1_service.execute("SELECT * FROM test")

        assert "results" in result
        assert result["results"][0]["id"] == 1

    @pytest.mark.asyncio
    async def test_execute_with_params(self, d1_service, httpx_mock: HTTPXMock):
        """Test query execution with parameters."""
        httpx_mock.add_response(
            json={
                "success": True,
                "result": [{"results": [{"id": 1, "name": "Alice"}], "meta": {}}],
            }
        )

        result = await d1_service.execute(
            "SELECT * FROM users WHERE name = ?", ["Alice"]
        )

        assert result["results"][0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_execute_failure(self, d1_service, httpx_mock: HTTPXMock):
        """Test query execution failure."""
        httpx_mock.add_response(
            json={"success": False, "errors": [{"message": "Query failed"}]}
        )

        with pytest.raises(RuntimeError, match="D1 query failed"):
            await d1_service.execute("SELECT * FROM test")

    @pytest.mark.asyncio
    async def test_query(self, d1_service, httpx_mock: HTTPXMock):
        """Test query method returns results list."""
        httpx_mock.add_response(
            json={
                "success": True,
                "result": [
                    {
                        "results": [
                            {"id": 1, "name": "Alice"},
                            {"id": 2, "name": "Bob"},
                        ],
                        "meta": {},
                    }
                ],
            }
        )

        results = await d1_service.query("SELECT * FROM users")

        assert len(results) == 2
        assert results[0]["name"] == "Alice"
        assert results[1]["name"] == "Bob"

    @pytest.mark.asyncio
    async def test_query_one(self, d1_service, httpx_mock: HTTPXMock):
        """Test query_one returns first result."""
        httpx_mock.add_response(
            json={
                "success": True,
                "result": [{"results": [{"id": 1, "name": "Alice"}], "meta": {}}],
            }
        )

        result = await d1_service.query_one("SELECT * FROM users LIMIT 1")

        assert result is not None
        assert result["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_query_one_no_results(self, d1_service, httpx_mock: HTTPXMock):
        """Test query_one returns None when no results."""
        httpx_mock.add_response(
            json={"success": True, "result": [{"results": [], "meta": {}}]}
        )

        result = await d1_service.query_one("SELECT * FROM users WHERE id = 999")

        assert result is None

    @pytest.mark.asyncio
    async def test_execute_update(self, d1_service, httpx_mock: HTTPXMock):
        """Test execute_update returns affected rows count."""
        httpx_mock.add_response(
            json={"success": True, "result": [{"meta": {"changes": 5}}]}
        )

        affected_rows = await d1_service.execute_update(
            "DELETE FROM users WHERE active = 0"
        )

        assert affected_rows == 5

    @pytest.mark.asyncio
    async def test_execute_batch(self, d1_service, httpx_mock: HTTPXMock):
        """Test batch query execution."""
        httpx_mock.add_response(
            json={
                "success": True,
                "result": [
                    {"results": [{"id": 1}], "meta": {"changes": 1}},
                    {"results": [{"id": 2}], "meta": {"changes": 1}},
                    {"results": [{"count": 2}], "meta": {}},
                ],
            }
        )

        queries = [
            {"sql": "INSERT INTO users (id) VALUES (1)"},
            {"sql": "INSERT INTO users (id) VALUES (2)"},
            {"sql": "SELECT COUNT(*) as count FROM users"},
        ]

        results = await d1_service.execute_batch(queries)

        assert len(results) == 3
        assert results[2]["results"][0]["count"] == 2

    @pytest.mark.asyncio
    async def test_get_database_info(self, d1_service, httpx_mock: HTTPXMock):
        """Test getting database info."""
        httpx_mock.add_response(
            json={
                "success": True,
                "result": {
                    "name": "ensenia-ministry-db",
                    "created_at": "2025-01-01T00:00:00Z",
                },
            }
        )

        info = await d1_service.get_database_info()

        assert info["name"] == "ensenia-ministry-db"
        assert "created_at" in info
