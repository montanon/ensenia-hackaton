"""Tests for exercise Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.ensenia.schemas.exercises import (
    DifficultyLevel,
    EssayContent,
    ExerciseType,
    GenerateExerciseRequest,
    MultipleChoiceContent,
    SearchExercisesRequest,
    ShortAnswerContent,
    TrueFalseContent,
)


class TestMultipleChoiceContent:
    """Tests for MultipleChoiceContent schema."""

    def test_valid_multiple_choice(self, sample_multiple_choice_exercise):
        """Test valid multiple choice exercise creation."""
        content = MultipleChoiceContent(**sample_multiple_choice_exercise)
        assert content.question == sample_multiple_choice_exercise["question"]
        assert len(content.options) == 4
        assert content.correct_answer == 0

    def test_correct_answer_out_of_range(self, sample_multiple_choice_exercise):
        """Test that correct_answer must be within options range."""
        sample_multiple_choice_exercise["correct_answer"] = 10
        with pytest.raises(ValidationError) as exc_info:
            MultipleChoiceContent(**sample_multiple_choice_exercise)
        assert "out of range" in str(exc_info.value)

    def test_too_few_options(self, sample_multiple_choice_exercise):
        """Test that at least 2 options are required."""
        sample_multiple_choice_exercise["options"] = ["Only one"]
        with pytest.raises(ValidationError):
            MultipleChoiceContent(**sample_multiple_choice_exercise)

    def test_too_many_options(self, sample_multiple_choice_exercise):
        """Test that max 5 options are allowed."""
        sample_multiple_choice_exercise["options"] = [f"Option {i}" for i in range(10)]
        with pytest.raises(ValidationError):
            MultipleChoiceContent(**sample_multiple_choice_exercise)

    def test_short_question(self, sample_multiple_choice_exercise):
        """Test that question has minimum length."""
        sample_multiple_choice_exercise["question"] = "Short"
        with pytest.raises(ValidationError):
            MultipleChoiceContent(**sample_multiple_choice_exercise)

    def test_short_explanation(self, sample_multiple_choice_exercise):
        """Test that explanation has minimum length."""
        sample_multiple_choice_exercise["explanation"] = "Too short"
        with pytest.raises(ValidationError):
            MultipleChoiceContent(**sample_multiple_choice_exercise)


class TestTrueFalseContent:
    """Tests for TrueFalseContent schema."""

    def test_valid_true_false(self, sample_true_false_exercise):
        """Test valid true/false exercise creation."""
        content = TrueFalseContent(**sample_true_false_exercise)
        assert content.correct_answer is True
        assert len(content.explanation) >= 20

    def test_requires_explanation(self, sample_true_false_exercise):
        """Test that explanation is required."""
        sample_true_false_exercise["explanation"] = "Short"
        with pytest.raises(ValidationError):
            TrueFalseContent(**sample_true_false_exercise)


class TestShortAnswerContent:
    """Tests for ShortAnswerContent schema."""

    def test_valid_short_answer(self, sample_short_answer_exercise):
        """Test valid short answer exercise creation."""
        content = ShortAnswerContent(**sample_short_answer_exercise)
        assert len(content.rubric) >= 2
        assert content.max_words == 100

    def test_rubric_min_length(self, sample_short_answer_exercise):
        """Test that rubric needs at least 2 items."""
        sample_short_answer_exercise["rubric"] = ["Only one criterion"]
        with pytest.raises(ValidationError):
            ShortAnswerContent(**sample_short_answer_exercise)

    def test_rubric_max_length(self, sample_short_answer_exercise):
        """Test that rubric max is 10 items."""
        sample_short_answer_exercise["rubric"] = [f"Criterion {i}" for i in range(15)]
        with pytest.raises(ValidationError):
            ShortAnswerContent(**sample_short_answer_exercise)


class TestEssayContent:
    """Tests for EssayContent schema."""

    def test_valid_essay(self, sample_essay_exercise):
        """Test valid essay exercise creation."""
        content = EssayContent(**sample_essay_exercise)
        assert len(content.rubric) >= 3
        assert len(content.key_points) >= 2
        assert content.min_words < content.max_words

    def test_max_words_less_than_min_words(self, sample_essay_exercise):
        """Test that max_words must be greater than min_words."""
        sample_essay_exercise["min_words"] = 500
        sample_essay_exercise["max_words"] = 100
        with pytest.raises(ValidationError) as exc_info:
            EssayContent(**sample_essay_exercise)
        assert "must be greater than min_words" in str(exc_info.value)

    def test_rubric_min_items(self, sample_essay_exercise):
        """Test that rubric needs at least 3 items for essays."""
        sample_essay_exercise["rubric"] = ["Only", "Two"]
        with pytest.raises(ValidationError):
            EssayContent(**sample_essay_exercise)

    def test_key_points_min_items(self, sample_essay_exercise):
        """Test that key_points needs at least 2 items."""
        sample_essay_exercise["key_points"] = ["Only one"]
        with pytest.raises(ValidationError):
            EssayContent(**sample_essay_exercise)


class TestGenerateExerciseRequest:
    """Tests for GenerateExerciseRequest schema."""

    def test_valid_request(self):
        """Test valid exercise generation request."""
        request = GenerateExerciseRequest(
            exercise_type=ExerciseType.MULTIPLE_CHOICE,
            grade=8,
            subject="Matemáticas",
            topic="Fracciones",
            difficulty_level=DifficultyLevel.MEDIUM,
        )
        assert request.grade == 8
        assert request.exercise_type == ExerciseType.MULTIPLE_CHOICE

    def test_grade_validation(self):
        """Test that grade must be between 1 and 12."""
        with pytest.raises(ValidationError):
            GenerateExerciseRequest(
                exercise_type=ExerciseType.MULTIPLE_CHOICE,
                grade=0,
                subject="Math",
                topic="Test",
            )

        with pytest.raises(ValidationError):
            GenerateExerciseRequest(
                exercise_type=ExerciseType.MULTIPLE_CHOICE,
                grade=13,
                subject="Math",
                topic="Test",
            )

    def test_optional_parameters(self):
        """Test that optional parameters have defaults."""
        request = GenerateExerciseRequest(
            exercise_type=ExerciseType.TRUE_FALSE,
            grade=5,
            subject="Ciencias",
            topic="Animales",
        )
        assert request.difficulty_level == DifficultyLevel.MEDIUM
        assert request.max_iterations is None
        assert request.quality_threshold is None

    def test_max_iterations_validation(self):
        """Test that max_iterations is bounded."""
        with pytest.raises(ValidationError):
            GenerateExerciseRequest(
                exercise_type=ExerciseType.ESSAY,
                grade=10,
                subject="Historia",
                topic="Independencia",
                max_iterations=0,
            )

        with pytest.raises(ValidationError):
            GenerateExerciseRequest(
                exercise_type=ExerciseType.ESSAY,
                grade=10,
                subject="Historia",
                topic="Independencia",
                max_iterations=20,
            )


class TestSearchExercisesRequest:
    """Tests for SearchExercisesRequest schema."""

    def test_empty_search(self):
        """Test search with no filters."""
        request = SearchExercisesRequest()
        assert request.grade is None
        assert request.subject is None
        assert request.limit == 10

    def test_with_filters(self):
        """Test search with filters."""
        request = SearchExercisesRequest(
            grade=8,
            subject="Matemáticas",
            topic="Álgebra",
            exercise_type=ExerciseType.MULTIPLE_CHOICE,
            difficulty_level=DifficultyLevel.HARD,
            limit=20,
        )
        assert request.grade == 8
        assert request.limit == 20

    def test_limit_validation(self):
        """Test that limit is bounded."""
        with pytest.raises(ValidationError):
            SearchExercisesRequest(limit=0)

        with pytest.raises(ValidationError):
            SearchExercisesRequest(limit=100)
