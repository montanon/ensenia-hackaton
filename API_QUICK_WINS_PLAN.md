# API Quick Wins Implementation Plan
## Chilean Education AI Assistant - Hackathon Edition

**Document Version:** 1.0
**Created:** 2025-10-25
**Estimated Total Time:** 2 hours 15 minutes
**Priority Level:** HIGH - Pre-Demo Critical

---

## Executive Summary

### Overview
This plan details 5 high-impact, low-effort improvements to our FastAPI application that will significantly enhance judge appeal and API quality. All improvements can be completed in under 2.5 hours with minimal risk.

### Impact on Judging Criteria

| Criteria | Impact | Improvement |
|----------|--------|-------------|
| **Innovation (25%)** | Medium | Better API discoverability, modern patterns |
| **Technical Complexity (25%)** | High | Demonstrates REST mastery, performance awareness |
| **User Experience (25%)** | High | Clearer docs, faster debugging, better DX |
| **Social Impact (25%)** | Low | Indirect (better UX = more accessible) |

### Expected Outcomes
- ✅ **Better OpenAPI/Swagger Documentation** - Interactive examples, clear status codes
- ✅ **RESTful Compliance** - Proper HTTP method usage (critical for judges)
- ✅ **Performance Visibility** - Response time headers for all requests
- ✅ **Standardized Error Handling** - Consistent error format across API
- ✅ **Professional Polish** - Production-ready API appearance

### Risk Assessment
- **Technical Risk:** LOW - All changes are additive or non-breaking
- **Time Risk:** LOW - Conservative estimates with buffer
- **Demo Risk:** LOW - Easy to rollback if issues arise

### Success Criteria
- [ ] All tests pass after implementation
- [ ] OpenAPI docs show examples and status codes
- [ ] Search endpoint uses GET method
- [ ] All responses include `X-Process-Time` header
- [ ] Error responses follow standard format

---

## Implementation Order

Execute in this sequence (optimized for dependencies and risk):

1. **Task 4: Add Process Time Headers** (15 min) - Lowest risk, high demo value
2. **Task 1: Fix Search Endpoint** (20 min) - Critical for REST compliance
3. **Task 2: Add Response Status Codes** (35 min) - Enhances docs
4. **Task 3: Add Request/Response Examples** (50 min) - Most time-consuming
5. **Task 5: Standardize Error Responses** (35 min) - Optional if time runs out

**Total:** 2h 15min (with 15min buffer)

---

## Task 1: Fix Search Endpoint HTTP Method

### Overview
- **What**: Change `/exercises/search` from POST to GET with query parameters
- **Why**: Search operations should be idempotent, cacheable, and bookmarkable
- **Time Estimate**: 20 minutes
- **Priority**: 🔴 MUST-HAVE (Critical for judging)
- **Risk**: Low - isolated change

### Implementation Steps

#### Step 1.1: Update SearchExercisesRequest Schema

**File:** `app/ensenia/schemas/exercises.py`

**Action:** Make all fields optional for GET request

```python
# Add after line 235 (after SearchExercisesRequest class)

# BEFORE:
class SearchExercisesRequest(BaseModel):
    """Request schema for searching exercises."""

    grade: int | None = Field(None, ge=1, le=12, description="Grade level filter")
    subject: str | None = Field(None, max_length=100, description="Subject filter")
    topic: str | None = Field(None, max_length=200, description="Topic filter")
    exercise_type: ExerciseType | None = Field(None, description="Exercise type filter")
    difficulty_level: DifficultyLevel | None = Field(
        None, description="Difficulty level filter"
    )

# AFTER: (No changes needed - already optional)
# Just verify all fields are Optional (they are)
```

#### Step 1.2: Modify Search Endpoint

**File:** `app/ensenia/api/routes/exercises.py:193`

```python
# BEFORE:
@router.post("/search")
async def search_exercises(
    request: SearchExercisesRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    repository: Annotated[ExerciseRepository, Depends(get_exercise_repository)],
) -> ExerciseListResponse:

# AFTER:
@router.get("")  # Root /exercises endpoint for search
async def search_exercises(
    grade: int | None = Query(None, ge=1, le=12, description="Grade level filter"),
    subject: str | None = Query(None, max_length=100, description="Subject filter"),
    topic: str | None = Query(None, max_length=200, description="Topic filter"),
    exercise_type: ExerciseType | None = Query(None, description="Exercise type filter"),
    difficulty_level: DifficultyLevel | None = Query(None, description="Difficulty level filter"),
    db: Annotated[AsyncSession, Depends(get_db)],
    repository: Annotated[ExerciseRepository, Depends(get_exercise_repository)],
) -> ExerciseListResponse:
```

