# 🎓 Ensenia - AI Teaching Assistant for Chilean Students

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Ensenia** is an AI-powered teaching assistant specifically designed for Chilean students, aligned with the Ministry of Education's curriculum standards (Bases Curriculares). It provides personalized learning experiences through intelligent conversation, adaptive exercises, and voice interaction.

## ✨ Features

### 🤖 Intelligent Teaching Modes
- **Learn Mode**: Step-by-step concept explanations with Chilean context
- **Practice Mode**: Adaptive exercise generation with instant feedback
- **Study Mode**: Structured review sessions and knowledge reinforcement
- **Evaluation Mode**: Fair assessment with constructive feedback

### 🎯 Curriculum-Aligned Content
- **Ministry Standards**: Fully aligned with Chilean Bases Curriculares
- **Grade-Specific**: Tailored content for grades 1-12
- **Subject Coverage**: Mathematics, Language, Sciences, History, and more
- **Deep Research**: Powered by Cloudflare's semantic search over curriculum documents

### 🎙️ Voice Interaction
- **Text-to-Speech**: Natural Chilean Spanish voice powered by ElevenLabs
- **Grade-Adaptive**: Speech pace and complexity adjust by grade level
- **Real-time Streaming**: Instant audio playback with WebSocket support
- **Smart Caching**: Reduces API costs and improves response times

### 📝 Advanced Exercise Generation
- **AI-Powered**: Uses LangGraph agent-validator loop for quality assurance
- **Multiple Types**: Multiple choice, true/false, short answer, and essays
- **Iterative Refinement**: Automatically improves exercises until quality threshold is met
- **Validation Scores**: Each exercise rated 0-10 for curriculum alignment and pedagogy

### 🔄 Real-Time Chat
- **WebSocket Support**: Instant message delivery and streaming responses
- **Context Awareness**: Maintains conversation history and research context
- **Mode Switching**: Seamlessly toggle between text and audio output
- **Session Management**: Persistent conversations with full history

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (React + TypeScript)              │
│   - Student interface                                        │
│   - Audio player                                             │
│   - Exercise components                                      │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API / WebSocket
┌────────────────────▼────────────────────────────────────────┐
│              Python FastAPI Backend                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API Routes                                           │   │
│  │  - Chat, TTS, Exercises, WebSocket                   │   │
│  └────────────────┬─────────────────────────────────────┘   │
│  ┌────────────────▼─────────────────────────────────────┐   │
│  │  Services                                             │   │
│  │  - ChatService (OpenAI)                              │   │
│  │  - GenerationService (LangGraph)                     │   │
│  │  - ElevenLabsService (TTS)                           │   │
│  │  - ResearchService (Cloudflare Worker)               │   │
│  │  - WebSocketManager                                   │   │
│  └────────────────┬─────────────────────────────────────┘   │
│  ┌────────────────▼─────────────────────────────────────┐   │
│  │  Database (PostgreSQL)                                │   │
│  │  - Sessions, Messages, Exercises                      │   │
│  └───────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP REST
┌────────────────────▼────────────────────────────────────────┐
│         Cloudflare Worker (TypeScript)                       │
│  - Semantic Search (Vectorize + Workers AI)                  │
│  - Content Generation (Llama 3.1)                            │
│  - Ministry Validation                                       │
│  - D1 Database (Curriculum Storage)                          │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

**Backend:**
- **FastAPI**: Async Python web framework
- **SQLAlchemy**: Async ORM for PostgreSQL
- **LangGraph**: State machine for exercise generation workflow
- **LangChain**: OpenAI integration
- **Pydantic**: Data validation and settings management
- **ElevenLabs**: Text-to-speech API
- **httpx**: Async HTTP client

**Cloudflare Worker:**
- **TypeScript**: Type-safe worker implementation
- **Workers AI**: Embeddings and text generation
- **Vectorize**: Vector database for semantic search
- **D1**: SQLite database for curriculum content
- **KV**: Response caching

**Database:**
- **PostgreSQL**: Primary data store
- **Alembic**: Database migrations

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 15+
- Cloudflare account (free tier works)
- OpenAI API key
- ElevenLabs API key

### 1. Clone the Repository

```bash
git clone https://github.com/montanon/ensenia-hackaton.git
cd ensenia-hackaton
```

### 2. Backend Setup

```bash
# Install Python dependencies using uv (recommended)
brew install uv
uv sync

# Copy environment template
cp .env.sample .env

# Edit .env with your API keys
# Required:
#   - OPENAI_API_KEY
#   - ELEVENLABS_API_KEY
#   - CLOUDFLARE_API_TOKEN
#   - CLOUDFLARE_ACCOUNT_ID
#   - ...
```

