"""Content generation service for structured learning materials.

Generates organized learning content and study guides from research context
using OpenAI, aligned with Chilean Ministry of Education curriculum standards.
"""

import json
import logging
from typing import Any

from openai import AsyncOpenAI

from app.ensenia.core.config import settings

logger = logging.getLogger(__name__)


class ContentGenerationService:
    """Service for generating structured learning content."""

    def __init__(self):
        """Initialize with OpenAI client."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o-mini"

    async def generate_learning_content(
        self,
        subject: str,
        grade: int,
        curriculum_context: str,
        topic: str | None = None,
    ) -> dict[str, Any]:
        """Generate structured learning content from research context.

        Args:
            subject: School subject (e.g., "Matemáticas")
            grade: Grade level (1-12)
            curriculum_context: Research context from Cloudflare
            topic: Optional specific topic for this session

        Returns:
            Structured learning content with sections, explanations, and examples

        """
        logger.info(
            "[Content] Generating learning content - Subject: %s, Grade: %d, Topic: %s",
            subject,
            grade,
            topic or "General",
        )
        logger.info(
            "[Content] Using curriculum context: %d chars",
            len(curriculum_context),
        )
        logger.debug("[Content] Context preview: %s...", curriculum_context[:200])

        try:
            import time

            start_time = time.time()

            prompt = f"""Basándote en el siguiente contexto curricular, crea una guía de
            aprendizaje estructurada para estudiantes chilenos.

CONTEXTO CURRICULAR:
{curriculum_context}

PARÁMETROS:
- Asignatura: {subject}
- Grado: {grade}° Básico
- Tema: {topic or subject}

Tu respuesta DEBE ser un JSON válido con la siguiente estructura:
{{
    "title": "Título descriptivo de la lección",
    "overview": "Párrafo breve de qué se aprenderá",
    "learning_objectives": ["Objetivo 1", "Objetivo 2", "Objetivo 3"],
    "sections": [
        {{
            "title": "Nombre de la sección",
            "content": "Explicación clara y pedagógica del concepto",
            "key_points": ["Punto clave 1", "Punto clave 2"],
            "examples": [
                {{
                    "description": "Descripción del ejemplo",
                    "explanation": "Explicación de cómo se aplica"
                }}
            ]
        }}
    ],
    "vocabulary": [
        {{
            "term": "Término importante",
            "definition": "Definición clara"
        }}
    ],
    "summary": "Resumen de los conceptos principales"
}}

Asegúrate de:
1. Usar terminología chilena apropriada
2. Alinear con las Bases Curriculares
3. Ser apropiado para el nivel de grado
4. Ser claro y pedagógicamente sólido
5. Incluir ejemplos relevantes para estudiantes chilenos

Responde SOLO con el JSON válido, sin texto adicional."""

            logger.info(
                "[Content] Calling OpenAI API with model %s (prompt: %d chars)...",
                self.model,
                len(prompt),
            )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000,
            )

            elapsed = time.time() - start_time
            logger.info("[Content] OpenAI API call completed in %.2fs", elapsed)

            content_text = response.choices[0].message.content
            logger.debug(
                "[Content] Received response: %d chars, %d tokens used",
                len(content_text),
                response.usage.total_tokens if response.usage else 0,
            )

            # Strip markdown code blocks if present
            import re
            content_text = re.sub(r'^```(?:json)?\n?', '', content_text)
            content_text = re.sub(r'\n?```$', '', content_text)

            content_json = json.loads(content_text)

            logger.info(
                "[Content] ✓ Successfully generated learning content - "
                "Title: '%s', %d sections, %d learning objectives (%.2fs total)",
                content_json.get("title", "Unknown")[:50],
                len(content_json.get("sections", [])),
                len(content_json.get("learning_objectives", [])),
                elapsed,
            )

            return content_json

        except json.JSONDecodeError as e:
            logger.error(
                "[Content] Failed to parse learning content JSON: %s",
                str(e),
            )
            logger.error("[Content] Raw response: %s", content_text[:500])
            logger.exception("[Content] Full JSON decode error:")
            # Return minimal valid structure
            fallback = {
                "title": f"Aprendizaje: {topic or subject}",
                "overview": curriculum_context[:500],
                "learning_objectives": [],
                "sections": [],
                "vocabulary": [],
                "summary": curriculum_context[:300],
            }
            logger.warning("[Content] Returning fallback learning content structure")
            return fallback
        except Exception as e:
            logger.error(
                "[Content] Error generating learning content: %s",
                str(e),
            )
            logger.exception("[Content] Full error traceback:")
            raise

    async def generate_study_guide(
        self,
        subject: str,
        grade: int,
        curriculum_context: str,
        topic: str | None = None,
    ) -> dict[str, Any]:
        """Generate a study guide summarizing key concepts.

        Args:
            subject: School subject (e.g., "Matemáticas")
            grade: Grade level (1-12)
            curriculum_context: Research context from Cloudflare
            topic: Optional specific topic for this session

        Returns:
            Structured study guide with summaries, key concepts, and review materials

        """
        logger.info(
            "[Content] Generating study guide - Subject: %s, Grade: %d, Topic: %s",
            subject,
            grade,
            topic or "General",
        )
        logger.info(
            "[Content] Using curriculum context: %d chars",
            len(curriculum_context),
        )

        try:
            import time

            start_time = time.time()

            prompt = f"""Basándote en el siguiente contexto curricular, crea una guía
            de estudio para estudiantes chilenos que necesitan
            revisar y consolidar su aprendizaje.

