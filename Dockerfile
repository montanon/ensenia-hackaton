# Ensenia AI Teaching Assistant - Python Backend Dockerfile
# Multi-stage build for optimized production image

# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM python:3.12-slim as builder

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock ./

# Install dependencies using uv
# --no-dev excludes development dependencies for production
RUN uv sync --frozen --no-dev

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 ensenia && \
    mkdir -p /app/cache/audio && \
    chown -R ensenia:ensenia /app

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=ensenia:ensenia /app/.venv /app/.venv

# Copy application code
COPY --chown=ensenia:ensenia app/ /app/app/

# Switch to non-root user
USER ensenia

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.ensenia.main:app", "--host", "0.0.0.0", "--port", "8000"]
