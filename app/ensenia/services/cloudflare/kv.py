"""Cloudflare KV (Key-Value Storage) service wrapper."""

import json
from typing import Any

import httpx

from app.ensenia.core.config import settings

# HTTP Status Codes
HTTP_NOT_FOUND = 404


class KVService:
    """Service wrapper for Cloudflare KV operations."""

    def __init__(self, namespace_prefix: str = "ensenia") -> None:
        """Initialize KV service with credentials from settings.

        Args:
            namespace_prefix: Prefix for all keys (for organization)

        """
        self.account_id = settings.cloudflare_account_id
        self.namespace_id = settings.cloudflare_kv_namespace_id
        self.api_token = settings.cloudflare_api_token
        self.namespace_prefix = namespace_prefix
        self.base_url = (
            f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}"
        )

    def _get_headers(self) -> dict[str, str]:
        """Get API headers with authentication."""
        return {
            "Authorization": f"Bearer {self.api_token}",
        }

    def _make_key(self, key: str) -> str:
        """Add namespace prefix to key."""
        return f"{self.namespace_prefix}:{key}"

    async def get(
        self, key: str, *, parse_json: bool = True
    ) -> str | dict[str, Any] | None:
        """Get value from KV.

        Args:
            key: Cache key
            parse_json: Whether to parse value as JSON

        Returns:
            Cached value or None if not found

        """
        full_key = self._make_key(key)
        url = (
            f"{self.base_url}/storage/kv/namespaces/"
            f"{self.namespace_id}/values/{full_key}"
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._get_headers())

            if response.status_code == HTTP_NOT_FOUND:
                return None

            response.raise_for_status()
            value = response.text

            if parse_json and value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value

            return value

    async def set(
        self,
        key: str,
        value: object,
        ttl: int | None = None,
        *,
        serialize_json: bool = True,
    ) -> None:
        """Set value in KV with optional TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = no expiration)
            serialize_json: Whether to serialize value as JSON

        """
        full_key = self._make_key(key)
        url = (
            f"{self.base_url}/storage/kv/namespaces/"
            f"{self.namespace_id}/values/{full_key}"
        )

        if serialize_json and not isinstance(value, str):
            content = json.dumps(value, ensure_ascii=False)
        else:
            content = str(value)

        params = {}
        if ttl:
            params["expiration_ttl"] = ttl

        async with httpx.AsyncClient() as client:
            response = await client.put(
                url, headers=self._get_headers(), content=content, params=params
            )
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                error_msg = data.get("errors", ["Unknown error"])[0]
                msg = f"KV set failed: {error_msg}"
                raise RuntimeError(msg)

    async def delete(self, key: str) -> None:
        """Delete value from KV.

        Args:
            key: Cache key to delete

        """
        full_key = self._make_key(key)
        url = (
            f"{self.base_url}/storage/kv/namespaces/"
            f"{self.namespace_id}/values/{full_key}"
        )

        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=self._get_headers())
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                error_msg = data.get("errors", ["Unknown error"])[0]
                msg = f"KV delete failed: {error_msg}"
                raise RuntimeError(msg)

    async def exists(self, key: str) -> bool:
        """Check if a key exists in KV.

        Args:
            key: Cache key to check

        Returns:
            True if key exists, False otherwise

        """
        value = await self.get(key, parse_json=False)
        return value is not None

    async def list_keys(
        self, prefix: str = "", limit: int = 1000
    ) -> list[dict[str, Any]]:
        """List keys in the namespace.

        Args:
            prefix: Filter keys by prefix (after namespace prefix)
            limit: Maximum number of keys to return

        Returns:
            List of key metadata dictionaries

        """
        full_prefix = self._make_key(prefix) if prefix else self.namespace_prefix
        url = f"{self.base_url}/storage/kv/namespaces/{self.namespace_id}/keys"

        params = {"prefix": full_prefix, "limit": limit}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                error_msg = data.get("errors", ["Unknown error"])[0]
                msg = f"KV list keys failed: {error_msg}"
                raise RuntimeError(msg)

            return data.get("result", [])

    async def get_namespace_info(self) -> dict[str, Any]:
        """Get KV namespace information.

        Returns:
            Namespace metadata

        """
        url = f"{self.base_url}/storage/kv/namespaces/{self.namespace_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                error_msg = data.get("errors", ["Unknown error"])[0]
                msg = f"Failed to get namespace info: {error_msg}"
                raise RuntimeError(msg)

            return data.get("result", {})
