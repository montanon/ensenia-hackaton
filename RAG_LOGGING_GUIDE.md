# RAG Logging Guide - Validate Content Analysis

## Overview

Comprehensive logging has been added to track RAG (Retrieval-Augmented Generation) operations and content analysis during the "Analizando el contenido..." phase. This allows you to validate that:

1. **Semantic search is working** - Curriculum content is being found
2. **Content retrieval is working** - Full documents are being fetched
3. **Context building is working** - Research context is being assembled
4. **Performance is acceptable** - Operations complete in reasonable time

## What Was Added

### Enhanced Logging in ResearchService

All RAG operations now have detailed logging with the `[RAG]` prefix for easy filtering.

### Enhanced Logging in ContentGenerationService

All content analysis operations now have detailed logging with the `[Content]` prefix for easy filtering.

#### 1. Semantic Search (`search_curriculum`)
Logs when searching curriculum content using vector embeddings:
- Search query, grade, subject, and limit
- Time taken for search request
- Number of results found
- Top result IDs and similarity scores
- Warnings when no results found

#### 2. Content Fetching (`fetch_content`)
Logs when retrieving full content by IDs:
- Number of documents being fetched
- Time taken for fetch request
- Details of each fetched document (title, grade, subject, length)
- Learning objectives for each document

#### 3. Context Building (`get_context`)
Logs the 3-step process of building research context:
- Step 1: Searching curriculum
- Step 2: Fetching top documents
- Step 3: Building formatted context
- Total time, document count, character count
- Preview of built context

#### 4. Session Context Update (`update_session_context`)
Logs when updating a session with research context:
- Session details (ID, grade, subject)
- Total time for context retrieval
- Context length and summary
- Success/failure status

### Content Generation Logging

#### 5. Learning Content Generation (`generate_learning_content`)
Logs when generating structured learning materials from RAG context:
- Subject, grade, and topic
- Curriculum context size
- OpenAI API call with model and timing
- Token usage
- Generated content structure (title, sections, objectives)
- Success/failure status

#### 6. Study Guide Generation (`generate_study_guide`)
Logs when generating study guides from RAG context:
- Subject, grade, and topic
- Curriculum context size
- OpenAI API call timing
- Token usage
- Generated guide structure (concepts, questions)
- Success/failure status

### Exercise Generation Logging

#### 7. Exercise Pool Generation (`generate_initial_pool`)
Logs when generating initial exercise pool for a session:
- Pool size and parameters (grade, subject, topic)
- Exercise mix (types and difficulties)
- Individual task progress (X/Y)
- Parallel generation timing
- Success/failure for each exercise with details
- Total generation statistics (success rate, failures, timing)
- Warnings when exercises fail

#### 8. Individual Exercise Generation (`_generate_and_link_exercise`)
Logs each exercise generation and database save:
- Exercise type and difficulty
- LangGraph workflow timing and iterations
- Validation score
- Database save and linking
- Total time per exercise

#### 9. LangGraph Workflow (`generate_exercise`)
Logs the core exercise generation using LangGraph:
- Exercise parameters and configuration
- LangGraph workflow invocation
- Workflow completion timing
- Iteration count and validation scores
- Exercise content preview
- Errors with full traceback

## Log Output Examples

### Successful RAG + Content Generation Flow

