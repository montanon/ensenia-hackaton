"""Pydantic models and enums for Ensenia."""

from enum import Enum

from app.ensenia.models.curriculum import (
    CurriculumContent,
    FetchResponse,
    GenerateRequest,
    GenerateResponse,
    SearchRequest,
    SearchResponse,
    SearchResultMetadata,
    ValidateRequest,
    ValidateResponse,
    ValidationDetails,
)


class ChatMode(str, Enum):
    """Chat mode enumeration.

    Defines the available modes for chat sessions.
    """

    LEARN = "learn"
    PRACTICE = "practice"
    EVALUATION = "evaluation"
    STUDY = "study"


__all__ = [
    "ChatMode",
    "SearchRequest",
    "SearchResponse",
    "SearchResultMetadata",
    "FetchResponse",
    "CurriculumContent",
    "GenerateRequest",
    "GenerateResponse",
    "ValidateRequest",
    "ValidateResponse",
    "ValidationDetails",
]