### 3. Database Setup

```bash
# Start PostgreSQL (using Docker)
docker-compose up -d postgres

# Run migrations
alembic upgrade head

# Verify database
psql postgresql://ensenia:hackathon@localhost:5433/ensenia -c "\dt"
```

### 4. Cloudflare Worker Setup

```bash
cd app/worker

# Install dependencies
npm install

# Configure Cloudflare (edit wrangler.toml with your account ID)
# Create D1 database
wrangler d1 create ensenia-hackaton-d1

# Create Vectorize index
wrangler vectorize create ai-search-basic-rag \
  --dimensions=1024 \
  --metric=cosine

# Create KV namespace
wrangler kv:namespace create SEARCH_CACHE

# Initialize database schema
wrangler d1 execute ensenia-hackaton-d1 --file=scripts/schema.sql --local

# Start worker (development)
npm run dev
```

### 5. Load Curriculum Data

```bash
# Process PDF files and populate Vectorize
# (This endpoint is available once the worker is running)
curl -X POST http://localhost:8787/admin/populate-vectorize \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_directory": "./data",
    "batch_size": 50
  }'
```

### 6. Start the Backend

```bash
# From project root
uvicorn app.ensenia.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Access the API

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Cloudflare Worker**: http://localhost:8787
- **Worker Health**: http://localhost:8787/health

## 📚 Usage Examples

### Create a Chat Session

```bash
curl -X POST http://localhost:8000/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "grade": 5,
    "subject": "Matemática",
    "mode": "learn",
    "topic": "fracciones"
  }'
```

### Send a Message

```bash
curl -X POST http://localhost:8000/chat/sessions/1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Cómo sumo fracciones con diferente denominador?"
  }'
```

### Generate an Exercise

```bash
curl -X POST http://localhost:8000/exercises/generate \
  -H "Content-Type: application/json" \
  -d '{
    "exercise_type": "multiple_choice",
    "grade": 5,
    "subject": "Matemática",
    "topic": "Suma de fracciones",
    "difficulty_level": 3,
    "max_iterations": 3,
    "quality_threshold": 8
  }'
```

### Generate Text-to-Speech

```bash
curl "http://localhost:8000/tts/speak?text=Hola%20estudiante&grade=5" \
  --output audio.mp3
```

### WebSocket Chat (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat/1');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'text_chunk':
      console.log('Text:', data.content);
      break;
    case 'audio_chunk':
      // Play audio chunk
      playAudio(data.audio_data);
      break;
    case 'complete':
      console.log('Message complete');
      break;
  }
};

// Send a message
ws.send(JSON.stringify({
  type: 'user_message',
  content: '¿Qué son las fracciones?'
}));

// Toggle to audio mode
ws.send(JSON.stringify({
  type: 'set_mode',
  mode: 'audio'
}));
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_chat_service.py

# Run integration tests
pytest tests/integration/

# Cloudflare Worker tests
cd app/worker
npm test
```

## 📖 API Documentation

### Backend Endpoints

#### Chat API
- `POST /chat/sessions` - Create new chat session
- `POST /chat/sessions/{id}/messages` - Send message
- `GET /chat/sessions/{id}` - Get session details
- `POST /chat/sessions/{id}/research` - Trigger curriculum research
- `PATCH /chat/sessions/{id}/mode` - Update output mode (text/audio)

#### Exercise API
- `POST /exercises/generate` - Generate new exercise with validation
- `POST /exercises/search` - Search existing exercises
- `GET /exercises/{id}` - Get specific exercise
- `POST /exercises/{id}/sessions/{session_id}` - Link exercise to session
- `POST /exercises/sessions/{exercise_session_id}/submit` - Submit answer
- `GET /exercises/sessions/{session_id}/exercises` - Get session exercises

#### TTS API
- `GET /tts/speak` - Simple text-to-speech (returns audio)
- `POST /tts/generate` - Advanced TTS with options
- `GET /tts/stream` - Streaming audio generation
- `POST /tts/batch` - Generate multiple audio segments

#### WebSocket API
- `WS /ws/chat/{session_id}` - Real-time chat with streaming

### Cloudflare Worker Endpoints

- `POST /search` - Semantic curriculum search
- `POST /fetch` - Fetch curriculum content by IDs
- `POST /generate` - Generate Chilean-context explanations
- `POST /validate` - Validate content against ministry standards
- `POST /admin/populate-vectorize` - Populate vector database

Full API documentation available at `/docs` when running the server.

## 🔧 Configuration

### Environment Variables

All configuration is managed through environment variables. See `.env.sample` for a complete list with descriptions.

**Key Settings:**

