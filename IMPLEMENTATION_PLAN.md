# Implementation Plan: Chilean Education AI Teaching Assistant

**Project**: Ensenia - AI Teaching Assistant for Chilean Students
**Timeline**: < 12 hours for MVP
**Architecture**: Hybrid TypeScript CloudFlare Worker + Python FastAPI
**Status**: Ready for Implementation

---

## Executive Summary

### MVP Goals
1. **Functional AI Teaching Assistant** for Chilean 5th grade Mathematics
2. **CloudFlare Deep Research** integration via REST endpoints
3. **ElevenLabs TTS** for voice interaction
4. **Abstract, extensible architecture** ready to scale to 9 subjects × 12 grades
5. **Ministry-compliant** curriculum alignment

### Timeline Breakdown
- **Phase 1**: CloudFlare Worker (TypeScript) - 2-3 hours
- **Phase 2**: Python Backend Core - 3-4 hours
- **Phase 3**: Integration & Testing - 1-2 hours
- **Phase 4**: Buffer & Demo Prep - 1-2 hours
- **Total**: 7-11 hours (< 12 hour target)

### Critical Success Factors
✅ Abstract architecture from day 1
✅ Configuration-driven subject/grade handling
✅ CloudFlare Worker as thin adapter only
✅ Python backend owns all business logic
✅ Type safety with Pydantic throughout
✅ MVP focus: one subject, quality > features

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (React + TypeScript)              │
│   - Student interface                                        │
│   - Audio player                                             │
│   - Exercise components                                      │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API (JSON)
┌────────────────────▼────────────────────────────────────────┐
│              Python FastAPI Backend (CORE LOGIC)             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  API Layer (FastAPI Routes)                            │ │
│  └────────────────────┬───────────────────────────────────┘ │
│  ┌────────────────────▼───────────────────────────────────┐ │
│  │  Orchestration Layer                                   │ │
│  │  - LearningSessionOrchestrator                         │ │
│  │  - ExerciseOrchestrator                                │ │
│  └────────────────────┬───────────────────────────────────┘ │
│  ┌────────────────────▼───────────────────────────────────┐ │
│  │  Core Abstractions (EXTENSIBILITY LAYER)               │ │
│  │  - AbstractSubjectHandler                              │ │
│  │  - AbstractCurriculumValidator                         │ │
│  │  - AbstractExerciseGenerator                           │ │
│  │  - SubjectRegistry (plugin pattern)                    │ │
│  └────────────────────┬───────────────────────────────────┘ │
│  ┌────────────────────▼───────────────────────────────────┐ │
│  │  Concrete Implementations                              │ │
│  │  - MathematicsHandler (MVP)                            │ │
│  │  - [Future: LanguageHandler, ScienceHandler, etc.]    │ │
│  └────────────────────┬───────────────────────────────────┘ │
│  ┌────────────────────▼───────────────────────────────────┐ │
│  │  Service Layer                                         │ │
│  │  - CloudFlareService (HTTP client)                     │ │
│  │  - ElevenLabsService (TTS)                             │ │
│  │  - CacheService (in-memory)                            │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP REST
┌────────────────────▼────────────────────────────────────────┐
│         TypeScript CloudFlare Worker (THIN ADAPTER)          │
│  Endpoints:                                                  │
│  - POST /search     → Vectorize + AI embeddings              │
│  - POST /fetch      → D1 database query                      │
│  - POST /generate   → Workers AI text generation             │
│  - POST /validate   → Ministry compliance check              │
└────────────────────┬────────────────────────────────────────┘
                     │
      ┌──────────────┴───────────────┐
      │                              │
┌─────▼──────────────┐   ┌──────────▼────────────┐
│ CloudFlare Services│   │ ElevenLabs TTS API    │
│ - Workers AI       │   │                        │
│ - D1 Database      │   └────────────────────────┘
│ - Vectorize        │
│ - KV Cache         │
└────────────────────┘
```

### Component Responsibilities

#### 1. TypeScript CloudFlare Worker (Adapter)
**Purpose**: Thin HTTP adapter exposing CloudFlare services as REST endpoints

**Responsibilities**:
- Receive HTTP requests from Python backend
- Call CloudFlare services (Workers AI, D1, Vectorize, KV)
- Return JSON responses
- NO business logic
- NO curriculum validation
- NO subject-specific code

**Technology**: TypeScript, Cloudflare Workers runtime

#### 2. Python FastAPI Backend (Core)
**Purpose**: All business logic, orchestration, and extensibility

**Responsibilities**:
- Student query orchestration
- Exercise generation logic
- Curriculum validation (agent-validator loop)
- Subject/grade abstraction
- Ministry compliance enforcement
- Audio generation via ElevenLabs
- Caching strategy
- Configuration management

**Technology**: Python 3.12, FastAPI, Pydantic, httpx

---

## Abstraction Strategy

### Core Abstraction Hierarchy

```python
# app/ensenia/core/abstractions/subject_handler.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pydantic import BaseModel

class CurriculumStandard(BaseModel):
    """Objetivo de Aprendizaje (OA)"""
    id: str  # e.g., "OA-MAT-5-03"
    grade: int
    subject: str
    description: str
    keywords: List[str]

class Exercise(BaseModel):
    question: str
    options: List[str] | None = None
    correct_answer: str
    explanation: str
    difficulty: str  # basic, intermediate, advanced
    learning_objectives: List[str]
    ministry_standard_ref: str

class AbstractSubjectHandler(ABC):
    """Base class for all subject handlers"""

    def __init__(self, grade: int):
        self.grade = grade
        self.subject_name = self.get_subject_name()
        self.standards = self.load_standards()

    @abstractmethod
    def get_subject_name(self) -> str:
        """Return subject identifier (e.g., 'mathematics')"""
        pass

    @abstractmethod
    def load_standards(self) -> List[CurriculumStandard]:
        """Load curriculum standards for this grade"""
        pass

    @abstractmethod
    async def generate_exercise(
        self,
        topic: str,
        difficulty: str,
        exercise_type: str,
        context: Dict[str, Any]
    ) -> Exercise:
        """Generate subject-specific exercise"""
        pass

    @abstractmethod
    async def validate_answer(
        self,
        question: str,
        student_answer: str,
        correct_answer: str
    ) -> Dict[str, Any]:
        """Validate student answer with subject-specific logic"""
        pass

    @abstractmethod
    def get_topic_keywords(self, topic: str) -> List[str]:
        """Get subject-specific keywords for topic search"""
        pass

    @abstractmethod
    async def enrich_explanation(
        self,
        raw_explanation: str,
        topic: str
    ) -> str:
        """Add subject-specific context to explanation"""
        pass


