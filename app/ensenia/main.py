"""Main FastAPI application for Chilean Education TTS API.

Integrates:
- ElevenLabs TTS routes
- CORS configuration
- Static file serving for cached audio
- Logging configuration
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.ensenia.api.routes import chat, exercises, tts, websocket
from app.ensenia.core.config import settings
from app.ensenia.database.session import close_db, init_db
from app.ensenia.services.research_service import cleanup_research_service

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan for the FastAPI application."""
    logger.info("Starting up...")
    await init_db()
    logger.info("Startup complete")
    yield
    logger.info("Shutting down...")
    await cleanup_research_service()
    await close_db()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Chilean Education AI Assistant API",
    description=(
        "AI-powered teaching assistant for Chilean students "
        "with TTS and chat capabilities"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tts.router)
app.include_router(chat.router)
app.include_router(websocket.router)  # WebSocket routes for real-time chat
app.include_router(exercises.router)  # Exercise generation and management routes

# Mount static files for cached audio
cache_path = Path(settings.cache_dir)
if cache_path.exists():
    app.mount("/audio", StaticFiles(directory=str(cache_path)), name="audio")
    logger.info("Mounted audio cache at /audio")


@app.get("/")
def root() -> dict[str, Any]:
    """Root endpoint with API information."""
    return {
        "message": "Chilean Education AI Assistant API",
        "version": "1.0.0",
        "status": "running",
        "voice": "Dorothy (Chilean Spanish)",
        "endpoints": {
            "tts": {
                "simple": "GET /tts/speak?text=Hola&grade=5",
                "advanced": "POST /tts/generate",
                "streaming": "GET /tts/stream?text=Hola&grade=5",
                "batch": "POST /tts/batch",
                "health": "GET /tts/health",
            },
            "chat": {
                "create_session": "POST /chat/sessions",
                "send_message": "POST /chat/sessions/{id}/messages",
                "get_session": "GET /chat/sessions/{id}",
                "trigger_research": "POST /chat/sessions/{id}/research",
                "update_mode": "PATCH /chat/sessions/{id}/mode",
                "health": "GET /chat/health",
            },
            "websocket": {
                "chat": "WS /ws/chat/{session_id}",
            },
            "exercises": {
                "generate": "POST /exercises/generate",
                "search": "POST /exercises/search",
                "get": "GET /exercises/{id}",
                "link_to_session": "POST /exercises/{id}/sessions/{session_id}",
                "submit_answer": (
                    "POST /exercises/sessions/{exercise_session_id}/submit"
                ),
                "get_session_exercises": (
                    "GET /exercises/sessions/{session_id}/exercises"
                ),
            },
            "docs": "GET /docs",
        },
    }


@app.get("/health")
def health_check() -> dict[str, Any]:
    """Application health check."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "cache_dir": settings.cache_dir,
        "voice_id": settings.elevenlabs_voice_id,
        "model": settings.elevenlabs_model_id,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.ensenia.main:app",
        host="0.0.0.0",  # noqa: S104 - Binding to all interfaces for development
        port=8000,
        reload=settings.environment == "development",
    )
