#!/bin/bash

# Ensenia - Database Management Script
# Easy commands to manage PostgreSQL via Docker

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Database configuration
DB_CONTAINER="ensenia-postgres"
DB_HOST="localhost"
DB_PORT="5433"
POSTGRES_USER="ensenia"
POSTGRES_PASSWORD="hackathon"

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

show_help() {
    cat << EOF
${BLUE}╔════════════════════════════════════════╗${NC}
${BLUE}║   Ensenia - Database Management       ║${NC}
${BLUE}╚════════════════════════════════════════╝${NC}

Usage: ./db.sh [command]

Commands:
  start           Start PostgreSQL container
  stop            Stop PostgreSQL container
  restart         Restart PostgreSQL container
  status          Show PostgreSQL status
  logs            Show PostgreSQL logs

  setup           Set up databases and run migrations
  reset           Reset all databases (WARNING: deletes data)
  migrate         Run Alembic migrations

  shell           Open psql shell (ensenia database)
  test-shell      Open psql shell (test database)

  backup          Backup all databases
  restore [file]  Restore from backup

  clean           Remove container and volumes
  help            Show this help message

Examples:
  ./db.sh start              # Start PostgreSQL
  ./db.sh setup              # Initialize everything
  ./db.sh shell              # Connect to database
  ./db.sh migrate            # Run migrations
  ./db.sh reset              # Reset and recreate databases

EOF
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install Docker first."
        exit 1
    fi
}

wait_for_db() {
    log_info "Waiting for PostgreSQL to be ready..."
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if docker exec $DB_CONTAINER pg_isready -U $POSTGRES_USER &> /dev/null; then
            log_success "PostgreSQL is ready"
            return 0
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done

    log_error "PostgreSQL failed to start"
    return 1
}

# ============================================================================
# Commands
# ============================================================================

cmd_start() {
    log_info "Starting PostgreSQL..."

    if docker ps -a | grep -q $DB_CONTAINER; then
        if docker ps | grep -q $DB_CONTAINER; then
            log_warning "PostgreSQL is already running"
        else
            docker start $DB_CONTAINER
            wait_for_db
            log_success "PostgreSQL started"
        fi
    else
        log_info "Creating PostgreSQL container..."
        docker-compose up -d postgres
        wait_for_db
        log_success "PostgreSQL started"
    fi

    echo ""
    log_info "PostgreSQL running on port $DB_PORT"
    echo "  Connection: postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$DB_HOST:$DB_PORT/ensenia"
}

cmd_stop() {
    log_info "Stopping PostgreSQL..."
    docker-compose stop postgres
    log_success "PostgreSQL stopped"
}

cmd_restart() {
    cmd_stop
    sleep 2
    cmd_start
}

cmd_status() {
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   PostgreSQL Status                    ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo ""

    if docker ps | grep -q $DB_CONTAINER; then
        log_success "PostgreSQL is running"
        echo ""
        docker exec $DB_CONTAINER psql -U $POSTGRES_USER -c "SELECT version();" | head -3
        echo ""
        log_info "Databases:"
        docker exec $DB_CONTAINER psql -U $POSTGRES_USER -l | grep -E "ensenia|test"
    else
        log_warning "PostgreSQL is not running"
    fi
}

cmd_logs() {
    docker-compose logs -f postgres
}

cmd_setup() {
    log_info "Setting up Ensenia databases..."
    echo ""

    # Start PostgreSQL if not running
    if ! docker ps | grep -q $DB_CONTAINER; then
        cmd_start
        sleep 3
    fi

    # Check if test database exists, create if not
    log_info "Checking for test database..."
    if ! docker exec $DB_CONTAINER psql -U $POSTGRES_USER -lqt | cut -d \| -f 1 | grep -qw test; then
        log_info "Creating test database..."
        docker exec $DB_CONTAINER psql -U $POSTGRES_USER -d ensenia -c "CREATE DATABASE test OWNER $POSTGRES_USER;" || true
    fi
    log_success "Database 'test' exists"

    # Run migrations for ensenia database
    log_info "Running migrations for ensenia database..."
    export DATABASE_URL="postgresql+asyncpg://$POSTGRES_USER:$POSTGRES_PASSWORD@$DB_HOST:$DB_PORT/ensenia"
    if uv run alembic upgrade head; then
        log_success "Ensenia database migrated"
    else
        log_error "Failed to migrate ensenia database"
        exit 1
    fi

    # Run migrations for test database
    log_info "Running migrations for test database..."
    export DATABASE_URL="postgresql+asyncpg://$POSTGRES_USER:$POSTGRES_PASSWORD@$DB_HOST:$DB_PORT/test"
    if uv run alembic upgrade head; then
        log_success "Test database migrated"
    else
        log_warning "Failed to migrate test database (may need manual setup)"
    fi

    echo ""
    log_success "Database setup complete!"
    echo ""
    echo "Databases ready:"
    echo "  • ensenia (development)"
    echo "  • test (testing)"
}