CONTEXTO CURRICULAR:
{curriculum_context}

PARÁMETROS:
- Asignatura: {subject}
- Grado: {grade}° Básico
- Tema: {topic or subject}

Tu respuesta DEBE ser un JSON válido con la siguiente estructura:
{{
    "title": "Título de la guía de estudio",
    "subject": "{subject}",
    "grade": {grade},
    "key_concepts": [
        {{
            "concept": "Concepto importante",
            "explanation": "Explicación breve",
            "importance": "Por qué es importante"
        }}
    ],
    "summary_sections": [
        {{
            "title": "Tema a repasar",
            "summary": "Resumen conciso de los puntos principales",
            "remember": ["Cosa importante a recordar 1", "Cosa importante a recordar 2"]
        }}
    ],
    "common_mistakes": [
        {{
            "mistake": "Error común",
            "correction": "Cómo corregirlo",
            "explanation": "Por qué es un error"
        }}
    ],
    "practice_tips": [
        "Consejo de estudio 1",
        "Consejo de estudio 2",
        "Consejo de estudio 3"
    ],
    "review_questions": [
        "Pregunta de repaso 1",
        "Pregunta de repaso 2",
        "Pregunta de repaso 3"
    ]
}}

Asegúrate de:
1. Resumir los conceptos principales de forma clara
2. Enfatizar los puntos clave para recordar
3. Incluir errores comunes y cómo evitarlos
4. Ser apropiado para {grade}° Básico
5. Usar terminología chilena

Responde SOLO con el JSON válido, sin texto adicional."""

            logger.info(
                "[Content] Calling OpenAI API for study guide with model %s...",
                self.model,
            )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000,
            )

            elapsed = time.time() - start_time
            logger.info("[Content] OpenAI API call completed in %.2fs", elapsed)

            content_text = response.choices[0].message.content
            logger.debug(
                "[Content] Received study guide response: %d chars, %d tokens used",
                len(content_text),
                response.usage.total_tokens if response.usage else 0,
            )

            # Strip markdown code blocks if present
            import re
            content_text = re.sub(r'^```(?:json)?\n?', '', content_text)
            content_text = re.sub(r'\n?```$', '', content_text)

            study_json = json.loads(content_text)

            logger.info(
                "[Content] ✓ Successfully generated study guide - "
                "Title: '%s', %d key concepts, %d review questions (%.2fs total)",
                study_json.get("title", "Unknown")[:50],
                len(study_json.get("key_concepts", [])),
                len(study_json.get("review_questions", [])),
                elapsed,
            )

            return study_json

        except json.JSONDecodeError as e:
            logger.error(
                "[Content] Failed to parse study guide JSON: %s",
                str(e),
            )
            logger.error("[Content] Raw response: %s", content_text[:500])
            logger.exception("[Content] Full JSON decode error:")
            # Return minimal valid structure
            fallback = {
                "title": f"Guía de Estudio: {topic or subject}",
                "subject": subject,
                "grade": grade,
                "key_concepts": [],
                "summary_sections": [],
                "common_mistakes": [],
                "practice_tips": [],
                "review_questions": [],
            }
            logger.warning("[Content] Returning fallback study guide structure")
            return fallback
        except Exception as e:
            logger.error(
                "[Content] Error generating study guide: %s",
                str(e),
            )
            logger.exception("[Content] Full error traceback:")
            raise