# app/ensenia/core/subjects/mathematics.py

class MathematicsHandler(AbstractSubjectHandler):
    """Concrete implementation for Mathematics"""

    def get_subject_name(self) -> str:
        return "mathematics"

    def load_standards(self) -> List[CurriculumStandard]:
        """Load from app/ensenia/data/curriculum/mathematics.json"""
        import json
        from pathlib import Path

        data_path = Path(__file__).parent.parent.parent / "data" / "curriculum"
        with open(data_path / f"mathematics_grade_{self.grade}.json") as f:
            data = json.load(f)

        return [CurriculumStandard(**std) for std in data["standards"]]

    async def generate_exercise(
        self,
        topic: str,
        difficulty: str,
        exercise_type: str,
        context: Dict[str, Any]
    ) -> Exercise:
        """Generate mathematics exercise"""
        # Use CloudFlare to generate, then validate with math-specific logic
        prompt = self._build_math_prompt(topic, difficulty, exercise_type, context)
        raw_exercise = await self.cloudflare_service.generate(prompt)

        # Validate it's a proper math exercise
        validated = self._validate_math_exercise(raw_exercise)

        return Exercise(**validated)

    def _build_math_prompt(self, topic: str, difficulty: str, exercise_type: str, context: Dict) -> str:
        """Build Chilean math-specific prompt"""
        relevant_oas = [s for s in self.standards if topic.lower() in s.keywords]

        return f"""Eres un experto en educación matemática chilena para {self.grade}° básico.

Objetivos de Aprendizaje relevantes:
{json.dumps([oa.dict() for oa in relevant_oas], indent=2, ensure_ascii=False)}

Genera un ejercicio de {difficulty} dificultad sobre "{topic}".
Tipo: {exercise_type}
Usa contexto chileno (pesos, nombres locales, situaciones familiares).

Formato JSON:
{{
    "question": "pregunta aquí",
    "options": ["opción 1", "opción 2", "opción 3", "opción 4"],
    "correct_answer": "respuesta correcta",
    "explanation": "explicación paso a paso",
    "learning_objectives": ["OA-MAT-{self.grade}-XX"]
}}"""

    # Additional math-specific methods...


# app/ensenia/core/subjects/registry.py

class SubjectRegistry:
    """Plugin registry for subject handlers"""

    _handlers: Dict[str, Type[AbstractSubjectHandler]] = {}

    @classmethod
    def register(cls, subject: str, handler_class: Type[AbstractSubjectHandler]):
        """Register a subject handler"""
        cls._handlers[subject] = handler_class

    @classmethod
    def get_handler(cls, subject: str, grade: int) -> AbstractSubjectHandler:
        """Get handler instance for subject and grade"""
        if subject not in cls._handlers:
            raise ValueError(f"Unknown subject: {subject}")

        return cls._handlers[subject](grade)

    @classmethod
    def list_subjects(cls) -> List[str]:
        """List all registered subjects"""
        return list(cls._handlers.keys())


# Register MVP subject
SubjectRegistry.register("mathematics", MathematicsHandler)

# Future: easily add more subjects
# SubjectRegistry.register("language", LanguageHandler)
# SubjectRegistry.register("science", ScienceHandler)
```

---

## Complete Directory Structure

```
ensenia-hackaton-worktrees/cloudflare/
│
├── app/
│   └── ensenia/
│       ├── __init__.py
│       ├── main.py                      # FastAPI application entry
│       ├── config.py                    # Pydantic Settings
│       │
│       ├── api/                         # API Layer
│       │   ├── __init__.py
│       │   ├── dependencies.py          # FastAPI dependencies
│       │   └── routes/
│       │       ├── __init__.py
│       │       ├── query.py             # POST /api/query
│       │       ├── exercise.py          # POST /api/exercise
│       │       ├── audio.py             # GET /api/audio/{id}
│       │       └── health.py            # GET /api/health
│       │
│       ├── core/                        # Core Business Logic
│       │   ├── __init__.py
│       │   │
│       │   ├── abstractions/            # Abstract Base Classes
│       │   │   ├── __init__.py
│       │   │   ├── subject_handler.py   # AbstractSubjectHandler
│       │   │   ├── curriculum_validator.py
│       │   │   └── exercise_generator.py
│       │   │
│       │   ├── orchestration/           # Orchestrators
│       │   │   ├── __init__.py
│       │   │   ├── learning_session.py  # LearningSessionOrchestrator
│       │   │   └── exercise_orchestrator.py
│       │   │
│       │   └── subjects/                # Subject Implementations
│       │       ├── __init__.py
│       │       ├── registry.py          # SubjectRegistry
│       │       ├── mathematics.py       # MathematicsHandler (MVP)
│       │       ├── language.py          # (Future)
│       │       ├── science.py           # (Future)
│       │       └── ...
│       │
│       ├── services/                    # External Services
│       │   ├── __init__.py
│       │   ├── cloudflare.py            # CloudFlareService
│       │   ├── elevenlabs.py            # ElevenLabsService
│       │   └── cache.py                 # CacheService (in-memory)
│       │
│       ├── models/                      # Pydantic Models
│       │   ├── __init__.py
│       │   ├── curriculum.py            # CurriculumStandard, Content
│       │   ├── exercise.py              # Exercise, ExerciseRequest
│       │   ├── audio.py                 # AudioGeneration, AudioMetadata
│       │   ├── query.py                 # QueryRequest, QueryResponse
│       │   └── api_schemas.py           # API request/response schemas
│       │
│       ├── data/                        # Static Data
│       │   ├── __init__.py
│       │   └── curriculum/
│       │       ├── mathematics_grade_5.json
│       │       ├── language_grade_5.json  # (Future)
│       │       └── standards_mapping.json
│       │
│       └── utils/                       # Utilities
│           ├── __init__.py
│           ├── validators.py
│           ├── errors.py                # Custom exceptions
│           └── logging_config.py
│
├── cloudflare-worker/                   # TypeScript Worker
│   ├── src/
│   │   ├── index.ts                     # Worker entry point
│   │   ├── routes/
│   │   │   ├── search.ts
│   │   │   ├── fetch.ts
│   │   │   ├── generate.ts
│   │   │   └── validate.ts
│   │   ├── services/
│   │   │   ├── vectorize.ts
│   │   │   ├── d1.ts
│   │   │   └── ai.ts
│   │   └── types/
│   │       └── env.ts                   # CloudFlare bindings
│   ├── wrangler.toml
│   ├── package.json
│   ├── tsconfig.json
│   └── schema.sql                       # D1 database schema
│
├── docs/
│   ├── IMPLEMENTATION_PLAN.md           # This file
│   ├── PRODUCT_SPEC.md
│   ├── architecture-summary.md
│   ├── cloudflare/
│   └── ...
│
├── tests/
│   ├── unit/
│   │   ├── test_subject_handlers.py
│   │   ├── test_orchestrators.py
│   │   └── test_services.py
│   ├── integration/
│   │   ├── test_api_routes.py
│   │   └── test_cloudflare_integration.py
│   └── e2e/
│       └── test_full_flows.py
│
├── .env.sample                          # Environment variables template
├── pyproject.toml                       # Python dependencies
├── uv.lock
├── README.md
└── .gitignore
```

---

## Data Models (Pydantic)

### Core Domain Models

```python
# app/ensenia/models/curriculum.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class CurriculumStandard(BaseModel):
    """Objetivo de Aprendizaje (OA) - Ministry standard"""
    id: str = Field(..., description="OA identifier (e.g., OA-MAT-5-03)")
    grade: int = Field(..., ge=1, le=12, description="Grade level")
    subject: str = Field(..., description="Subject identifier")
    description: str = Field(..., description="Standard description in Spanish")
    keywords: List[str] = Field(default_factory=list, description="Search keywords")
    ministry_code: str = Field(..., description="Official Ministry code")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "OA-MAT-5-03",
                "grade": 5,
                "subject": "mathematics",
                "description": "Demostrar que comprenden las fracciones con denominadores 100, 12, 10, 8, 6, 5, 4, 3, 2",
                "keywords": ["fracciones", "denominador", "numerador", "partes", "todo"],
                "ministry_code": "MA05 OA 03"
            }
        }