#### Step 1.3: Update Function Body

**File:** `app/ensenia/api/routes/exercises.py:218-222`

```python
# BEFORE:
    try:
        msg = f"Searching exercises with filters: {request.model_dump()}"
        logger.info(msg)

        exercises = await repository.search_exercises(
            grade=request.grade,
            subject=request.subject,
            topic=request.topic,
            exercise_type=request.exercise_type,
            difficulty_level=request.difficulty_level,
        )

# AFTER:
    try:
        filters = {
            "grade": grade,
            "subject": subject,
            "topic": topic,
            "exercise_type": exercise_type,
            "difficulty_level": difficulty_level,
        }
        msg = f"Searching exercises with filters: {filters}"
        logger.info(msg)

        exercises = await repository.search_exercises(
            grade=grade,
            subject=subject,
            topic=topic,
            exercise_type=exercise_type,
            difficulty_level=difficulty_level,
        )
```

#### Step 1.4: Add Query Import

**File:** `app/ensenia/api/routes/exercises.py:12`

```python
# BEFORE:
from fastapi import APIRouter, Depends, HTTPException

# AFTER:
from fastapi import APIRouter, Depends, HTTPException, Query
```

### Checklist
- [ ] Add `Query` import to exercises.py
- [ ] Change `@router.post("/search")` to `@router.get("")`
- [ ] Replace `request: SearchExercisesRequest` with individual Query parameters
- [ ] Update function body to use individual parameters instead of `request.field`
- [ ] Test search with curl/Postman
- [ ] Verify OpenAPI docs show GET method
- [ ] Update root endpoint documentation if needed

### Testing

```bash
# Test 1: Basic search (should work)
curl "http://localhost:8000/exercises?grade=5&subject=Matemáticas"

# Test 2: Search with multiple filters
curl "http://localhost:8000/exercises?grade=5&subject=Matemáticas&difficulty_level=3"

# Test 3: Search with no filters (should return all public exercises)
curl "http://localhost:8000/exercises"

# Test 4: Verify OpenAPI docs
open http://localhost:8000/docs
# Check that /exercises shows GET method with query parameters
```

### Verification
- ✅ GET request returns exercise list
- ✅ Query parameters properly validated
- ✅ Swagger UI shows GET method
- ✅ Can bookmark/share search URLs

### Rollback
```bash
git checkout app/ensenia/api/routes/exercises.py
```

---

## Task 2: Add Response Status Codes to OpenAPI

### Overview
- **What**: Add `status_code` and `responses` to all route decorators
- **Why**: Better OpenAPI docs, clearer API contract, professional appearance
- **Time Estimate**: 35 minutes
- **Priority**: 🟡 SHOULD-HAVE (High judge appeal)
- **Risk**: Very Low - documentation only

### Implementation Steps

#### Step 2.1: Exercise Generation Endpoint

**File:** `app/ensenia/api/routes/exercises.py:55`

```python
# BEFORE:
@router.post("/generate")
async def generate_exercise(

# AFTER:
@router.post(
    "/generate",
    status_code=201,  # Created
    responses={
        201: {
            "description": "Exercise successfully generated and validated",
            "model": GenerateExerciseResponse,
        },
        400: {
            "description": "Invalid request parameters or validation failed",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid grade level: must be between 1 and 12"}
                }
            },
        },
        500: {
            "description": "Exercise generation failed after max iterations",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to generate exercise meeting quality threshold"}
                }
            },
        },
    },
)
async def generate_exercise(
```

#### Step 2.2: Exercise Search Endpoint

**File:** `app/ensenia/api/routes/exercises.py:193`

```python
# AFTER Task 1 changes:
@router.get(
    "",
    status_code=200,
    responses={
        200: {
            "description": "List of exercises matching search criteria",
            "model": ExerciseListResponse,
        },
        500: {
            "description": "Search operation failed",
        },
    },
)
async def search_exercises(
```

#### Step 2.3: TTS Simple Endpoint

**File:** `app/ensenia/api/routes/tts.py`

Find the `/speak` endpoint and add:

```python
@router.get(
    "/speak",
    status_code=200,
    responses={
        200: {
            "description": "Audio file successfully generated",
            "content": {"audio/mpeg": {}},
        },
        400: {
            "description": "Missing or invalid parameters",
        },
        500: {
            "description": "TTS service error",
        },
    },
)
async def text_to_speech_simple(
```

#### Step 2.4: Chat Session Creation

**File:** `app/ensenia/api/routes/chat.py`

```python
@router.post(
    "/sessions",
    status_code=201,
    responses={
        201: {
            "description": "Chat session successfully created",
            "model": CreateSessionResponse,
        },
        400: {
            "description": "Invalid session parameters",
        },
        500: {
            "description": "Failed to create session",
        },
    },
)
async def create_session(
```

#### Step 2.5: WebSocket Endpoint

**File:** `app/ensenia/api/routes/websocket.py:27`

```python
@router.websocket(
    "/chat/{session_id}",
    # WebSockets don't use status codes, but add name for docs
    name="websocket_chat",
)
async def websocket_endpoint(
```

### Checklist

- [ ] Add status codes to `/exercises/generate` (201)
- [ ] Add status codes to `/exercises` search (200)
- [ ] Add status codes to `/tts/speak` (200)
- [ ] Add status codes to `/tts/generate` (201)
- [ ] Add status codes to `/chat/sessions` POST (201)
- [ ] Add status codes to `/chat/sessions/{id}` GET (200)
- [ ] Add status codes to `/chat/sessions/{id}/messages` GET (200)
- [ ] Review all endpoints in Swagger UI
- [ ] Verify examples show in docs

### Testing

```bash
# View OpenAPI spec
curl http://localhost:8000/openapi.json | jq '.paths'

# Check Swagger UI
open http://localhost:8000/docs
# Verify each endpoint shows:
# - Correct status code (201 for POST create, 200 for GET, etc.)
# - Response schema
# - Error responses (400, 500)
```

### Verification
- ✅ All POST create endpoints return 201
- ✅ All GET endpoints return 200
- ✅ Error responses documented (400, 500)
- ✅ Swagger UI shows status codes in green boxes

---

## Task 3: Add Request/Response Examples

### Overview
- **What**: Add `model_config` with examples to all Pydantic schemas
- **Why**: Makes Swagger UI interactive and testable
- **Time Estimate**: 50 minutes
- **Priority**: 🟡 SHOULD-HAVE (Great for demos)
- **Risk**: Very Low - schema enhancement only

### Implementation Steps

#### Step 3.1: GenerateExerciseRequest Example

**File:** `app/ensenia/schemas/exercises.py` (after GenerateExerciseRequest class)

```python
class GenerateExerciseRequest(BaseModel):
    """Request schema for exercise generation."""

    exercise_type: ExerciseType = Field(
        ..., description="Type of exercise to generate"
    )
    grade: int = Field(..., ge=1, le=12, description="Grade level (1-12)")
    subject: str = Field(
        ..., min_length=2, max_length=100, description="Subject area"
    )
    topic: str = Field(..., min_length=2, max_length=200, description="Specific topic")
    difficulty_level: DifficultyLevel = Field(
        default=DifficultyLevel.MEDIUM, description="Exercise difficulty (1-5)"
    )
    curriculum_context: str | None = Field(
        None,
        max_length=2000,
        description="Additional context from Chilean curriculum (optional)",
    )
    max_iterations: int | None = Field(
        None, ge=1, le=10, description="Max validation iterations (optional)"
    )
    quality_threshold: int | None = Field(
        None, ge=0, le=10, description="Minimum quality score (0-10, optional)"
    )

    # ADD THIS:
    model_config = {
        "json_schema_extra": {
            "example": {
                "exercise_type": "multiple_choice",
                "grade": 5,
                "subject": "Matemáticas",
                "topic": "Fracciones - Suma y Resta",
                "difficulty_level": 3,
                "curriculum_context": "Según las Bases Curriculares de 5° básico, los estudiantes deben demostrar comprensión de fracciones propias e impropias, y realizar operaciones básicas.",
                "max_iterations": 3,
                "quality_threshold": 8
            }
        }
    }
```

#### Step 3.2: MultipleChoiceContent Example

**File:** `app/ensenia/schemas/exercises.py` (after MultipleChoiceContent class)

