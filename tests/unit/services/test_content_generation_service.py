"""Unit tests for ContentGenerationService."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.ensenia.services.content_generation_service import ContentGenerationService


@pytest.fixture
def content_service():
    """Create ContentGenerationService instance."""
    return ContentGenerationService()


class TestGenerateLearningContent:
    """Tests for generate_learning_content method."""

    @pytest.mark.asyncio
    async def test_generate_learning_content_success(self, content_service):
        """Test successful learning content generation."""
        # Sample valid response from OpenAI
        mock_response = {
            "title": "Introducción a la Photosíntesis",
            "overview": "Aprenderemos cómo las plantas convierten luz en energía",
            "learning_objectives": [
                "Entender el proceso de photosíntesis",
                "Identificar los componentes principales",
            ],
            "sections": [
                {
                    "title": "¿Qué es la Photosíntesis?",
                    "content": "La photosíntesis es el proceso...",
                    "key_points": ["Requiere luz", "Produce oxígeno"],
                    "examples": [
                        {
                            "description": "Planta en el sol",
                            "explanation": "La planta absorbe luz...",
                        }
                    ],
                }
            ],
            "vocabulary": [
                {
                    "term": "Clorofila",
                    "definition": "Pigmento que absorbe luz",
                }
            ],
            "summary": "La photosíntesis es fundamental...",
        }

        with patch.object(
            content_service.client.chat.completions,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_message = AsyncMock()
            mock_message.content = json.dumps(mock_response)
            mock_create.return_value.choices = [AsyncMock(message=mock_message)]

            result = await content_service.generate_learning_content(
                subject="Biología",
                grade=8,
                curriculum_context="Bases Curriculares de Biología 8°",
                topic="Photosíntesis",
            )

            assert result["title"] == "Introducción a la Photosíntesis"
            assert len(result["sections"]) == 1
            assert len(result["vocabulary"]) == 1
            assert "learning_objectives" in result
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_learning_content_invalid_json(self, content_service):
        """Test handling of invalid JSON response."""
        with patch.object(
            content_service.client.chat.completions,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_message = AsyncMock()
            mock_message.content = "invalid json {not valid}"
            mock_create.return_value.choices = [AsyncMock(message=mock_message)]

            result = await content_service.generate_learning_content(
                subject="Biología",
                grade=8,
                curriculum_context="Context",
                topic="Topic",
            )

            # Should return fallback structure
            assert result["title"] == "Aprendizaje: Topic"
            assert result["learning_objectives"] == []
            assert result["sections"] == []

    @pytest.mark.asyncio
    async def test_generate_learning_content_openai_error(self, content_service):
        """Test handling of OpenAI API error."""
        with (
            patch.object(
                content_service.client.chat.completions,
                "create",
                side_effect=Exception("OpenAI API error"),
            ),
            pytest.raises(Exception, match="OpenAI API error"),
        ):
            await content_service.generate_learning_content(
                subject="Biología",
                grade=8,
                curriculum_context="Context",
                topic="Topic",
            )

    @pytest.mark.asyncio
    async def test_generate_learning_content_includes_context(self, content_service):
        """Test that curriculum context is included in the prompt."""
        context = "Bases Curriculares específicas"

        with patch.object(
            content_service.client.chat.completions,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_message = AsyncMock()
            mock_message.content = json.dumps(
                {
                    "title": "Test",
                    "overview": "Test",
                    "learning_objectives": [],
                    "sections": [],
                    "vocabulary": [],
                    "summary": "Test",
                }
            )
            mock_create.return_value.choices = [AsyncMock(message=mock_message)]

            await content_service.generate_learning_content(
                subject="Biología",
                grade=8,
                curriculum_context=context,
                topic="Topic",
            )

            # Verify context was passed in the prompt
            call_args = mock_create.call_args
            assert context in call_args[1]["messages"][0]["content"]


class TestGenerateStudyGuide:
    """Tests for generate_study_guide method."""

    @pytest.mark.asyncio
    async def test_generate_study_guide_success(self, content_service):
        """Test successful study guide generation."""
        mock_response = {
            "title": "Guía de Estudio: Photosíntesis",
            "subject": "Biología",
            "grade": 8,
            "key_concepts": [
                {
                    "concept": "Photosíntesis",
                    "explanation": "Proceso de conversión de luz...",
                    "importance": "Es fundamental para la vida",
                }
            ],
            "summary_sections": [
                {
                    "title": "Conceptos Principales",
                    "summary": "La photosíntesis tiene dos fases...",
                    "remember": ["Requiere luz", "Produce glucosa"],
                }
            ],
            "common_mistakes": [
                {
                    "mistake": "La photosíntesis ocurre solo en hojas",
                    "correction": "Ocurre en cualquier parte verde",
                    "explanation": "Donde hay clorofila...",
                }
            ],
            "practice_tips": ["Dibuja los pasos", "Memoriza los productos"],
            "review_questions": ["¿Cuáles son las fases?", "¿Qué es clorofila?"],
        }

        with patch.object(
            content_service.client.chat.completions,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_message = AsyncMock()
            mock_message.content = json.dumps(mock_response)
            mock_create.return_value.choices = [AsyncMock(message=mock_message)]

            result = await content_service.generate_study_guide(
                subject="Biología",
                grade=8,
                curriculum_context="Context",
                topic="Photosíntesis",
            )

            assert result["title"] == "Guía de Estudio: Photosíntesis"
            assert result["subject"] == "Biología"
            assert len(result["key_concepts"]) == 1
            assert len(result["common_mistakes"]) == 1
            assert len(result["practice_tips"]) == 2
            assert len(result["review_questions"]) == 2

    @pytest.mark.asyncio
    async def test_generate_study_guide_invalid_json(self, content_service):
        """Test handling of invalid JSON response."""
        with patch.object(
            content_service.client.chat.completions,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_message = AsyncMock()
            mock_message.content = "not valid json"
            mock_create.return_value.choices = [AsyncMock(message=mock_message)]

            result = await content_service.generate_study_guide(
                subject="Biología",
                grade=8,
                curriculum_context="Context",
            )

            # Should return fallback structure
            assert result["subject"] == "Biología"
            assert result["grade"] == 8
            assert result["key_concepts"] == []
            assert result["common_mistakes"] == []

    @pytest.mark.asyncio
    async def test_generate_study_guide_includes_topic(self, content_service):
        """Test that topic is used when provided."""
        topic = "Photosíntesis"

        with patch.object(
            content_service.client.chat.completions,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_message = AsyncMock()
            mock_message.content = json.dumps(
                {
                    "title": "Test",
                    "subject": "Biología",
                    "grade": 8,
                    "key_concepts": [],
                    "summary_sections": [],
                    "common_mistakes": [],
                    "practice_tips": [],
                    "review_questions": [],
                }
            )
            mock_create.return_value.choices = [AsyncMock(message=mock_message)]

            await content_service.generate_study_guide(
                subject="Biología",
                grade=8,
                curriculum_context="Context",
                topic=topic,
            )

            # Verify topic was included in prompt
            call_args = mock_create.call_args
            assert topic in call_args[1]["messages"][0]["content"]

    @pytest.mark.asyncio
    async def test_generate_study_guide_defaults_to_subject(self, content_service):
        """Test that subject is used when topic is None."""
        subject = "Biología"

        with patch.object(
            content_service.client.chat.completions,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_message = AsyncMock()
            mock_message.content = json.dumps(
                {
                    "title": "Test",
                    "subject": subject,
                    "grade": 8,
                    "key_concepts": [],
                    "summary_sections": [],
                    "common_mistakes": [],
                    "practice_tips": [],
                    "review_questions": [],
                }
            )
            mock_create.return_value.choices = [AsyncMock(message=mock_message)]

            await content_service.generate_study_guide(
                subject=subject,
                grade=8,
                curriculum_context="Context",
                topic=None,
            )

            # Verify subject was included in prompt
            call_args = mock_create.call_args
            assert subject in call_args[1]["messages"][0]["content"]