class CurriculumContent(BaseModel):
    """Curriculum content from CloudFlare D1"""
    id: str
    title: str
    grade: int
    subject: str
    content_text: str
    learning_objectives: List[str]
    ministry_standard_ref: str
    last_updated: datetime


# app/ensenia/models/exercise.py

class ExerciseType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    OPEN_ENDED = "open_ended"
    PROBLEM_SOLVING = "problem_solving"

class Difficulty(str, Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class Exercise(BaseModel):
    """Generated exercise"""
    question: str = Field(..., description="Question in Chilean Spanish")
    options: Optional[List[str]] = Field(None, description="Options for multiple choice")
    correct_answer: str = Field(..., description="Correct answer")
    explanation: str = Field(..., description="Detailed explanation")
    difficulty: Difficulty
    exercise_type: ExerciseType
    learning_objectives: List[str] = Field(..., description="OA IDs addressed")
    ministry_standard_ref: str = Field(..., description="Primary OA reference")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "question": "María tiene 3/4 de una pizza. ¿Qué fracción le queda si come 1/4?",
                "options": ["1/4", "2/4", "1/2", "3/4"],
                "correct_answer": "2/4",
                "explanation": "Si María tenía 3/4 y come 1/4, restamos: 3/4 - 1/4 = 2/4 (que es equivalente a 1/2)",
                "difficulty": "intermediate",
                "exercise_type": "multiple_choice",
                "learning_objectives": ["OA-MAT-5-03"],
                "ministry_standard_ref": "OA-MAT-5-03"
            }
        }


# app/ensenia/models/api_schemas.py

class QueryRequest(BaseModel):
    """Student query request"""
    query: str = Field(..., min_length=3, description="Student question in Spanish")
    grade: int = Field(..., ge=1, le=12)
    subject: str = Field(default="mathematics")
    include_audio: bool = Field(default=True, description="Generate TTS audio")

class QueryResponse(BaseModel):
    """Query response with explanation"""
    query: str
    explanation: str
    learning_objectives: List[str]
    ministry_standards: List[str]
    audio_id: Optional[str] = None
    audio_available: bool = False
    generated_at: datetime

class ExerciseRequest(BaseModel):
    """Exercise generation request"""
    topic: str = Field(..., min_length=3)
    grade: int = Field(..., ge=1, le=12)
    subject: str = Field(default="mathematics")
    difficulty: Difficulty = Field(default=Difficulty.INTERMEDIATE)
    exercise_type: ExerciseType = Field(default=ExerciseType.MULTIPLE_CHOICE)

class ExerciseResponse(BaseModel):
    """Exercise generation response"""
    exercise: Exercise
    generated_at: datetime
    validated: bool = Field(..., description="Passed ministry validation")
    validation_score: int = Field(..., ge=0, le=100)


# app/ensenia/models/audio.py

class AudioGeneration(BaseModel):
    """Audio generation task"""
    id: str
    text: str
    voice_id: str
    status: str  # pending, processing, completed, failed
    audio_url: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class AudioResponse(BaseModel):
    """Audio retrieval response"""
    id: str
    audio_url: str
    duration_seconds: Optional[float] = None
    voice_id: str
```

---

## API Contract

### FastAPI Endpoints

#### 1. Health Check

```
GET /api/health
```

**Response 200**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "cloudflare_worker": "healthy",
    "elevenlabs": "healthy"
  },
  "timestamp": "2025-10-25T12:00:00Z"
}
```

#### 2. Student Query

```
POST /api/query
```

**Request**:
```json
{
  "query": "¿Qué es una fracción?",
  "grade": 5,
  "subject": "mathematics",
  "include_audio": true
}
```