```python
class MultipleChoiceContent(ExerciseContentBase):
    """Multiple choice exercise content."""

    options: list[str] = Field(..., min_length=2, max_length=5)
    correct_answer: int = Field(..., ge=0)
    explanation: str = Field(..., min_length=20, max_length=500)

    @field_validator("correct_answer")
    @classmethod
    def validate_correct_answer(cls, v: int, info: ValidationInfo) -> int:
        """Validate that correct_answer index is within options range."""
        if "options" in info.data and v >= len(info.data["options"]):
            msg = f"correct_answer index {v} is out of range for {len(info.data['options'])} options"
            raise ValueError(msg)
        return v

    # ADD THIS:
    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "¿Cuál es el resultado de sumar 1/4 + 1/4?",
                "learning_objective": "OA 7: Demostrar que comprenden las fracciones con denominadores 100, 12, 10, 8, 6, 5, 4, 3, 2 (5° básico)",
                "options": [
                    "1/8",
                    "2/4 (o 1/2)",
                    "2/8",
                    "1/2"
                ],
                "correct_answer": 1,
                "explanation": "Al sumar fracciones con el mismo denominador, sumamos los numeradores: 1 + 1 = 2, manteniendo el denominador 4. Por lo tanto, 1/4 + 1/4 = 2/4, que se puede simplificar a 1/2."
            }
        }
    }
```

#### Step 3.3: CreateSessionRequest Example

**File:** `app/ensenia/models/__init__.py` or create `app/ensenia/schemas/chat.py`

```python
class CreateSessionRequest(BaseModel):
    """Request schema for creating a chat session."""

    grade: int = Field(..., ge=1, le=12, description="Student grade level")
    subject: str = Field(..., min_length=2, max_length=100, description="Subject area")
    mode: ChatMode = Field(default=ChatMode.LEARN, description="Session mode")
    initial_context: str | None = Field(None, max_length=1000, description="Initial context")

    model_config = {
        "json_schema_extra": {
            "example": {
                "grade": 5,
                "subject": "Ciencias Naturales",
                "mode": "learn",
                "initial_context": "Quiero aprender sobre el ciclo del agua"
            }
        }
    }
```

#### Step 3.4: TTS Request Example

**File:** `app/ensenia/api/routes/tts.py` (find TTSRequest model)

```python
class TTSRequest(BaseModel):
    """Request schema for advanced TTS generation."""

    text: str = Field(..., min_length=1, max_length=5000)
    grade: int | None = Field(None, ge=1, le=12)
    use_cache: bool = Field(default=True)

    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "Hola, soy tu asistente educacional. Hoy vamos a aprender sobre las fracciones.",
                "grade": 5,
                "use_cache": True
            }
        }
    }
```

### Checklist

- [ ] Add example to `GenerateExerciseRequest`
- [ ] Add example to `MultipleChoiceContent`
- [ ] Add example to `TrueFalseContent`
- [ ] Add example to `ShortAnswerContent`
- [ ] Add example to `EssayContent`
- [ ] Add example to `CreateSessionRequest`
- [ ] Add example to `TTSRequest`
- [ ] Add example to `SearchExercisesRequest` (query params)
- [ ] Verify all examples in Swagger UI
- [ ] Test "Try it out" button with examples

### Testing

```bash
# Open Swagger UI
open http://localhost:8000/docs

# For each endpoint:
# 1. Click endpoint
# 2. Click "Try it out"
# 3. Verify example data is pre-filled
# 4. Click "Execute"
# 5. Verify request works
```

### Verification
- ✅ All schemas show examples in Swagger UI
- ✅ "Try it out" button pre-fills with example
- ✅ Examples use Chilean Spanish content
- ✅ Examples demonstrate real use cases

---

## Task 4: Add Process Time Headers

### Overview
- **What**: Add middleware to track and expose response time for every request
- **Why**: Shows performance awareness, useful for debugging, impresses judges
- **Time Estimate**: 15 minutes
- **Priority**: 🟢 NICE-TO-HAVE (Easy win with high demo value)
- **Risk**: Very Low - non-invasive middleware

### Implementation Steps

#### Step 4.1: Add Middleware

**File:** `app/ensenia/main.py` (add after CORS middleware, around line 60)

```python
# BEFORE (existing CORS middleware):
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ADD THIS AFTER:
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to all responses showing request duration."""
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    response.headers["X-Process-Time-Ms"] = f"{process_time * 1000:.2f}"
    return response
```

