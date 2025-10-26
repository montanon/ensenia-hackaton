#!/bin/bash

# Ensenia - Stop All Services Script

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Ensenia - Stopping Services         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

log_info() {
    echo -e "${BLUE}ℹ${NC}  $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠️${NC}  $1"
}

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKER_DIR="$SCRIPT_DIR/app/worker"
FRONTEND_DIR="$SCRIPT_DIR/app/web"

STOPPED=0

# Stop Backend
if [ -f "$SCRIPT_DIR/backend.pid" ]; then
    PID=$(cat "$SCRIPT_DIR/backend.pid")
    if kill -0 "$PID" 2>/dev/null; then
        log_info "Stopping Backend (PID: $PID)..."
        kill "$PID"
        rm "$SCRIPT_DIR/backend.pid"
        log_success "Backend stopped"
        STOPPED=$((STOPPED + 1))
    else
        log_warning "Backend process not running"
        rm "$SCRIPT_DIR/backend.pid"
    fi
else
    # Try to kill by process name
    if pkill -f "uvicorn.*app.ensenia.main:app" 2>/dev/null; then
        log_success "Backend stopped (by process name)"
        STOPPED=$((STOPPED + 1))
    else
        log_warning "No Backend process found"
    fi
fi

# Stop Worker
if [ -f "$WORKER_DIR/worker.pid" ]; then
    PID=$(cat "$WORKER_DIR/worker.pid")
    if kill -0 "$PID" 2>/dev/null; then
        log_info "Stopping Worker (PID: $PID)..."
        kill "$PID"
        rm "$WORKER_DIR/worker.pid"
        log_success "Worker stopped"
        STOPPED=$((STOPPED + 1))
    else
        log_warning "Worker process not running"
        rm "$WORKER_DIR/worker.pid"
    fi
else
    # Try to kill by process name
    if pkill -f "wrangler.*dev" 2>/dev/null; then
        log_success "Worker stopped (by process name)"
        STOPPED=$((STOPPED + 1))
    else
        log_warning "No Worker process found"
    fi
fi

# Stop Frontend
if [ -f "$FRONTEND_DIR/frontend.pid" ]; then
    PID=$(cat "$FRONTEND_DIR/frontend.pid")
    if kill -0 "$PID" 2>/dev/null; then
        log_info "Stopping Frontend (PID: $PID)..."
        kill "$PID"
        rm "$FRONTEND_DIR/frontend.pid"
        log_success "Frontend stopped"
        STOPPED=$((STOPPED + 1))
    else
        log_warning "Frontend process not running"
        rm "$FRONTEND_DIR/frontend.pid"
    fi
else
    # Try to kill by process name
    if pkill -f "vite" 2>/dev/null; then
        log_success "Frontend stopped (by process name)"
        STOPPED=$((STOPPED + 1))
    else
        log_warning "No Frontend process found"
    fi
fi

# Stop PostgreSQL
if [ -f "$SCRIPT_DIR/db.sh" ]; then
    log_info "Stopping PostgreSQL..."
    if "$SCRIPT_DIR/db.sh" stop 2>/dev/null; then
        STOPPED=$((STOPPED + 1))
    fi
fi

echo ""
if [ $STOPPED -eq 0 ]; then
    log_warning "No services were running"
else
    log_success "Stopped $STOPPED service(s)"
fi

echo ""
log_info "All services stopped"
echo ""