**Response 200**:
```json
{
  "query": "¿Qué es una fracción?",
  "explanation": "Una fracción representa partes de un todo. Se compone de un numerador (parte superior) que indica cuántas partes tomamos, y un denominador (parte inferior) que indica en cuántas partes dividimos el todo. Por ejemplo, en 3/4, el numerador es 3 y el denominador es 4, lo que significa 3 partes de 4 partes iguales.",
  "learning_objectives": ["OA-MAT-5-03"],
  "ministry_standards": ["MA05 OA 03"],
  "audio_id": "audio_abc123",
  "audio_available": false,
  "generated_at": "2025-10-25T12:00:00Z"
}
```

**Response 400** (validation error):
```json
{
  "detail": "Query must be at least 3 characters"
}
```

#### 3. Generate Exercise

```
POST /api/exercise
```

**Request**:
```json
{
  "topic": "fracciones",
  "grade": 5,
  "subject": "mathematics",
  "difficulty": "intermediate",
  "exercise_type": "multiple_choice"
}
```

**Response 200**:
```json
{
  "exercise": {
    "question": "Si tienes 5/8 de una torta y comes 2/8, ¿qué fracción te queda?",
    "options": ["3/8", "7/8", "3/16", "5/8"],
    "correct_answer": "3/8",
    "explanation": "Para resolver: 5/8 - 2/8 = 3/8. Cuando las fracciones tienen el mismo denominador, restamos los numeradores: 5 - 2 = 3, manteniendo el denominador 8.",
    "difficulty": "intermediate",
    "exercise_type": "multiple_choice",
    "learning_objectives": ["OA-MAT-5-03", "OA-MAT-5-04"],
    "ministry_standard_ref": "OA-MAT-5-03",
    "metadata": {}
  },
  "generated_at": "2025-10-25T12:00:00Z",
  "validated": true,
  "validation_score": 92
}
```

#### 4. Get Audio

```
GET /api/audio/{audio_id}
```

**Response 200**:
```json
{
  "id": "audio_abc123",
  "audio_url": "https://cdn.elevenlabs.io/...",
  "duration_seconds": 15.3,
  "voice_id": "es_CL_female_1"
}
```

**Response 404**:
```json
{
  "detail": "Audio not found or still processing"
}
```

---

## CloudFlare Worker Endpoints

### TypeScript Implementation

```typescript
// cloudflare-worker/src/types/env.ts

export interface Env {
  AI: any;                          // Workers AI binding
  MINISTRY_DB: D1Database;          // D1 database
  VECTORIZE_INDEX: VectorizeIndex;  // Vectorize index
  CACHE: KVNamespace;               // KV cache
  ENVIRONMENT: string;
  LOG_LEVEL: string;
}

export interface SearchRequest {
  query: string;
  grade: number;
  subject: string;
  limit?: number;
}

export interface SearchResponse {
  query: string;
  grade: number;
  subject: string;
  total_found: number;
  content_ids: string[];
  metadata: Array<{
    id: string;
    score: number;
    title: string;
  }>;
}

// ... other interfaces
```

### Endpoint 1: Search Curriculum

```typescript
// cloudflare-worker/src/routes/search.ts

export async function handleSearch(
  request: Request,
  env: Env
): Promise<Response> {
  try {
    const body: SearchRequest = await request.json();

    // Validate
    if (!body.query || body.query.length < 3) {
      return new Response(
        JSON.stringify({ error: "Query must be at least 3 characters" }),
        { status: 400 }
      );
    }

    // Generate embedding
    const embedding = await env.AI.run('@cf/baai/bge-base-en-v1.5', {
      text: body.query
    });

    // Search Vectorize
    const results = await env.VECTORIZE_INDEX.query(
      embedding.data[0],
      {
        topK: body.limit || 10,
        filter: {
          grade: body.grade,
          subject: body.subject
        }
      }
    );

    const response: SearchResponse = {
      query: body.query,
      grade: body.grade,
      subject: body.subject,
      total_found: results.count,
      content_ids: results.matches.map(m => m.id),
      metadata: results.matches.map(m => ({
        id: m.id,
        score: m.score,
        title: m.metadata.title as string
      }))
    };

    return new Response(JSON.stringify(response), {
      headers: { 'Content-Type': 'application/json' }
    });

  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500 }
    );
  }
}
```

### Endpoint 2: Fetch Content

```typescript
// cloudflare-worker/src/routes/fetch.ts

export async function handleFetch(
  request: Request,
  env: Env
): Promise<Response> {
  const body: { content_ids: string[] } = await request.json();

  const contents = [];

  for (const id of body.content_ids) {
    const result = await env.MINISTRY_DB.prepare(
      `SELECT * FROM curriculum_content WHERE id = ? AND ministry_approved = 1`
    ).bind(id).first();

    if (result) {
      contents.push({
        id: result.id,
        title: result.title,
        grade: result.grade,
        subject: result.subject,
        content: result.content_text,
        objectives: JSON.parse(result.learning_objectives),
        ministry_standard: result.ministry_standard_ref,
        last_updated: result.updated_at
      });
    }
  }

  return new Response(
    JSON.stringify({
      retrieved: contents.length,
      contents
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );
}
```

### Endpoint 3: Generate with AI

```typescript
// cloudflare-worker/src/routes/generate.ts

export async function handleGenerate(
  request: Request,
  env: Env
): Promise<Response> {
  const body: {
    prompt: string;
    max_tokens?: number;
    temperature?: number;
  } = await request.json();

  const response = await env.AI.run('@cf/meta/llama-3.1-8b-instruct', {
    prompt: body.prompt,
    max_tokens: body.max_tokens || 1000,
    temperature: body.temperature || 0.7
  });

  return new Response(
    JSON.stringify({
      response: response.response,
      generated_at: new Date().toISOString()
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );
}
```

### Endpoint 4: Validate Compliance

```typescript
// cloudflare-worker/src/routes/validate.ts

export async function handleValidate(
  request: Request,
  env: Env
): Promise<Response> {
  const body: {
    content: string;
    grade: number;
    subject: string;
  } = await request.json();

  // Get ministry standards
  const standards = await env.MINISTRY_DB.prepare(
    `SELECT * FROM ministry_standards WHERE grade = ? AND subject = ?`
  ).bind(body.grade, body.subject).all();

  // Build validation prompt
  const prompt = `Valida si este contenido cumple con los estándares del Ministerio de Educación chileno.

