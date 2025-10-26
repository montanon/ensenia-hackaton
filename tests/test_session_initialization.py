"""Tests for session initialization with research and exercise generation.

Tests the background initialization process including:
- Deep research context loading
- Initial exercise pool generation
- Session status tracking
- Error handling
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ensenia.api.routes.chat import initialize_session_background


@pytest.mark.asyncio
class TestSessionInitialization:
    """Test suite for session initialization background tasks."""

    @patch("app.ensenia.api.routes.chat.get_research_service")
    @patch("app.ensenia.api.routes.chat.get_generation_service")
    @patch("app.ensenia.api.routes.chat.get_exercise_repository")
    @patch("app.ensenia.api.routes.chat.get_exercise_pool_service")
    async def test_initialize_session_success(
        self,
        mock_get_pool_service,
        mock_get_repository,
        mock_get_generation,
        mock_get_research,
    ):
        """Test successful session initialization."""
        # Mock services
        mock_research = AsyncMock()
        mock_research.update_session_context = AsyncMock(
            return_value="Curriculum context for Matemáticas 5° Básico"
        )
        mock_get_research.return_value = mock_research

        mock_pool = AsyncMock()
        mock_pool.generate_initial_pool = AsyncMock(return_value=[1, 2, 3, 4, 5])
        mock_get_pool_service.return_value = mock_pool

        # Mock DB session factory
        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=None)
        mock_session_maker = MagicMock(return_value=mock_db)

        # Run initialization
        await initialize_session_background(
            session_id=1,
            grade=5,
            subject="Matemáticas",
            topic="Fracciones",
            db_session_maker=mock_session_maker,
        )

        # Verify research was triggered
        mock_research.update_session_context.assert_called_once_with(
            1, "Fracciones", mock_db
        )

        # Verify pool generation was triggered
        mock_pool.generate_initial_pool.assert_called_once()
        call_kwargs = mock_pool.generate_initial_pool.call_args.kwargs
        assert call_kwargs["session_id"] == 1
        assert call_kwargs["grade"] == 5
        assert call_kwargs["subject"] == "Matemáticas"
        assert call_kwargs["pool_size"] == 5
        assert "Curriculum context" in call_kwargs["curriculum_context"]

    @patch("app.ensenia.api.routes.chat.get_research_service")
    @patch("app.ensenia.api.routes.chat.get_generation_service")
    @patch("app.ensenia.api.routes.chat.get_exercise_repository")
    @patch("app.ensenia.api.routes.chat.get_exercise_pool_service")
    async def test_initialize_session_with_default_topic(
        self,
        mock_get_pool_service,
        mock_get_repository,
        mock_get_generation,
        mock_get_research,
    ):
        """Test initialization with default topic when none provided."""
        mock_research = AsyncMock()
        mock_research.update_session_context = AsyncMock(return_value="Context")
        mock_get_research.return_value = mock_research

        mock_pool = AsyncMock()
        mock_pool.generate_initial_pool = AsyncMock(return_value=[1, 2, 3])
        mock_get_pool_service.return_value = mock_pool

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=None)
        mock_session_maker = MagicMock(return_value=mock_db)

        # Run initialization without topic
        await initialize_session_background(
            session_id=1,
            grade=5,
            subject="Matemáticas",
            topic=None,  # No topic provided
            db_session_maker=mock_session_maker,
        )

        # Verify default topic was used
        mock_research.update_session_context.assert_called_once_with(
            1, "Matemáticas - 5° Básico", mock_db
        )

    @patch("app.ensenia.api.routes.chat.get_research_service")
    @patch("app.ensenia.api.routes.chat.get_generation_service")
    @patch("app.ensenia.api.routes.chat.get_exercise_repository")
    @patch("app.ensenia.api.routes.chat.get_exercise_pool_service")
    async def test_initialize_session_research_failure(
        self,
        mock_get_pool_service,
        mock_get_repository,
        mock_get_generation,
        mock_get_research,
    ):
        """Test initialization continues when research fails."""
        # Mock research failure
        mock_research = AsyncMock()
        mock_research.update_session_context = AsyncMock(
            side_effect=Exception("Research API failed")
        )
        mock_get_research.return_value = mock_research

        mock_pool = AsyncMock()
        mock_pool.generate_initial_pool = AsyncMock(return_value=[1, 2, 3])
        mock_get_pool_service.return_value = mock_pool

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=None)
        mock_session_maker = MagicMock(return_value=mock_db)

        # Should not raise exception
        await initialize_session_background(
            session_id=1,
            grade=5,
            subject="Matemáticas",
            topic="Fracciones",
            db_session_maker=mock_session_maker,
        )

        # Verify pool generation still happened (with None context)
        mock_pool.generate_initial_pool.assert_called_once()
        call_kwargs = mock_pool.generate_initial_pool.call_args.kwargs
        assert call_kwargs["curriculum_context"] is None

    @patch("app.ensenia.api.routes.chat.get_research_service")
    @patch("app.ensenia.api.routes.chat.get_generation_service")
    @patch("app.ensenia.api.routes.chat.get_exercise_repository")
    @patch("app.ensenia.api.routes.chat.get_exercise_pool_service")
    async def test_initialize_session_exercise_failure(
        self,
        mock_get_pool_service,
        mock_get_repository,
        mock_get_generation,
        mock_get_research,
    ):
        """Test initialization handles exercise generation failure."""
        mock_research = AsyncMock()
        mock_research.update_session_context = AsyncMock(return_value="Context")
        mock_get_research.return_value = mock_research

        # Mock exercise generation failure
        mock_pool = AsyncMock()
        mock_pool.generate_initial_pool = AsyncMock(
            side_effect=Exception("Exercise generation failed")
        )
        mock_get_pool_service.return_value = mock_pool

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=None)
        mock_session_maker = MagicMock(return_value=mock_db)

        # Should not raise exception
        await initialize_session_background(
            session_id=1,
            grade=5,
            subject="Matemáticas",
            topic="Fracciones",
            db_session_maker=mock_session_maker,
        )

        # Verify research still happened
        mock_research.update_session_context.assert_called_once()

    @patch("app.ensenia.api.routes.chat.get_research_service")
    @patch("app.ensenia.api.routes.chat.get_generation_service")
    @patch("app.ensenia.api.routes.chat.get_exercise_repository")
    @patch("app.ensenia.api.routes.chat.get_exercise_pool_service")
    async def test_initialize_session_complete_failure(
        self,
        mock_get_pool_service,
        mock_get_repository,
        mock_get_generation,
        mock_get_research,
    ):
        """Test initialization handles complete failure gracefully."""
        # Mock DB session factory failure
        mock_session_maker = MagicMock(
            side_effect=Exception("Database connection failed")
        )

        # Should not raise exception (logs error internally)
        await initialize_session_background(
            session_id=1,
            grade=5,
            subject="Matemáticas",
            topic="Fracciones",
            db_session_maker=mock_session_maker,
        )

        # Verify no services were called
        mock_get_research.assert_not_called()
        mock_get_pool_service.assert_not_called()


@pytest.mark.asyncio
class TestSessionInitializationTiming:
    """Test timing and concurrency of session initialization."""

    @patch("app.ensenia.api.routes.chat.get_research_service")
    @patch("app.ensenia.api.routes.chat.get_generation_service")
    @patch("app.ensenia.api.routes.chat.get_exercise_repository")
    @patch("app.ensenia.api.routes.chat.get_exercise_pool_service")
    async def test_initialization_runs_async(
        self,
        mock_get_pool_service,
        mock_get_repository,
        mock_get_generation,
        mock_get_research,
    ):
        """Test that initialization steps run asynchronously."""
        # Track call order
        call_order = []

        async def mock_research_call(*args, **kwargs):
            call_order.append("research_start")
            await asyncio.sleep(0.1)
            call_order.append("research_end")
            return "Context"

        async def mock_pool_call(*args, **kwargs):
            call_order.append("pool_start")
            await asyncio.sleep(0.1)
            call_order.append("pool_end")
            return [1, 2, 3]

        mock_research = AsyncMock()
        mock_research.update_session_context = mock_research_call
        mock_get_research.return_value = mock_research

        mock_pool = AsyncMock()
        mock_pool.generate_initial_pool = mock_pool_call
        mock_get_pool_service.return_value = mock_pool

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=None)
        mock_session_maker = MagicMock(return_value=mock_db)

        # Run initialization
        await initialize_session_background(
            session_id=1,
            grade=5,
            subject="Matemáticas",
            topic="Fracciones",
            db_session_maker=mock_session_maker,
        )

        # Verify research completed before pool started
        assert call_order == [
            "research_start",
            "research_end",
            "pool_start",
            "pool_end",
        ]

    @patch("app.ensenia.api.routes.chat.get_research_service")
    @patch("app.ensenia.api.routes.chat.get_generation_service")
    @patch("app.ensenia.api.routes.chat.get_exercise_repository")
    @patch("app.ensenia.api.routes.chat.get_exercise_pool_service")
    async def test_multiple_session_initialization_concurrent(
        self,
        mock_get_pool_service,
        mock_get_repository,
        mock_get_generation,
        mock_get_research,
    ):
        """Test multiple sessions can initialize concurrently."""
        mock_research = AsyncMock()
        mock_research.update_session_context = AsyncMock(return_value="Context")
        mock_get_research.return_value = mock_research

        mock_pool = AsyncMock()
        mock_pool.generate_initial_pool = AsyncMock(return_value=[1, 2, 3])
        mock_get_pool_service.return_value = mock_pool

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=None)
        mock_session_maker = MagicMock(return_value=mock_db)

        # Initialize 3 sessions concurrently
        tasks = [
            initialize_session_background(
                session_id=i,
                grade=5,
                subject="Matemáticas",
                topic=f"Topic {i}",
                db_session_maker=mock_session_maker,
            )
            for i in range(1, 4)
        ]

        await asyncio.gather(*tasks)

        # Verify all 3 sessions were initialized
        assert mock_research.update_session_context.call_count == 3
        assert mock_pool.generate_initial_pool.call_count == 3
