"""Cloudflare Workers AI service wrapper."""

from typing import Any

import httpx

from app.ensenia.core.config import settings


class WorkersAIService:
    """Service wrapper for Cloudflare Workers AI operations."""

    def __init__(self) -> None:
        """Initialize Workers AI service with credentials from settings."""
        self.account_id = settings.cloudflare_account_id
        self.api_token = settings.cloudflare_api_token
        self.embedding_model = settings.workers_ai_embedding_model
        self.base_url = (
            f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run"
        )

    def _get_headers(self) -> dict[str, str]:
        """Get API headers with authentication."""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def generate_embedding(
        self, text: str, model: str | None = None
    ) -> list[float]:
        """Generate embedding vector for text.

        Args:
            text: Text to embed
            model: Embedding model to use (default: from settings)

        Returns:
            Embedding vector as list of floats

        Raises:
            httpx.HTTPError: If embedding generation fails

        """
        model_name = model or self.embedding_model
        url = f"{self.base_url}/{model_name}"

        payload = {"text": text}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                error_msg = data.get("errors", ["Unknown error"])[0]
                msg = f"Workers AI embedding failed: {error_msg}"
                raise RuntimeError(msg)

            result = data.get("result", {})
            # Workers AI returns embeddings in data[0]
            embedding_data = result.get("data")

            if not embedding_data:
                msg = "No embedding data returned from Workers AI"
                raise RuntimeError(msg)

            return embedding_data[0]

    async def generate_embeddings_batch(
        self, texts: list[str], model: str | None = None
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Note: Calls API sequentially. For production, implement proper batching.

        Args:
            texts: List of texts to embed
            model: Embedding model to use

        Returns:
            List of embedding vectors

        """
        embeddings = []

        for text in texts:
            embedding = await self.generate_embedding(text, model)
            embeddings.append(embedding)

        return embeddings

    async def run_model(self, model: str, inputs: dict[str, Any]) -> dict[str, Any]:
        """Run any Workers AI model.

        Args:
            model: Model identifier (e.g., '@cf/meta/llama-2-7b-chat-int8')
            inputs: Model inputs

        Returns:
            Model output dictionary

        Raises:
            httpx.HTTPError: If model execution fails

        """
        url = f"{self.base_url}/{model}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=self._get_headers(), json=inputs)
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                error_msg = data.get("errors", ["Unknown error"])[0]
                msg = f"Workers AI model run failed: {error_msg}"
                raise RuntimeError(msg)

            return data.get("result", {})
