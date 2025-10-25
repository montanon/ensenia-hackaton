"""Cloudflare Deep Research Service.

Integrates with Cloudflare Workers MCP server to fetch curriculum-aligned
educational content and research context for chat sessions.
"""

import logging
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ensenia.config import get_settings
from app.ensenia.database.models import Session as DBSession

logger = logging.getLogger(__name__)
settings = get_settings()

# Module-level HTTP client (singleton pattern)
_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    """Get or create shared HTTP client.

    Returns:
        Shared AsyncClient instance

    """
    global _http_client  # noqa: PLW0603
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=30.0)
        logger.info("Created shared HTTP client for ResearchService")
    return _http_client


async def _close_http_client() -> None:
    """Close the shared HTTP client."""
    global _http_client  # noqa: PLW0603
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
        logger.info("Closed shared HTTP client")


class ResearchService:
    """Service for Cloudflare Deep Research integration."""

    def __init__(self):
        """Initialize the research service."""
        self.base_url = settings.cloudflare_worker_url.rstrip("/")
        self.client = _get_http_client()

    def _get_headers(self) -> dict[str, str]:
        """Get headers for Cloudflare API requests.

        Returns:
            Dict of headers including auth if configured

        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Ensenia-Backend/1.0",
        }

        if settings.cloudflare_api_token:
            headers["cf-aig-authorization"] = f"Bearer {settings.cloudflare_api_token}"

        return headers

    async def search_curriculum(
        self, query: str, grade: int, subject: str, limit: int = 10
    ) -> dict[str, Any]:
        """Search curriculum content via Worker.

        Args:
            query: Search query
            grade: Grade level (1-12)
            subject: Subject area
            limit: Maximum results

        Returns:
            Search results with content IDs and metadata

        Raises:
            httpx.HTTPError: If request fails

        """
        endpoint = f"{self.base_url}/search"

        payload = {"query": query, "grade": grade, "subject": subject, "limit": limit}

        try:
            response = await self.client.post(
                endpoint, json=payload, headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            logger.exception("Error searching curriculum")
            raise

    async def fetch_content(self, content_ids: list[str]) -> dict[str, Any]:
        """Fetch full curriculum content by IDs.

        Args:
            content_ids: List of content IDs to retrieve

        Returns:
            Retrieved content with full details

        Raises:
            httpx.HTTPError: If request fails

        """
        endpoint = f"{self.base_url}/fetch"

        payload = {"content_ids": content_ids}

        try:
            response = await self.client.post(
                endpoint, json=payload, headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            logger.exception("Error fetching content")
            raise

    async def get_context(self, topic: str, grade: int, subject: str) -> str:
        """Get research context for a topic.

        Searches curriculum and fetches top results to build context.

        Args:
            topic: Topic to research
            grade: Grade level
            subject: Subject area

        Returns:
            Research context as formatted string

        """
        try:
            # Search for relevant content
            search_results = await self.search_curriculum(
                query=topic, grade=grade, subject=subject, limit=5
            )

            # Extract content IDs
            content_ids = search_results.get("content_ids", [])[:3]

            if not content_ids:
                logger.warning("No curriculum content found for topic: %s", topic)
                return f"Topic: {topic}\nNo specific curriculum content found."

            # Fetch detailed content
            content_data = await self.fetch_content(content_ids)
            contents = content_data.get("contents", [])

            # Format context
            context_parts = [
                f"Topic: {topic}",
                f"Grade: {grade}",
                f"Subject: {subject}",
                "",
            ]

            for i, content in enumerate(contents, 1):
                context_parts.append(f"Content {i}:")
                context_parts.append(f"  Title: {content.get('title', 'N/A')}")
                context_parts.append(
                    f"  Description: {content.get('description', 'N/A')}"
                )
                if content.get("learning_objectives"):
                    context_parts.append(
                        f"  Objectives: {', '.join(content['learning_objectives'])}"
                    )
                context_parts.append("")

            return "\n".join(context_parts)

        except Exception:
            logger.exception("Error getting research context")
            return f"Topic: {topic}\nError retrieving curriculum content."

    async def update_session_context(
        self, session_id: int, topic: str, db: AsyncSession
    ) -> str:
        """Update session with research context.

        Args:
            session_id: Session ID to update
            topic: Topic to research
            db: Database session

        Returns:
            Research context that was set

        Raises:
            ValueError: If session not found

        """
        # Load session
        stmt = select(DBSession).where(DBSession.id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            msg = f"Session {session_id} not found"
            raise ValueError(msg)

        # Get research context
        context = await self.get_context(topic, session.grade, session.subject)

        # Update session
        session.research_context = context
        await db.commit()

        logger.info("Updated session %s with research context", session_id)
        return context


def get_research_service() -> ResearchService:
    """Create a new ResearchService instance.

    Returns:
        ResearchService instance

    """
    return ResearchService()


async def cleanup_research_service() -> None:
    """Cleanup shared HTTP client.

    Should be called on application shutdown.
    """
    await _close_http_client()
