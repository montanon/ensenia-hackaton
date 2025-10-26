"""Cloudflare Worker Research Service.

Integrates with Cloudflare Worker to provide curriculum-aligned
educational content and research capabilities.
"""

import logging
from typing import Literal

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ensenia.config import get_settings
from app.ensenia.database.models import Session as DBSession
from app.ensenia.models.curriculum import (
    FetchResponse,
    GenerateRequest,
    GenerateResponse,
    SearchRequest,
    SearchResponse,
    ValidateRequest,
    ValidateResponse,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Module-level HTTP client (singleton pattern)
_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    """Get or create shared HTTP client with retries.

    Returns:
        Shared AsyncClient instance with retry configuration

    """
    global _http_client  # noqa: PLW0603
    if _http_client is None:
        transport = httpx.AsyncHTTPTransport(retries=settings.cloudflare_max_retries)
        _http_client = httpx.AsyncClient(
            timeout=settings.cloudflare_request_timeout,
            transport=transport,
        )
        logger.info(
            "Created shared HTTP client for ResearchService with %d retries",
            settings.cloudflare_max_retries,
        )
    return _http_client


async def _close_http_client() -> None:
    """Close the shared HTTP client."""
    global _http_client  # noqa: PLW0603
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
        logger.info("Closed shared HTTP client")


class ResearchService:
    """Service for Cloudflare Worker integration.

    Provides curriculum search, content generation, and validation
    through the deployed Cloudflare Worker.
    """

    def __init__(self):
        """Initialize the research service."""
        self.base_url = settings.cloudflare_worker_url.rstrip("/")
        self.client = _get_http_client()

    def _get_headers(self) -> dict[str, str]:
        """Get headers for Worker API requests.

        Returns:
            Dict of headers including auth if configured

        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Ensenia-Backend/1.0",
        }

        if settings.cloudflare_api_token:
            headers["Authorization"] = f"Bearer {settings.cloudflare_api_token}"

        return headers

    async def search_curriculum(
        self,
        query: str,
        grade: int,
        subject: str,
        limit: int = 10,
    ) -> SearchResponse:
        """Search curriculum content using semantic search.

        Args:
            query: Search query
            grade: Grade level (1-12)
            subject: Subject area (e.g., 'matemáticas')
            limit: Maximum results to return

        Returns:
            SearchResponse with matching content

        Raises:
            httpx.HTTPError: If request fails
            ValueError: If response validation fails

        """
        endpoint = f"{self.base_url}/search"

        request_data = SearchRequest(
            query=query,
            grade=grade,
            subject=subject,
            limit=limit,
        )

        try:
            response = await self.client.post(
                endpoint,
                json=request_data.model_dump(),
                headers=self._get_headers(),
            )
            response.raise_for_status()

            data = response.json()
            return SearchResponse.model_validate(data)

        except httpx.HTTPError:
            logger.exception(
                "Error searching curriculum: %s",
                response.text if "response" in locals() else "No response",
            )
            raise
        except Exception:
            logger.exception("Error parsing search response")
            raise

    async def fetch_content(self, content_ids: list[str]) -> FetchResponse:
        """Fetch full curriculum content by IDs.

        Args:
            content_ids: List of content IDs to retrieve

        Returns:
            FetchResponse with full content details

        Raises:
            httpx.HTTPError: If request fails
            ValueError: If response validation fails

        """
        endpoint = f"{self.base_url}/fetch"

        payload = {"content_ids": content_ids}

        try:
            response = await self.client.post(
                endpoint,
                json=payload,
                headers=self._get_headers(),
            )
            response.raise_for_status()

            data = response.json()
            return FetchResponse.model_validate(data)

        except httpx.HTTPError:
            logger.exception(
                "Error fetching content: %s",
                response.text if "response" in locals() else "No response",
            )
            raise
        except Exception:
            logger.exception("Error parsing fetch response")
            raise

    async def generate_explanation(  # noqa: PLR0913
        self,
        context: str,
        query: str,
        grade: int,
        subject: str,
        oa_codes: list[str],
        style: Literal["explanation", "summary", "example"] = "explanation",
    ) -> GenerateResponse:
        """Generate educational content using Workers AI.

        Args:
            context: Context information for generation
            query: User query or topic
            grade: Grade level (1-12)
            subject: Subject area
            oa_codes: Objetivo de Aprendizaje codes to align with
            style: Generation style (explanation, summary, or example)

        Returns:
            GenerateResponse with generated content

        Raises:
            httpx.HTTPError: If request fails
            ValueError: If response validation fails

        """
        endpoint = f"{self.base_url}/generate"

        request_data = GenerateRequest(
            context=context,
            query=query,
            grade=grade,
            subject=subject,
            oa_codes=oa_codes,
            style=style,
        )

        try:
            response = await self.client.post(
                endpoint,
                json=request_data.model_dump(),
                headers=self._get_headers(),
            )
            response.raise_for_status()

            data = response.json()
            return GenerateResponse.model_validate(data)

        except httpx.HTTPError:
            logger.exception(
                "Error generating content: %s",
                response.text if "response" in locals() else "No response",
            )
            raise
        except Exception:
            logger.exception("Error parsing generation response")
            raise

    async def validate_content(
        self,
        content: str,
        grade: int,
        subject: str,
        expected_oa: list[str],
    ) -> ValidateResponse:
        """Validate content against Chilean Ministry standards.

        Args:
            content: Content to validate
            grade: Target grade level (1-12)
            subject: Subject area
            expected_oa: Expected OA codes for validation

        Returns:
            ValidateResponse with validation results

        Raises:
            httpx.HTTPError: If request fails
            ValueError: If response validation fails

        """
        endpoint = f"{self.base_url}/validate"

        request_data = ValidateRequest(
            content=content,
            grade=grade,
            subject=subject,
            expected_oa=expected_oa,
        )

        try:
            response = await self.client.post(
                endpoint,
                json=request_data.model_dump(),
                headers=self._get_headers(),
            )
            response.raise_for_status()

            data = response.json()
            return ValidateResponse.model_validate(data)

        except httpx.HTTPError:
            logger.exception(
                "Error validating content: %s",
                response.text if "response" in locals() else "No response",
            )
            raise
        except Exception:
            logger.exception("Error parsing validation response")
            raise

    async def get_context(self, topic: str, grade: int, subject: str) -> str:
        """Get research context for a topic.

        Searches curriculum and fetches top results to build context string.

        Args:
            topic: Topic to research
            grade: Grade level (1-12)
            subject: Subject area

        Returns:
            Research context as formatted string

        """
        try:
            # Search for relevant content
            search_results = await self.search_curriculum(
                query=topic, grade=grade, subject=subject, limit=5
            )

            # Extract top content IDs
            content_ids = search_results.content_ids[:3]

            if not content_ids:
                logger.warning("No curriculum content found for topic: %s", topic)
                return f"Topic: {topic}\nNo specific curriculum content found."

            # Fetch detailed content
            fetch_response = await self.fetch_content(content_ids)
            contents = fetch_response.contents

            # Format context
            context_parts = [
                f"Topic: {topic}",
                f"Grade: {grade}",
                f"Subject: {subject}",
                f"Found {len(contents)} curriculum items",
                "",
            ]

            for i, content in enumerate(contents, 1):
                context_parts.append(f"Content {i}: {content.title}")
                context_parts.append(f"  OA: {content.ministry_standard_ref}")
                context_parts.append(f"  Level: {content.difficulty_level}")
                if content.learning_objectives:
                    context_parts.append(
                        f"  Objectives: {', '.join(content.learning_objectives[:2])}"
                    )
                # Add snippet of content text
                snippet = (
                    content.content_text[:200] + "..."
                    if len(content.content_text) > 200  # noqa: PLR2004
                    else content.content_text
                )
                context_parts.append(f"  Content: {snippet}")
                context_parts.append("")

            return "\n".join(context_parts)

        except Exception:
            logger.exception("Error getting research context for topic: %s", topic)
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