Contenido: ${body.content}

Estándares oficiales para ${body.grade}° básico ${body.subject}:
${JSON.stringify(standards.results, null, 2)}

Responde en JSON con:
{
  "is_compliant": boolean,
  "alignment_score": 0-100,
  "matched_standards": ["OA-XXX-X-XX"],
  "issues": ["problema 1", "problema 2"],
  "recommendations": ["sugerencia 1", "sugerencia 2"]
}`;

  const response = await env.AI.run('@cf/meta/llama-3.1-8b-instruct', {
    prompt,
    max_tokens: 800,
    temperature: 0.3
  });

  return new Response(response.response, {
    headers: { 'Content-Type': 'application/json' }
  });
}
```

### Main Router

```typescript
// cloudflare-worker/src/index.ts

import { handleSearch } from './routes/search';
import { handleFetch } from './routes/fetch';
import { handleGenerate } from './routes/generate';
import { handleValidate } from './routes/validate';
import { Env } from './types/env';

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Route to handlers
    let response: Response;

    switch (url.pathname) {
      case '/search':
        response = await handleSearch(request, env);
        break;
      case '/fetch':
        response = await handleFetch(request, env);
        break;
      case '/generate':
        response = await handleGenerate(request, env);
        break;
      case '/validate':
        response = await handleValidate(request, env);
        break;
      default:
        response = new Response('Not Found', { status: 404 });
    }

    // Add CORS headers to response
    Object.entries(corsHeaders).forEach(([key, value]) => {
      response.headers.set(key, value);
    });

    return response;
  }
};
```

---

## Configuration Strategy

### Environment Variables

```bash
# .env.sample

# === CloudFlare Worker ===
CLOUDFLARE_WORKER_URL=https://your-worker.your-subdomain.workers.dev

# === ElevenLabs ===
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=es_CL_female_1  # Chilean Spanish voice

# === Application ===
ENVIRONMENT=development  # development | production
LOG_LEVEL=INFO          # DEBUG | INFO | WARNING | ERROR
DEBUG=true

# === Caching ===
CACHE_TTL_SEARCH=3600           # 1 hour
CACHE_TTL_CONTENT=86400         # 24 hours
CACHE_TTL_AUDIO=604800          # 7 days

# === MVP Settings ===
MVP_SUBJECT=mathematics
MVP_GRADE=5

# === Valid Subjects (comma-separated) ===
VALID_SUBJECTS=mathematics,language,science,history,english,arts,music,physical_education,technology
```

### Pydantic Settings

```python
# app/ensenia/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # CloudFlare
    cloudflare_worker_url: str

    # ElevenLabs
    elevenlabs_api_key: str
    elevenlabs_voice_id: str = "es_CL_female_1"

    # Application
    environment: str = "development"
    log_level: str = "INFO"
    debug: bool = True

    # Caching
    cache_ttl_search: int = 3600
    cache_ttl_content: int = 86400
    cache_ttl_audio: int = 604800

    # MVP
    mvp_subject: str = "mathematics"
    mvp_grade: int = 5

    # Subjects
    valid_subjects: str = "mathematics,language,science,history,english,arts,music,physical_education,technology"

    @property
    def subjects_list(self) -> List[str]:
        """Parse valid subjects"""
        return [s.strip() for s in self.valid_subjects.split(",")]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
```

---

## Extension Patterns

### Adding a New Subject (Step-by-Step)

#### Step 1: Create Subject Handler

```python
# app/ensenia/core/subjects/language.py

from app.ensenia.core.abstractions.subject_handler import AbstractSubjectHandler
from app.ensenia.models.curriculum import CurriculumStandard, Exercise
from typing import List, Dict, Any

class LanguageHandler(AbstractSubjectHandler):
    """Handler for Lenguaje y Comunicación"""

    def get_subject_name(self) -> str:
        return "language"

    def load_standards(self) -> List[CurriculumStandard]:
        import json
        from pathlib import Path

        data_path = Path(__file__).parent.parent.parent / "data" / "curriculum"
        with open(data_path / f"language_grade_{self.grade}.json") as f:
            data = json.load(f)

        return [CurriculumStandard(**std) for std in data["standards"]]

    async def generate_exercise(
        self,
        topic: str,
        difficulty: str,
        exercise_type: str,
        context: Dict[str, Any]
    ) -> Exercise:
        """Generate language exercise (e.g., reading comprehension)"""
        prompt = self._build_language_prompt(topic, difficulty, exercise_type, context)
        # ... implementation

    async def validate_answer(
        self,
        question: str,
        student_answer: str,
        correct_answer: str
    ) -> Dict[str, Any]:
        """Language-specific answer validation (e.g., accept synonyms)"""
        # ... implementation

    def get_topic_keywords(self, topic: str) -> List[str]:
        """Language-specific keywords"""
        keywords_map = {
            "verbos": ["verbo", "conjugación", "tiempo verbal", "modo"],
            "comprensión": ["lectura", "comprensión lectora", "texto"],
            # ... more mappings
        }
        return keywords_map.get(topic.lower(), [topic])

    async def enrich_explanation(
        self,
        raw_explanation: str,
        topic: str
    ) -> str:
        """Add language-specific examples"""
        # Add Chilean literature references, local authors, etc.
        # ... implementation
```

#### Step 2: Define Curriculum Standards

```json
// app/ensenia/data/curriculum/language_grade_5.json

{
  "subject": "language",
  "grade": 5,
  "standards": [
    {
      "id": "OA-LEN-5-01",
      "grade": 5,
      "subject": "language",
      "description": "Leer de manera fluida textos variados apropiados a su edad",
      "keywords": ["lectura", "fluidez", "comprensión", "textos"],
      "ministry_code": "LE05 OA 01"
    },
    {
      "id": "OA-LEN-5-02",
      "grade": 5,
      "subject": "language",
      "description": "Comprender textos aplicando estrategias de comprensión lectora",
      "keywords": ["comprensión", "estrategias", "lectura", "análisis"],
      "ministry_code": "LE05 OA 02"
    }
  ]
}
```

