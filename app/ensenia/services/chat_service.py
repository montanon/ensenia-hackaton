"""OpenAI Chat Service.

Handles conversation management, OpenAI API integration, and
mode-specific prompting for the Chilean education assistant.
"""

import logging
from datetime import UTC, datetime

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ensenia.core.config import settings
from app.ensenia.database.models import InputMode, OutputMode
from app.ensenia.database.models import Message as DBMessage
from app.ensenia.database.models import Session as DBSession
from app.ensenia.models import ChatMode

logger = logging.getLogger(__name__)


# System prompts for different modes
SYSTEM_PROMPTS = {
    "learn": """Eres un asistente educativo para estudiantes chilenos del curso \
{grade} en la materia {subject}.

Tu rol es EXPLICAR conceptos de forma clara y pedagógica, siguiendo las \
directrices del Ministerio de Educación de Chile.

Contexto curricular:
{research_context}

Instrucciones:
- Explica conceptos paso a paso
- Usa ejemplos relevantes para estudiantes chilenos
- Adapta tu lenguaje al nivel del curso
- Fomenta la comprensión profunda, no solo memorización
- Haz preguntas para verificar comprensión
- Usa terminología del currículum chileno""",
    "practice": """Eres un asistente educativo para estudiantes chilenos del \
curso {grade} en la materia {subject}.

Tu rol es GENERAR EJERCICIOS y proporcionar retroalimentación constructiva.

Contexto curricular:
{research_context}

Instrucciones:
- Genera ejercicios alineados con el currículum chileno
- Proporciona retroalimentación detallada
- Explica errores comunes
- Sugiere estrategias de resolución
- Ajusta dificultad según el desempeño del estudiante
- Celebra logros y motiva el aprendizaje""",
    "evaluation": """Eres un asistente educativo para estudiantes chilenos del \
curso {grade} en la materia {subject}.

Tu rol es EVALUAR el conocimiento del estudiante de forma justa y constructiva.

Contexto curricular:
{research_context}

Instrucciones:
- Haz preguntas que evalúen comprensión real
- Usa formatos de evaluación del Ministerio de Educación
- Proporciona retroalimentación específica
- Identifica fortalezas y áreas de mejora
- Sé objetivo pero motivador
- Sugiere recursos para mejorar""",
    "study": """Eres un asistente educativo para estudiantes chilenos del curso \
{grade} en la materia {subject}.

Tu rol es AYUDAR A REVISAR y reforzar conceptos aprendidos.

Contexto curricular:
{research_context}

Instrucciones:
- Revisa conceptos clave de forma estructurada
- Identifica vacíos de conocimiento
- Conecta conceptos nuevos con previos
- Usa técnicas de estudio efectivas
- Proporciona resúmenes y mapas conceptuales
- Prepara al estudiante para evaluaciones""",
}


