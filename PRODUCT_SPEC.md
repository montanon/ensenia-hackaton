# Product Specification: Ensenia - AI Teaching Assistant for Chilean Students

**Version**: 1.0.0
**Status**: Ready for Development
**Target**: Hackathon MVP (< 30 hours)
**Date**: October 25, 2025

---

## Table of Contents

1. [Product Vision](#product-vision)
2. [Target Users](#target-users)
3. [MVP Scope](#mvp-scope)
4. [Core Features](#core-features)
5. [Chilean Ministry Compliance](#chilean-ministry-compliance)
6. [User Flows](#user-flows)
7. [Exercise Specifications](#exercise-specifications)
8. [Voice Interaction](#voice-interaction)
9. [Content Requirements](#content-requirements)
10. [Success Metrics](#success-metrics)
11. [Technical Requirements](#technical-requirements)
12. [Demo Scenarios](#demo-scenarios)
13. [Future Roadmap](#future-roadmap)

---

## Product Vision

### Mission Statement

**Ensenia democratizes access to high-quality, personalized education for all Chilean students by providing an AI-powered teaching assistant that:**

- Follows Chilean Ministry of Education curriculum standards
- Provides explanations in Chilean Spanish with local context
- Generates practice exercises aligned with official assessment formats
- Offers voice interaction for accessibility and engagement
- Adapts to each student's learning needs

### Core Value Proposition

**For Chilean students (grades 1-12)** who need help understanding curriculum concepts and practicing for assessments, **Ensenia** is an AI teaching assistant that provides instant, curriculum-aligned explanations and exercises in Chilean Spanish. **Unlike** generic AI tutors or foreign educational platforms, **Ensenia** is specifically designed for the Chilean education system, using official Ministry standards, SIMCE-style assessments, and local cultural context.

### Social Impact Goals

1. **Educational Equity**: Provide free, quality educational support to students regardless of economic background
2. **Ministry Alignment**: Ensure 100% compliance with official curriculum standards (Objetivos de Aprendizaje)
3. **Accessibility**: Offer voice interaction for students with different learning styles or disabilities
4. **Scalability**: Architecture supports all subjects (9) and grades (12) for nationwide impact
5. **Chilean Context**: Use local examples, currency, names, and cultural references students recognize

---

## Target Users

### Primary Persona (MVP): 5th Grade Mathematics Student

**Name**: Matías, 10 years old
**Location**: Santiago, Chile
**Grade**: 5° Básico (5th grade)
**Subject**: Matemática

**Context**:
- Struggles with understanding fractions
- Preparing for SIMCE evaluation
- Limited access to private tutoring
- Parents work and can't always help with homework
- Has access to computer/tablet at home or school

**Needs**:
- Clear explanations in Spanish he understands
- Practice exercises similar to SIMCE format
- Immediate feedback on answers
- Examples using familiar contexts (Chilean pesos, local foods, etc.)
- Audio option because sometimes reading long text is tiring

**Pain Points**:
- Textbook explanations too abstract
- Can't ask questions when stuck on homework
- Doesn't know if practice problems are right until next class
- Generic online resources use foreign examples (dollars, inches, etc.)

### Secondary Persona: 7th Grade Science Student

**Name**: Valentina, 12 years old
**Location**: Valparaíso, Chile
**Grade**: 7° Básico (7th grade)
**Subject**: Ciencias Naturales

**Context**:
- Curious about science, wants deeper explanations
- Finds memorizing facts boring
- Learns better by hearing information
- Uses phone for studying

**Needs**:
- Detailed explanations with examples
- Audio explanations for studying on the go
- Exercises that test understanding, not just memory
- Connection to real-world Chilean contexts

### Future Personas (Post-MVP)

1. **Primary School Student (1-4° Básico)**: Needs simpler language, more visual elements
2. **High School Student (I-IV Medio)**: Advanced topics, university prep, PSU/PAES preparation
3. **Teacher**: Dashboard to review student progress, generate classroom exercises
4. **Parent**: Monitor child's learning, understand curriculum to help with homework

---

## MVP Scope

### In Scope (MVP - 12 hours)

#### Subject & Grade
- **Subject**: Matemática (Mathematics) only
- **Grade**: 5° Básico (5th grade) only
- **Topics**: 5-10 Objetivos de Aprendizaje for 5th grade mathematics

#### Core Features
✅ **Learn Mode**: Ask questions, receive curriculum-aligned explanations
✅ **Practice Mode**: Generate SIMCE-style multiple choice exercises
✅ **Voice Support**: Text-to-speech for explanations and exercises
✅ **Chilean Compliance**: 100% alignment with Ministry standards
✅ **Instant Feedback**: Immediate answer validation with explanations

#### Technical Scope
✅ Hybrid CloudFlare Worker (TypeScript) + Python FastAPI backend
✅ CloudFlare Deep Research (Workers AI, D1, Vectorize) integration
✅ ElevenLabs text-to-speech integration
✅ Abstract architecture for future extensibility
✅ In-memory caching (no persistent database for MVP)

### Out of Scope (MVP)

❌ User authentication and accounts
❌ Student progress tracking across sessions
❌ Multiple subjects (only Mathematics)
❌ Multiple grades (only 5th grade)
❌ Speech-to-text (voice input)
❌ Teacher dashboard
❌ Parent monitoring features
❌ Mobile native app
❌ Gamification (points, badges, leaderboards)
❌ Social features (student collaboration)
❌ Homework submission
❌ Video explanations
❌ Persistent student profiles

### MVP Success Criteria

1. ✅ Can answer 5th grade math questions with curriculum-aligned explanations
2. ✅ Generates valid SIMCE-style multiple choice exercises
3. ✅ Provides text-to-speech audio in Chilean Spanish
4. ✅ Response time < 3 seconds
5. ✅ Zero crashes during 3 demo scenarios
6. ✅ Impresses judges on all 4 criteria (Innovation, Technical, UX, Impact)

---

## Core Features

### Feature 1: Learn Mode (Query & Explanation)

#### User Story
> "As a 5th grade student, I want to ask questions about math concepts in my own words, so that I can understand topics I'm struggling with."

#### Acceptance Criteria
1. Student can enter question in natural Chilean Spanish
2. System returns explanation aligned with Ministry curriculum
3. Explanation uses Chilean Spanish terminology
4. Explanation includes relevant Objetivos de Aprendizaje (OA) references
5. Audio version available within 5 seconds
6. Response time < 3 seconds for text
7. Examples use Chilean context (pesos, local foods, familiar situations)

#### Functional Requirements

**Input**:
- Text field accepting 3-500 character questions
- Natural language processing (no need for perfect grammar)
- Grade selection (fixed to 5° for MVP)
- Subject selection (fixed to Matemática for MVP)
- Audio toggle (request TTS or not)

**Processing**:
1. Query submitted to Python backend
2. Backend calls CloudFlare search to find relevant curriculum content
3. Backend fetches top 3-5 matching content items
4. Subject handler (MathematicsHandler) enriches explanation with local context
5. Curriculum validator ensures Ministry OA alignment
6. If audio requested, ElevenLabs generates TTS (asynchronously)
7. Response returned immediately

**Output**:
- Clear, concise explanation (200-500 words)
- List of relevant OAs addressed
- Ministry standard references
- Audio ID (if requested)
- Audio available status
- Generated timestamp

#### Example Interaction

**Student Input**:
```
"¿Qué es una fracción?"
```

**System Output**:
```
Explicación:
Una fracción representa partes de un todo. Se compone de dos
elementos principales:

• El numerador (parte superior) indica cuántas partes tomamos
• El denominador (parte inferior) indica en cuántas partes
  dividimos el todo

Por ejemplo: Si divides una pizza en 8 partes iguales y comes
3 partes, has comido 3/8 (tres octavos) de la pizza.

En fracciones:
- 3 es el numerador (las partes que comiste)
- 8 es el denominador (el total de partes)

Este concepto es fundamental para entender operaciones más
avanzadas como sumar y restar fracciones.

Objetivos de Aprendizaje:
• OA-MAT-5-03: Demostrar que comprenden las fracciones

[🔊 Audio disponible]
```

#### Non-Functional Requirements
- Response latency: < 3 seconds (text)
- Audio generation: < 5 seconds (background)
- Language: Chilean Spanish only
- Readability: 5th grade level (Flesch-Kincaid)
- Accessibility: WCAG 2.1 AA compliant

---

### Feature 2: Practice Mode (Exercise Generation)

#### User Story
> "As a 5th grade student, I want to practice math problems similar to what I'll see on SIMCE tests, so that I can prepare for my evaluation."

#### Acceptance Criteria
1. Student can request exercise on specific topic
2. Exercise follows SIMCE multiple-choice format (4 options)
3. Questions use Chilean context and Spanish
4. Instant feedback on answer selection
5. Detailed explanation provided after answering
6. Difficulty level adjustable (basic, intermediate, advanced)
7. Each exercise mapped to specific Ministry OAs

#### Functional Requirements

**Input**:
- Topic selection (e.g., "fracciones", "suma de fracciones")
- Difficulty level (basic, intermediate, advanced)
- Exercise type (multiple_choice for MVP)
- Grade (fixed to 5°)
- Subject (fixed to Matemática)

**Processing**:
1. Request submitted to Python backend
2. Backend searches curriculum for topic context
3. MathematicsHandler generates exercise using CloudFlare AI
4. Exercise validated in agent-validator loop:
   - Check answer is correct
   - Verify options are reasonable distractors
   - Confirm Chilean Spanish and local context
   - Ensure Ministry OA alignment
   - Validation score must be ≥ 70/100
5. Validated exercise returned to student

**Output**:
- Question text (clear, age-appropriate)
- 4 multiple choice options (1 correct, 3 plausible distractors)
- Correct answer
- Detailed explanation (200-300 words)
- Learning objectives addressed
- Ministry standard reference
- Difficulty level
- Validation score

#### Exercise Structure

```json
{
  "question": "María compró 3/4 kg de manzanas y 1/4 kg de peras. ¿Cuántos kilogramos de fruta compró en total?",
  "options": [
    "1 kg",
    "4/8 kg",
    "4/4 kg",
    "2/4 kg"
  ],
  "correct_answer": "1 kg",
  "explanation": "Para sumar fracciones con el mismo denominador, sumamos los numeradores:\n\n3/4 + 1/4 = (3+1)/4 = 4/4\n\n4/4 es igual a 1 entero, entonces María compró 1 kg de fruta en total.\n\nRecuerda: Cuando el numerador y denominador son iguales, la fracción equivale a 1 entero.",
  "difficulty": "intermediate",
  "exercise_type": "multiple_choice",
  "learning_objectives": ["OA-MAT-5-03", "OA-MAT-5-04"],
  "ministry_standard_ref": "OA-MAT-5-04"
}
```

#### Quality Requirements (Agent-Validator Loop)

**Validation Checklist**:
1. ✅ Question is grammatically correct Chilean Spanish
2. ✅ Question uses local context (pesos, Chilean names, local situations)
3. ✅ Correct answer is mathematically accurate
4. ✅ All 4 options are plausible (no obvious wrong answers)
5. ✅ Distractors represent common student mistakes
6. ✅ Difficulty matches requested level
7. ✅ Aligns with specified Ministry OAs
8. ✅ Explanation is clear and educational
9. ✅ Age-appropriate language for 5th grade
10. ✅ Follows SIMCE question format

**Validation Process**:
```python
while validation_score < 70 and attempts < 3:
    exercise = generate_exercise()
    validation_score = validate_with_ministry_standards(exercise)
    if validation_score < 70:
        feedback = get_validation_feedback(exercise)
        # Regenerate with feedback
```

---

### Feature 3: Voice Interaction (Text-to-Speech)

#### User Story
> "As a 5th grade student, I want to hear explanations read aloud in a clear voice, so that I can learn while walking, doing chores, or when I'm tired of reading."

#### Acceptance Criteria
1. All text explanations available as audio
2. Audio in Chilean Spanish accent
3. Clear, natural-sounding voice
4. Playback controls (play, pause, replay)
5. Audio generated within 5 seconds
6. Audio cached to avoid regeneration
7. Works on desktop and mobile browsers

#### Functional Requirements

**Voice Selection**:
- ElevenLabs Chilean Spanish voice model
- Female voice (more engaging for young students)
- Clear enunciation
- Natural prosody (not robotic)

**Audio Generation**:
- Triggered when `include_audio: true` in request
- Generated asynchronously (non-blocking)
- Stored temporarily with unique ID
- Cached for 7 days to reduce API calls
- Falls back to text-only if TTS fails

**Audio Delivery**:
- Audio ID returned immediately in response
- `audio_available: false` initially
- Frontend polls `/api/audio/{id}` endpoint
- When ready, returns audio URL
- Browser-native audio player

#### Technical Implementation

**Request with Audio**:
```json
POST /api/query
{
  "query": "¿Cómo sumo fracciones?",
  "grade": 5,
  "subject": "mathematics",
  "include_audio": true
}
```

**Immediate Response**:
```json
{
  "explanation": "Para sumar fracciones...",
  "audio_id": "audio_abc123",
  "audio_available": false,
  "generated_at": "2025-10-25T12:00:00Z"
}
```

**Polling for Audio**:
```
GET /api/audio/audio_abc123

Response 200:
{
  "id": "audio_abc123",
  "audio_url": "https://cdn.elevenlabs.io/...",
  "duration_seconds": 23.5,
  "voice_id": "es_CL_female_1"
}
```

**Frontend Integration**:
```javascript
// Display explanation immediately
showExplanation(response.explanation)

// Start polling for audio
if (response.audio_id) {
  pollForAudio(response.audio_id)
}

async function pollForAudio(audioId) {
  const maxAttempts = 10
  for (let i = 0; i < maxAttempts; i++) {
    await sleep(1000) // Wait 1 second
    const audio = await fetch(`/api/audio/${audioId}`)
    if (audio.ok) {
      const data = await audio.json()
      playAudio(data.audio_url)
      return
    }
  }
  // Fallback: audio not available
  showTextOnly()
}
```

#### Chat Modes (Future Enhancement)

**Mode 1: Text In / Text Out**
- Default mode
- No audio generation

**Mode 2: Text In / Audio Out**
- User types questions
- System responds with audio + text
- Useful for multitasking

**Mode 3: Voice Toggle**
- Can switch audio on/off any time
- Conversations logged as text

---

## Chilean Ministry Compliance

### Curriculum Framework

Ensenia strictly follows the **Bases Curriculares** established by the Chilean Ministry of Education (Ministerio de Educación de Chile).

#### Objetivos de Aprendizaje (OA)

Each subject and grade has official **Objetivos de Aprendizaje** (Learning Objectives) that define what students should learn. All Ensenia content is mapped to specific OAs.

**Example OAs for 5th Grade Mathematics**:

| OA Code | Description | Topics |
|---------|-------------|--------|
| OA-MAT-5-01 | Representar y describir números naturales hasta 1.000.000 | Números grandes, valor posicional |
| OA-MAT-5-02 | Aplicar estrategias de cálculo mental | Cálculo mental, estimación |
| OA-MAT-5-03 | Demostrar que comprenden las fracciones | Fracciones, numerador, denominador |
| OA-MAT-5-04 | Resolver adiciones y sustracciones de fracciones | Operaciones con fracciones |
| OA-MAT-5-05 | Resolver problemas rutinarios y no rutinarios | Resolución de problemas |

#### Content Alignment Strategy

**1. Content Validation**
Every explanation and exercise goes through Ministry compliance validation:

```python
validation_criteria = {
    "oa_alignment": 40%,        # Matches specific OAs
    "grade_appropriate": 30%,    # Suitable for grade level
    "chilean_terminology": 20%,  # Uses Ministry-approved terms
    "learning_coverage": 10%     # Covers required concepts
}

minimum_score = 70/100  # Must pass to be shown to students
```

**2. Chilean Spanish Requirements**

**Use**:
- ✅ Matemática (not "Matemáticas")
- ✅ Numerador / Denominador
- ✅ Pesos chilenos (not dollars)
- ✅ Kilogramos (not pounds)
- ✅ Chilean names (María, José, Valentina, Matías)
- ✅ Local foods (empanadas, completos, mote con huesillo)
- ✅ Chilean cities (Santiago, Valparaíso, Concepción)

**Avoid**:
- ❌ Spain Spanish (vosotros, ordenador, móvil)
- ❌ Mexico Spanish (platicar, chamaco)
- ❌ Generic Latin American Spanish
- ❌ Foreign examples or context

**3. SIMCE Alignment**

SIMCE (Sistema de Medición de la Calidad de la Educación) is Chile's national standardized test. Ensenia exercises follow SIMCE format:

**SIMCE Multiple Choice Format**:
- 1 question stem
- 4 options (A, B, C, D)
- 1 correct answer
- 3 distractors (wrong but plausible)
- Age-appropriate language
- Clear, unambiguous wording
- Tests understanding, not memorization

**Example SIMCE-Style Question**:
```
¿Cuál de las siguientes fracciones es equivalente a 1/2?

A) 1/4
B) 2/4  ← Correct answer
C) 3/4
D) 4/4
```

#### Ministry Validation Process

**Step 1: OA Mapping**
```json
{
  "topic": "fracciones",
  "grade": 5,
  "relevant_oas": [
    "OA-MAT-5-03",
    "OA-MAT-5-04"
  ]
}
```

**Step 2: Content Generation**
Generate content with OA context injected into prompt.

**Step 3: Validation with AI**
```
Prompt: "Eres un validador del Ministerio de Educación de Chile.
Valida si este contenido cumple con los estándares..."
```

**Step 4: Scoring**
- OA alignment: Does it teach the specified objectives?
- Grade level: Is language and complexity appropriate for 5°?
- Chilean context: Uses local terminology and examples?
- Learning value: Is it educational and accurate?

**Step 5: Iterative Improvement**
If score < 70, regenerate with feedback up to 3 attempts.

---

## User Flows

### Flow 1: Student Asks Question

```
[Student] → "¿Qué es una fracción?"
    ↓
[Frontend] → POST /api/query { query, grade, subject, include_audio: true }
    ↓
[Backend - LearningSessionOrchestrator]
    ↓
[CloudFlare Worker] → Search curriculum (Vectorize)
    ↓ Returns content_ids
[CloudFlare Worker] → Fetch content (D1)
    ↓ Returns full content
[Backend - MathematicsHandler] → Enrich explanation with Chilean context
    ↓
[Backend - Validator] → Validate Ministry compliance
    ↓
[Backend - ElevenLabs] → Generate audio (async)
    ↓
[Backend] → Return response { explanation, audio_id, audio_available: false }
    ↓
[Frontend] → Display explanation immediately
    ↓
[Frontend] → Poll /api/audio/{id} every 1s
    ↓
[Backend] → Audio ready → Return { audio_url }
    ↓
[Frontend] → Show audio player 🔊
    ↓
[Student] → Read or listen to explanation
```

**Timeline**:
- T+0s: Student submits question
- T+0.5s: CloudFlare search complete
- T+1.5s: Content fetched and enriched
- T+2.5s: Explanation displayed to student ✅
- T+3-5s: Audio available 🔊

### Flow 2: Student Practices Exercise

```
[Student] → Click "Practicar" button
    ↓
[Frontend] → POST /api/exercise { topic, grade, difficulty, exercise_type }
    ↓
[Backend - ExerciseOrchestrator]
    ↓
[CloudFlare Worker] → Search curriculum for topic context
    ↓
[Backend - MathematicsHandler] → Build Chilean math exercise prompt
    ↓
[CloudFlare Worker] → Generate exercise with Workers AI
    ↓
[Backend - Validator] → Validate exercise
    ├─ Score ≥ 70? → ✅ Return exercise
    └─ Score < 70? → Regenerate with feedback (max 3 attempts)
    ↓
[Frontend] → Display question with 4 options
    ↓
[Student] → Select answer
    ↓
[Frontend] → Immediate feedback (client-side validation)
    ├─ Correct? → ✅ "¡Correcto! [explanation]"
    └─ Wrong? → ❌ "Incorrecto. La respuesta correcta es... [explanation]"
    ↓
[Frontend] → Show learning objectives addressed
    ↓
[Student] → Click "Siguiente ejercicio" → Repeat
```

**Timeline**:
- T+0s: Student requests exercise
- T+0.5s: Context search complete
- T+1.5s: Exercise generated
- T+2.5s: Validated and returned
- T+2.5s: Exercise displayed ✅
- T+2.5s+: Student answers, instant feedback

### Flow 3: Voice Interaction

```
[Student] → Toggle "Escuchar explicación" ON
    ↓
[Frontend] → include_audio: true in request
    ↓
[Backend] → Process query normally + trigger audio generation
    ↓
[ElevenLabs API] → Generate TTS (async, 3-5s)
    ↓
[Backend] → Cache audio with 7-day TTL
    ↓
[Frontend] → Poll for audio availability
    ↓
[Backend] → Return audio_url when ready
    ↓
[Frontend] → Load audio in browser player
    ↓
[Student] → Press play 🔊
    ↓
[Student] → Listen while reading, walking, or doing other tasks
    ↓
[Student] → Can replay, pause, resume
```

---

## Exercise Specifications

### Multiple Choice Exercise Format

#### Question Structure

**Components**:
1. **Context** (optional): Situation setup
2. **Question stem**: What is being asked
3. **Options**: 4 choices (A, B, C, D)
4. **Correct answer**: 1 option
5. **Distractors**: 3 plausible wrong answers
6. **Explanation**: Detailed walkthrough

#### Chilean Context Requirements

**Use Local Context**:
- Chilean pesos for money problems
- Chilean foods (empanadas, completos, etc.)
- Chilean names (María, José, Valentina, Matías, etc.)
- Chilean locations (Santiago, Valparaíso, etc.)
- Familiar situations (going to school, buying at almacén, etc.)

**Example with Good Chilean Context**:
```
Matías fue al almacén y compró 3 paquetes de galletas a $500
cada uno. ¿Cuánto gastó en total?

A) $500
B) $1.000
C) $1.500 ← Correct
D) $2.000
```

**Example with Poor Context** (avoid):
```
John went to the store and bought 3 packages of cookies at
$5 each. How much did he spend?
```

#### Difficulty Levels

**Basic (Básico)**:
- Direct application of concept
- Single-step problems
- Simple numbers
- Familiar contexts

Example:
```
¿Cuál fracción representa la mitad de un todo?
A) 1/4
B) 1/2 ← Correct
C) 2/3
D) 3/4
```

**Intermediate (Intermedio)**:
- Multi-step problems
- Requires understanding and application
- More complex numbers
- Real-world scenarios

Example:
```
María tenía 3/4 de pizza. Comió 1/4. ¿Qué fracción le queda?
A) 1/4
B) 2/4 ← Correct
C) 3/4
D) 4/4
```

**Advanced (Avanzado)**:
- Complex multi-step problems
- Requires analysis and synthesis
- Abstract thinking
- Non-routine problems

Example:
```
Si 2/3 de los estudiantes de 5°A son mujeres, y hay 18 mujeres,
¿cuántos estudiantes hay en total?
A) 12
B) 24
C) 27 ← Correct
D) 36
```

#### Distractor Design

**Good Distractors**:
- Represent common mistakes students make
- Plausible given the question
- Based on typical errors (e.g., adding denominators)

**Example**:
```
Question: ¿Cuánto es 1/4 + 1/4?

A) 2/8  ← Distractor: Added both numerator and denominator
B) 1/2  ← Correct: 2/4 = 1/2
C) 2/4  ← Distractor: Correct before simplification (also acceptable)
D) 1/8  ← Distractor: Multiplied instead of added
```

#### Explanation Format

**Structure**:
1. Restate the correct answer
2. Show step-by-step solution
3. Explain the reasoning
4. Connect to learning objective
5. (Optional) Note common mistakes

**Example**:
```
Respuesta correcta: B) 1/2

Solución paso a paso:
1. Identificamos que ambas fracciones tienen el mismo denominador (4)
2. Cuando los denominadores son iguales, sumamos los numeradores:
   1/4 + 1/4 = (1+1)/4 = 2/4
3. Simplificamos 2/4 dividiendo numerador y denominador por 2:
   2/4 = 1/2

Por lo tanto, 1/4 + 1/4 = 1/2

Concepto clave: Cuando sumamos fracciones con el mismo denominador,
mantenemos el denominador y sumamos solo los numeradores.

Este ejercicio trabaja el OA-MAT-5-04: Resolver adiciones de fracciones.

Error común: Algunos estudiantes suman tanto numeradores como
denominadores (1+1)/(4+4) = 2/8. Recuerda: ¡solo sumamos numeradores!
```

---

## Content Requirements

### Minimum Content for MVP

#### 5th Grade Mathematics Objetivos de Aprendizaje

**Required OAs** (minimum 5-10):

1. **OA-MAT-5-01**: Representar y describir números naturales hasta 1.000.000
   - Keywords: números grandes, valor posicional, representación

2. **OA-MAT-5-02**: Aplicar estrategias de cálculo mental
   - Keywords: cálculo mental, estrategias, estimación

3. **OA-MAT-5-03**: Demostrar que comprenden las fracciones
   - Keywords: fracciones, numerador, denominador, partes de un todo

4. **OA-MAT-5-04**: Resolver adiciones y sustracciones de fracciones
   - Keywords: suma de fracciones, resta de fracciones, mismo denominador

5. **OA-MAT-5-05**: Resolver multiplicación y división de fracciones
   - Keywords: multiplicación, división, fracciones

6. **OA-MAT-5-06**: Demostrar que comprenden el concepto de razón
   - Keywords: razón, proporción, comparación

7. **OA-MAT-5-07**: Demostrar que comprenden el concepto de porcentaje
   - Keywords: porcentaje, %, fracciones decimales

8. **OA-MAT-5-08**: Resolver problemas rutinarios y no rutinarios
   - Keywords: resolución de problemas, estrategias, aplicación

9. **OA-MAT-5-09**: Demostrar que comprenden el concepto de área
   - Keywords: área, superficie, unidades cuadradas

10. **OA-MAT-5-10**: Demostrar que comprenden el concepto de volumen
    - Keywords: volumen, unidades cúbicas, capacidad

#### D1 Database Content

**Curriculum Content Table**:
```sql
-- Minimum 10-15 entries for MVP
INSERT INTO curriculum_content VALUES
  ('curr-mat-5-001', 'Fracciones: Conceptos Básicos', 5, 'mathematics',
   'Las fracciones representan partes de un todo...',
   '["OA-MAT-5-03"]', 'OA-MAT-5-03', 1, CURRENT_TIMESTAMP),

  ('curr-mat-5-002', 'Suma de Fracciones con Mismo Denominador', 5, 'mathematics',
   'Para sumar fracciones con el mismo denominador...',
   '["OA-MAT-5-04"]', 'OA-MAT-5-04', 1, CURRENT_TIMESTAMP),

  -- ... 10-15 more entries
```

**Ministry Standards Table**:
```sql
-- All 10 OAs for 5th grade math
INSERT INTO ministry_standards VALUES
  ('OA-MAT-5-03', 5, 'mathematics',
   'Demostrar que comprenden las fracciones con denominadores 100, 12, 10, 8, 6, 5, 4, 3, 2',
   '{"skills":["identificar","representar","comparar"]}',
   '["Identifica partes de un todo","Representa fracciones gráficamente"]',
   'Bases Curriculares Matemática 5° Básico',
   '2024-01-01', CURRENT_TIMESTAMP),

  -- ... 9 more OAs
```

#### Vectorize Embeddings

**Generate embeddings for all curriculum content**:
```typescript
// Embed all 10-15 curriculum content items
for (const content of curriculumContents) {
  const embedding = await env.AI.run('@cf/baai/bge-base-en-v1.5', {
    text: `${content.title} ${content.content_text}`
  })

  await env.VECTORIZE_INDEX.insert([{
    id: content.id,
    values: embedding.data[0],
    metadata: {
      title: content.title,
      grade: 5,
      subject: 'mathematics',
      oa: content.ministry_standard_ref
    }
  }])
}
```

---

## Success Metrics (Hackathon Judging)

### Innovation (25 points)

**What Makes Ensenia Innovative**:
1. **First AI assistant specifically for Chilean curriculum**
   - Not adapted from foreign system
   - Built from ground up for Chilean standards

2. **Novel Ministry compliance validation**
   - Agent-validator loop ensures quality
   - Automatic OA mapping
   - Content scoring against official standards

3. **Voice interaction for education equity**
   - Accessibility for different learning styles
   - Reduces barriers for students with reading difficulties
   - Learn while multitasking

4. **Hybrid architecture**
   - CloudFlare edge computing for speed
   - Python backend for flexibility
   - Abstract design for unlimited scalability

**Demo Talking Points**:
- "First AI tutor that speaks Chilean, not just Spanish"
- "Every answer validated against Ministry standards"
- "Scalable architecture: built for 1 subject, designed for 108"
- "Voice makes education accessible to all students"

### Technical Complexity (25 points)

**Technical Achievements**:
1. **Multi-service orchestration**
   - CloudFlare Workers AI (embeddings, generation)
   - CloudFlare D1 (database)
   - CloudFlare Vectorize (semantic search)
   - ElevenLabs (TTS)
   - Python FastAPI (orchestration)

2. **Advanced AI techniques**
   - Semantic search with vector embeddings
   - LLM-powered content generation
   - Agent-validator loop for quality
   - Context-aware prompt engineering

3. **Scalable architecture**
   - Abstract base classes
   - Plugin pattern (SubjectRegistry)
   - Configuration-driven extensibility
   - Separation of concerns

4. **Real-time processing**
   - Async audio generation
   - Parallel API calls
   - Response streaming
   - Efficient caching

**Demo Talking Points**:
- "5 different AI services working together seamlessly"
- "Semantic search through 100,000s of curriculum items in <1s"
- "Self-improving with validation loops"
- "Abstract architecture: change 1 config file to add a subject"

### User Experience (25 points)

**UX Excellence**:
1. **Fast response times**
   - Text explanations < 3 seconds
   - Audio available < 5 seconds
   - Instant exercise feedback

2. **Natural interactions**
   - Natural language questions (no keywords)
   - Chilean Spanish throughout
   - Familiar examples and context

3. **Clear feedback**
   - Easy-to-understand explanations
   - Step-by-step solutions
   - Learning objectives shown

4. **Accessibility**
   - Voice option for all content
   - Simple, clean interface
   - Works on mobile and desktop

**Demo Talking Points**:
- "Students use their own words, like asking a friend"
- "Explanations use empanadas and pesos, not pizza and dollars"
- "Hear the answer while walking to school"
- "Fast enough that students stay engaged"

### Social Impact (25 points)

**Impact on Chilean Education**:
1. **Educational equity**
   - Free AI tutor for all students
   - No expensive private tutoring needed
   - Accessible 24/7

2. **Ministry alignment**
   - 100% compliant with official curriculum
   - Prepares for SIMCE evaluations
   - Uses approved terminology and methods

3. **Scalability**
   - Architecture supports all 9 subjects
   - All 12 grades (1° Básico to IV Medio)
   - Nationwide deployment potential

4. **Addresses real needs**
   - Many Chilean families can't afford tutors
   - Parents may not remember 5th grade math
   - Students need practice outside school hours

**Demo Talking Points**:
- "Democratizes access to quality education"
- "Every student in Chile can have a personal AI tutor"
- "Built for Chilean students, using Chilean standards"
- "Scales from 1 classroom to 3 million students"

### Scoring Strategy

**Maximize Points**:
- **Innovation**: Emphasize "first for Chile", novel validation
- **Technical**: Showcase 5 services, advanced architecture
- **UX**: Demonstrate speed, naturalness, accessibility
- **Impact**: Highlight equity, scalability, Ministry alignment

**Target Score**: 85-95 / 100 points

---

## Technical Requirements

### Functional Requirements

**FR-1: Query Processing**
- Accept natural language questions (3-500 characters)
- Support Chilean Spanish input
- Return curriculum-aligned explanations
- Map to Ministry OAs
- Generate optional TTS audio

**FR-2: Exercise Generation**
- Generate SIMCE-style multiple choice questions
- 4 options per question (1 correct, 3 distractors)
- Adjustable difficulty (basic, intermediate, advanced)
- Chilean context in all questions
- Detailed explanations

**FR-3: Ministry Compliance**
- All content validated against Ministry standards
- Minimum 70/100 alignment score required
- Automatic OA mapping
- Chilean Spanish terminology enforcement
- Age-appropriate language

**FR-4: Voice Interaction**
- Text-to-speech for all text content
- Chilean Spanish voice
- Audio caching (7-day TTL)
- Graceful degradation if TTS fails

**FR-5: Response Management**
- Text responses < 3 seconds
- Audio generation < 5 seconds (async)
- Error handling and recovery
- Fallback mechanisms

### Non-Functional Requirements

**NFR-1: Performance**
- API response time: < 3 seconds (p95)
- Audio generation: < 5 seconds (p95)
- Database queries: < 500ms (p95)
- Vector search: < 1 second (p95)
- Support 100 concurrent users

**NFR-2: Reliability**
- 99% uptime during demo
- Zero crashes in demo scenarios
- Graceful error handling
- Fallback to demo mode if needed

**NFR-3: Scalability**
- Architecture supports 9 subjects × 12 grades
- Configuration-driven subject addition
- Can scale to 1000s of concurrent users (post-MVP)
- Horizontal scaling capability

**NFR-4: Maintainability**
- Type-safe code (Pydantic, TypeScript)
- Abstract architecture with clear interfaces
- Comprehensive test coverage (> 70%)
- Clear documentation

**NFR-5: Accessibility**
- WCAG 2.1 AA compliant (text)
- Voice option for all content
- Works on mobile and desktop
- Clear, simple UI

**NFR-6: Localization**
- 100% Chilean Spanish
- Local cultural context
- Ministry-approved terminology
- Age-appropriate language

---

## Demo Scenarios

### Scenario 1: Learn - Understanding Fractions

**Setup**: Fresh browser, clear cache

**Script**:
```
[Narrator]: "Meet Matías, a 5th grader struggling with fractions."

[Demo]:
1. Open Ensenia homepage
2. Type question: "¿Qué es una fracción?"
3. Click "Preguntar"
4. [WAIT ~2 seconds]
5. Explanation appears with OA references
6. Audio indicator shows 🔊
7. Click play button
8. [Listen to first 5 seconds of audio]

[Highlight]:
- Fast response (< 3s)
- Clear Chilean Spanish explanation
- Uses empanada example (not pizza)
- Ministry OAs shown
- Voice option available

[Quote]: "In under 3 seconds, Matías gets a Ministry-approved
explanation in his language, with examples he recognizes."
```

**Expected Output**:
```
Explicación:
Una fracción representa partes de un todo. Imagina que tienes
una empanada completa y la cortas en 4 partes iguales. Si comes
1 parte, has comido 1/4 (un cuarto) de la empanada.

Las fracciones tienen dos números:
• El numerador (arriba): indica cuántas partes tomamos
• El denominador (abajo): indica en cuántas partes dividimos el todo

Ejemplo: En 3/4, el 3 es el numerador (tomamos 3 partes) y el
4 es el denominador (dividimos en 4 partes).

Objetivos de Aprendizaje:
• OA-MAT-5-03: Demostrar que comprenden las fracciones

🔊 [Audio player ready]
```

### Scenario 2: Practice - SIMCE-Style Exercise

**Setup**: Continue from Scenario 1

**Script**:
```
[Narrator]: "Now Matías wants to practice for his SIMCE test."

[Demo]:
1. Click "Practicar" button
2. Select topic: "Fracciones"
3. Select difficulty: "Intermedio"
4. Click "Generar ejercicio"
5. [WAIT ~2.5 seconds]
6. SIMCE-style question appears with 4 options
7. Select correct answer (B)
8. [INSTANT] Green checkmark appears
9. Detailed explanation shown with OA reference

[Highlight]:
- SIMCE format (exactly like real test)
- Chilean context (pesos, Chilean names)
- Instant feedback
- Detailed explanation
- Ministry OA mapping

[Quote]: "Exercises generated on-demand, validated against
Ministry standards, using contexts Matías recognizes from daily life."
```

**Expected Output**:
```
Ejercicio:

María compró 3/4 kg de manzanas en la feria. Si consume 1/4 kg,
¿qué fracción de las manzanas le queda?

A) 1/4
B) 2/4  ← Student selects this
C) 3/4
D) 4/4

✅ ¡Correcto!

Explicación:
Para resolver este problema, restamos las fracciones:
3/4 - 1/4 = (3-1)/4 = 2/4

Como ambas fracciones tienen el mismo denominador (4),
simplemente restamos los numeradores: 3 - 1 = 2

Por lo tanto, a María le quedan 2/4 kg de manzanas.

Nota: 2/4 es equivalente a 1/2 (si simplificamos).

Este ejercicio trabaja:
• OA-MAT-5-04: Resolver sustracciones de fracciones
```

### Scenario 3: Voice Interaction

**Setup**: Continue from previous scenarios

**Script**:
```
[Narrator]: "Matías can also learn while doing other activities."

[Demo]:
1. Toggle "Audio" switch ON
2. Type new question: "¿Cómo sumo fracciones con diferente denominador?"
3. Click "Preguntar"
4. Explanation appears immediately (~2.5s)
5. Audio indicator shows "Generando audio..."
6. [WAIT 3 seconds]
7. Audio ready 🔊
8. Click play
9. [Listen while showing student doing homework, walking, etc.]

[Highlight]:
- Non-blocking audio generation
- Chilean Spanish voice
- Can multitask while learning
- Accessibility benefit

[Quote]: "With voice support, Matías can learn while walking
home from school, helping his parents, or when he's tired of reading."
```

---

## Future Roadmap (Post-MVP)

### Phase 1: Complete Mathematics (1-2 weeks)
- All grades 1-12 for Mathematics
- All exercise types (open-ended, problem-solving)
- Student progress tracking
- Adaptive difficulty based on performance

### Phase 2: Add Core Subjects (1 month)
- Lenguaje y Comunicación (Language)
- Ciencias Naturales (Science)
- Historia, Geografía y Ciencias Sociales (History/Social Studies)

### Phase 3: Full Curriculum (2-3 months)
- All 9 subjects
- All 12 grades
- 108 subject-grade combinations complete

### Phase 4: Teacher Features (2-3 months)
- Teacher dashboard
- Classroom exercise generation
- Student progress monitoring
- Custom lesson plans
- Assessment creation tools

### Phase 5: Advanced Features (3-6 months)
- Personalized learning paths
- Predictive difficulty adjustment
- Peer collaboration features
- Parent monitoring dashboard
- Mobile native apps (iOS/Android)
- Offline mode

### Phase 6: National Deployment (6-12 months)
- Official Ministry certification
- Partnership with schools
- Integration with existing education systems
- Pilot programs in selected regions
- Nationwide rollout

### Ultimate Vision (1-2 years)
- Every Chilean student has access
- Free tier for basic features
- Premium tier for schools
- Integration with PSU/PAES prep
- Expansion to neighboring countries
- Multi-language support for indigenous languages

---

## Constraints and Assumptions

### Constraints

**Technical**:
- MVP must be built in < 12 hours
- CloudFlare Workers for adapter layer
- Python FastAPI for core logic
- ElevenLabs for TTS (no alternatives)
- No persistent student database for MVP

**Scope**:
- Single subject: Matemática
- Single grade: 5° Básico
- Single exercise type: Multiple choice
- No user authentication
- No progress tracking

**Resources**:
- CloudFlare account ready to use
- ElevenLabs API access
- Limited API quotas (free tiers)
- Solo developer or small team

### Assumptions

**User Assumptions**:
- Students have internet access
- Students have desktop or mobile device
- Students can read and type in Spanish
- Students familiar with SIMCE format

**Technical Assumptions**:
- CloudFlare services available and reliable
- ElevenLabs TTS API working
- Sufficient API quotas for demo
- Browser supports HTML5 audio

**Content Assumptions**:
- Ministry curriculum standards are public and accessible
- Sample curriculum content can be created manually
- 5-10 OAs sufficient for meaningful demo
- SIMCE format is well-documented

**Business Assumptions**:
- Free tier sufficient for MVP
- Judges value innovation over polish
- Demo scenarios will work reliably
- Social impact is important criterion

---

## Appendix

### Glossary of Chilean Education Terms

**Básica**: Primary/elementary education (1° to 8° Básico)
**Media**: Secondary/high school education (I to IV Medio)
**OA**: Objetivo de Aprendizaje (Learning Objective)
**SIMCE**: Sistema de Medición de la Calidad de la Educación (standardized test)
**PSU/PAES**: University entrance exam
**Mineduc**: Ministerio de Educación (Ministry of Education)
**Bases Curriculares**: Official curriculum framework

### Subject List (All 9)

1. Matemática (Mathematics)
2. Lenguaje y Comunicación (Language and Communication)
3. Ciencias Naturales (Natural Sciences)
4. Historia, Geografía y Ciencias Sociales (History, Geography, Social Studies)
5. Inglés (English)
6. Artes Visuales (Visual Arts)
7. Música (Music)
8. Educación Física y Salud (Physical Education and Health)
9. Tecnología (Technology)

### Grade Levels (All 12)

**Educación Básica** (Primary):
- 1° Básico (6-7 years old)
- 2° Básico (7-8 years old)
- 3° Básico (8-9 years old)
- 4° Básico (9-10 years old)
- 5° Básico (10-11 years old) ← MVP
- 6° Básico (11-12 years old)
- 7° Básico (12-13 years old)
- 8° Básico (13-14 years old)

**Educación Media** (Secondary):
- I Medio (14-15 years old)
- II Medio (15-16 years old)
- III Medio (16-17 years old)
- IV Medio (17-18 years old)

---

**Document Status**: Ready for Implementation
**Last Updated**: October 25, 2025
**Version**: 1.0.0
**Next Steps**: Begin Phase 1 implementation (CloudFlare Worker)