#### Step 3: Register in Subject Registry

```python
# app/ensenia/core/subjects/__init__.py

from app.ensenia.core.subjects.registry import SubjectRegistry
from app.ensenia.core.subjects.mathematics import MathematicsHandler
from app.ensenia.core.subjects.language import LanguageHandler

# Register all subjects
SubjectRegistry.register("mathematics", MathematicsHandler)
SubjectRegistry.register("language", LanguageHandler)

# Future subjects
# SubjectRegistry.register("science", ScienceHandler)
# SubjectRegistry.register("history", HistoryHandler)
```

#### Step 4: Add Tests

```python
# tests/unit/test_language_handler.py

import pytest
from app.ensenia.core.subjects.language import LanguageHandler

@pytest.mark.asyncio
async def test_language_handler_initialization():
    handler = LanguageHandler(grade=5)
    assert handler.get_subject_name() == "language"
    assert len(handler.standards) > 0

@pytest.mark.asyncio
async def test_generate_language_exercise():
    handler = LanguageHandler(grade=5)
    exercise = await handler.generate_exercise(
        topic="verbos",
        difficulty="intermediate",
        exercise_type="multiple_choice",
        context={}
    )
    assert exercise.question
    assert len(exercise.options) == 4
    assert exercise.learning_objectives
```

#### Step 5: Update Configuration

```bash
# .env (add to VALID_SUBJECTS if not already there)
VALID_SUBJECTS=mathematics,language,science,history,english,arts,music,physical_education,technology
```

**That's it!** The new subject is now fully integrated and can be used via:

```python
POST /api/query
{
  "query": "¿Qué es un verbo?",
  "grade": 5,
  "subject": "language"
}
```

---

## Implementation Phases

### Phase 1: CloudFlare Worker (TypeScript) - 2-3 hours

#### Tasks

1. **Project Setup (30 min)**
   ```bash
   mkdir cloudflare-worker
   cd cloudflare-worker
   npm init -y
   npm install -D wrangler typescript @cloudflare/workers-types
   npx wrangler init
   ```

2. **Create D1 Database (30 min)**
   ```bash
   # Create database
   npx wrangler d1 create chilean_ministry_curriculum

   # Copy database_id to wrangler.toml
   # Create schema.sql
   # Apply schema
   npx wrangler d1 execute chilean_ministry_curriculum --file=schema.sql

   # Insert sample data for 5th grade mathematics
   ```

3. **Create Vectorize Index (15 min)**
   ```bash
   npx wrangler vectorize create curriculum_embeddings \
     --dimensions=768 \
     --metric=cosine
   ```

4. **Create KV Namespace (15 min)**
   ```bash
   npx wrangler kv:namespace create CACHE
   ```

5. **Implement Routes (60 min)**
   - `/search` endpoint with Vectorize
   - `/fetch` endpoint with D1
   - `/generate` endpoint with Workers AI
   - `/validate` endpoint

6. **Deploy and Test (30 min)**
   ```bash
   npx wrangler deploy

   # Test each endpoint
   curl -X POST https://your-worker.workers.dev/search \
     -H "Content-Type: application/json" \
     -d '{"query":"fracciones","grade":5,"subject":"mathematics"}'
   ```

#### Deliverable
✅ CloudFlare Worker deployed and responding to all 4 endpoints

---

### Phase 2: Python Backend Core - 3-4 hours

#### Tasks

1. **Project Setup (30 min)**
   ```bash
   cd app/ensenia

   # Update pyproject.toml dependencies
   uv add fastapi uvicorn httpx pydantic pydantic-settings elevenlabs

   # Create directory structure
   mkdir -p api/routes core/{abstractions,orchestration,subjects} services models data/curriculum utils
   ```

2. **Configuration and Models (30 min)**
   - Implement `config.py` with Pydantic Settings
   - Create all Pydantic models in `models/`
   - Update `.env.sample`

3. **Abstract Layer (45 min)**
   - Implement `AbstractSubjectHandler` in `core/abstractions/subject_handler.py`
   - Implement `SubjectRegistry` in `core/subjects/registry.py`
   - Create base error classes in `utils/errors.py`

4. **Services Layer (60 min)**
   - **CloudFlareService** (`services/cloudflare.py`):
     ```python
     class CloudFlareService:
         def __init__(self, worker_url: str):
             self.worker_url = worker_url
             self.client = httpx.AsyncClient(timeout=30.0)

         async def search_curriculum(self, query: str, grade: int, subject: str, limit: int = 10):
             # HTTP POST to /search

         async def fetch_content(self, content_ids: List[str]):
             # HTTP POST to /fetch

         async def generate(self, prompt: str, max_tokens: int = 1000):
             # HTTP POST to /generate

         async def validate_compliance(self, content: str, grade: int, subject: str):
             # HTTP POST to /validate
     ```

   - **ElevenLabsService** (`services/elevenlabs.py`):
     ```python
     from elevenlabs import generate, save

     class ElevenLabsService:
         def __init__(self, api_key: str, voice_id: str):
             self.api_key = api_key
             self.voice_id = voice_id

         async def generate_audio(self, text: str) -> str:
             # Generate audio, return ID

         async def get_audio(self, audio_id: str) -> Optional[str]:
             # Retrieve audio URL
     ```

   - **CacheService** (`services/cache.py`):
     ```python
     class CacheService:
         def __init__(self):
             self._cache: Dict[str, Tuple[Any, float]] = {}

         async def get(self, key: str) -> Optional[Any]:
             # Get from in-memory cache with TTL check

         async def set(self, key: str, value: Any, ttl: int):
             # Set in cache with expiration
     ```

5. **Mathematics Handler (45 min)**
   - Implement `MathematicsHandler` in `core/subjects/mathematics.py`
   - Create `data/curriculum/mathematics_grade_5.json` with 5-10 OAs
   - Register in `SubjectRegistry`

