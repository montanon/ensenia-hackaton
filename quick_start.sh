#!/bin/bash

# Ensenia Deep Research - Quick Start Script
# Automates the setup process for local development

set -e

echo "=================================================="
echo "Ensenia Deep Research - Quick Start"
echo "=================================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."
echo ""

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js v18 or later."
    exit 1
fi
echo "✓ Node.js $(node --version)"

# Check Wrangler
if ! command -v wrangler &> /dev/null; then
    echo "⚠️  Wrangler not found. Installing..."
    npm install -g wrangler
fi
echo "✓ Wrangler $(wrangler --version | head -n1)"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11 or later."
    exit 1
fi
echo "✓ Python $(python3 --version)"

echo ""
echo "=================================================="
echo "Step 1: Setting up Worker"
echo "=================================================="
echo ""

cd app/worker

# Install dependencies
echo "Installing Worker dependencies..."
npm install

echo ""
echo "✓ Worker dependencies installed"
echo ""

# Check if .env exists
if [ ! -f "../../.env" ]; then
    echo "Creating .env file from template..."
    cp ../../.env.sample ../../.env
    echo "⚠️  Please edit .env with your Cloudflare credentials"
    echo "   You can do this later if using local development"
fi

echo ""
echo "=================================================="
echo "Step 2: Initializing Database"
echo "=================================================="
echo ""

# Initialize D1
if [ -f "./scripts/init_db.sh" ]; then
    chmod +x ./scripts/init_db.sh
    ./scripts/init_db.sh
else
    echo "⚠️  Database init script not found. Run manually later."
fi

echo ""
echo "=================================================="
echo "Step 3: Starting Worker"
echo "=================================================="
echo ""

echo "Starting Worker in background..."
echo "Logs will be saved to worker.log"
echo ""

# Start worker in background
nohup npm run dev > worker.log 2>&1 &
WORKER_PID=$!

echo "Worker PID: $WORKER_PID"
echo "Waiting for Worker to start..."
sleep 5

# Check if worker is running
if curl -s -f http://localhost:8787/health > /dev/null 2>&1; then
    echo "✓ Worker is running on http://localhost:8787"
else
    echo "❌ Worker failed to start. Check worker.log for errors."
    exit 1
fi

echo ""
echo "=================================================="
echo "Step 4: Populating Vectorize Index"
echo "=================================================="
echo ""

if [ -f "./scripts/populate_vectorize.sh" ]; then
    chmod +x ./scripts/populate_vectorize.sh
    ./scripts/populate_vectorize.sh
else
    echo "⚠️  Vectorize population script not found. Run manually later."
fi

echo ""
echo "=================================================="
echo "✓ Setup Complete!"
echo "=================================================="
echo ""
echo "Your Deep Research system is ready!"
echo ""
echo "What's running:"
echo "  • Worker: http://localhost:8787 (PID: $WORKER_PID)"
echo "  • Logs: app/worker/worker.log"
echo ""
echo "To stop the Worker:"
echo "  kill $WORKER_PID"
echo ""
echo "Next steps:"
echo "  1. Start Python backend:"
echo "     cd app/ensenia"
echo "     python -m uvicorn main:app --reload"
echo ""
echo "  2. Test the API:"
echo "     curl http://localhost:8787/health"
echo ""
echo "  3. Try a search:"
echo "     curl -X POST http://localhost:8787/search \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"query\":\"multiplicación\",\"grade\":5,\"subject\":\"Matemática\"}'"
echo ""
echo "For full documentation, see DEEP_RESEARCH_SETUP.md"
echo ""
