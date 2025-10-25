# AI Teaching Assistant for Chilean Students - Hackathon Project

## Project Overview

This is an AI-powered teaching assistant designed for Chilean students that:
- Follows Chilean Ministry of Education guidelines and content requirements
- Assists students with learning and understanding concepts
- Creates customized exercises and assessments
- Provides voice interaction capabilities for accessibility

### Hackathon Context
- **Time-boxed**: Strict deadline requires MVP-first approach
- **Judging Criteria**: Innovation, Technical Complexity, User Experience, Social Impact
- **Required Technologies**: Cloudflare Deep Research, ElevenLabs Text-to-Speech
- **Delivery Format**: Web application with frontend and backend
- **Keep it simple and concise**
- **If user overcomplicates things, rebate**

## Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (TS/JS)                        │
│  - Student interface                                        │
│  - Audio conversation (ElevenLabs)                          │
│  - Learn, Study, Practice, Evaluation pages                 │
└─────────────────┬───────────────────────────────────────────┘
                  │ REST/WebSocket API with FastAPI
┌─────────────────▼───────────────────────────────────────────┐
│              Python Async Backend                           │
│  - Orchestration layer                                      │
│  - Request handling & routing                               │
│  - Session management                                       │
└─────┬─────────────────┬─────────────────────┬───────────────┘
      │                 │                     │
      ▼                 ▼                     ▼