cmd_migrate() {
    log_info "Running Alembic migrations..."

    # Migrate ensenia database
    export DATABASE_URL="postgresql+asyncpg://$POSTGRES_USER:$POSTGRES_PASSWORD@$DB_HOST:$DB_PORT/ensenia"
    uv run alembic upgrade head

    log_success "Migrations complete"
}

cmd_reset() {
    log_warning "This will DELETE all data in the databases!"
    read -p "Are you sure? (yes/no): " -r
    echo

    if [[ ! $REPLY =~ ^yes$ ]]; then
        log_info "Reset cancelled"
        exit 0
    fi

    log_info "Resetting databases..."

    # Drop and recreate databases
    docker exec -i $DB_CONTAINER psql -U $POSTGRES_USER <<EOF
DROP DATABASE IF EXISTS ensenia;
DROP DATABASE IF EXISTS test;
CREATE DATABASE ensenia OWNER postgres;
CREATE DATABASE test OWNER test;
GRANT ALL PRIVILEGES ON DATABASE ensenia TO postgres;
GRANT ALL PRIVILEGES ON DATABASE test TO test;
EOF

    log_success "Databases reset"

    # Run migrations
    cmd_setup
}

cmd_shell() {
    log_info "Opening psql shell for ensenia database..."
    docker exec -it $DB_CONTAINER psql -U $POSTGRES_USER -d ensenia
}

cmd_test_shell() {
    log_info "Opening psql shell for test database..."
    docker exec -it $DB_CONTAINER psql -U test -d test
}

cmd_backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="$SCRIPT_DIR/backups"
    mkdir -p "$backup_dir"

    log_info "Backing up databases..."

    # Backup ensenia
    docker exec $DB_CONTAINER pg_dump -U $POSTGRES_USER ensenia > "$backup_dir/ensenia_$timestamp.sql"
    log_success "Backed up ensenia → backups/ensenia_$timestamp.sql"

    # Backup test
    docker exec $DB_CONTAINER pg_dump -U $POSTGRES_USER test > "$backup_dir/test_$timestamp.sql"
    log_success "Backed up test → backups/test_$timestamp.sql"
}

cmd_restore() {
    local backup_file="$1"

    if [ -z "$backup_file" ]; then
        log_error "Please specify backup file: ./db.sh restore <file>"
        exit 1
    fi

    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        exit 1
    fi

    log_warning "This will restore the database from: $backup_file"
    read -p "Continue? (yes/no): " -r
    echo

    if [[ ! $REPLY =~ ^yes$ ]]; then
        log_info "Restore cancelled"
        exit 0
    fi

    log_info "Restoring database..."
    cat "$backup_file" | docker exec -i $DB_CONTAINER psql -U $POSTGRES_USER ensenia
    log_success "Database restored"
}

cmd_clean() {
    log_warning "This will remove the PostgreSQL container and ALL data!"
    read -p "Are you sure? (yes/no): " -r
    echo

    if [[ ! $REPLY =~ ^yes$ ]]; then
        log_info "Clean cancelled"
        exit 0
    fi

    log_info "Removing PostgreSQL container and volumes..."
    docker-compose down -v
    log_success "Cleaned up"
}

# ============================================================================
# Main
# ============================================================================

check_docker

case "${1:-help}" in
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    status)
        cmd_status
        ;;
    logs)
        cmd_logs
        ;;
    setup)
        cmd_setup
        ;;
    reset)
        cmd_reset
        ;;
    migrate)
        cmd_migrate
        ;;
    shell)
        cmd_shell
        ;;
    test-shell)
        cmd_test_shell
        ;;
    backup)
        cmd_backup
        ;;
    restore)
        cmd_restore "$2"
        ;;
    clean)
        cmd_clean
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