```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview

# ElevenLabs
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB  # Dorothy (Chilean Spanish)

# Cloudflare
CLOUDFLARE_API_TOKEN=...
CLOUDFLARE_ACCOUNT_ID=...
CLOUDFLARE_WORKER_URL=http://localhost:8787

# Database
DATABASE_URL=postgresql+asyncpg://ensenia:hackathon@localhost:5433/ensenia

# Exercise Generation
GENERATION_MAX_ITERATIONS=3
GENERATION_QUALITY_THRESHOLD=8
```

### Voice Settings by Grade

The system automatically adjusts speech characteristics based on grade level:

| Grade | Speed | Stability | Style |
|-------|-------|-----------|-------|
| 1-4 (Elementary) | 0.85x | 0.70 | Simple |
| 5-8 (Middle) | 0.95x | 0.65 | Balanced |
| 9-12 (High) | 1.00x | 0.60 | Natural |

## 🎯 Exercise Generation Workflow

The system uses a sophisticated LangGraph-based agent-validator loop:

```
┌──────────────┐
│   Request    │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Generator Agent  │  ◄─┐
│ (OpenAI GPT-4)   │    │
└──────┬───────────┘    │
       │                │ Refine
       ▼                │
┌──────────────────┐    │
│ Validator Agent  │    │
│ (Quality Check)  │    │
└──────┬───────────┘    │
       │                │
       ▼                │
   Score ≥ 8? ──No─────┘
       │
      Yes
       ▼
┌──────────────────┐
│  Save Exercise   │
└──────────────────┘
```

**Quality Criteria (0-10 points):**
- Curriculum alignment (2 pts)
- Grade appropriateness (2 pts)
- Difficulty match (2 pts)
- Pedagogical quality (2 pts)
- Chilean Spanish correctness (2 pts)

## 📂 Project Structure

```
ensenia-hackaton/
├── app/
│   ├── ensenia/                  # Python backend
│   │   ├── api/                  # FastAPI routes
│   │   │   └── routes/           # Chat, TTS, Exercise, WebSocket
│   │   ├── services/             # Business logic
│   │   │   ├── cloudflare/       # Cloudflare service clients
│   │   │   ├── chat_service.py
│   │   │   ├── generation_service.py
│   │   │   ├── elevenlabs_service.py
│   │   │   └── research_service.py
│   │   ├── database/             # SQLAlchemy models
│   │   ├── models/               # Pydantic models
│   │   ├── schemas/              # API schemas
│   │   └── main.py               # FastAPI app
│   ├── worker/                   # Cloudflare Worker
│   │   ├── src/
│   │   │   ├── routes/           # Search, Fetch, Generate, Validate
│   │   │   ├── types/            # TypeScript types
│   │   │   └── index.ts          # Worker entry point
│   │   └── scripts/              # Database setup scripts
│   └── web/                      # Frontend (TBD)
├── data/                         # Chilean curriculum PDFs
├── tests/                        # Test suite
├── alembic/                      # Database migrations
├── pyproject.toml                # Python dependencies
├── .env.sample                   # Environment template
└── README.md
```

## 🤝 Contributing

Contributions are welcome! This project was created for a hackathon but is being developed as a production-ready open-source tool.

### Development Setup

```bash
# Install development dependencies
uv sync --dev

# Run linting
ruff check .

# Format code
ruff format .

# Type checking
mypy app/

# Run tests
pytest
```

### Code Standards

- **Python**: Follow PEP 8, use type hints, document with docstrings
- **TypeScript**: Strict mode enabled, use explicit types
- **Testing**: Aim for >80% coverage on critical paths
- **Commits**: Use conventional commits (feat:, fix:, docs:, etc.)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Chilean Ministry of Education** for providing open curriculum documents
- **Cloudflare** for Workers AI, Vectorize, and D1 database
- **ElevenLabs** for high-quality Spanish text-to-speech
- **OpenAI** for GPT-4 and language understanding
- **LangChain/LangGraph** for agent orchestration framework

## 📞 Support

- **Documentation**: See `/docs` API endpoint when server is running
- **Issues**: Please open an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions

## 🗺️ Roadmap

- [ ] Complete frontend React application
- [ ] Multi-subject support (currently Math-focused)
- [ ] Student progress analytics
- [ ] Teacher dashboard
- [ ] Mobile app (React Native)
- [ ] Voice input (speech-to-text)
- [ ] Deployment guides (Docker, Kubernetes)
- [ ] Performance optimization
- [ ] Multi-language support (Mapudungun, English)

## 🌟 Star History

If you find this project useful, please consider giving it a star ⭐

---

**Built with ❤️ for Chilean students**
