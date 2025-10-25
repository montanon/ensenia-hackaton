"""Cloudflare Vectorize (Vector Database) service wrapper."""

from typing import Any

import httpx

from app.ensenia.core.config import settings


class VectorizeService:
    """Service wrapper for Cloudflare Vectorize operations."""

    def __init__(self) -> None:
        """Initialize Vectorize service with credentials from settings."""
        self.account_id = settings.cloudflare_account_id
        self.index_name = settings.cloudflare_vectorize_index
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

    async def insert_vectors(self, vectors: list[dict[str, Any]]) -> dict[str, Any]:
        """Insert vectors into the index.

        Args:
            vectors: List of vector dictionaries with:
                - id: Unique identifier (string)
                - values: Embedding vector (list of floats)
                - metadata: Optional metadata (dict)

        Returns:
            Insert operation result

        Raises:
            httpx.HTTPError: If insertion fails

        """
        url = f"{self.base_url}/vectorize/indexes/{self.index_name}/insert"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url, headers=self._get_headers(), json={"vectors": vectors}
            )
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                error_msg = data.get("errors", ["Unknown error"])[0]
                msg = f"Vectorize insert failed: {error_msg}"
                raise RuntimeError(msg)

            return data.get("result", {})

    async def upsert_vectors(self, vectors: list[dict[str, Any]]) -> dict[str, Any]:
        """Upsert vectors (insert or update if exists).

        Args:
            vectors: List of vector dictionaries

        Returns:
            Upsert operation result

        """
        url = f"{self.base_url}/vectorize/indexes/{self.index_name}/upsert"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url, headers=self._get_headers(), json={"vectors": vectors}
            )
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                error_msg = data.get("errors", ["Unknown error"])[0]
                msg = f"Vectorize upsert failed: {error_msg}"
                raise RuntimeError(msg)

            return data.get("result", {})

    async def query(
        self,
        vector: list[float],
        top_k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
        *,
        return_values: bool = False,
        return_metadata: bool = True,
    ) -> list[dict[str, Any]]:
        """Query for similar vectors.

        Args:
            vector: Query embedding vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            return_values: Whether to return vector values in results
            return_metadata: Whether to return metadata in results

        Returns:
            List of matches with id, score, and optionally metadata/values

        Raises:
            httpx.HTTPError: If query fails

        """
        url = f"{self.base_url}/vectorize/indexes/{self.index_name}/query"

        payload: dict[str, Any] = {
            "vector": vector,
            "topK": top_k,
            "returnValues": return_values,
            "returnMetadata": return_metadata,
        }

        if filter_metadata:
            payload["filter"] = filter_metadata

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                error_msg = data.get("errors", ["Unknown error"])[0]
                msg = f"Vectorize query failed: {error_msg}"
                raise RuntimeError(msg)

            result = data.get("result", {})
            return result.get("matches", [])

    async def delete_by_ids(self, ids: list[str]) -> dict[str, Any]:
        """Delete vectors by their IDs.

        Args:
            ids: List of vector IDs to delete

        Returns:
            Delete operation result

        Raises:
            httpx.HTTPError: If deletion fails

        """
        url = f"{self.base_url}/vectorize/indexes/{self.index_name}/delete"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url, headers=self._get_headers(), json={"ids": ids}
            )
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                error_msg = data.get("errors", ["Unknown error"])[0]
                msg = f"Vectorize delete failed: {error_msg}"
                raise RuntimeError(msg)

            return data.get("result", {})

    async def get_index_info(self) -> dict[str, Any]:
        """Get Vectorize index information.

        Returns:
            Index metadata including dimensions, metric, etc.

        """
        url = f"{self.base_url}/vectorize/indexes/{self.index_name}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                error_msg = data.get("errors", ["Unknown error"])[0]
                msg = f"Failed to get index info: {error_msg}"
                raise RuntimeError(msg)

            return data.get("result", {})