class ChatService:
    """Service for OpenAI chat operations."""

    def __init__(self):
        """Initialize the OpenAI client."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        # Cap max_tokens at 4096 for gpt-3.5-turbo compatibility
        # gpt-4-turbo-preview supports more, but gpt-3.5-turbo only supports 4096
        self.max_tokens = min(settings.openai_max_tokens, 4096)
        self.temperature = settings.openai_temperature

        logger.info(
            "[ChatService] Initialized with model=%s, max_tokens=%d (configured: %d)",
            self.model,
            self.max_tokens,
            settings.openai_max_tokens,
        )

    def _build_system_prompt(
        self, mode: str, grade: int, subject: str, research_context: str | None
    ) -> str:
        """Build system prompt based on mode and context.

        Args:
            mode: Chat mode (learn/practice/evaluation/study)
            grade: Grade level
            subject: Subject area
            research_context: Research context from Cloudflare

        Returns:
            Formatted system prompt

        Raises:
            ValueError: If mode is invalid

        """
        # Validate mode
        valid_modes = {m.value for m in ChatMode}
        if mode not in valid_modes:
            msg = f"Invalid mode: {mode}. Must be one of {valid_modes}"
            raise ValueError(msg)

        template = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["learn"])

        context = (
            research_context or "No hay contexto curricular específico disponible."
        )

        return template.format(grade=grade, subject=subject, research_context=context)

    async def send_message(
        self, session_id: int, user_message: str, db: AsyncSession
    ) -> str:
        """Send a message and get AI response.

        Args:
            session_id: Session ID
            user_message: User's message
            db: Database session

        Returns:
            AI assistant's response

        Raises:
            ValueError: If session not found

        """
        # Load session with messages (eager loading)
        stmt = (
            select(DBSession)
            .options(selectinload(DBSession.messages))
            .where(DBSession.id == session_id)
        )

        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            msg = f"Session {session_id} not found"
            raise ValueError(msg)

        # Build conversation history (last N messages)
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in session.messages[-settings.chat_context_window :]
        ]

        # Build system prompt
        system_prompt = self._build_system_prompt(
            mode=session.mode,
            grade=session.grade,
            subject=session.subject,
            research_context=session.research_context,
        )

        # Construct messages for OpenAI
        messages = [
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": user_message},
        ]

        try:
            # Call OpenAI API
            logger.info(
                "Sending message to OpenAI (session=%s, mode=%s)",
                session_id,
                session.mode,
            )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            assistant_message = response.choices[0].message.content
            if not assistant_message:
                logger.error(
                    "OpenAI returned empty response for session %s", session_id
                )
                msg = "Received empty response from OpenAI"
                raise ValueError(msg)

            # Save both messages to database
            user_msg = DBMessage(
                session_id=session_id,
                role="user",
                content=user_message,
                timestamp=datetime.now(UTC),
            )

            assistant_msg = DBMessage(
                session_id=session_id,
                role="assistant",
                content=assistant_message,
                timestamp=datetime.now(UTC),
            )

            db.add(user_msg)
            db.add(assistant_msg)

            try:
                await db.commit()
            except Exception:
                await db.rollback()
                logger.exception("Error committing messages to database")
                raise

            logger.info(
                "Message exchange saved (session=%s, tokens=%s)",
                session_id,
                response.usage.total_tokens,
            )

            return assistant_message

        except Exception:
            logger.exception("Error in chat completion")
            raise

    async def send_message_streaming(
        self,
        session: DBSession,
        user_message: str,
        db: AsyncSession,  # noqa: ARG002
    ) -> object:
        """Send a message and stream AI response chunks.

        Args:
            session: The database session object
            user_message: User's message
            db: Database session

        Yields:
            Text chunks from OpenAI streaming response

        """
        # Build conversation history (last N messages)
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in session.messages[-settings.chat_context_window :]
        ]

        # Build system prompt
        system_prompt = self._build_system_prompt(
            mode=session.mode,
            grade=session.grade,
            subject=session.subject,
            research_context=session.research_context,
        )

        # Construct messages for OpenAI
        messages = [
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": user_message},
        ]

        try:
            # Call OpenAI streaming API
            logger.info(
                "Streaming message from OpenAI (session=%s, mode=%s)",
                session.id,
                session.mode,
            )

            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True,
            )

            chunk_count = 0
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    chunk_count += 1
                    logger.debug(f"[ChatService] Yielding chunk {chunk_count}: {len(content)} chars")
                    yield content

        except Exception:
            logger.exception("Error in streaming chat completion")
            raise

    async def get_session(self, session_id: int, db: AsyncSession) -> DBSession | None:
        """Get a session by ID with messages loaded.

        Args:
            session_id: The session ID to fetch
            db: Database session

        Returns:
            Session object or None if not found

        """
        stmt = (
            select(DBSession)
            .options(selectinload(DBSession.messages))
            .where(DBSession.id == session_id)
        )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_session_mode(
        self, session_id: int, new_mode: str, db: AsyncSession
    ) -> None:
        """Update a session's current output mode (text/audio).

        Alias for update_session_output_mode for backward compatibility.

        Args:
            session_id: The session ID to update
            new_mode: The new mode ('text' or 'audio')
            db: Database session

        Raises:
            ValueError: If session not found or invalid mode

        """
        await self.update_session_output_mode(session_id, new_mode, db)

    async def update_session_output_mode(
        self, session_id: int, new_mode: str, db: AsyncSession
    ) -> None:
        """Update a session's current output mode (text/audio).

        Args:
            session_id: The session ID to update
            new_mode: The new mode ('text' or 'audio')
            db: Database session

        Raises:
            ValueError: If session not found or invalid mode

        """
        # Validate mode using enum
        if new_mode not in [OutputMode.TEXT.value, OutputMode.AUDIO.value]:
            msg = f"Invalid output mode: {new_mode}. Must be 'text' or 'audio'"
            raise ValueError(msg)

        stmt = select(DBSession).where(DBSession.id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            msg = f"Session {session_id} not found"
            raise ValueError(msg)

        session.current_mode = new_mode

        try:
            await db.commit()
            msg = f"Session {session_id} output mode updated to {new_mode}"
            logger.info(msg)
        except Exception:
            await db.rollback()
            logger.exception(msg)
            raise

    async def update_session_input_mode(
        self, session_id: int, new_mode: str, db: AsyncSession
    ) -> None:
        """Update a session's input mode (text/voice).

        Args:
            session_id: The session ID to update
            new_mode: The new mode ('text' or 'voice')
            db: Database session

        Raises:
            ValueError: If session not found or invalid mode

        """
        # Validate mode using enum
        if new_mode not in [InputMode.TEXT.value, InputMode.VOICE.value]:
            msg = f"Invalid input mode: {new_mode}. Must be 'text' or 'voice'"
            raise ValueError(msg)

        stmt = select(DBSession).where(DBSession.id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            msg = f"Session {session_id} not found"
            raise ValueError(msg)

        session.input_mode = new_mode

        try:
            await db.commit()
            msg = f"Session {session_id} input mode updated to {new_mode}"
            logger.info(msg)
        except Exception:
            await db.rollback()
            logger.exception(msg)
            raise


def get_chat_service() -> ChatService:
    """Create a new ChatService instance.

    Returns:
        ChatService instance

    """
    return ChatService()
