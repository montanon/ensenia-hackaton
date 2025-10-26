"""Cloudflare Worker Research Service.

Integrates with Cloudflare Worker to provide curriculum-aligned
educational content and research capabilities.
"""

import logging
from typing import Literal

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ensenia.core.config import settings
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

        logger.info(
            "[RAG] Starting semantic search - Query: '%s', Grade: %d, Subject: '%s', Limit: %d",
            query[:100],  # Truncate long queries
            grade,
            subject,
            limit,
        )
        logger.debug("[RAG] Search endpoint: %s", endpoint)

        try:
            import time

            start_time = time.time()

            response = await self.client.post(
                endpoint,
                json=request_data.model_dump(),
                headers=self._get_headers(),
            )
            response.raise_for_status()

            elapsed = time.time() - start_time
            logger.info("[RAG] Search request completed in %.2fs", elapsed)

            data = response.json()
            search_response = SearchResponse.model_validate(data)

            logger.info(
                "[RAG] Search found %d results (search_time: %.2fms)",
                len(search_response.content_ids),
                search_response.search_time_ms,
            )

            if search_response.content_ids:
                logger.info(
                    "[RAG] Top results: %s",
                    ", ".join(search_response.content_ids[:3]),
                )
                if search_response.metadata:
                    logger.info(
                        "[RAG] Top scores: %s",
                        ", ".join(f"{m.score:.3f}" for m in search_response.metadata[:3]),
                    )
            else:
                logger.warning("[RAG] No results found for query: '%s'", query)

            return search_response

        except httpx.HTTPError as e:
            logger.error(
                "[RAG] HTTP error during search (status: %s): %s",
                getattr(e.response, "status_code", "unknown"),
                response.text if "response" in locals() else "No response",
            )
            raise
        except Exception as e:
            logger.error("[RAG] Error during search: %s", str(e))
            logger.exception("Full search error traceback:")
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

        logger.info(
            "[RAG] Fetching %d content documents: %s",
            len(content_ids),
            ", ".join(content_ids[:5]) + ("..." if len(content_ids) > 5 else ""),
        )

        try:
            import time

            start_time = time.time()

            response = await self.client.post(
                endpoint,
                json=payload,
                headers=self._get_headers(),
            )
            response.raise_for_status()

            elapsed = time.time() - start_time
            logger.info("[RAG] Fetch request completed in %.2fs", elapsed)

            data = response.json()
            fetch_response = FetchResponse.model_validate(data)

            logger.info(
                "[RAG] Retrieved %d documents (fetch_time: %.2fms)",
                len(fetch_response.contents),
                fetch_response.fetch_time_ms,
            )

            # Log details about each fetched document
            for i, content in enumerate(fetch_response.contents, 1):
                logger.info(
                    "[RAG] Document %d: '%s' (Grade: %d, Subject: %s, Length: %d chars)",
                    i,
                    content.title[:60],
                    content.grade,
                    content.subject,
                    len(content.content_text),
                )
                if content.learning_objectives:
                    logger.debug(
                        "[RAG]   Learning Objectives: %s",
                        ", ".join(content.learning_objectives[:3]),
                    )

            return fetch_response

        except httpx.HTTPError as e:
            logger.error(
                "[RAG] HTTP error during fetch (status: %s): %s",
                getattr(e.response, "status_code", "unknown"),
                response.text if "response" in locals() else "No response",
            )
            raise
        except Exception as e:
            logger.error("[RAG] Error during fetch: %s", str(e))
            logger.exception("Full fetch error traceback:")
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
        logger.info(
            "[RAG] Building context for topic: '%s' (Grade: %d, Subject: %s)",
            topic,
            grade,
            subject,
        )

        try:
            import time

            context_start = time.time()

            # Search for relevant content
            logger.info("[RAG] Step 1/3: Searching curriculum...")
            search_results = await self.search_curriculum(
                query=topic, grade=grade, subject=subject, limit=5
            )

            # Extract top content IDs
            content_ids = search_results.content_ids[:3]

            if not content_ids:
                logger.warning(
                    "[RAG] No curriculum content found for topic: '%s' (Grade: %d, Subject: %s)",
                    topic,
                    grade,
                    subject,
                )
                return f"Topic: {topic}\nNo specific curriculum content found."

            logger.info(
                "[RAG] Step 2/3: Fetching top %d documents...",
                len(content_ids),
            )

            # Fetch detailed content
            fetch_response = await self.fetch_content(content_ids)
            contents = fetch_response.contents

            logger.info("[RAG] Step 3/3: Building formatted context...")

            # Format context
            context_parts = [
                f"Topic: {topic}",
                f"Grade: {grade}",
                f"Subject: {subject}",
                f"Found {len(contents)} curriculum items",
                "",
            ]

            total_chars = 0
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
                total_chars += len(content.content_text)

            context = "\n".join(context_parts)
            elapsed = time.time() - context_start

            logger.info(
                "[RAG] Context built successfully in %.2fs - %d documents, %d total chars, %d context length",
                elapsed,
                len(contents),
                total_chars,
                len(context),
            )
            logger.debug("[RAG] Context preview: %s...", context[:300])

            return context

        except Exception as e:
            logger.error(
                "[RAG] Error getting research context for topic '%s': %s",
                topic,
                str(e),
            )
            logger.exception("[RAG] Full context building error traceback:")
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
        logger.info(
            "[RAG] Updating session %d with research context for topic: '%s'",
            session_id,
            topic,
        )

        # Load session
        stmt = select(DBSession).where(DBSession.id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            msg = f"Session {session_id} not found"
            logger.error("[RAG] %s", msg)
            raise ValueError(msg)

        logger.info(
            "[RAG] Session loaded: Grade=%d, Subject='%s'",
            session.grade,
            session.subject,
        )

        # Get research context
        import time

        start_time = time.time()
        context = await self.get_context(topic, session.grade, session.subject)
        elapsed = time.time() - start_time

        # Update session
        session.research_context = context
        await db.commit()

        logger.info(
            "[RAG] ✓ Successfully updated session %d with research context (%.2fs total, %d chars)",
            session_id,
            elapsed,
            len(context),
        )
        logger.info(
            "[RAG] Context summary: %s", context.split("\n")[0] if context else "Empty"
        )

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
