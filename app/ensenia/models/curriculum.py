"""Pydantic models for Cloudflare Worker curriculum API.

These models match the TypeScript schemas defined in app/worker/src/types/schemas.ts
"""

from typing import Literal

from pydantic import BaseModel, Field

# ============================================================================
# SEARCH ENDPOINT
# ============================================================================


class SearchRequest(BaseModel):
    """Request model for curriculum search."""

    query: str = Field(..., description="Search query text")
    grade: int = Field(..., ge=1, le=12, description="Grade level (1-12)")
    subject: str = Field(..., description="Subject area (e.g., 'matemáticas')")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results to return")


class SearchResultMetadata(BaseModel):
    """Metadata for a single search result."""

    id: str = Field(..., description="Content ID")
    score: float = Field(..., description="Relevance score (0.0-1.0)")
    title: str = Field(..., description="Content title")
    oa: str = Field(..., description="Objetivo de Aprendizaje (OA) code")


class SearchResponse(BaseModel):
    """Response model for curriculum search."""

    query: str = Field(..., description="Original search query")
    grade: int = Field(..., description="Grade level searched")
    subject: str = Field(..., description="Subject searched")
    total_found: int = Field(..., description="Total results found")
    content_ids: list[str] = Field(..., description="List of content IDs")
    metadata: list[SearchResultMetadata] = Field(..., description="Result metadata")
    cached: bool = Field(..., description="Whether result was cached")
    search_time_ms: float = Field(..., description="Search time in milliseconds")


# ============================================================================
# FETCH ENDPOINT
# ============================================================================


class CurriculumContent(BaseModel):
    """Full curriculum content details."""

    id: str = Field(..., description="Content ID")
    title: str = Field(..., description="Content title")
    grade: int = Field(..., description="Grade level")
    subject: str = Field(..., description="Subject area")
    content_text: str = Field(..., description="Full content text")
    learning_objectives: list[str] = Field(..., description="Learning objectives")
    ministry_standard_ref: str = Field(..., description="Ministry standard reference")
    ministry_approved: bool = Field(..., description="Ministry approval status")
    keywords: str = Field(..., description="Comma-separated keywords")
    difficulty_level: str = Field(..., description="Difficulty level")


class FetchResponse(BaseModel):
    """Response model for fetching curriculum content."""

    contents: list[CurriculumContent] = Field(
        ..., description="Retrieved content items"
    )
    fetch_time_ms: float = Field(..., description="Fetch time in milliseconds")


# ============================================================================
# GENERATE ENDPOINT
# ============================================================================


class GenerateRequest(BaseModel):
    """Request model for generating educational content."""

    context: str = Field(..., description="Context for generation")
    query: str = Field(..., description="User query or topic")
    grade: int = Field(..., ge=1, le=12, description="Grade level (1-12)")
    subject: str = Field(..., description="Subject area")
    oa_codes: list[str] = Field(..., description="OA codes to align with")
    style: Literal["explanation", "summary", "example"] = Field(
        default="explanation", description="Generation style"
    )


class GenerateResponse(BaseModel):
    """Response model for generated content."""

    generated_text: str = Field(..., description="Generated educational content")
    oa_codes: list[str] = Field(..., description="OA codes used in generation")
    model_used: str = Field(..., description="AI model used for generation")
    generation_time_ms: float = Field(
        ..., description="Generation time in milliseconds"
    )


# ============================================================================
# VALIDATE ENDPOINT
# ============================================================================


class ValidationDetails(BaseModel):
    """Detailed validation metrics."""

    oa_alignment_score: float = Field(..., description="OA alignment score (0.0-1.0)")
    grade_appropriate_score: float = Field(
        ..., description="Grade appropriateness score (0.0-1.0)"
    )
    chilean_terminology_score: float = Field(
        ..., description="Chilean terminology score (0.0-1.0)"
    )
    learning_coverage_score: float = Field(
        ..., description="Learning coverage score (0.0-1.0)"
    )
    issues: list[str] = Field(..., description="Identified issues")
    recommendations: list[str] = Field(..., description="Improvement recommendations")


class ValidateRequest(BaseModel):
    """Request model for content validation."""

    content: str = Field(..., description="Content to validate")
    grade: int = Field(..., ge=1, le=12, description="Target grade level (1-12)")
    subject: str = Field(..., description="Subject area")
    expected_oa: list[str] = Field(..., description="Expected OA codes")


class ValidateResponse(BaseModel):
    """Response model for content validation."""

    is_valid: bool = Field(..., description="Overall validation result")
    score: float = Field(..., ge=0.0, le=1.0, description="Overall validation score")
    validation_details: ValidationDetails = Field(..., description="Detailed metrics")
    validation_time_ms: float = Field(
        ..., description="Validation time in milliseconds"
    )
