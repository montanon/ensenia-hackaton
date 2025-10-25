# Ensenia CloudFlare Worker - API Reference

## Base URL

- **Development**: `http://localhost:8787`
- **Production**: `https://ensenia-ai-search.<your-subdomain>.workers.dev`

## Endpoints

### 1. Health Check

Check the status of the worker and all services.

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "environment": "development",
  "services": {
    "ai": "available",
    "database": "healthy",
    "vectorize": "available",
    "cache": "available"
  }
}
```

---

### 2. Semantic Search

Perform semantic search on curriculum content using AI embeddings.

**Endpoint**: `POST /search`

**Request Body**:
```json
{
  "query": "¿Qué son las fracciones?",
  "grade": 5,
  "subject": "Matemática",
  "limit": 10
}
```

**Parameters**:
- `query` (string, required): Search query in Chilean Spanish (min 3 characters)
- `grade` (number, required): Grade level 1-12
- `subject` (string, required): Subject name (e.g., "Matemática")
- `limit` (number, optional): Maximum results to return (default: 10, max: 50)

**Response**:
```json
{
  "query": "¿Qué son las fracciones?",
  "grade": 5,
  "subject": "Matemática",
  "total_found": 6,
  "content_ids": [
    "curr-mat-5-001",
    "curr-mat-5-004",
    "curr-mat-5-002"
  ],
  "metadata": [
    {
      "id": "curr-mat-5-001",
      "score": 0.92,
      "title": "Fracciones: Conceptos Básicos",
      "oa": "OA-MAT-5-03"
    },
    {
      "id": "curr-mat-5-004",
      "score": 0.87,
      "title": "Fracciones Equivalentes",
      "oa": "OA-MAT-5-03, OA-MAT-5-05"
    }
  ],
  "cached": false,
  "search_time_ms": 456
}
```

---

### 3. Fetch Content

Retrieve full curriculum content by IDs.

**Endpoint**: `POST /fetch`

**Request Body**:
```json
{
  "content_ids": ["curr-mat-5-001", "curr-mat-5-002"]
}
```

**Parameters**:
- `content_ids` (string[], required): Array of content IDs (max 50)

**Response**:
```json
{
  "contents": [
    {
      "id": "curr-mat-5-001",
      "title": "Fracciones: Conceptos Básicos",
      "grade": 5,
      "subject": "Matemática",
      "content_text": "Las fracciones son números que representan partes de un entero...",
      "learning_objectives": ["oa-mat-5-03"],
      "ministry_standard_ref": "OA-MAT-5-03",
      "ministry_approved": true,
      "keywords": "fracciones, numerador, denominador, partes, entero",
      "difficulty_level": "basic"
    }
  ],
  "fetch_time_ms": 123
}
```

---

### 4. Generate Explanation

Generate Chilean-context educational explanations using AI.

**Endpoint**: `POST /generate`

**Request Body**:
```json
{
  "context": "Las fracciones representan partes de un todo. El numerador indica cuántas partes tomamos...",
  "query": "¿Cómo sumo fracciones con el mismo denominador?",
  "grade": 5,
  "subject": "Matemática",
  "oa_codes": ["OA-MAT-5-04"],
  "style": "explanation"
}
```

**Parameters**:
- `context` (string, required): Curriculum context (min 10 characters)
- `query` (string, required): Student's question (min 3 characters)
- `grade` (number, required): Grade level 1-12
- `subject` (string, required): Subject name
- `oa_codes` (string[], optional): Relevant learning objective codes
- `style` (string, optional): Response style - "explanation" | "summary" | "example" (default: "explanation")

**Response**:
```json
{
  "generated_text": "Para sumar fracciones con el mismo denominador, solo sumas los numeradores y mantienes el denominador igual. Por ejemplo: 2/5 + 1/5 = 3/5. Imagina que tienes 2 pedazos de pizza de 5 partes iguales...",
  "oa_codes": ["OA-MAT-5-04"],
  "model_used": "@cf/meta/llama-3.1-8b-instruct",
  "generation_time_ms": 534
}
```

---

### 5. Validate Content

Validate curriculum content compliance with Chilean Ministry standards.

**Endpoint**: `POST /validate`

**Request Body**:
```json
{
  "content": "Las fracciones son números que representan partes de un entero. Por ejemplo, 1/2 significa una de dos partes iguales...",
  "grade": 5,
  "subject": "Matemática",
  "expected_oa": ["OA-MAT-5-03"]
}
```

**Parameters**:
- `content` (string, required): Content to validate (min 10 characters)
- `grade` (number, required): Grade level 1-12
- `subject` (string, required): Subject name
- `expected_oa` (string[], optional): Expected learning objective codes

**Response**:
```json
{
  "is_valid": true,
  "score": 87,
  "validation_details": {
    "oa_alignment_score": 90,
    "grade_appropriate_score": 85,
    "chilean_terminology_score": 88,
    "learning_coverage_score": 85,
    "issues": ["No se identificaron problemas"],
    "recommendations": ["El contenido cumple con los estándares"]
  },
  "validation_time_ms": 312
}
```

**Validation Scoring**:
- Overall score is weighted average:
  - OA Alignment: 40%
  - Grade Appropriate: 30%
  - Chilean Terminology: 20%
  - Learning Coverage: 10%
- Content is valid if score >= 70/100

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "error": "Error",
  "code": "INVALID_QUERY",
  "message": "Query must be at least 3 characters",
  "details": null
}
```