#### Step 4.2: Add Time Import

**File:** `app/ensenia/main.py` (top of file)

```python
# Add to imports section
import time
```

### Checklist

- [ ] Add `import time` to main.py imports
- [ ] Add `from fastapi import Request` if not present
- [ ] Add middleware function after CORS setup
- [ ] Test endpoint and check response headers
- [ ] Verify header appears in Swagger UI responses

### Testing

```bash
# Test any endpoint and check headers
curl -i http://localhost:8000/

# Should see in response headers:
# X-Process-Time: 0.0123
# X-Process-Time-Ms: 12.34

# Test slow endpoint (exercise generation)
curl -i -X POST http://localhost:8000/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{"exercise_type":"multiple_choice","grade":5,"subject":"Math","topic":"Fractions"}'

# Check process time is higher (should be seconds for AI generation)
```

### Verification
- ✅ All responses include `X-Process-Time` header
- ✅ All responses include `X-Process-Time-Ms` header
- ✅ Times are accurate (use `time.perf_counter`)
- ✅ Headers visible in browser DevTools

### Demo Value

**Show judges:**
```bash
# Quick endpoint
curl -s http://localhost:8000/health | grep -i "process-time"
# X-Process-Time: 0.0015

# AI generation (slow)
curl -s http://localhost:8000/exercises/generate ...
# X-Process-Time: 3.5421  (AI takes time, but we track it!)
```

---

## Task 5: Standardize Error Responses

### Overview
- **What**: Create unified error response schema and custom exception handler
- **Why**: Consistent error format, better frontend error handling, professional API
- **Time Estimate**: 35 minutes
- **Priority**: 🟡 SHOULD-HAVE (High quality, but optional if time runs out)
- **Risk**: Medium - changes error handling globally

### Implementation Steps

#### Step 5.1: Create Error Schemas

**File:** Create `app/ensenia/schemas/errors.py`

```python
"""Standardized error response schemas."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Details about an error."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    field: str | None = Field(None, description="Field that caused the error (for validation)")


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
                    "field": "grade"
                },
                "timestamp": "2025-10-25T10:30:00Z",
                "path": "/exercises/generate"
            }
        }
    }


# Common error codes
class ErrorCode:
    """Standard error codes."""

    # Validation errors (400)
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
```

#### Step 5.2: Add Custom Exception Handler

**File:** `app/ensenia/main.py` (after app creation, before routes)

```python
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.ensenia.schemas.errors import ErrorCode, ErrorDetail, ErrorResponse

# Add after app = FastAPI(...)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTPException with standardized error format."""
    # Extract error code from exception or use default
    error_code = getattr(exc, "error_code", ErrorCode.INTERNAL_ERROR)

    # For 404 errors, use specific code
    if exc.status_code == 404:
        error_code = ErrorCode.RESOURCE_NOT_FOUND

    error_response = ErrorResponse(
        error=ErrorDetail(
            code=error_code,
            message=str(exc.detail),
        ),
        path=request.url.path,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors with standardized format."""
    # Get first error for simplicity
    first_error = exc.errors()[0]
    field = ".".join(str(loc) for loc in first_error["loc"])

    error_response = ErrorResponse(
        error=ErrorDetail(
            code=ErrorCode.VALIDATION_ERROR,
            message=first_error["msg"],
            field=field,
        ),
        path=request.url.path,
    )

    return JSONResponse(
        status_code=422,
        content=error_response.model_dump(),
    )
```

#### Step 5.3: Update HTTPException Raises

**File:** `app/ensenia/api/routes/exercises.py` (example)

```python
# BEFORE:
raise HTTPException(status_code=404, detail="Exercise not found")

# AFTER:
from app.ensenia.schemas.errors import ErrorCode

exc = HTTPException(status_code=404, detail="Exercise not found")
exc.error_code = ErrorCode.EXERCISE_NOT_FOUND
raise exc

# OR create helper function:
def raise_not_found(resource: str, resource_id: int):
    """Raise standardized 404 error."""
    exc = HTTPException(
        status_code=404,
        detail=f"{resource} with id {resource_id} not found"
    )
    exc.error_code = ErrorCode.RESOURCE_NOT_FOUND
    raise exc
```

### Checklist