```log
INFO - [Background] Starting exercise pool generation for session 1: grade=5, subject=Matemáticas, topic=Fracciones
INFO - [RAG] Updating session 1 with research context for topic: 'Fracciones'
INFO - [RAG] Session loaded: Grade=5, Subject='Matemáticas'
INFO - [RAG] Building context for topic: 'Fracciones' (Grade: 5, Subject: Matemáticas)
INFO - [RAG] Step 1/3: Searching curriculum...
INFO - [RAG] Starting semantic search - Query: 'Fracciones', Grade: 5, Subject: 'Matemáticas', Limit: 5
INFO - [RAG] Search request completed in 0.45s
INFO - [RAG] Search found 5 results (search_time: 123.45ms)
INFO - [RAG] Top results: content_001, content_002, content_003
INFO - [RAG] Top scores: 0.892, 0.856, 0.823
INFO - [RAG] Step 2/3: Fetching top 3 documents...
INFO - [RAG] Fetching 3 content documents: content_001, content_002, content_003
INFO - [RAG] Fetch request completed in 0.23s
INFO - [RAG] Retrieved 3 documents (fetch_time: 87.32ms)
INFO - [RAG] Document 1: 'Introducción a las Fracciones' (Grade: 5, Subject: Matemáticas, Length: 2847 chars)
INFO - [RAG] Document 2: 'Operaciones con Fracciones' (Grade: 5, Subject: Matemáticas, Length: 3156 chars)
INFO - [RAG] Document 3: 'Fracciones Equivalentes' (Grade: 5, Subject: Matemáticas, Length: 2234 chars)
INFO - [RAG] Step 3/3: Building formatted context...
INFO - [RAG] Context built successfully in 0.72s - 3 documents, 8237 total chars, 1247 context length
INFO - [RAG] ✓ Successfully updated session 1 with research context (0.72s total, 1247 chars)
INFO - [RAG] Context summary: Topic: Fracciones
INFO - [Content] Generating learning content - Subject: Matemáticas, Grade: 5, Topic: Fracciones
INFO - [Content] Using curriculum context: 1247 chars
INFO - [Content] Calling OpenAI API with model gpt-4o-mini (prompt: 3456 chars)...
INFO - [Content] OpenAI API call completed in 2.34s
INFO - [Content] Received response: 2847 chars, 892 tokens used
INFO - [Content] ✓ Successfully generated learning content - Title: 'Introducción a las Fracciones', 4 sections, 3 learning objectives (2.34s total)
INFO - [Content] Generating study guide - Subject: Matemáticas, Grade: 5, Topic: Fracciones
INFO - [Content] Using curriculum context: 1247 chars
INFO - [Content] Calling OpenAI API for study guide with model gpt-4o-mini...
INFO - [Content] OpenAI API call completed in 1.89s
INFO - [Content] Received study guide response: 2156 chars, 678 tokens used
INFO - [Content] ✓ Successfully generated study guide - Title: 'Guía de Estudio: Fracciones', 5 key concepts, 6 review questions (1.89s total)
INFO - [ExercisePool] Generating initial pool of 5 exercises for session 1
INFO - [ExercisePool] Parameters: grade=5, subject=Matemáticas, topic=Fracciones, has_context=True
INFO - [ExercisePool] Exercise mix: multiple_choice/easy, true_false/easy, multiple_choice/medium, true_false/medium, short_answer/medium
INFO - [ExercisePool] Task 1/5: Generating multiple_choice (difficulty=easy)...
INFO - [ExercisePool] Task 2/5: Generating true_false (difficulty=easy)...
INFO - [ExercisePool] Task 3/5: Generating multiple_choice (difficulty=medium)...
INFO - [ExercisePool] Task 4/5: Generating true_false (difficulty=medium)...
INFO - [ExercisePool] Task 5/5: Generating short_answer (difficulty=medium)...
INFO - [ExercisePool] Starting parallel generation of 5 exercises...
INFO - [Generation] Starting exercise generation: type=multiple_choice, difficulty=easy, grade=5, subject=Matemáticas, topic=Fracciones
INFO - [Generation] Invoking LangGraph workflow...
INFO - [Generation] LangGraph workflow completed in 2.13s
INFO - [Generation] ✓ Exercise generation complete: iterations=1, final_score=8, elapsed=2.13s
INFO - [ExercisePool] ✓ Generated and linked exercise 101 (type=multiple_choice, difficulty=easy) to session 1 (2.45s)
INFO - [ExercisePool] ✓ Exercise 1/5 SUCCESS (multiple_choice/easy) - ID: 101
INFO - [ExercisePool] ✓ Exercise 2/5 SUCCESS (true_false/easy) - ID: 102
INFO - [ExercisePool] ✓ Exercise 3/5 SUCCESS (multiple_choice/medium) - ID: 103
INFO - [ExercisePool] ✓ Exercise 4/5 SUCCESS (true_false/medium) - ID: 104
INFO - [ExercisePool] ✓ Exercise 5/5 SUCCESS (short_answer/medium) - ID: 105
INFO - [ExercisePool] ✓ Generated 5/5 exercises for session 1 in 8.92s (failed: 0)
INFO - [Background] Successfully generated 5 exercises for session 1
```

### No Results Found

```log
INFO - [RAG] Starting semantic search - Query: 'UnknownTopic', Grade: 8, Subject: 'Historia', Limit: 5
INFO - [RAG] Search request completed in 0.34s
INFO - [RAG] Search found 0 results (search_time: 98.23ms)
WARNING - [RAG] No results found for query: 'UnknownTopic'
WARNING - [RAG] No curriculum content found for topic: 'UnknownTopic' (Grade: 8, Subject: Historia)
```

