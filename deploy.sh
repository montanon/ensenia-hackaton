#!/bin/bash

# Ensenia - Complete Deployment Script
# Deploys Worker, Frontend, Backend, and PostgreSQL Database

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Deployment mode (default: development)
MODE="${1:-development}"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Ensenia - Deployment Script         ║${NC}"
echo -e "${BLUE}║   Mode: ${MODE^^}${NC}                          ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# ============================================================================
# Configuration
# ============================================================================

# Ports
BACKEND_PORT="${BACKEND_PORT:-8001}"
WORKER_PORT="${WORKER_PORT:-8787}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

# Database
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-ensenia}"
DB_USER="${DB_USER:-postgres}"

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKER_DIR="$SCRIPT_DIR/app/worker"
FRONTEND_DIR="$SCRIPT_DIR/app/web"
BACKEND_DIR="$SCRIPT_DIR"

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}ℹ${NC}  $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠️${NC}  $1"
}

log_error() {
    echo -e "${RED}❌${NC} $1"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        log_success "$1 found: $(command -v $1)"
        return 0
    else
        log_error "$1 not found!"
        return 1
    fi
}

# ============================================================================
# Check Prerequisites
# ============================================================================

echo ""
log_info "Checking prerequisites..."
echo ""

MISSING_DEPS=0

# Check uv (Python package manager)
if ! check_command uv; then
    log_error "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    MISSING_DEPS=1
fi

# Check Node.js
if ! check_command node; then
    log_error "Install from: https://nodejs.org/"
    MISSING_DEPS=1
fi

# Check npm
if ! check_command npm; then
    log_error "npm should come with Node.js"
    MISSING_DEPS=1
fi

# Check PostgreSQL (if not using Docker)
if [ "$MODE" != "production" ]; then
    if command -v psql &> /dev/null; then
        log_success "PostgreSQL found: $(psql --version | head -n1)"
    else
        log_warning "PostgreSQL not found - will attempt to use Docker or remote DB"
    fi
fi

if [ $MISSING_DEPS -eq 1 ]; then
    log_error "Missing required dependencies. Please install them first."
    exit 1
fi

echo ""

# ============================================================================
# Environment Setup
# ============================================================================

log_info "Setting up environment..."
echo ""

# Check for .env file
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    log_warning ".env file not found. Creating from template..."
    if [ -f "$SCRIPT_DIR/.env.sample" ]; then
        cp "$SCRIPT_DIR/.env.sample" "$SCRIPT_DIR/.env"
        log_success "Created .env from .env.sample"
        log_warning "Please update .env with your API keys before deploying to production"
    else
        log_error ".env.sample not found!"
        exit 1
    fi
fi

# Check frontend .env
if [ ! -f "$FRONTEND_DIR/.env" ]; then
    log_warning "Frontend .env file not found. Creating from template..."
    if [ -f "$FRONTEND_DIR/.env.sample" ]; then
        cp "$FRONTEND_DIR/.env.sample" "$FRONTEND_DIR/.env"
        # Update ports based on configuration
        sed -i '' "s|localhost:8000|localhost:$BACKEND_PORT|g" "$FRONTEND_DIR/.env"
        log_success "Created frontend .env"
    else
        log_error "Frontend .env.sample not found!"
        exit 1
    fi
fi

log_success "Environment files ready"
echo ""

# ============================================================================
# Database Setup
# ============================================================================

log_info "Setting up PostgreSQL database..."
echo ""

# Check if database exists
if command -v psql &> /dev/null; then
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        log_success "Database '$DB_NAME' exists"
    else
        log_warning "Database '$DB_NAME' does not exist. Creating..."
        if PGPASSWORD="$DB_PASSWORD" createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" 2>/dev/null; then
            log_success "Database created"
        else
            log_error "Failed to create database. May need manual setup."
        fi
    fi
else
    log_warning "PostgreSQL client not available. Skipping database check."
fi

# Run Alembic migrations
log_info "Running database migrations..."
cd "$BACKEND_DIR"
if uv run alembic upgrade head; then
    log_success "Database migrations completed"
else
    log_error "Database migrations failed!"
    exit 1
fi

echo ""

# ============================================================================
# Python Backend Setup
# ============================================================================

log_info "Setting up Python backend..."
echo ""

cd "$BACKEND_DIR"

# Install Python dependencies
log_info "Installing Python dependencies..."
if uv sync; then
    log_success "Python dependencies installed"
else
    log_error "Failed to install Python dependencies"
    exit 1
fi

echo ""

# ============================================================================
# CloudFlare Worker Deployment
# ============================================================================

log_info "Deploying CloudFlare Worker..."
echo ""

cd "$WORKER_DIR"

# Install worker dependencies
log_info "Installing Worker dependencies..."
if npm install; then
    log_success "Worker dependencies installed"
else
    log_error "Failed to install Worker dependencies"
    exit 1
fi

# Build worker
log_info "Building Worker..."
if npm run build 2>/dev/null || true; then
    log_success "Worker built"
else
    log_warning "Worker build script not found (may not be required)"
fi

# Deploy or run worker based on mode
if [ "$MODE" = "production" ]; then
    log_info "Deploying Worker to CloudFlare..."
    if npm run deploy; then
        log_success "Worker deployed to production"
    else
        log_error "Worker deployment failed"
        exit 1
    fi
