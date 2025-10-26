"""Tests for exercise generation service."""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from app.ensenia.schemas.exercises import DifficultyLevel, ExerciseType
from app.ensenia.services.generation_service import (
    GenerationService,
    get_generation_service,
)


@pytest.fixture
def generation_service():
    """Create generation service instance."""
    return GenerationService()


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    content = """{
        "question": "¿Cuánto es 1/2 + 1/4?",
        "learning_objective": "Sumar fracciones con diferentes denominadores",
        "options": ["1/6", "2/6", "3/4", "1/8"],
        "correct_answer": 2,
        "explanation": "Para sumar fracciones con diferentes denominadores, primero encontramos un denominador común."
    }"""
    return AIMessage(content=content)


@pytest.fixture
def mock_validation_response():
    """Mock validation response from OpenAI."""
    content = """{
        "score": 9,
        "breakdown": {
            "curriculum_alignment": 2,
            "grade_appropriate": 2,
            "difficulty_match": 2,
            "pedagogical_quality": 2,
            "chilean_spanish": 1
        },
        "feedback": "Excelente ejercicio, bien alineado con el currículo chileno.",
        "recommendation": "APROBAR"
    }"""
    return AIMessage(content=content)


class TestGenerationService:
    """Tests for GenerationService class."""

    def test_singleton_pattern(self):
        """Test that get_generation_service returns singleton."""
        service1 = get_generation_service()
        service2 = get_generation_service()

        assert service1 is service2

    @patch("app.ensenia.services.generation_service.ChatOpenAI")
    async def test_generate_exercise_success(
        self,
        mock_chat_openai,
        generation_service,
        mock_openai_response,
        mock_validation_response,
    ):
        """Test successful exercise generation with approval on first iteration."""
        # Mock LLM responses
        mock_llm = MagicMock()
        mock_llm.invoke = MagicMock(
            side_effect=[mock_openai_response, mock_validation_response]
        )
        mock_chat_openai.return_value = mock_llm

        # Generate exercise
        content, history, iterations = await generation_service.generate_exercise(
            exercise_type=ExerciseType.MULTIPLE_CHOICE,
            grade=8,
            subject="Matemáticas",
            topic="Fracciones",
            difficulty_level=DifficultyLevel.MEDIUM,
        )

        # Assertions
        assert content is not None
        assert "question" in content
        assert len(history) == 1
        assert history[0].score == 9
        assert history[0].is_approved is True
        assert iterations == 1

    @patch("app.ensenia.services.generation_service.ChatOpenAI")
    async def test_generate_exercise_multiple_iterations(
        self, mock_chat_openai, generation_service, mock_openai_response
    ):
        """Test exercise generation with multiple refinement iterations."""
        # Mock LLM responses - first validation fails, second succeeds
        mock_llm = MagicMock()

        # First iteration: low score
        first_validation = AIMessage(
            content="""{
            "score": 5,
            "feedback": "Necesita mejoras en la explicación",
            "recommendation": "REVISAR"
        }"""
        )

        # Second iteration: high score
        second_validation = AIMessage(
            content="""{
            "score": 9,
            "feedback": "Mucho mejor",
            "recommendation": "APROBAR"
        }"""
        )

        mock_llm.invoke = MagicMock(
            side_effect=[
                mock_openai_response,  # Generate
                first_validation,  # Validate (fail)
                mock_openai_response,  # Refine
                second_validation,  # Validate (pass)
            ]
        )
        mock_chat_openai.return_value = mock_llm

        # Generate exercise
        _, history, iterations = await generation_service.generate_exercise(
            exercise_type=ExerciseType.MULTIPLE_CHOICE,
            grade=8,
            subject="Matemáticas",
            topic="Fracciones",
            max_iterations=3,
            quality_threshold=8,
        )

        # Assertions
        assert iterations == 2
        assert len(history) == 2
        assert history[0].score == 5
        assert history[0].is_approved is False
        assert history[1].score == 9
        assert history[1].is_approved is True

    @patch("app.ensenia.services.generation_service.ChatOpenAI")
    async def test_generate_exercise_max_iterations_reached(
        self, mock_chat_openai, generation_service, mock_openai_response
    ):
        """Test that generation stops after max iterations."""
        # Mock LLM responses - always low score
        mock_llm = MagicMock()

        low_score_validation = AIMessage(
            content="""{
            "score": 5,
            "feedback": "Necesita mejoras",
            "recommendation": "REVISAR"
        }"""
        )

        mock_llm.invoke = MagicMock(
            side_effect=[
                mock_openai_response,  # Generate iteration 1
                low_score_validation,  # Validate iteration 1
                mock_openai_response,  # Refine iteration 2
                low_score_validation,  # Validate iteration 2
                mock_openai_response,  # Refine iteration 3
                low_score_validation,  # Validate iteration 3
            ]
        )
        mock_chat_openai.return_value = mock_llm

        # Generate exercise with max 3 iterations
        _, history, iterations = await generation_service.generate_exercise(
            exercise_type=ExerciseType.TRUE_FALSE,
            grade=5,
            subject="Ciencias",
            topic="Animales",
            max_iterations=3,
            quality_threshold=8,
        )

        # Assertions
        assert iterations == 3
        assert len(history) == 3
        assert all(not h.is_approved for h in history)

    def test_validate_content_schema_multiple_choice(
        self, generation_service, sample_multiple_choice_exercise
    ):
        """Test content schema validation for multiple choice."""
        is_valid = generation_service.validate_content_schema(
            ExerciseType.MULTIPLE_CHOICE, sample_multiple_choice_exercise
        )

        assert is_valid is True

    def test_validate_content_schema_invalid(self, generation_service):
        """Test content schema validation with invalid content."""
        invalid_content = {"question": "Test"}  # Missing required fields

        is_valid = generation_service.validate_content_schema(
            ExerciseType.MULTIPLE_CHOICE, invalid_content
        )

        assert is_valid is False

    def test_validate_content_schema_true_false(
        self, generation_service, sample_true_false_exercise
    ):
        """Test content schema validation for true/false."""
        is_valid = generation_service.validate_content_schema(
            ExerciseType.TRUE_FALSE, sample_true_false_exercise
        )

        assert is_valid is True

    def test_validate_content_schema_short_answer(
        self, generation_service, sample_short_answer_exercise
    ):
        """Test content schema validation for short answer."""
        is_valid = generation_service.validate_content_schema(
            ExerciseType.SHORT_ANSWER, sample_short_answer_exercise
        )

        assert is_valid is True

    def test_validate_content_schema_essay(
        self, generation_service, sample_essay_exercise
    ):
        """Test content schema validation for essay."""
        is_valid = generation_service.validate_content_schema(
            ExerciseType.ESSAY, sample_essay_exercise
        )

        assert is_valid is True

    @patch("app.ensenia.services.generation_service.ChatOpenAI")
    async def test_generate_with_curriculum_context(
        self,
        mock_chat_openai,
        generation_service,
        mock_openai_response,
        mock_validation_response,
    ):
        """Test generation with additional curriculum context."""
        mock_llm = MagicMock()
        mock_llm.invoke = MagicMock(
            side_effect=[mock_openai_response, mock_validation_response]
        )
        mock_chat_openai.return_value = mock_llm

        curriculum_context = "Bases Curriculares de Matemáticas 8° básico"

        _, _, _ = await generation_service.generate_exercise(
            exercise_type=ExerciseType.MULTIPLE_CHOICE,
            grade=8,
            subject="Matemáticas",
            topic="Fracciones",
            curriculum_context=curriculum_context,
        )

        # Verify curriculum context was used in the call
        assert mock_llm.invoke.called
        call_args = mock_llm.invoke.call_args_list[0][0][0]
        assert any(curriculum_context in str(msg.content) for msg in call_args)

    @patch("app.ensenia.services.generation_service.ChatOpenAI")
    async def test_generate_all_exercise_types(
        self,
        mock_chat_openai,
        generation_service,
        mock_openai_response,
        mock_validation_response,
    ):
        """Test that all exercise types can be generated."""
        mock_llm = MagicMock()
        mock_llm.invoke = MagicMock(
            side_effect=[
                mock_openai_response,
                mock_validation_response,
            ]
            * 4  # For each type
        )
        mock_chat_openai.return_value = mock_llm

        exercise_types = [
            ExerciseType.MULTIPLE_CHOICE,
            ExerciseType.TRUE_FALSE,
            ExerciseType.SHORT_ANSWER,
            ExerciseType.ESSAY,
        ]

        for exercise_type in exercise_types:
            content, history, iterations = await generation_service.generate_exercise(
                exercise_type=exercise_type,
                grade=8,
                subject="Test",
                topic="Test Topic",
            )

            assert content is not None
            assert len(history) >= 1
            assert iterations >= 1
