"""Tests for curriculum Pydantic models.

Validates that models correctly parse Worker responses and reject invalid data.
"""

import pytest
from pydantic import ValidationError

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


class TestSearchModels:
    """Test search-related Pydantic models."""

    def test_search_request_valid(self):
        """Test SearchRequest with valid data."""
        request = SearchRequest(
            query="fracciones", grade=5, subject="matemáticas", limit=10
        )
        assert request.query == "fracciones"
        assert request.grade == 5
        assert request.limit == 10

    def test_search_request_defaults(self):
        """Test SearchRequest with default limit."""
        request = SearchRequest(query="test", grade=5, subject="matemáticas")
        assert request.limit == 10  # Default value

    def test_search_request_grade_validation(self):
        """Test SearchRequest rejects invalid grade."""
        with pytest.raises(ValidationError):
            SearchRequest(
                query="test",
                grade=0,  # Must be 1-12
                subject="matemáticas",
            )

        with pytest.raises(ValidationError):
            SearchRequest(
                query="test",
                grade=13,  # Must be 1-12
                subject="matemáticas",
            )

    def test_search_response_valid(self):
        """Test SearchResponse with valid data."""
        response = SearchResponse(
            query="fracciones",
            grade=5,
            subject="matemáticas",
            total_found=3,
            content_ids=["id1", "id2", "id3"],
            metadata=[
                SearchResultMetadata(
                    id="id1", score=0.95, title="Test", oa="MAT.5.OA.1"
                )
            ],
            cached=False,
            search_time_ms=45.2,
        )
        assert response.total_found == 3
        assert len(response.content_ids) == 3
        assert response.metadata[0].score == 0.95

    def test_search_response_missing_fields(self):
        """Test SearchResponse rejects missing required fields."""
        with pytest.raises(ValidationError):
            SearchResponse(
                query="test",
                # Missing grade, subject, total_found, etc.
            )


class TestFetchModels:
    """Test fetch-related Pydantic models."""

    def test_curriculum_content_valid(self):
        """Test CurriculumContent with valid data."""
        content = CurriculumContent(
            id="id1",
            title="Suma de Fracciones",
            grade=5,
            subject="matemáticas",
            content_text="Las fracciones...",
            learning_objectives=["Comprender", "Sumar"],
            ministry_standard_ref="MAT.5.OA.1",
            ministry_approved=True,
            keywords="fracciones,suma",
            difficulty_level="medium",
        )
        assert content.id == "id1"
        assert content.ministry_approved is True
        assert len(content.learning_objectives) == 2

    def test_fetch_response_valid(self):
        """Test FetchResponse with valid data."""
        response = FetchResponse(
            contents=[
                CurriculumContent(
                    id="id1",
                    title="Test",
                    grade=5,
                    subject="matemáticas",
                    content_text="Text",
                    learning_objectives=[],
                    ministry_standard_ref="REF",
                    ministry_approved=True,
                    keywords="test",
                    difficulty_level="easy",
                )
            ],
            fetch_time_ms=12.5,
        )
        assert len(response.contents) == 1
        assert response.fetch_time_ms == 12.5

    def test_fetch_response_empty_contents(self):
        """Test FetchResponse allows empty contents list."""
        response = FetchResponse(contents=[], fetch_time_ms=5.0)
        assert len(response.contents) == 0


