"""Pydantic models and enums for Ensenia."""

from enum import Enum


class ChatMode(str, Enum):
    """Chat mode enumeration.

    Defines the available modes for chat sessions.
    """

    LEARN = "learn"
    PRACTICE = "practice"
    EVALUATION = "evaluation"
    STUDY = "study"


__all__ = ["ChatMode"]
