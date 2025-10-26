"""Standardized error response schemas."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Details about an error."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    field: str | None = Field(
        None, description="Field that caused the error (for validation)"
    )


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: ErrorDetail
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    path: str | None = Field(None, description="Request path that caused the error")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid grade level: must be between 1 and 12",
                    "field": "grade",
                },
                "timestamp": "2025-10-26T00:00:00Z",
                "path": "/exercises/generate",
            }
        }
    }


# Common error codes
class ErrorCode:
    """Standard error codes."""

    # Validation errors (400/422)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"

    # Not found errors (404)
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    EXERCISE_NOT_FOUND = "EXERCISE_NOT_FOUND"

    # Server errors (500)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_ERROR = "SERVICE_ERROR"
    GENERATION_FAILED = "GENERATION_FAILED"
    TTS_ERROR = "TTS_ERROR"
    RESEARCH_ERROR = "RESEARCH_ERROR"