- [ ] Create `app/ensenia/schemas/errors.py`
- [ ] Add `ErrorDetail`, `ErrorResponse`, and `ErrorCode` classes
- [ ] Add exception handlers to main.py
- [ ] Update key HTTPException raises to include error_code
- [ ] Test validation errors (invalid grade, missing field)
- [ ] Test 404 errors (invalid session ID)
- [ ] Test 500 errors (service failures)
- [ ] Verify error format in Swagger UI

### Testing

```bash
# Test 1: Validation error (422)
curl -X POST http://localhost:8000/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{"grade": 100}'

# Expected response:
# {
#   "error": {
#     "code": "VALIDATION_ERROR",
#     "message": "ensure this value is less than or equal to 12",
#     "field": "grade"
#   },
#   "timestamp": "2025-10-25T...",
#   "path": "/exercises/generate"
# }

# Test 2: Not found error (404)
curl http://localhost:8000/chat/sessions/99999

# Expected response:
# {
#   "error": {
#     "code": "RESOURCE_NOT_FOUND",
#     "message": "Session not found"
#   },
#   "timestamp": "...",
#   "path": "/chat/sessions/99999"
# }
```

### Verification
- ✅ All errors return consistent JSON structure
- ✅ Error codes are machine-readable
- ✅ Validation errors include field name
- ✅ Timestamps are in ISO format
- ✅ Path is included in response

---

## Testing Strategy

### Pre-Implementation
```bash
# 1. Create feature branch
git checkout -b api-quick-wins

# 2. Run tests to establish baseline
uv run pytest tests/ -q

# 3. Note current test count
# Expected: 310 passed
```

### During Implementation

After each task:

```bash
# 1. Run full test suite
uv run pytest tests/ -q

# 2. If tests fail, investigate immediately
uv run pytest tests/ -v --tb=short

# 3. Test manually via Swagger UI
open http://localhost:8000/docs

# 4. Test with curl
curl -i http://localhost:8000/[endpoint]
```

### Post-Implementation

```bash
# 1. Run full test suite
uv run pytest tests/ -v

# 2. Check code formatting
uv run ruff check app/

# 3. Test all modified endpoints manually
# See individual task testing sections above

# 4. Review OpenAPI spec
curl http://localhost:8000/openapi.json | jq '.' > openapi_new.json

# 5. Verify no breaking changes
# Compare with original openapi.json (if saved)
```

### Integration Testing Scenarios

**Scenario 1: Exercise Generation Flow**
```bash
# 1. Generate exercise
curl -X POST http://localhost:8000/exercises/generate \
  -H "Content-Type: application/json" \
  -d @test_data/generate_request.json

# 2. Check response includes:
# - Status 201
# - X-Process-Time header
# - Validation history
# - Proper error format if fails

# 3. Search for generated exercise
curl "http://localhost:8000/exercises?grade=5&subject=Matemáticas"

# 4. Verify GET method works
```

**Scenario 2: Chat Session Flow**
```bash
# 1. Create session
curl -X POST http://localhost:8000/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{"grade": 5, "subject": "Ciencias", "mode": "learn"}'

# 2. Check status 201 and headers

# 3. Send message
curl -X POST http://localhost:8000/chat/sessions/1/messages \
  -H "Content-Type: application/json" \
  -d '{"content": "¿Qué es la fotosíntesis?"}'

# 4. Verify response time in headers
```

**Scenario 3: TTS Flow**
```bash
# 1. Generate speech
curl "http://localhost:8000/tts/speak?text=Hola+estudiante&grade=5" \
  --output test.mp3

# 2. Check:
# - Status 200
# - X-Process-Time header
# - File size > 0
# - Content-Type: audio/mpeg
```

### Demo Rehearsal Checklist

- [ ] All endpoints return expected status codes
- [ ] Swagger UI shows examples for all endpoints
- [ ] Error responses are consistent and helpful
- [ ] Process time headers appear in all responses
- [ ] Search endpoint uses GET method
- [ ] Can share/bookmark search URLs
- [ ] No console errors when using Swagger UI
- [ ] WebSocket connection works
- [ ] All tests pass

---

## Rollback Plan

### Per-Task Rollback

If any task fails:

```bash
# Rollback specific file
git checkout HEAD -- [file_path]

# Or rollback entire task
git reset --hard HEAD
```

### Complete Rollback

If implementation is broken before demo:

```bash
# 1. Checkout dev branch
git checkout dev

# 2. Verify tests pass
uv run pytest tests/ -q

# 3. Continue with original code for demo
```

