"""Main FastAPI application for Chilean Education TTS API.

Integrates:
- ElevenLabs TTS routes
- CORS configuration
- Static file serving for cached audio
- Logging configuration
"""

import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.ensenia.api.routes import tts
from app.ensenia.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Chilean Education TTS API",
    description="Text-to-Speech API for Chilean educational content using ElevenLabs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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

# Mount static files for cached audio
cache_path = Path(settings.cache_dir)
if cache_path.exists():
    app.mount("/audio", StaticFiles(directory=str(cache_path)), name="audio")
    logger.info("Mounted audio cache at /audio")


@app.get("/")
def root() -> dict[str, Any]:
    """Root endpoint with API information."""
    return {
        "message": "Chilean Education TTS API",
        "version": "1.0.0",
        "status": "running",
        "voice": "Dorothy (Chilean Spanish)",
        "endpoints": {
            "simple_tts": "GET /tts/speak?text=Hola&grade=5",
            "advanced_tts": "POST /tts/generate",
            "streaming": "GET /tts/stream?text=Hola&grade=5",
            "batch": "POST /tts/batch",
            "health": "GET /tts/health",
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
