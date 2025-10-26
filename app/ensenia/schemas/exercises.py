"""Pydantic schemas for exercise generation and validation.

This module defines schemas for all exercise types and their validation.
Follows Chilean Ministry of Education curriculum alignment requirements.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class ExerciseType(str, Enum):
    """Supported exercise types."""

    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"


class DifficultyLevel(int, Enum):
    """Exercise difficulty levels (1-5)."""

    VERY_EASY = 1
    EASY = 2
    MEDIUM = 3
    HARD = 4
    VERY_HARD = 5


# ============================================================================
# Base Schemas
# ============================================================================


class ExerciseContentBase(BaseModel):
    """Base schema for all exercise content types."""

    question: str = Field(
        ..., min_length=10, max_length=1000, description="The exercise question"
    )
    learning_objective: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description=(
            "Learning objective aligned with Chilean curriculum (Bases Curriculares)"
        ),
    )


# ============================================================================
# Exercise Type-Specific Content Schemas
# ============================================================================


class MultipleChoiceContent(ExerciseContentBase):
    """Content schema for multiple choice exercises."""

    options: list[str] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="Answer options (2-5 choices)",
    )
    correct_answer: int = Field(
        ...,
        ge=0,
        description="Index of the correct answer in options array (0-based)",
    )
    explanation: str = Field(
        ...,
        min_length=20,
        max_length=500,
        description="Explanation of why the correct answer is correct",
    )

    @field_validator("correct_answer")
    @classmethod
    def validate_correct_answer(cls, v: int, info: ValidationInfo) -> int:
        """Ensure correct_answer index is within options range."""
        if "options" in info.data and v >= len(info.data["options"]):
            msg = (
                f"correct_answer index {v} is out of range "
                f"for {len(info.data['options'])} options"
            )
            raise ValueError(msg)
        return v


class TrueFalseContent(ExerciseContentBase):
    """Content schema for true/false exercises."""

    correct_answer: bool = Field(..., description="The correct answer (True or False)")
    explanation: str = Field(
        ...,
        min_length=20,
        max_length=500,
        description="Explanation of why the statement is true or false",
    )


class ShortAnswerContent(ExerciseContentBase):
    """Content schema for short answer exercises."""

    rubric: list[str] = Field(
        ...,
        min_length=2,
        max_length=10,
        description="Rubric points for evaluating the answer",
    )
    example_answer: str = Field(
        ...,
        min_length=10,
        max_length=300,
        description="Example of a good answer (1-3 sentences)",
    )
    max_words: int = Field(default=100, ge=10, le=300, description="Maximum word count")


class EssayContent(ExerciseContentBase):
    """Content schema for essay exercises."""

    rubric: list[str] = Field(
        ...,
        min_length=3,
        max_length=15,
        description="Rubric points for evaluating the essay",
    )
    key_points: list[str] = Field(
        ...,
        min_length=2,
        max_length=10,
        description="Key points that should be addressed in the essay",
    )
    min_words: int = Field(default=150, ge=50, le=500, description="Minimum word count")
    max_words: int = Field(
        default=500, ge=100, le=2000, description="Maximum word count"
    )

    @field_validator("max_words")
    @classmethod
    def validate_word_counts(cls, v: int, info: ValidationInfo) -> int:
        """Ensure max_words is greater than min_words."""
        if "min_words" in info.data and v <= info.data["min_words"]:
            msg = (
                f"max_words ({v}) must be greater "
                f"than min_words ({info.data['min_words']})"
            )
            raise ValueError(msg)
        return v


# ============================================================================
# Request Schemas
# ============================================================================


class GenerateExerciseRequest(BaseModel):
    """Request schema for generating a new exercise."""

    exercise_type: ExerciseType = Field(..., description="Type of exercise to generate")
    grade: int = Field(..., ge=1, le=12, description="Grade level (1-12)")
    subject: str = Field(..., min_length=1, max_length=100, description="Subject area")
    topic: str = Field(..., min_length=1, max_length=200, description="Specific topic")
    difficulty_level: DifficultyLevel = Field(
        default=DifficultyLevel.MEDIUM,
        description="Desired difficulty level",
    )
    max_iterations: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description="Max validation iterations (overrides config default)",
    )
    quality_threshold: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description="Minimum quality score (overrides config default)",
    )
    curriculum_context: str | None = Field(
        default=None,
        max_length=2000,
        description="Additional curriculum context from research",
    )
    force_new: bool = Field(
        default=False,
        description="If True, skip reusing existing exercises and generate new one",
    )


class SearchExercisesRequest(BaseModel):
    """Request schema for searching existing exercises."""

    grade: int | None = Field(
        default=None, ge=1, le=12, description="Filter by grade level"
    )
    subject: str | None = Field(
        default=None, max_length=100, description="Filter by subject"
    )
    topic: str | None = Field(
        default=None, max_length=200, description="Filter by topic"
    )
    exercise_type: ExerciseType | None = Field(
        default=None, description="Filter by type"
    )
    difficulty_level: DifficultyLevel | None = Field(
        default=None, description="Filter by difficulty"
    )
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results to return")


class LinkExerciseRequest(BaseModel):
    """Request schema for linking an exercise to a session."""

    session_id: int = Field(..., ge=1, description="Session ID to link exercise to")


class SubmitAnswerRequest(BaseModel):
    """Request schema for submitting an exercise answer."""

    answer: str = Field(
        ..., min_length=1, max_length=5000, description="Student's answer"
    )


# ============================================================================
# Response Schemas
# ============================================================================


class ValidationResult(BaseModel):
    """Validation result from agent-validator loop."""

    score: int = Field(..., ge=0, le=10, description="Quality score (0-10)")
    breakdown: dict[str, int] = Field(..., description="Score breakdown by criteria")
    feedback: str = Field(..., description="Validation feedback")
    recommendation: str = Field(..., description="Recommendation (APROBAR/REVISAR)")
    is_approved: bool = Field(
        ..., description="Whether the exercise meets quality threshold"
    )
    iteration: int = Field(..., ge=1, description="Iteration number in the loop")


class ExerciseResponse(BaseModel):
    """Response schema for a generated or retrieved exercise."""

    id: int = Field(..., description="Exercise ID")
    exercise_type: ExerciseType = Field(..., description="Type of exercise")
    grade: int = Field(..., description="Grade level")
    subject: str = Field(..., description="Subject area")
    topic: str = Field(..., description="Specific topic")
    content: (
        MultipleChoiceContent | TrueFalseContent | ShortAnswerContent | EssayContent
    ) = Field(..., description="Exercise content (type-specific)")
    validation_score: int = Field(..., description="Final validation score (0-10)")
    difficulty_level: int = Field(..., description="Difficulty level (1-5)")
    is_public: bool = Field(..., description="Whether exercise can be reused")
    created_at: datetime = Field(..., description="When the exercise was created")

    model_config = ConfigDict(from_attributes=True)


class ExerciseWithSessionInfo(BaseModel):
    """Exercise response with session link information."""

    exercise: ExerciseResponse = Field(..., description="The exercise details")
    exercise_session_id: int = Field(..., description="ID of the exercise-session link")


class ExerciseListResponse(BaseModel):
    """Response schema for a list of exercises."""

    exercises: list[ExerciseResponse] = Field(..., description="List of exercises")
    total: int = Field(..., description="Total number of exercises found")


class SessionExercisesListResponse(BaseModel):
    """Response schema for exercises linked to a session."""

    exercises: list[ExerciseWithSessionInfo] = Field(..., description="List of exercises with session info")
    total: int = Field(..., description="Total number of exercises found")


class GenerateExerciseResponse(BaseModel):
    """Response schema for exercise generation."""

    exercise: ExerciseResponse = Field(..., description="The generated exercise")
    validation_history: list[ValidationResult] = Field(
        ..., description="History of validation iterations"
    )
    iterations_used: int = Field(..., description="Number of iterations performed")


class LinkExerciseResponse(BaseModel):
    """Response schema for linking exercise to session."""

    exercise_session_id: int = Field(..., description="ID of the exercise-session link")
    exercise_id: int = Field(..., description="Exercise ID")
    session_id: int = Field(..., description="Session ID")
    assigned_at: datetime = Field(..., description="When the exercise was assigned")


class SubmitAnswerResponse(BaseModel):
    """Response schema for submitting an answer."""

    is_completed: bool = Field(
        ..., description="Whether the exercise is now marked complete"
    )
    completed_at: datetime | None = Field(
        default=None, description="When the exercise was completed"
    )
    feedback: str | None = Field(
        default=None, description="Optional feedback on the submitted answer"
    )