### Git Strategy

**Recommended Approach: Single Branch with Checkpoints**

```bash
# Initial commit
git checkout -b api-quick-wins
git commit -m "chore: start API quick wins implementation"

# After each task
git add .
git commit -m "feat: [Task X] - [description]"

# Example commits:
git commit -m "feat: add process time headers middleware"
git commit -m "fix: change exercise search to GET method"
git commit -m "docs: add response status codes to OpenAPI"
git commit -m "docs: add request/response examples to schemas"
git commit -m "feat: standardize error response format"

# If all successful
git checkout dev
git merge api-quick-wins --no-ff
```

**Alternative: Branch Per Task (If High Risk)**

```bash
git checkout -b task-1-search-endpoint
# implement & test
git checkout dev
git merge task-1-search-endpoint

git checkout -b task-2-status-codes
# implement & test
# etc.
```

---

## Documentation Updates

### README.md Updates

Add to API section:

```markdown
## API Features

- **RESTful Design**: Proper HTTP methods (GET for search, POST for create)
- **Performance Monitoring**: All responses include `X-Process-Time` headers
- **Interactive Documentation**: Swagger UI with examples at `/docs`
- **Standardized Errors**: Consistent error format with error codes
- **Type-Safe**: Full Pydantic validation on all requests/responses
```

### Root Endpoint Updates

**File:** `app/ensenia/main.py` (root endpoint)

Update examples to reflect new GET search:

```python
"endpoints": {
    "exercises": {
        "generate": "POST /exercises/generate",
        "search": "GET /exercises?grade=5&subject=Math",  # UPDATED
        "get": "GET /exercises/{exercise_id}",
    },
    # ...
}
```

### CHANGELOG.md (Create if doesn't exist)

```markdown
# Changelog

## [Unreleased] - 2025-10-25

### Added
- Process time headers (`X-Process-Time`, `X-Process-Time-Ms`) to all responses
- Request/response examples to all Pydantic schemas for better Swagger UI
- Response status codes (201, 200, 400, 500) to OpenAPI documentation
- Standardized error response format with error codes

### Changed
- `/exercises/search` changed from POST to GET (RESTful compliance)
- Search now uses query parameters instead of request body

### Fixed
- Error responses now consistent across all endpoints
- HTTP status codes now properly documented in OpenAPI spec
```

---

## Demo Preparation

### Key Talking Points for Judges

#### Innovation (25%)

**Talking Point:** "Modern API Design Patterns"

```python
# Show in Swagger UI:
# 1. Self-documenting endpoints with examples
# 2. Performance transparency (X-Process-Time headers)
# 3. Type-safe validation

# Demo script:
"Our API follows modern REST principles with full OpenAPI documentation.
Notice how every endpoint includes interactive examples and performance metrics."
```

#### Technical Complexity (25%)

**Talking Point:** "Production-Ready Error Handling"

```python
# Show standardized error response:
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid grade level: must be between 1 and 12",
    "field": "grade"
  },
  "timestamp": "2025-10-25T10:30:00Z",
  "path": "/exercises/generate"
}

# Demo script:
"We've implemented enterprise-grade error handling with machine-readable error
codes, enabling robust frontend error handling and debugging."
```

#### User Experience (25%)

**Talking Point:** "Developer Experience Excellence"

```bash
# Show in browser DevTools:
curl -i http://localhost:8000/exercises/generate
# X-Process-Time: 2.3451
# X-Process-Time-Ms: 2345.10

# Demo script:
"Developers can monitor API performance in real-time with response time headers,
and our interactive Swagger docs make integration testing immediate."
```

### Code Snippets to Highlight

**1. Process Time Middleware** (shows async expertise)

```python
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response
```

**2. RESTful Search Endpoint** (shows REST mastery)

```python
@router.get("")  # Proper GET method for search
async def search_exercises(
    grade: int | None = Query(None, ge=1, le=12),
    subject: str | None = Query(None, max_length=100),
    # ... bookmarkable, cacheable URLs
```

**3. Rich Schema Examples** (shows documentation excellence)

```python
model_config = {
    "json_schema_extra": {
        "example": {
            "exercise_type": "multiple_choice",
            "grade": 5,
            "subject": "Matemáticas",
            "topic": "Fracciones",
            # ... Chilean-specific content
```

### Metrics to Showcase

Prepare these metrics before demo:

