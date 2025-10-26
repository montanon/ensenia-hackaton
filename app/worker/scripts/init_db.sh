#!/bin/bash

# Ensenia Database Initialization Script
# Sets up D1 database with schema and seed data for local development

set -e  # Exit on error

echo "=================================================="
echo "Ensenia - D1 Database Initialization"
echo "=================================================="
echo ""

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "❌ Error: wrangler CLI not found"
    echo "Please install it with: npm install -g wrangler"
    exit 1
fi

echo "✓ Wrangler CLI found"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKER_DIR="$(dirname "$SCRIPT_DIR")"

echo "Script directory: $SCRIPT_DIR"
echo "Worker directory: $WORKER_DIR"
echo ""

# Navigate to worker directory
cd "$WORKER_DIR"

# Check if schema file exists
if [ ! -f "$SCRIPT_DIR/schema.sql" ]; then
    echo "❌ Error: schema.sql not found at $SCRIPT_DIR/schema.sql"
    exit 1
fi

# Check if seed data file exists
if [ ! -f "$SCRIPT_DIR/seed_data.sql" ]; then
    echo "❌ Error: seed_data.sql not found at $SCRIPT_DIR/seed_data.sql"
    exit 1
fi

echo "✓ SQL files found"
echo ""

# Apply schema
echo "=================================================="
echo "Step 1: Creating database schema..."
echo "=================================================="
wrangler d1 execute ensenia-curriculum --local --file="$SCRIPT_DIR/schema.sql"

if [ $? -eq 0 ]; then
    echo "✓ Schema created successfully"
else
    echo "❌ Error creating schema"
    exit 1
fi

echo ""

# Seed data
echo "=================================================="
echo "Step 2: Seeding curriculum data..."
echo "=================================================="
wrangler d1 execute ensenia-curriculum --local --file="$SCRIPT_DIR/seed_data.sql"

if [ $? -eq 0 ]; then
    echo "✓ Data seeded successfully"
else
    echo "❌ Error seeding data"
    exit 1
fi

echo ""

# Verify data
echo "=================================================="
echo "Step 3: Verifying data..."
echo "=================================================="
echo ""
echo "Ministry Standards:"
wrangler d1 execute ensenia-curriculum --local --command="SELECT COUNT(*) as count FROM ministry_standards"
echo ""
echo "Curriculum Content:"
wrangler d1 execute ensenia-curriculum --local --command="SELECT COUNT(*) as count FROM curriculum_content"
echo ""

echo "=================================================="
echo "✓ Database initialization complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Run 'npm run dev' to start the Worker"
echo "2. Run the embedding script to populate Vectorize"
echo "3. Test the API endpoints"
echo ""