### Error During Search

```log
INFO - [RAG] Starting semantic search - Query: 'Matemáticas', Grade: 5, Subject: 'Matemáticas', Limit: 5
ERROR - [RAG] HTTP error during search (status: 500): Internal server error
ERROR - [RAG] Error during search: Request failed with status 500
ERROR - [RAG] Full search error traceback:
Traceback (most recent call last):
...
```

## How to Monitor RAG Operations

### 1. Watch Logs in Real-Time

```bash
# Filter for RAG operations only
docker-compose logs -f backend | grep "\[RAG\]"

# Filter for content generation only
docker-compose logs -f backend | grep "\[Content\]"

# Filter for exercise generation only
docker-compose logs -f backend | grep "\[ExercisePool\]"

# Filter for LangGraph generation only
docker-compose logs -f backend | grep "\[Generation\]"

# All background operations (includes RAG and content)
docker-compose logs -f backend | grep "\[Background\]"

# Everything together (RAG, content, exercises, and background)
docker-compose logs -f backend | grep -E "\[RAG\]|\[Content\]|\[ExercisePool\]|\[Generation\]|\[Background\]"
```

### 2. Check Specific Session

```bash
# Replace SESSION_ID with actual session ID
docker-compose logs backend | grep "session 1" | grep "\[RAG\]"
```

### 3. Monitor Performance

```bash
# Find slow operations (>1 second)
docker-compose logs backend | grep "\[RAG\]" | grep -E "completed in [1-9]\.[0-9]+s"

# Check success rate
docker-compose logs backend | grep "\[RAG\]" | grep "Successfully updated"
```

### 4. Debug Issues

```bash
# Find errors
docker-compose logs backend | grep "\[RAG\]" | grep -i error

# Find warnings
docker-compose logs backend | grep "\[RAG\]" | grep -i warning

# Find empty results
docker-compose logs backend | grep "\[RAG\]" | grep "No results found"
```

## Testing RAG Operations

### Test 1: Create Session and Watch RAG

```bash
# Terminal 1: Watch logs
docker-compose logs -f backend | grep -E "\[RAG\]|\[Background\]"

# Terminal 2: Create session
curl -X POST http://localhost:8000/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "grade": 5,
    "subject": "Matemáticas",
    "topic": "Fracciones",
    "mode": "learn"
  }'
```

**Expected Output:**
You should see a complete sequence of logs showing:
1. Background task initialization
2. RAG: Semantic search for "Fracciones"
3. RAG: Content retrieval
4. RAG: Context building
5. Content: Learning content generation with OpenAI
6. Content: Study guide generation with OpenAI
7. Exercise generation (separate flow)
8. Success messages with timing

### Test 2: Check RAG Performance

```bash
# Create session and measure time
time curl -X POST http://localhost:8000/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "grade": 8,
    "subject": "Historia",
    "topic": "Independencia de Chile",
    "mode": "learn"
  }'
```

**Expected Performance:**
- Semantic search: 0.3-0.8s
- Content fetch: 0.2-0.5s
- Context building: 0.5-1.5s
- Learning content generation: 1.5-3.5s
- Study guide generation: 1.0-2.5s
- Single exercise generation: 1.5-4.0s
- 5 exercises in parallel: 8-15s
- Total "Analizando contenido" phase: 10-20s

### Test 3: Verify Context Content

```bash
# Get session details to see research context
curl http://localhost:8000/chat/sessions/1 | jq '.research_context'
```

**Expected Output:**
Should show formatted curriculum content:
```json
{
  "research_context": "Topic: Fracciones\nGrade: 5\nSubject: Matemáticas\nFound 3 curriculum items\n\nContent 1: Introducción a las Fracciones\n  OA: OA05\n  Level: medium\n  Objectives: MA.5.OA.01, MA.5.OA.02\n  Content: Las fracciones representan partes de un todo...",
  "learning_content": {
    "title": "Introducción a las Fracciones",
    "sections": [...],
    "learning_objectives": [...]
  },
  "study_guide": {
    "title": "Guía de Estudio: Fracciones",
    "key_concepts": [...],
    "review_questions": [...]
  }
}
```

## Log Levels

