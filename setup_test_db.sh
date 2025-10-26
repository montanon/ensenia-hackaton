#!/bin/bash

# Setup Test Database for Ensenia
# Creates test database and user for running pytest

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}════════════════════════════════════════${NC}"
echo -e "${YELLOW}  Ensenia - Test Database Setup${NC}"
echo -e "${YELLOW}════════════════════════════════════════${NC}"
echo ""

# Configuration
TEST_USER="test"
TEST_PASSWORD="test"
TEST_DB="test"
PG_HOST="${PG_HOST:-localhost}"
PG_PORT="${PG_PORT:-5433}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"

echo -e "${GREEN}Configuration:${NC}"
echo "  Host: $PG_HOST"
echo "  Port: $PG_PORT"
echo "  Test User: $TEST_USER"
echo "  Test Database: $TEST_DB"
echo ""

# Check if PostgreSQL is running
if ! pg_isready -h "$PG_HOST" -p "$PG_PORT" -U "$POSTGRES_USER" &>/dev/null; then
    echo -e "${RED}❌ PostgreSQL is not running on $PG_HOST:$PG_PORT${NC}"
    echo ""
    echo "Please start PostgreSQL first:"
    echo "  # Using Homebrew:"
    echo "  brew services start postgresql@14"
    echo ""
    echo "  # Using Docker:"
    echo "  docker run -d -p $PG_PORT:5432 -e POSTGRES_PASSWORD=postgres postgres:14"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ PostgreSQL is running${NC}"
echo ""

# Create test user if doesn't exist
echo "Creating test user '$TEST_USER'..."
if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$PG_HOST" -p "$PG_PORT" -U "$POSTGRES_USER" -tc "SELECT 1 FROM pg_user WHERE usename = '$TEST_USER'" | grep -q 1; then
    echo -e "${YELLOW}⚠  User '$TEST_USER' already exists${NC}"
else
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$PG_HOST" -p "$PG_PORT" -U "$POSTGRES_USER" <<EOF
CREATE USER $TEST_USER WITH PASSWORD '$TEST_PASSWORD';
ALTER USER $TEST_USER CREATEDB;
EOF
    echo -e "${GREEN}✓ User '$TEST_USER' created${NC}"
fi

# Create test database if doesn't exist
echo "Creating test database '$TEST_DB'..."
if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$PG_HOST" -p "$PG_PORT" -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "$TEST_DB"; then
    echo -e "${YELLOW}⚠  Database '$TEST_DB' already exists${NC}"

    # Drop and recreate to ensure clean state
    read -p "Drop and recreate database for clean state? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$PG_HOST" -p "$PG_PORT" -U "$POSTGRES_USER" <<EOF
DROP DATABASE IF EXISTS $TEST_DB;
CREATE DATABASE $TEST_DB OWNER $TEST_USER;
EOF
        echo -e "${GREEN}✓ Database '$TEST_DB' recreated${NC}"
    fi
else
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$PG_HOST" -p "$PG_PORT" -U "$POSTGRES_USER" <<EOF
CREATE DATABASE $TEST_DB OWNER $TEST_USER;
EOF
    echo -e "${GREEN}✓ Database '$TEST_DB' created${NC}"
fi

# Grant privileges
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$PG_HOST" -p "$PG_PORT" -U "$POSTGRES_USER" <<EOF
GRANT ALL PRIVILEGES ON DATABASE $TEST_DB TO $TEST_USER;
EOF

echo ""
echo -e "${GREEN}✓ Database and user created${NC}"
echo ""

# Set up database schema using Alembic
echo "Setting up database schema..."

# Set the test database URL for migrations
export DATABASE_URL="postgresql+asyncpg://$TEST_USER:$TEST_PASSWORD@$PG_HOST:$PG_PORT/$TEST_DB"

# Check if alembic.ini exists
if [ ! -f "alembic.ini" ]; then
    echo -e "${RED}❌ alembic.ini not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Run Alembic migrations
echo "Running database migrations..."
if uv run alembic upgrade head; then
    echo -e "${GREEN}✓ Database schema created${NC}"
else
    echo -e "${RED}❌ Failed to run migrations${NC}"
    echo "You may need to run migrations manually:"
    echo "  DATABASE_URL=$DATABASE_URL uv run alembic upgrade head"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ Test database setup complete!${NC}"
echo ""
echo "Connection details:"
echo "  postgresql+asyncpg://$TEST_USER:$TEST_PASSWORD@$PG_HOST:$PG_PORT/$TEST_DB"
echo ""
echo "Database includes:"
echo "  ✓ User '$TEST_USER' with password '$TEST_PASSWORD'"
echo "  ✓ Database '$TEST_DB'"
echo "  ✓ All tables and schema from Alembic migrations"
echo ""
echo "You can now run tests with:"
echo "  uv run pytest tests/"
echo ""