class TestGenerateModels:
    """Test generation-related Pydantic models."""

    def test_generate_request_valid(self):
        """Test GenerateRequest with valid data."""
        request = GenerateRequest(
            context="Context text",
            query="Query text",
            grade=5,
            subject="matemáticas",
            oa_codes=["MAT.5.OA.1"],
            style="explanation",
        )
        assert request.style == "explanation"
        assert len(request.oa_codes) == 1

    def test_generate_request_default_style(self):
        """Test GenerateRequest with default style."""
        request = GenerateRequest(
            context="Context",
            query="Query",
            grade=5,
            subject="matemáticas",
            oa_codes=[],
        )
        assert request.style == "explanation"  # Default

    def test_generate_request_invalid_style(self):
        """Test GenerateRequest rejects invalid style."""
        with pytest.raises(ValidationError):
            GenerateRequest(
                context="Context",
                query="Query",
                grade=5,
                subject="matemáticas",
                oa_codes=[],
                style="invalid_style",  # Must be explanation/summary/example
            )

    def test_generate_response_valid(self):
        """Test GenerateResponse with valid data."""
        response = GenerateResponse(
            generated_text="Generated content here",
            oa_codes=["MAT.5.OA.1"],
            model_used="@cf/meta/llama-3.1-8b-instruct",
            generation_time_ms=234.5,
        )
        assert len(response.generated_text) > 0
        assert response.generation_time_ms > 0


class TestValidateModels:
    """Test validation-related Pydantic models."""

    def test_validation_details_valid(self):
        """Test ValidationDetails with valid data."""
        details = ValidationDetails(
            oa_alignment_score=90,
            grade_appropriate_score=85,
            chilean_terminology_score=92,
            learning_coverage_score=88,
            issues=["Issue 1"],
            recommendations=["Recommendation 1"],
        )
        assert details.oa_alignment_score == 90
        assert len(details.issues) == 1

    def test_validate_request_valid(self):
        """Test ValidateRequest with valid data."""
        request = ValidateRequest(
            content="Content to validate",
            grade=5,
            subject="matemáticas",
            expected_oa=["MAT.5.OA.1"],
        )
        assert request.grade == 5
        assert len(request.expected_oa) == 1

    def test_validate_response_valid(self):
        """Test ValidateResponse with valid data."""
        response = ValidateResponse(
            is_valid=True,
            score=87,
            validation_details=ValidationDetails(
                oa_alignment_score=92,
                grade_appropriate_score=85,
                chilean_terminology_score=90,
                learning_coverage_score=83,
                issues=[],
                recommendations=["Add examples"],
            ),
            validation_time_ms=156.3,
        )
        assert response.is_valid is True
        assert response.score == 87
        assert 0.0 <= response.score <= 100.0

    def test_validate_response_score_bounds(self):
        """Test ValidateResponse enforces score bounds."""
        # Score too high
        with pytest.raises(ValidationError):
            ValidateResponse(
                is_valid=True,
                score=150,  # Must be 0-100
                validation_details=ValidationDetails(
                    oa_alignment_score=92,
                    grade_appropriate_score=85,
                    chilean_terminology_score=90,
                    learning_coverage_score=83,
                    issues=[],
                    recommendations=[],
                ),
                validation_time_ms=100.0,
            )


class TestModelSerialization:
    """Test model serialization/deserialization."""

    def test_search_response_roundtrip(self):
        """Test SearchResponse can serialize and deserialize."""
        original = SearchResponse(
            query="test",
            grade=5,
            subject="matemáticas",
            total_found=1,
            content_ids=["id1"],
            metadata=[
                SearchResultMetadata(
                    id="id1", score=0.95, title="Test", oa="MAT.5.OA.1"
                )
            ],
            cached=False,
            search_time_ms=10.0,
        )

        # Serialize to dict
        data = original.model_dump()

        # Deserialize back
        restored = SearchResponse.model_validate(data)

        assert restored.query == original.query
        assert restored.total_found == original.total_found
        assert restored.metadata[0].score == original.metadata[0].score

    def test_generate_request_json_compatible(self):
        """Test GenerateRequest serializes to JSON-compatible dict."""
        request = GenerateRequest(
            context="Context",
            query="Query",
            grade=5,
            subject="matemáticas",
            oa_codes=["MAT.5.OA.1"],
            style="explanation",
        )

        data = request.model_dump()

        # Verify all values are JSON-serializable
        assert isinstance(data["context"], str)
        assert isinstance(data["grade"], int)
        assert isinstance(data["oa_codes"], list)
        assert isinstance(data["style"], str)