### INFO Level (Default)
Shows all RAG and content generation operations:
- Search requests and results
- Content fetches and document details
- Context building progress
- OpenAI API calls and responses
- Token usage
- Success/failure status
- Performance timing for each step

### DEBUG Level (Verbose)
Additional details:
- Full API endpoints
- Learning objectives for each document
- Context preview (first 200 chars)
- Full OpenAI token usage breakdown
- Complete error stack traces

To enable DEBUG:
```bash
# In .env or environment
LOG_LEVEL=DEBUG
```

## Key Metrics to Monitor

### 1. Success Rate
```bash
# Count successful RAG operations
docker-compose logs backend | grep "\[RAG\]" | grep -c "Successfully updated"

# Count successful content generations
docker-compose logs backend | grep "\[Content\]" | grep -c "Successfully generated"

# Count errors in RAG
docker-compose logs backend | grep "\[RAG\]" | grep -c "Error"

# Count errors in content generation
docker-compose logs backend | grep "\[Content\]" | grep -c "Error"

# Count successful exercise generations
docker-compose logs backend | grep "\[ExercisePool\]" | grep -c "SUCCESS"

# Count failed exercise generations
docker-compose logs backend | grep "\[ExercisePool\]" | grep -c "FAILED"
```

### 2. Performance
```bash
# Average search time
docker-compose logs backend | grep "\[RAG\].*Search request completed" | \
  grep -oP "in \K[0-9.]+s" | awk '{sum+=$1; count++} END {print sum/count "s"}'

# Average total time
docker-compose logs backend | grep "\[RAG\].*Successfully updated" | \
  grep -oP "\([0-9.]+s" | tr -d '(' | awk '{sum+=$1; count++} END {print sum/count "s"}'
```

### 3. Result Quality
```bash
# Count sessions with RAG results
docker-compose logs backend | grep "\[RAG\].*Search found" | \
  grep -v "0 results" | wc -l

# Count sessions with no RAG results
docker-compose logs backend | grep "\[RAG\].*No results found" | wc -l

# Count content generation fallbacks
docker-compose logs backend | grep "\[Content\]" | grep -c "Returning fallback"
```

### 4. Token Usage (Cost Monitoring)
```bash
# Total tokens used
docker-compose logs backend | grep "\[Content\].*tokens used" | \
  grep -oP "\d+ tokens" | awk '{sum+=$1} END {print sum " tokens total"}'

# Average tokens per request
docker-compose logs backend | grep "\[Content\].*tokens used" | \
  grep -oP "\d+ tokens" | awk '{sum+=$1; count++} END {print sum/count " tokens avg"}'
```

## Common Issues and Solutions

### Issue: No Results Found

**Symptoms:**
```log
WARNING - [RAG] No results found for query: 'SomeTopic'
```

**Possible Causes:**
1. Topic not in curriculum database
2. Embeddings not generated for content
3. Search query too specific
4. Grade/subject mismatch

**Solutions:**
```bash
# Check if curriculum content exists
docker-compose exec backend python -c "
from app.ensenia.database.session import AsyncSessionLocal
from app.ensenia.database.models import CurriculumContent
from sqlalchemy import select
import asyncio

async def check():
    async with AsyncSessionLocal() as db:
        stmt = select(CurriculumContent).limit(10)
        result = await db.execute(stmt)
        items = result.scalars().all()
        print(f'Found {len(items)} curriculum items')
        for item in items:
            print(f'  - {item.title} (Grade: {item.grade}, Subject: {item.subject})')

asyncio.run(check())
"
```

### Issue: Slow Performance

**Symptoms:**
```log
INFO - [RAG] Search request completed in 3.45s
```

**Possible Causes:**
1. Cloudflare Worker slow response
2. Network latency
3. Large content retrieval
4. Database performance

**Solutions:**
```bash
# Check Worker status
curl -s https://your-worker.workers.dev/health

# Check Worker logs
wrangler tail

# Verify network latency
time curl -X POST https://your-worker.workers.dev/search \
  -H "Content-Type: application/json" \
  -d '{"query":"test","grade":5,"subject":"Matemáticas","limit":5}'
```

### Issue: HTTP Errors

**Symptoms:**
```log
ERROR - [RAG] HTTP error during search (status: 500)
```

**Possible Causes:**
1. Worker not deployed
2. Worker crashed
3. Database connection failed
4. API authentication failed

