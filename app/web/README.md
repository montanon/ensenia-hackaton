# Ensenia - Frontend

AI Teaching Assistant for Chilean Students - Frontend Application

## Tech Stack

- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS v3
- **State Management:** Zustand
- **UI Components:** Headless UI
- **HTTP Client:** Axios
- **WebSocket:** Native WebSocket API
- **Speech:** Web Speech API (STT)

## Features

### ✅ Implemented

- **Session Management:** Create sessions with grade, subject, and learning mode
- **Real-Time Chat:** WebSocket-based streaming text conversation
- **Voice I/O:**
  - Text-to-Speech (TTS) auto-play from backend (ElevenLabs)
  - Speech-to-Text (STT) voice input (Web Speech API - Chilean Spanish)
  - Hot-swappable modes (Text ↔️ Voice)
- **Exercise System:**
  - Multiple choice questions
  - True/False questions
  - Short answer questions
  - Real-time feedback
- **Learning Modes:**
  - Learn (explanations)
  - Practice (exercises)
  - Study (review)
  - Evaluation (assessment)

## Setup

### Prerequisites

- Node.js 18+
- Backend API running at `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Create environment file
cp .env.sample .env

# Start development server
npm run dev

# Build for production
npm run build
```

### Environment Variables

Create `.env` file with:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Project Structure

```
src/
├── components/
│   ├── layout/          # AppLayout, Sidebar
│   ├── chat/            # ChatTab, MessageList, Message, ChatInput, VoiceButton
│   ├── exercises/       # ExerciseCard, MultipleChoice, TrueFalse, ShortAnswer
│   ├── session/         # NewSessionDialog
│   └── ui/              # Button, Input (reusable components)
├── services/
│   ├── api.ts           # REST API client (Axios)
│   ├── websocket.ts     # WebSocket service
│   └── speech.ts        # Web Speech API wrapper
├── stores/
│   ├── sessionStore.ts  # Current session, mode, I/O preferences
│   ├── chatStore.ts     # Messages, streaming state
│   ├── audioStore.ts    # Audio playback state
│   └── exerciseStore.ts # Current exercise state
├── types/               # TypeScript type definitions
└── utils/               # Constants, helpers
```

## Usage

### 1. Create a Session

1. Click "Nueva Sesión" in sidebar
2. Select:
   - Grade (1-12)
   - Subject (Matemáticas, Lenguaje, etc.)
   - Mode (Learn/Practice/Study/Evaluation)
   - Optional: Topic for research
3. Click "Crear Sesión"

### 2. Chat Interaction

**Text Mode:**
- Type message and press Enter
- AI responds with streaming text
- If audio output enabled, responses are spoken automatically

**Voice Mode:**
- Click input mode toggle to switch to voice
- Hold "🎤" button to speak
- Release when finished
- Transcription sent automatically

### 3. Generate Exercises (Practice Mode)

1. Switch to Practice mode in sidebar
2. Click "Generar Ejercicio"
3. Answer the question
4. Submit for feedback

### 4. Mode Switching

Change learning mode anytime:
- **Learn:** Step-by-step explanations
- **Practice:** Exercises with feedback
- **Study:** Review sessions
- **Evaluation:** Knowledge assessment

## API Integration

### Backend Endpoints Used

**Sessions:**
- `POST /chat/sessions` - Create new session
- `GET /chat/sessions/{id}` - Get session details

**WebSocket:**
- `WS /ws/chat/{session_id}` - Real-time chat
- Messages: `text_chunk`, `audio_ready`, `message_complete`

**Exercises:**
- `POST /exercises/generate` - Generate exercise (agent-validator loop)
- `POST /exercises/{id}/sessions/{session_id}` - Assign to session
- `POST /exercises/sessions/{id}/submit` - Submit answer

**TTS:**
- `/audio/{audio_id}.mp3` - Cached audio files

## Browser Compatibility

- **Voice Input (STT):** Chrome/Edge (WebKit Speech API)
- **Voice Output (TTS):** All modern browsers
- **WebSocket:** All modern browsers

## Development

```bash
npm run dev      # Start dev server (http://localhost:5173)
npm run build    # Production build
npm run preview  # Preview production build
```

## Demo Script

1. **Create Session:** Grade 5, Matemáticas, Learn mode
2. **Ask Question:** "Explica qué son las fracciones"
3. **Toggle Audio:** Switch output to voice mode
4. **Listen:** AI speaks response in Chilean Spanish
5. **Switch Mode:** Change to Practice mode
6. **Generate Exercise:** Click generate exercise button
7. **Answer:** Select option and submit
8. **Voice Input:** Toggle to voice input mode
9. **Speak:** "Dame otro ejemplo"
10. **Show Modes:** Demonstrate all 4 modes

## Troubleshooting

**WebSocket won't connect:**
- Ensure backend is running at port 8000
- Check VITE_WS_URL in .env

**Voice input not working:**
- Use Chrome/Edge browser
- Grant microphone permissions

**Audio won't play:**
- Check browser audio permissions
- Verify backend TTS service is running