6. **Orchestration Layer (45 min)**
   - **LearningSessionOrchestrator**:
     ```python
     class LearningSessionOrchestrator:
         async def handle_query(
             self,
             query: str,
             grade: int,
             subject: str,
             include_audio: bool
         ) -> QueryResponse:
             # 1. Search curriculum (CloudFlare)
             # 2. Fetch relevant content
             # 3. Generate explanation with subject handler
             # 4. Validate with ministry standards
             # 5. Generate audio (background task)
             # 6. Return response
     ```

   - **ExerciseOrchestrator**:
     ```python
     class ExerciseOrchestrator:
         async def generate_exercise(
             self,
             topic: str,
             grade: int,
             subject: str,
             difficulty: str,
             exercise_type: str
         ) -> ExerciseResponse:
             # 1. Get subject handler
             # 2. Search curriculum for context
             # 3. Generate exercise
             # 4. Validate with agent-validator loop
             # 5. Return validated exercise
     ```

7. **API Routes (30 min)**
   - Implement all routes in `api/routes/`
   - Set up FastAPI app in `main.py`
   - Add CORS middleware
   - Add error handlers

8. **FastAPI App Setup (15 min)**
   ```python
   # app/ensenia/main.py

   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware
   from app.ensenia.api.routes import query, exercise, audio, health
   from app.ensenia.config import get_settings

   app = FastAPI(
       title="Ensenia - Chilean Education AI Assistant",
       version="1.0.0"
   )

   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )

   app.include_router(health.router, prefix="/api", tags=["health"])
   app.include_router(query.router, prefix="/api", tags=["query"])
   app.include_router(exercise.router, prefix="/api", tags=["exercise"])
   app.include_router(audio.router, prefix="/api", tags=["audio"])
   ```

#### Deliverable
✅ Python backend running locally with all endpoints functional

---

### Phase 3: Integration & Testing - 1-2 hours

#### Tasks

1. **End-to-End Testing (45 min)**
   - Test full query flow (Python → CloudFlare → Python → ElevenLabs)
   - Test exercise generation with validation loop
   - Test audio generation and retrieval
   - Fix any integration issues

2. **Sample Data Creation (30 min)**
   - Create comprehensive `mathematics_grade_5.json` with 10 OAs
   - Populate D1 database with sample curriculum content
   - Create sample embeddings in Vectorize

3. **Configuration Validation (15 min)**
   - Verify all environment variables
   - Test configuration loading
   - Ensure CORS working for frontend

4. **Performance Testing (15 min)**
   - Verify response times < 3 seconds
   - Test caching effectiveness
   - Check concurrent request handling

#### Deliverable
✅ Fully integrated system with end-to-end flows working

---

### Phase 4: Buffer & Demo Prep - 1-2 hours

#### Tasks

1. **Bug Fixes (30-60 min)**
   - Address any issues from integration testing
   - Improve error messages
   - Handle edge cases

2. **Demo Scenarios (30 min)**
   - Prepare 3 tested demo flows:
     1. "¿Qué es una fracción?" → Explanation with audio
     2. Generate intermediate exercise on fracciones
     3. Voice interaction demonstration
   - Pre-cache demo queries for reliability

3. **Fallback Mechanisms (15 min)**
   - Implement demo mode with hardcoded responses
   - Graceful degradation if services fail
   - Error recovery strategies

4. **Documentation (15 min)**
   - Update README with setup instructions
   - Document API endpoints
   - Create deployment guide

#### Deliverable
✅ Demo-ready application with tested scenarios and fallbacks

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/test_subject_handlers.py

import pytest
from app.ensenia.core.subjects.mathematics import MathematicsHandler

class TestMathematicsHandler:

    @pytest.fixture
    def handler(self):
        return MathematicsHandler(grade=5)

    def test_initialization(self, handler):
        assert handler.get_subject_name() == "mathematics"
        assert handler.grade == 5
        assert len(handler.standards) > 0

    def test_load_standards(self, handler):
        standards = handler.load_standards()
        assert all(s.grade == 5 for s in standards)
        assert all(s.subject == "mathematics" for s in standards)

    @pytest.mark.asyncio
    async def test_generate_exercise(self, handler, mock_cloudflare):
        exercise = await handler.generate_exercise(
            topic="fracciones",
            difficulty="intermediate",
            exercise_type="multiple_choice",
            context={}
        )
        assert exercise.question
        assert len(exercise.options) == 4
        assert exercise.correct_answer in exercise.options


# tests/unit/test_services.py

@pytest.mark.asyncio
async def test_cloudflare_service_search():
    service = CloudFlareService("https://test.workers.dev")

    # Mock httpx response
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value.json.return_value = {
            "query": "fracciones",
            "content_ids": ["curr-mat-5-001"]
        }

        result = await service.search_curriculum("fracciones", 5, "mathematics")
        assert "content_ids" in result
```

### Integration Tests

```python
# tests/integration/test_api_routes.py

from fastapi.testclient import TestClient
from app.ensenia.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_query_endpoint():
    response = client.post("/api/query", json={
        "query": "¿Qué es una fracción?",
        "grade": 5,
        "subject": "mathematics",
        "include_audio": False
    })
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert "learning_objectives" in data

def test_exercise_endpoint():
    response = client.post("/api/exercise", json={
        "topic": "fracciones",
        "grade": 5,
        "subject": "mathematics",
        "difficulty": "intermediate",
        "exercise_type": "multiple_choice"
    })
    assert response.status_code == 200
    data = response.json()
    assert "exercise" in data
    assert data["validated"] == True
```

### End-to-End Tests

```python
# tests/e2e/test_full_flows.py

@pytest.mark.asyncio
async def test_complete_learning_flow():
    """Test full flow: query → explanation → audio"""

    # 1. Submit query
    response = client.post("/api/query", json={
        "query": "¿Cómo sumo fracciones con diferente denominador?",
        "grade": 5,
        "subject": "mathematics",
        "include_audio": True
    })
    assert response.status_code == 200
    data = response.json()
    audio_id = data["audio_id"]

    # 2. Wait for audio processing
    await asyncio.sleep(5)

    # 3. Retrieve audio
    audio_response = client.get(f"/api/audio/{audio_id}")
    assert audio_response.status_code == 200
    assert "audio_url" in audio_response.json()