**Solutions:**
```bash
# Check Worker deployment
wrangler deployments list

# View Worker logs
wrangler tail

# Test Worker directly
curl -X POST https://your-worker.workers.dev/search \
  -H "Content-Type: application/json" \
  -d '{"query":"Matemáticas","grade":5,"subject":"Matemáticas","limit":5}'
```

## Validating RAG is Working

### ✅ Checklist

Use this checklist to verify RAG is operational:

**1. Semantic Search Works**
- [ ] Logs show `[RAG] Starting semantic search`
- [ ] Results found: `[RAG] Search found X results`
- [ ] Results have reasonable similarity scores (> 0.7)
- [ ] Search completes in <1s

**2. Content Fetching Works**
- [ ] Logs show `[RAG] Fetching X content documents`
- [ ] Documents retrieved: `[RAG] Retrieved X documents`
- [ ] Document details logged (title, grade, subject)
- [ ] Fetch completes in <1s

**3. Context Building Works**
- [ ] All 3 steps complete successfully
- [ ] Context contains multiple documents
- [ ] Context length is reasonable (>500 chars)
- [ ] Total time <2s

**4. Session Update Works**
- [ ] Logs show `[RAG] ✓ Successfully updated session`
- [ ] Session has research_context populated
- [ ] Context can be retrieved via API

**5. Content Generation Works**
- [ ] Logs show `[Content] Generating learning content`
- [ ] Context size logged: `[Content] Using curriculum context: X chars`
- [ ] OpenAI API calls complete: `[Content] OpenAI API call completed in Xs`
- [ ] Token usage reasonable (500-1500 tokens per request)
- [ ] Success message: `[Content] ✓ Successfully generated`
- [ ] Generation completes in <4s per item

**6. Study Guide Generation Works**
- [ ] Logs show `[Content] Generating study guide`
- [ ] OpenAI API call completes successfully
- [ ] Generated structure has concepts and questions
- [ ] Generation completes in <3s

**7. Exercise Pool Generation Works**
- [ ] Logs show `[ExercisePool] Generating initial pool`
- [ ] Exercise mix logged with types and difficulties
- [ ] Each task shows progress (X/Y)
- [ ] Parallel generation starts
- [ ] Each exercise shows SUCCESS or FAILED with details
- [ ] Final statistics show X/Y success rate
- [ ] If failures occur, full error tracebacks are logged
- [ ] Total generation completes in <15s for 5 exercises

**8. Individual Exercise Generation Works**
- [ ] Logs show `[Generation] Starting exercise generation`
- [ ] LangGraph workflow invoked
- [ ] Workflow completes with iteration count
- [ ] Validation score is reasonable (>6)
- [ ] Exercise saved to database
- [ ] Exercise linked to session
- [ ] Generation completes in <4s per exercise

## Summary

With these logs, you can now:

1. ✅ **Validate RAG is working** - See search → fetch → context flow
2. ✅ **Validate content generation** - See learning content and study guides being created
3. ✅ **Validate exercise generation** - See each exercise being created in detail
4. ✅ **Monitor performance** - Track timing at each step (RAG, content, exercises)
5. ✅ **Debug issues** - Clear error messages and full stack traces for every failure
6. ✅ **Analyze quality** - See content retrieved, exercises generated, validation scores
7. ✅ **Track success rates** - Count successful/failed operations for each component

All logs use prefixes for easy filtering:
- `[RAG]` - Semantic search, content fetch, context building
- `[Content]` - Learning content and study guide generation
- `[ExercisePool]` - Exercise pool management and parallel generation
- `[Generation]` - Individual exercise generation via LangGraph
- `[Background]` - Background task orchestration

Each log includes:
- Descriptive messages explaining what's happening
- Performance timing for each operation
- Success (✓) / Failure (✗) indicators
- Detailed error information with full tracebacks
- Step-by-step progress tracking
- Warnings (⚠️) for incomplete operations

**To see the complete "Analizando contenido" flow:**
```bash
docker-compose logs -f backend | grep -E "\[RAG\]|\[Content\]|\[ExercisePool\]|\[Generation\]"
```

**To debug exercise generation issues specifically:**
```bash
# See which exercises are failing
docker-compose logs backend | grep "\[ExercisePool\].*FAILED"

# See full error details
docker-compose logs backend | grep -A 20 "\[ExercisePool\].*FAILED"
```

Then create a session and watch the complete flow! 🎉

