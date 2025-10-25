#!/bin/bash

# Ensenia CloudFlare Worker Setup Script
# This script automates the initial CloudFlare setup

set -e

echo "🚀 Ensenia CloudFlare Worker Setup"
echo "===================================="
echo ""

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "❌ Wrangler CLI not found. Installing..."
    npm install -g wrangler
fi

echo "✅ Wrangler CLI found"
echo ""

# Login to CloudFlare (if not already logged in)
echo "🔐 Checking CloudFlare authentication..."
if ! wrangler whoami &> /dev/null; then
    echo "Please log in to CloudFlare:"
    wrangler login
else
    echo "✅ Already authenticated"
fi
echo ""

# Create D1 Database
echo "📦 Creating D1 Database..."
DB_OUTPUT=$(wrangler d1 create ensenia-curriculum 2>&1)
echo "$DB_OUTPUT"

# Extract database ID from output
DB_ID=$(echo "$DB_OUTPUT" | grep -o 'database_id = "[^"]*"' | cut -d'"' -f2)

if [ -z "$DB_ID" ]; then
    echo "⚠️  Could not extract database ID. Please check wrangler.toml manually."
else
    echo "✅ Database ID: $DB_ID"
    # Update wrangler.toml with database ID
    sed -i.bak "s/database_id = \"\"/database_id = \"$DB_ID\"/" ../wrangler.toml
    echo "✅ Updated wrangler.toml with database ID"
fi
echo ""

# Create Vectorize Index
echo "🔍 Creating Vectorize Index..."
wrangler vectorize create curriculum-embeddings \
  --dimensions=768 \
  --metric=cosine
echo "✅ Vectorize index created"
echo ""

# Create KV Namespace
echo "💾 Creating KV Namespace..."
KV_OUTPUT=$(wrangler kv:namespace create "SEARCH_CACHE" 2>&1)
echo "$KV_OUTPUT"

# Extract KV namespace ID from output
KV_ID=$(echo "$KV_OUTPUT" | grep -o 'id = "[^"]*"' | cut -d'"' -f2)

if [ -z "$KV_ID" ]; then
    echo "⚠️  Could not extract KV namespace ID. Please check wrangler.toml manually."
else
    echo "✅ KV Namespace ID: $KV_ID"
    # Update wrangler.toml with KV ID
    sed -i.bak "s/id = \"\" # TODO: Will be created during setup/id = \"$KV_ID\"/" ../wrangler.toml
    echo "✅ Updated wrangler.toml with KV namespace ID"
fi
echo ""

# Initialize database schema
echo "📋 Initializing database schema..."
wrangler d1 execute ensenia-curriculum --file=./schema.sql
echo "✅ Database schema created"
echo ""

# Load sample data
echo "📚 Loading sample curriculum data..."
wrangler d1 execute ensenia-curriculum --file=./sample-data.sql
echo "✅ Sample data loaded"
echo ""

echo "✨ Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Update wrangler.toml with your account_id"
echo "2. Run 'npm install' in the worker directory"
echo "3. Run 'npm run dev' to start local development"
echo "4. Run 'npm run deploy' to deploy to CloudFlare"
echo ""
echo "Happy coding! 🎉"
