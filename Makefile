# Ensenia - Development Makefile
# Manages both Python (uv) and TypeScript (npm) dependencies

.PHONY: help install dev test clean setup

# Default target
help:
	@echo "Ensenia Development Commands"
	@echo "============================"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install      - Install all dependencies (Python + Worker)"
	@echo "  make setup        - Full setup (install + CloudFlare setup)"
	@echo ""
	@echo "Development:"
	@echo "  make dev-python   - Run Python backend (FastAPI)"
	@echo "  make dev-worker   - Run CloudFlare Worker (local)"
	@echo "  make dev-web      - Run React frontend (when ready)"
	@echo ""
	@echo "Docker (Recommended for Hackathon):"
	@echo "  make docker-build    - Build Docker images"
	@echo "  make docker-up       - Start containers (detached)"
	@echo "  make docker-down     - Stop containers"
	@echo "  make docker-stack    - Build + start full stack"
	@echo "  make docker-logs     - Show all container logs"
	@echo "  make docker-restart  - Restart containers"
	@echo "  make docker-clean    - Clean all Docker resources"
	@echo "  make deploy-all      - Deploy Worker + start Docker stack"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests"
	@echo "  make test-python  - Run Python tests"
	@echo "  make test-worker  - Run Worker tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint         - Lint all code"
	@echo "  make format       - Format all code"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy-worker - Deploy Worker to CloudFlare"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        - Remove all dependencies"
	@echo ""

# ============================================================================
# Installation
# ============================================================================

install: install-python install-worker
	@echo "✅ All dependencies installed!"

install-python:
	@echo "🐍 Installing Python dependencies..."
	uv sync

install-worker:
	@echo "📦 Installing Worker dependencies..."
	cd app/worker && npm install

install-web:
	@echo "⚛️  Installing Web dependencies..."
	cd app/web && npm install

# ============================================================================
# Development
# ============================================================================

dev-python:
	@echo "🚀 Starting Python backend..."
	uv run uvicorn app.ensenia.main:app --reload --host 0.0.0.0 --port 8000

dev-worker:
	@echo "⚡ Starting CloudFlare Worker..."
	cd app/worker && npm run dev

dev-web:
	@echo "⚛️  Starting React frontend..."
	cd app/web && npm run dev

# ============================================================================
# Testing
# ============================================================================

test: test-python test-worker
	@echo "✅ All tests passed!"

test-python:
	@echo "🧪 Running Python tests..."
	uv run pytest

test-worker:
	@echo "🧪 Running Worker tests..."
	cd app/worker && npm test

# ============================================================================
# Code Quality
# ============================================================================

lint: lint-python
	@echo "✅ Linting complete!"

lint-python:
	@echo "🔍 Linting Python code..."
	uv run ruff check .

format: format-python
	@echo "✅ Formatting complete!"

format-python:
	@echo "✨ Formatting Python code..."
	uv run ruff format .

# ============================================================================
# Deployment
# ============================================================================

deploy-worker:
	@echo "🚀 Deploying Worker to CloudFlare..."
	cd app/worker && npm run deploy

# ============================================================================
# Setup
# ============================================================================

setup: install
	@echo "⚙️  Running CloudFlare setup..."
	cd app/worker/scripts && ./setup.sh
	@echo "✅ Setup complete!"

# ============================================================================
# Cleanup
# ============================================================================

clean: clean-python clean-worker
	@echo "✅ Cleanup complete!"

clean-python:
	@echo "🧹 Cleaning Python dependencies..."
	rm -rf .venv uv.lock

clean-worker:
	@echo "🧹 Cleaning Worker dependencies..."
	cd app/worker && rm -rf node_modules package-lock.json

clean-web:
	@echo "🧹 Cleaning Web dependencies..."
	cd app/web && rm -rf node_modules package-lock.json

# ============================================================================
# Database
# ============================================================================

seed-db:
	@echo "🌱 Seeding database..."
	cd app/worker/scripts && wrangler d1 execute ensenia-curriculum --file=./schema.sql
	cd app/worker/scripts && wrangler d1 execute ensenia-curriculum --file=./sample-data.sql

seed-vectorize:
	@echo "🔍 Seeding Vectorize index..."
	curl -X POST "http://localhost:8787/seed?action=populate"

# ============================================================================
# Docker Commands
# ============================================================================

docker-build:
	@echo "🐳 Building Docker images..."
	docker-compose build

docker-up:
	@echo "🐳 Starting containers..."
	docker-compose up -d
	@echo "✅ Containers started!"
	@echo "   Backend: http://localhost:8000"
	@echo "   PostgreSQL: localhost:5433"

docker-down:
	@echo "🐳 Stopping containers..."
	docker-compose down

docker-logs:
	@echo "📜 Showing container logs..."
	docker-compose logs -f

docker-logs-backend:
	@echo "📜 Showing backend logs..."
	docker-compose logs -f backend

docker-restart:
	@echo "🔄 Restarting containers..."
	docker-compose restart

docker-clean:
	@echo "🧹 Cleaning Docker resources..."
	docker-compose down -v
	docker system prune -f

docker-shell:
	@echo "🐚 Opening shell in backend container..."
	docker-compose exec backend /bin/bash

# Full stack (build + up)
docker-stack: docker-build docker-up
	@echo "✅ Full stack is running!"

# Development with live reload (mounts code)
docker-dev:
	@echo "🔧 Starting development stack with live reload..."
	@echo "   Uncomment volume mount in docker-compose.yml first!"
	docker-compose up

# Integration deployment (Worker + Backend)
deploy-all: deploy-worker docker-stack
	@echo "🚀 Full deployment complete!"
	@echo "   Worker: Check wrangler output for URL"
	@echo "   Backend: http://localhost:8000"
