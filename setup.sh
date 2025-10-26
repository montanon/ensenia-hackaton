#!/bin/bash

# Ensenia - Complete Setup Script
# Sets up both Python (uv) and TypeScript (npm) environments

set -e

echo "╔════════════════════════════════════════╗"
echo "║   Ensenia - Complete Setup Script     ║"
echo "║   Chilean Education AI Assistant      ║"
echo "╚════════════════════════════════════════╝"
echo ""

# ============================================================================
# Check Prerequisites
# ============================================================================

echo "📋 Checking prerequisites..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed!"
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
echo "✅ uv found: $(uv --version)"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed!"
    echo "Install from: https://nodejs.org/"
    exit 1
fi
echo "✅ Node.js found: $(node --version)"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed!"
    exit 1
fi
echo "✅ npm found: $(npm --version)"

# Check if wrangler is installed (optional)
if command -v wrangler &> /dev/null; then
    echo "✅ wrangler found: $(wrangler --version)"
else
    echo "⚠️  wrangler not found (will be installed locally)"
fi

echo ""

# ============================================================================
# Python Setup
# ============================================================================

echo "🐍 Setting up Python environment..."

# Install Python dependencies
echo "  Installing Python dependencies..."
uv sync
echo "✅ Python dependencies installed"

# Verify Python environment
echo "  Verifying Python environment..."
uv run python --version
echo "✅ Python environment ready"

echo ""

# ============================================================================
# TypeScript/Worker Setup
# ============================================================================

echo "⚡ Setting up CloudFlare Worker..."

# Install Worker dependencies
echo "  Installing Worker dependencies..."
cd app/worker
npm install
cd ../..
echo "✅ Worker dependencies installed"

echo ""

# ============================================================================
# Web Frontend Setup (if exists)
# ============================================================================

if [ -f "app/web/package.json" ]; then
    echo "⚛️  Setting up React frontend..."
    echo "  Installing Web dependencies..."
    cd app/web
    npm install
    cd ../..
    echo "✅ Web dependencies installed"
    echo ""
fi

# ============================================================================
# CloudFlare Resources Setup
# ============================================================================

echo "☁️  CloudFlare setup..."
echo ""
echo "To set up CloudFlare resources (D1, Vectorize, KV):"
echo "  cd app/worker/scripts"
echo "  ./setup.sh"
echo ""
echo "Or manually create:"
echo "  1. D1 Database:     wrangler d1 create ensenia-curriculum"
echo "  2. Vectorize Index: wrangler vectorize create curriculum-embeddings --dimensions=768 --metric=cosine"
echo "  3. KV Namespace:    wrangler kv:namespace create SEARCH_CACHE"
echo ""

# ============================================================================
# Summary
# ============================================================================

echo "╔════════════════════════════════════════╗"
echo "║   Setup Complete! ✅                   ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "📦 Installed:"
echo "  ✅ Python dependencies (uv)"
echo "  ✅ Worker dependencies (npm)"
if [ -f "app/web/package.json" ]; then
    echo "  ✅ Web dependencies (npm)"
fi
echo ""
echo "🚀 Next steps:"
echo ""
echo "1. Set up CloudFlare resources:"
echo "   cd app/worker/scripts && ./setup.sh"
echo ""
echo "2. Start development servers:"
echo "   # Python Backend:"
echo "   make dev-python"
echo "   # or"
echo "   uv run uvicorn app.ensenia.main:app --reload"
echo ""
echo "   # CloudFlare Worker:"
echo "   make dev-worker"
echo "   # or"
echo "   cd app/worker && npm run dev"
echo ""
echo "3. Seed Vectorize index:"
echo "   curl -X POST http://localhost:8787/seed?action=populate"
echo ""
echo "📚 Documentation:"
echo "  - README.md"
echo "  - app/worker/README.md"
echo "  - app/worker/VECTORIZE_SETUP.md"
echo "  - app/worker/API_REFERENCE.md"
echo ""
echo "Happy coding! 🎉"