```bash
# 1. API response times
curl -s -o /dev/null -w "Time: %{time_total}s\n" http://localhost:8000/health
# Time: 0.003s (fast!)

# 2. Number of endpoints
curl -s http://localhost:8000/openapi.json | jq '.paths | length'
# 15+ endpoints

# 3. Test coverage
uv run pytest tests/ --cov=app/ensenia --cov-report=term-missing
# Show 80%+ coverage

# 4. OpenAPI spec size
curl -s http://localhost:8000/openapi.json | jq '.' | wc -l
# 1000+ lines of API documentation
```

---

## Success Metrics

### Quantitative

- [ ] All 310 tests pass
- [ ] 0 console errors in Swagger UI
- [ ] 100% of endpoints have status codes
- [ ] 100% of schemas have examples
- [ ] < 50ms overhead from process time middleware
- [ ] All error responses follow standard format

### Qualitative

- [ ] Swagger UI is intuitive and navigable
- [ ] Error messages are helpful and actionable
- [ ] Search URLs are shareable (GET method)
- [ ] API feels "production-ready"
- [ ] Judges can easily test endpoints via Swagger
- [ ] Performance visibility impresses judges

---

## Final Checklist

### Pre-Demo Verification

- [ ] Run full test suite: `uv run pytest tests/ -v`
- [ ] Check Swagger UI: `open http://localhost:8000/docs`
- [ ] Test all modified endpoints manually
- [ ] Verify error responses with invalid requests
- [ ] Check headers in browser DevTools
- [ ] Review OpenAPI spec: `curl http://localhost:8000/openapi.json | jq`
- [ ] Ensure root endpoint is updated
- [ ] Git commit all changes with clear messages
- [ ] Prepare demo talking points

### Demo Day

- [ ] Server running on reliable port (8000)
- [ ] Swagger UI loads quickly
- [ ] All example data is Chilean-specific
- [ ] Error codes are professional
- [ ] Response times are reasonable
- [ ] WebSocket connection works
- [ ] Have curl commands ready for CLI demo
- [ ] Can explain each improvement clearly

---

## Appendix A: Complete File List

Files to be modified:

1. `app/ensenia/api/routes/exercises.py` (Tasks 1, 2)
2. `app/ensenia/api/routes/tts.py` (Task 2)
3. `app/ensenia/api/routes/chat.py` (Task 2)
4. `app/ensenia/api/routes/websocket.py` (Task 2)
5. `app/ensenia/schemas/exercises.py` (Tasks 1, 3)
6. `app/ensenia/schemas/errors.py` (Task 5 - NEW FILE)
7. `app/ensenia/models/__init__.py` (Task 3)
8. `app/ensenia/main.py` (Tasks 2, 4, 5)
9. `README.md` (Documentation)
10. `CHANGELOG.md` (Documentation - NEW FILE)

---

## Appendix B: Time Breakdown

| Task | Estimate | Buffer | Total |
|------|----------|--------|-------|
| Task 4: Process Time Headers | 15 min | 5 min | 20 min |
| Task 1: Fix Search Endpoint | 20 min | 5 min | 25 min |
| Task 2: Add Status Codes | 35 min | 10 min | 45 min |
| Task 3: Add Examples | 50 min | 10 min | 60 min |
| Task 5: Standardize Errors | 35 min | 10 min | 45 min |
| **TOTAL** | **155 min** | **40 min** | **195 min** |

**Grand Total:** 3 hours 15 minutes (with generous buffer)
**Realistic Total:** 2 hours 15 minutes (if experienced)

---

## Appendix C: Quick Reference Commands

```bash
# Start server
uv run uvicorn app.ensenia.main:app --reload --port 8000

# Run tests
uv run pytest tests/ -v

# Open Swagger UI
open http://localhost:8000/docs

# Test specific endpoint
curl -i http://localhost:8000/[endpoint]

# Check OpenAPI spec
curl http://localhost:8000/openapi.json | jq '.paths'

# Check response headers
curl -I http://localhost:8000/health

# Format code
uv run ruff check app/ --fix

# Git workflow
git checkout -b api-quick-wins
git add .
git commit -m "feat: [description]"
git checkout dev
git merge api-quick-wins --no-ff
```

---

**End of Implementation Plan**

*Last Updated: 2025-10-25*
*Version: 1.0*
*Author: Claude Code - API Design Specialist*
