#!/bin/bash

# Populate Vectorize Index Script
# This script calls a temporary Worker endpoint to populate the Vectorize index

set -e

echo "=================================================="
echo "Populating Vectorize Index with Embeddings"
echo "=================================================="
echo ""

# Check if Worker is running
WORKER_URL="${1:-http://localhost:8787}"

echo "Worker URL: $WORKER_URL"
echo ""
echo "⚠️  Note: The Worker must be running (npm run dev)"
echo "⚠️  Note: You need to add a /admin/populate-vectorize endpoint"
echo ""
echo "Checking if Worker is accessible..."

# Check health endpoint
if curl -s -f "$WORKER_URL/health" > /dev/null 2>&1; then
    echo "✓ Worker is running"
else
    echo "❌ Worker is not accessible at $WORKER_URL"
    echo ""
    echo "Please start the Worker first with:"
    echo "  cd app/worker && npm run dev"
    exit 1
fi

echo ""
echo "Triggering Vectorize population..."
echo "(This may take a few minutes depending on content volume)"
echo ""

# Call the admin endpoint
response=$(curl -s -X POST "$WORKER_URL/admin/populate-vectorize" \
  -H "Content-Type: application/json")

# Check if successful
if echo "$response" | grep -q '"success"'; then
    echo "✓ Vectorize population completed successfully!"
    echo ""
    echo "Response:"
    echo "$response" | jq '.' 2>/dev/null || echo "$response"
else
    echo "❌ Error during population"
    echo ""
    echo "Response:"
    echo "$response" | jq '.' 2>/dev/null || echo "$response"
    exit 1
fi

echo ""
echo "=================================================="
echo "✓ Vectorize index is ready!"
echo "=================================================="
echo ""
echo "You can now test semantic search with:"
echo "  curl -X POST $WORKER_URL/search \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"query\": \"multiplicación\", \"grade\": 5, \"subject\": \"Matemática\", \"limit\": 5}'"
echo ""