┌─────────────┐  ┌──────────────┐   ┌────────────────┐
│ Cloudflare  │  │  ElevenLabs  │   │ Chilean Ed.    │
│ Deep        │  │  TTS API     │   │ Content DB     │
│ Research    │  │              │   │ (Ministry      │
│ (REQUIRED)  │  │  (REQUIRED)  │   │  Guidelines)   │
└─────────────┘  └──────────────┘   └────────────────┘
```

### Technology Stack

**Backend (Python)**
- Async framework: FastAPI
- Task orchestration: asyncio 
- Key responsibilities:
  - Coordinate Cloudflare Deep Research queries
  - Generate exercises based on ministry content requirements
    - These should be validate on an Agent-Validator loop to asses quality, pertinence and correctness
  - Manage ElevenLabs TTS requests
    - **The goal is to be able to have an interoperable chat with online TTS**, meaning:
      - The user can just use the Chat interface directly
      - At any moment the agent can toggle TTS and start speaking instead of writing and the agent reponds by speaking (the chats are still logged)
      - The use can also set it such that the user writes, but the agent answers by speaking and vice versa
  - Validate educational content alignment
  - Handle student sessions and progress

**Frontend (TypeScript/JavaScript)**
- Framework: React
- Key responsibilities:
  - Student interaction interface
  - Exercise presentation and submission
  - Learning new subject interface
  - Reviewing learnt subjects interface
  - Evaluate subjects interface
  - Audio playback integration
  - Real-time feedback display
  - Progress visualization

**Required External Services**
- Cloudflare Deep Research (MANDATORY): Research and information retrieval
- ElevenLabs (MANDATORY): Text-to-speech for accessibility and engagement

### Module Structure

```
app/
├── ensenia/
│   ├── api/              # API endpoints
│   ├── orchestration/    # AI agent coordination
│   ├── services/
│   │   ├── cloudflare.py       # Deep Research integration
│   │   ├── elevenlabs.py      # TTS integration
│   │   └── ministry_content.py # Chilean education standards
│   ├── database/           # Data schemas
│   └── utils/            # Shared utilities
│
├── web/
│   ├── src/
│   │   ├── components/       # UI components
│   │   ├── services/         # API clients
│   │   ├── pages/           # Application pages
│   │   └── utils/           # Helpers
│   └── package.json
│
└── docs/                    # Documentation & planning
```

## Implementation Guidelines

### Chilean Ministry of Education Compliance

The assistant MUST:
- Align content with official curriculum standards (Bases Curriculares)
- Follow appropriate content and difficulty levels per grade
- Use Chilean Spanish terminology and examples
- Respect official subject classifications
- Generate exercises that match official assessment formats

**Implementation Note**: Create a content validation layer that checks generated content against ministry requirements before presenting to students with an agent-validator loop.

### AI Agent Orchestration

The teaching assistant should:
1. Use Cloudflare Deep Research to gather accurate, curriculum-aligned information
2. Generate contextual exercises based on student needs
3. Adapt difficulty based on student performance
4. Provide explanations in Chilean Spanish
5. Convert responses to speech using ElevenLabs for accessibility


### Hackathon Time-Boxing Strategy

**MVP Phase (Priority 1 - Required for Demo)**
- Cloudflare Deep Research integration
- ElevenLabs TTS integration
- Basic student query interface
- Simple exercise generation
- One subject area working end-to-end

**Enhancement Phase (Priority 2 - If Time Permits)**
- Multiple subject support
- Student progress tracking
- Adaptive difficulty
- Enhanced UI/UX
- Ministry content validation layer

**Polish Phase (Priority 3 - Final Hours)**
- Demo-ready UI improvements
- Error handling refinement
- Performance optimization
- Presentation materials

### API Integration Best Practices

**Cloudflare Deep Research**
- Implement retry logic with exponential backoff
- Cache research results when appropriate
- Handle rate limits gracefully
- Log all queries for debugging
- Include Chilean education context in prompts

**ElevenLabs TTS**
- Use Chilean Spanish voice models
- Implement audio caching to reduce API calls
- Handle streaming for long responses
- Graceful degradation if service unavailable
- Consider voice selection (student-friendly, clear)

## Judging Criteria Optimization

### Innovation (25%)
- Novel use of Deep Research for education
- Intelligent exercise generation
- Adaptive learning approach
- Voice interaction for accessibility

**Key Points to Highlight**:
- First AI teaching assistant aligned with Chilean curriculum
- Multi-modal learning (text + audio)
- Research-backed content generation

### Technical Complexity (25%)
- Async orchestration of multiple AI services
- Real-time request handling
- Integration of diverse APIs
- Content validation pipeline

**Key Points to Highlight**:
- Sophisticated async architecture
- Multiple AI service orchestration
- Custom curriculum alignment logic

### User Experience (25%)
- Intuitive student interface
- Fast response times
- Accessible design (audio support)
- Clear, helpful feedback

**Key Points to Highlight**:
- Student-first design
- Voice support for different learning styles
- Clean, distraction-free interface

### Social Impact (25%)
- Democratizes access to quality education
- Follows official ministry guidelines
- Supports Chilean students specifically
- Scalable to many students

**Key Points to Highlight**:
- Free AI tutor for all Chilean students
- Official curriculum compliance
- Closes educational gaps
- Language and cultural relevance

## Development Workflow

### Git Workflow
- NEVER sign commits or PRs (as per global config)
- Keep changes atomic when possible

### Code Quality (Time-Permitting)
- Type hints in Python code
- TypeScript strict mode in frontend
- Custom error handling everywhere
- Minimal documentation (comments for complex logic only)

### Testing Strategy (Hackathon Context)
- Manual testing for MVP
- Basic smoke tests for critical paths
- Test external API integrations with mock data
- Focus testing time on demo scenarios

## Critical Success Factors

1. **Both required integrations working** (Cloudflare + ElevenLabs)
2. **At least one subject area fully functional**
3. **Clear alignment with Chilean education standards**
4. **Smooth, impressive demo**
5. **Strong story for all four judging criteria**

## Environment Setup Notes

**Backend Environment Variables through .env files and Pydantic BaseSettings**
```
CLOUDFLARE_API_KEY=xxx
ELEVENLABS_API_KEY=xxx
ENVIRONMENT=hackathon
DEBUG=true
```
- **Modificationd of the BaseSettings should update the .env.sample**

**Frontend Environment Variables**
```
VITE_API_URL=http://localhost:8000
VITE_ENABLE_AUDIO=true
```

---

**Remember**: Speed and working demo > perfect code. Focus on the required integrations and one working end-to-end flow. Polish only after core functionality works.