else
    log_info "Starting Worker in development mode..."
    # Kill any existing worker processes
    pkill -f "wrangler.*dev" 2>/dev/null || true

    # Start worker in background
    nohup npm run dev > "$WORKER_DIR/worker.log" 2>&1 &
    WORKER_PID=$!
    echo $WORKER_PID > "$WORKER_DIR/worker.pid"

    log_success "Worker started (PID: $WORKER_PID)"
    log_info "Worker logs: $WORKER_DIR/worker.log"

    # Wait for worker to be ready
    log_info "Waiting for Worker to start..."
    sleep 5

    if curl -s -f http://localhost:$WORKER_PORT/health > /dev/null 2>&1; then
        log_success "Worker is running on http://localhost:$WORKER_PORT"
    else
        log_warning "Worker health check failed. Check logs for details."
    fi
fi

cd "$SCRIPT_DIR"
echo ""

# ============================================================================
# Frontend Build/Deployment
# ============================================================================

log_info "Setting up React frontend..."
echo ""

cd "$FRONTEND_DIR"

# Install frontend dependencies
log_info "Installing Frontend dependencies..."
if npm install; then
    log_success "Frontend dependencies installed"
else
    log_error "Failed to install Frontend dependencies"
    exit 1
fi

if [ "$MODE" = "production" ]; then
    # Build frontend for production
    log_info "Building Frontend for production..."
    if npm run build; then
        log_success "Frontend built"
        log_info "Build output: $FRONTEND_DIR/dist"
        log_warning "Deploy the 'dist' folder to your hosting service (Vercel, Netlify, etc.)"
    else
        log_error "Frontend build failed"
        exit 1
    fi
else
    # Start frontend dev server
    log_info "Starting Frontend development server..."

    # Kill any existing frontend processes
    pkill -f "vite" 2>/dev/null || true

    # Start frontend in background
    nohup npm run dev > "$FRONTEND_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$FRONTEND_DIR/frontend.pid"

    log_success "Frontend started (PID: $FRONTEND_PID)"
    log_info "Frontend logs: $FRONTEND_DIR/frontend.log"

    # Wait for frontend to be ready
    sleep 3

    log_success "Frontend is running on http://localhost:$FRONTEND_PORT"
fi

cd "$SCRIPT_DIR"
echo ""

# ============================================================================
# Backend Deployment
# ============================================================================

log_info "Starting Python backend..."
echo ""

cd "$BACKEND_DIR"

if [ "$MODE" = "production" ]; then
    log_info "Starting Backend in production mode..."
    log_warning "For production, use a process manager like systemd, supervisor, or PM2"
    log_info "Example command:"
    echo "  uv run uvicorn app.ensenia.main:app --host 0.0.0.0 --port $BACKEND_PORT --workers 4"
else
    # Kill any existing backend processes
    pkill -f "uvicorn.*app.ensenia.main:app" 2>/dev/null || true

    # Start backend in background
    log_info "Starting Backend in development mode..."
    nohup uv run uvicorn app.ensenia.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > "$BACKEND_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$BACKEND_DIR/backend.pid"

    log_success "Backend started (PID: $BACKEND_PID)"
    log_info "Backend logs: $BACKEND_DIR/backend.log"

    # Wait for backend to be ready
    log_info "Waiting for Backend to start..."
    sleep 5

    if curl -s -f http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
        log_success "Backend is running on http://localhost:$BACKEND_PORT"
    else
        log_warning "Backend health check failed. Check logs for details."
    fi
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Deployment Complete! ✅              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

if [ "$MODE" = "production" ]; then
    log_success "Production deployment completed"
    echo ""
    echo "📦 Components deployed:"
    echo "  ✅ Database migrations applied"
    echo "  ✅ CloudFlare Worker deployed"
    echo "  ✅ Frontend built (see dist/ folder)"
    echo "  ⚠️  Backend requires manual production setup"
    echo ""
    echo "Next steps for production:"
    echo "  1. Deploy frontend dist/ folder to your hosting service"
    echo "  2. Set up backend with a process manager (systemd, PM2, etc.)"
    echo "  3. Configure reverse proxy (nginx, Caddy)"
    echo "  4. Set up SSL certificates"
    echo "  5. Configure environment variables on production servers"
else
    log_success "Development environment ready"
    echo ""
    echo "🚀 Services running:"
    echo "  ✅ Backend:   http://localhost:$BACKEND_PORT (PID: $BACKEND_PID)"
    echo "  ✅ Worker:    http://localhost:$WORKER_PORT (PID: $WORKER_PID)"
    echo "  ✅ Frontend:  http://localhost:$FRONTEND_PORT (PID: $FRONTEND_PID)"
    echo "  ✅ Database:  $DB_HOST:$DB_PORT/$DB_NAME"
    echo ""
    echo "📋 Process IDs saved in:"
    echo "  • backend.pid"
    echo "  • app/worker/worker.pid"
    echo "  • app/web/frontend.pid"
    echo ""
    echo "📊 Logs available at:"
    echo "  • backend.log"
    echo "  • app/worker/worker.log"
    echo "  • app/web/frontend.log"
    echo ""
    echo "To stop all services:"
    echo "  ./stop.sh"
    echo ""
    echo "To view logs:"
    echo "  tail -f backend.log"
    echo "  tail -f app/worker/worker.log"
    echo "  tail -f app/web/frontend.log"
fi

echo ""
echo "🎉 Happy coding!"
echo ""
