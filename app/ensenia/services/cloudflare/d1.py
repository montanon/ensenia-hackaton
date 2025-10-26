"""Cloudflare D1 (SQL Database) service wrapper."""

from typing import Any

import httpx

from app.ensenia.core.config import settings


class D1Service:
    """Service wrapper for Cloudflare D1 database operations."""

    def __init__(self) -> None:
        """Initialize D1 service with credentials from settings."""
        self.account_id = settings.cloudflare_account_id
        self.database_id = settings.cloudflare_d1_database_id
        self.api_token = settings.cloudflare_api_token
        self.base_url = (
            f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}"
        )

    def _get_headers(self) -> dict[str, str]:
        """Get API headers with authentication."""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def execute(
        self, sql: str, params: list[Any] | None = None
    ) -> dict[str, Any]:
        """Execute a single SQL query.

        Args:
            sql: SQL query string
            params: Optional query parameters for parameterized queries

        Returns:
            Query result dictionary

        Raises:
            httpx.HTTPError: If query execution fails

        """
        url = f"{self.base_url}/d1/database/{self.database_id}/query"

        payload: dict[str, Any] = {"sql": sql}
        if params:
            payload["params"] = params

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                error_msg = data.get("errors", ["Unknown error"])[0]
                msg = f"D1 query failed: {error_msg}"
                raise RuntimeError(msg)

            return data["result"][0] if data.get("result") else {}

    async def execute_batch(
        self, queries: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Execute multiple SQL queries in a batch.

        Args:
            queries: List of query dictionaries with 'sql' and optional 'params'

        Returns:
            List of query results

        Raises:
            httpx.HTTPError: If batch execution fails

        """
        url = f"{self.base_url}/d1/database/{self.database_id}/query"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self._get_headers(), json=queries)
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                error_msg = data.get("errors", ["Unknown error"])[0]
                msg = f"D1 batch query failed: {error_msg}"
                raise RuntimeError(msg)

            return data.get("result", [])

    async def query(
        self, sql: str, params: list[Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a SELECT query and return results.

        Args:
            sql: SELECT SQL query
            params: Optional query parameters

        Returns:
            List of result rows as dictionaries

        """
        result = await self.execute(sql, params)
        return result.get("results", [])

    async def query_one(
        self, sql: str, params: list[Any] | None = None
    ) -> dict[str, Any] | None:
        """Execute a SELECT query and return first result.

        Args:
            sql: SELECT SQL query
            params: Optional query parameters

        Returns:
            First result row as dictionary, or None if no results

        """
        results = await self.query(sql, params)
        return results[0] if results else None

    async def execute_update(self, sql: str, params: list[Any] | None = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query.

        Args:
            sql: SQL query
            params: Optional query parameters

        Returns:
            Number of rows affected

        """
        result = await self.execute(sql, params)
        meta = result.get("meta", {})
        return meta.get("changes", 0)

    async def get_database_info(self) -> dict[str, Any]:
        """Get D1 database information.

        Returns:
            Database metadata dictionary

        """
        url = f"{self.base_url}/d1/database/{self.database_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                error_msg = data.get("errors", ["Unknown error"])[0]
                msg = f"Failed to get database info: {error_msg}"
                raise RuntimeError(msg)

            return data.get("result", {})
