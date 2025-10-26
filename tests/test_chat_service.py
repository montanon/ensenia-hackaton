"""Unit tests for ChatService."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ensenia.database.models import Message, Session
from app.ensenia.services.chat_service import get_chat_service


@pytest.mark.asyncio
class TestChatService:
    """Test suite for ChatService."""

    async def test_send_message_creates_messages(self, db_session: AsyncSession):
        """Test that send_message creates user and assistant messages."""
        # Create test session
        session = Session(
            grade=5, subject="Mathematics", mode="learn", research_context=None
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        # Mock OpenAI response
        mock_choice = MagicMock()
        mock_choice.message.content = "Test response from assistant"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage.total_tokens = 100

        with patch(
            "app.ensenia.services.chat_service.AsyncOpenAI"
        ) as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_class.return_value = mock_client

            chat_service = get_chat_service()
            response = await chat_service.send_message(
                session.id, "Test question", db_session
            )

            assert response == "Test response from assistant"

            # Verify messages were created
            stmt = (
                select(Message)
                .where(Message.session_id == session.id)
                .order_by(Message.timestamp)
            )
            result = await db_session.execute(stmt)
            messages = list(result.scalars())

            assert len(messages) == 2
            assert messages[0].role == "user"
            assert messages[0].content == "Test question"
            assert messages[1].role == "assistant"
            assert messages[1].content == "Test response from assistant"

    async def test_send_message_with_previous_context(self, db_session: AsyncSession):
        """Test that send_message includes previous messages in context."""
        # Create test session with previous message
        session = Session(
            grade=5, subject="Mathematics", mode="learn", research_context=None
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        prev_msg = Message(
            session_id=session.id,
            role="user",
            content="Previous question",
            timestamp=datetime.now(UTC),
        )
        db_session.add(prev_msg)
        await db_session.commit()

        # Mock OpenAI response
        mock_choice = MagicMock()
        mock_choice.message.content = "Response with context"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage.total_tokens = 150

        with patch(
            "app.ensenia.services.chat_service.AsyncOpenAI"
        ) as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_class.return_value = mock_client

            chat_service = get_chat_service()
            await chat_service.send_message(session.id, "New question", db_session)

            # Verify OpenAI was called with previous context
            call_args = mock_client.chat.completions.create.call_args
            messages_arg = call_args.kwargs["messages"]

            # Should have system + previous user + new user messages
            assert len(messages_arg) >= 3
            assert any("Previous question" in str(msg) for msg in messages_arg)

    async def test_mode_specific_prompts(self, db_session: AsyncSession):
        """Test that different modes generate appropriate system prompts."""
        modes = ["learn", "practice", "evaluation", "study"]

        for mode in modes:
            session = Session(
                grade=6, subject="History", mode=mode, research_context=None
            )
            db_session.add(session)
            await db_session.commit()
            await db_session.refresh(session)

            mock_choice = MagicMock()
            mock_choice.message.content = f"Response for {mode} mode"

            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            mock_response.usage.total_tokens = 100

            with patch(
                "app.ensenia.services.chat_service.AsyncOpenAI"
            ) as mock_openai_class:
                mock_client = AsyncMock()
                mock_client.chat.completions.create = AsyncMock(
                    return_value=mock_response
                )
                mock_openai_class.return_value = mock_client

                chat_service = get_chat_service()
                await chat_service.send_message(session.id, "Test question", db_session)

                # Verify OpenAI was called with mode-specific system prompt
                call_args = mock_client.chat.completions.create.call_args
                messages_arg = call_args.kwargs["messages"]

                system_message = messages_arg[0]["content"]
                # Verify system message exists and is mode-appropriate
                assert "asistente educativo" in system_message.lower()
                assert len(system_message) > 100  # Has substantial content

    async def test_send_message_invalid_session(self, db_session: AsyncSession):
        """Test that send_message raises ValueError for invalid session."""
        chat_service = get_chat_service()

        with pytest.raises(ValueError, match=r"Session .* not found"):
            await chat_service.send_message(99999, "Test", db_session)

    async def test_send_message_with_research_context(self, db_session: AsyncSession):
        """Test that research context is included in system prompt."""
        session = Session(
            grade=8,
            subject="Science",
            mode="learn",
            research_context="Introduction to photosynthesis",
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        mock_choice = MagicMock()
        mock_choice.message.content = "Response about photosynthesis"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage.total_tokens = 200

        with patch(
            "app.ensenia.services.chat_service.AsyncOpenAI"
        ) as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_class.return_value = mock_client

            chat_service = get_chat_service()
            await chat_service.send_message(
                session.id, "Explain photosynthesis", db_session
            )

            # Verify research context was included
            call_args = mock_client.chat.completions.create.call_args
            messages_arg = call_args.kwargs["messages"]

            system_message = messages_arg[0]["content"]
            assert "photosynthesis" in system_message.lower()