**Common Error Codes**:
- `INVALID_QUERY`: Query validation failed
- `INVALID_GRADE`: Grade must be between 1 and 12
- `INVALID_SUBJECT`: Subject is required
- `INVALID_REQUEST`: Request body validation failed
- `EMBEDDING_FAILED`: AI embedding generation failed
- `SEARCH_FAILED`: Search operation failed
- `DB_QUERY_FAILED`: Database query failed
- `FETCH_FAILED`: Content fetch failed
- `GENERATION_FAILED`: AI text generation failed
- `VALIDATION_FAILED`: Validation operation failed
- `NOT_FOUND`: Endpoint not found
- `METHOD_NOT_ALLOWED`: HTTP method not allowed
- `INTERNAL_ERROR`: Internal server error

---

## Response Headers

All responses include CORS headers:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
Content-Type: application/json
```

---

## Rate Limiting

Currently no rate limiting is enforced. In production, consider implementing:
- Per-IP rate limiting
- API key authentication
- Request quotas

---

## Caching Strategy

### Search Endpoint
- **Cache Duration**: 1 hour (hot cache)
- **Cache Key**: `search:{query}:{grade}:{subject}:{limit}`
- **Cached Response**: Includes `"cached": true`

### Other Endpoints
No automatic caching. Consider implementing caching for:
- Fetch endpoint (content rarely changes)
- Validate endpoint (same validation rules)

---

## Performance Targets

- Search: ~500ms (cached: ~10ms)
- Fetch: ~100ms
- Generate: ~500ms
- Validate: ~300ms
- **Total end-to-end**: < 3 seconds

---

## Testing with cURL

### Search Example
```bash
curl -X POST http://localhost:8787/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "fracciones equivalentes",
    "grade": 5,
    "subject": "Matemática",
    "limit": 3
  }'
```

### Fetch Example
```bash
curl -X POST http://localhost:8787/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "content_ids": ["curr-mat-5-001"]
  }'
```

### Generate Example
```bash
curl -X POST http://localhost:8787/generate \
  -H "Content-Type: application/json" \
  -d '{
    "context": "Las fracciones representan partes de un todo",
    "query": "¿Qué es una fracción?",
    "grade": 5,
    "subject": "Matemática",
    "style": "explanation"
  }'
```

### Validate Example
```bash
curl -X POST http://localhost:8787/validate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Las fracciones son partes de un entero",
    "grade": 5,
    "subject": "Matemática",
    "expected_oa": ["OA-MAT-5-03"]
  }'
```

---

## Integration with Python Backend

The Python backend should use these endpoints through the `CloudFlareService` class:

```python
from ensenia.services.cloudflare import CloudFlareService

cf_service = CloudFlareService(worker_url="http://localhost:8787")

# Search
results = await cf_service.search_curriculum(
    query="¿Qué son las fracciones?",
    grade=5,
    subject="Matemática",
    limit=10
)

# Fetch
contents = await cf_service.fetch_content(content_ids=results.content_ids)

# Generate
response = await cf_service.generate_explanation(
    context=contents[0].content_text,
    query="¿Cómo sumo fracciones?",
    grade=5,
    subject="Matemática",
    oa_codes=["OA-MAT-5-04"]
)

# Validate
validation = await cf_service.validate_content(
    content=response.generated_text,
    grade=5,
    subject="Matemática",
    expected_oa=["OA-MAT-5-04"]
)
```