@pytest.mark.asyncio
async def test_complete_exercise_flow():
    """Test full flow: topic → generate → validate"""

    response = client.post("/api/exercise", json={
        "topic": "suma de fracciones",
        "grade": 5,
        "subject": "mathematics",
        "difficulty": "intermediate",
        "exercise_type": "multiple_choice"
    })
    assert response.status_code == 200
    data = response.json()

    # Verify exercise structure
    exercise = data["exercise"]
    assert exercise["question"]
    assert len(exercise["options"]) == 4
    assert exercise["correct_answer"] in exercise["options"]
    assert exercise["explanation"]
    assert len(exercise["learning_objectives"]) > 0

    # Verify validation
    assert data["validated"] == True
    assert data["validation_score"] >= 70
```

---

## Deployment Checklist

### CloudFlare Worker

- [ ] D1 database created and populated
- [ ] Vectorize index created with embeddings
- [ ] KV namespace created
- [ ] `wrangler.toml` configured with all bindings
- [ ] Worker deployed: `npx wrangler deploy`
- [ ] All 4 endpoints tested via curl/Postman
- [ ] CORS headers configured
- [ ] Error handling tested

### Python Backend

- [ ] Dependencies installed: `uv sync`
- [ ] `.env` file created with all variables
- [ ] CloudFlare Worker URL configured
- [ ] ElevenLabs API key set
- [ ] Curriculum data files created
- [ ] Subject registry populated
- [ ] All routes tested locally
- [ ] Unit tests passing
- [ ] Integration tests passing

### Integration

- [ ] Python can call CloudFlare Worker successfully
- [ ] End-to-end query flow working
- [ ] Exercise generation with validation working
- [ ] Audio generation and retrieval working
- [ ] Response times < 3 seconds
- [ ] Caching working correctly
- [ ] Error handling graceful

### Demo Preparation

- [ ] 3 demo scenarios tested and working
- [ ] Demo mode implemented as fallback
- [ ] Pre-cached responses for demos
- [ ] Presentation slides prepared
- [ ] Demo script practiced
- [ ] Backup plan in case of API failures

---

## Risk Mitigation

### Critical Dependencies

| Dependency | Risk | Mitigation |
|-----------|------|------------|
| CloudFlare Workers AI | API limits or outages | Demo mode with cached responses |
| ElevenLabs TTS | API failures | Graceful degradation to text-only mode |
| D1 Database | Query failures | In-memory fallback data |
| Vectorize | Search failures | Simple keyword search fallback |

### Fallback Strategies

```python
# app/ensenia/utils/fallbacks.py

class FallbackManager:
    """Manage fallback strategies for external services"""

    @staticmethod
    async def get_explanation_with_fallback(
        query: str,
        cloudflare_service: CloudFlareService
    ) -> str:
        """Try CloudFlare, fall back to template"""
        try:
            result = await cloudflare_service.generate(query)
            return result
        except Exception:
            # Fallback to template-based response
            return FallbackManager._get_template_explanation(query)

    @staticmethod
    def _get_template_explanation(query: str) -> str:
        """Template-based explanation for demo mode"""
        templates = {
            "fracción": "Una fracción representa partes de un todo...",
            "suma": "Para sumar fracciones...",
            # More templates
        }
        # Find best matching template
        # ...
```

### Demo Mode

```python
# app/ensenia/config.py

class Settings(BaseSettings):
    # ... other settings ...

    demo_mode: bool = False  # Enable for guaranteed demo

    # Pre-cached demo responses
    demo_queries: Dict[str, str] = {
        "¿Qué es una fracción?": "demo_response_fracciones.json",
        "¿Cómo sumo fracciones?": "demo_response_suma.json"
    }
```

---

## Critical Path Items for MVP

### Must Have (MVP Blockers)
1. ✅ CloudFlare Worker with 4 working endpoints
2. ✅ Python backend with abstract architecture
3. ✅ MathematicsHandler for 5th grade
4. ✅ Query endpoint working end-to-end
5. ✅ Exercise generation with validation
6. ✅ ElevenLabs TTS integration
7. ✅ 5-10 Objetivos de Aprendizaje defined
8. ✅ Sample D1 database populated
9. ✅ 3 demo scenarios tested

### Should Have (Important)
- Comprehensive error handling
- Caching for performance
- Response time < 3 seconds
- Chilean Spanish throughout
- SIMCE-style exercise format
- Ministry compliance validation
- Unit and integration tests

### Could Have (Nice to Have)
- Multiple exercise types beyond multiple choice
- Advanced subject handler features
- Detailed analytics
- Admin dashboard
- More sophisticated caching

### Won't Have (Out of Scope for MVP)
- User authentication
- Student progress tracking
- Multiple subjects (only Mathematics)
- Multiple grades (only 5th grade)
- Teacher dashboard
- Mobile app
- Persistent database for student data

---

## Success Metrics

### Technical
- [ ] All API endpoints respond < 3 seconds
- [ ] Zero crashes during demo
- [ ] Smooth audio playback
- [ ] 100% Ministry OA mapping for 5th grade math
- [ ] Test coverage > 70%

### Functional
- [ ] Can answer Chilean curriculum questions
- [ ] Generates valid SIMCE-style exercises
- [ ] Produces clear Chilean Spanish explanations
- [ ] Audio is understandable and natural

### Extensibility
- [ ] Can add new subject in < 2 hours
- [ ] Can add new grade level in < 1 hour
- [ ] Abstract architecture validated
- [ ] Configuration-driven approach working

### Demo
- [ ] 3 flawless demo scenarios
- [ ] Impressive to judges
- [ ] Addresses all 4 judging criteria
- [ ] Differentiated from competitors

---

## Next Steps

1. **Immediate**: Review and approve this implementation plan
2. **Phase 1**: Start CloudFlare Worker implementation (2-3 hours)
3. **Phase 2**: Build Python backend core (3-4 hours)
4. **Phase 3**: Integration and testing (1-2 hours)
5. **Phase 4**: Demo preparation and buffer (1-2 hours)

**Total estimated time**: 7-11 hours (within < 12 hour constraint)

---

**Document Status**: Ready for Implementation
**Last Updated**: 2025-10-25
**Version**: 1.0.0
