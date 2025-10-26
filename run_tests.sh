#!/bin/bash
# Test execution script with different test suite modes
# Usage: ./run_tests.sh [fast|api|integration|e2e|smoke|coverage|all]

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

case "$1" in
    "fast")
        print_header "Running fast tests (unit + smoke)"
        pytest tests/unit tests/test_generation_service.py tests/test_session_api_enhanced.py \
            -v --tb=short -m "not slow"
        print_success "Fast tests passed"
        ;;

    "api")
        print_header "Running API endpoint tests"
        pytest tests/test_api_endpoints_comprehensive.py tests/test_session_api_enhanced.py \
            tests/test_api_routes.py -v --tb=short
        print_success "API tests passed"
        ;;

    "integration")
        print_header "Running integration tests"
        pytest tests/test_content_generation_integration.py tests/integration/ \
            tests/test_session_initialization.py -v --tb=short
        print_success "Integration tests passed"
        ;;

    "e2e")
        print_header "Running end-to-end tests"
        pytest tests/test_e2e_learn_flow.py -v --tb=short --timeout=60
        print_success "E2E tests passed"
        ;;

    "smoke")
        print_header "Running smoke tests (critical paths only)"
        pytest tests/test_e2e_learn_flow.py::TestLearnFlowE2E::test_learn_mode_complete_flow \
            tests/test_session_api_enhanced.py::TestSessionCreationWithPooling::test_create_session_triggers_background_init \
            tests/test_generation_service.py::TestGenerationService::test_generate_exercise_success \
            -v --tb=short --timeout=60
        print_success "Smoke tests passed"
        ;;

    "coverage")
        print_header "Running tests with coverage report"
        pytest tests/ -v --tb=short \
            --cov=app.ensenia \
            --cov-report=term-missing:skip-covered \
            --cov-report=html \
            --cov-fail-under=60

        if [ -f "htmlcov/index.html" ]; then
            print_success "Coverage report generated: htmlcov/index.html"
        fi
        ;;

    "all")
        print_header "Running all tests"
        pytest tests/ -v --tb=short \
            --timeout=30
        print_success "All tests passed"
        ;;

    "watch")
        print_header "Running tests in watch mode"
        print_warning "Install pytest-watch first: pip install pytest-watch"
        ptw tests/unit tests/test_generation_service.py -- -v --tb=short
        ;;

    "debug")
        print_header "Running tests with debug output"
        pytest tests/test_e2e_learn_flow.py -v -s --tb=long --timeout=60
        ;;

    *)
        echo "Usage: $0 [fast|api|integration|e2e|smoke|coverage|all|watch|debug]"
        echo ""
        echo "Options:"
        echo "  fast        - Fast unit and smoke tests (seconds)"
        echo "  api         - API endpoint contract tests"
        echo "  integration - Integration tests (database, services)"
        echo "  e2e         - End-to-end user flow tests"
        echo "  smoke       - Critical path smoke tests only"
        echo "  coverage    - All tests with coverage report"
        echo "  all         - All tests"
        echo "  watch       - Watch mode (requires pytest-watch)"
        echo "  debug       - Debug mode with verbose output"
        echo ""
        echo "Examples:"
        echo "  $0 fast      # Quick validation"
        echo "  $0 smoke     # Demo readiness check"
        echo "  $0 coverage  # Full coverage report"
        exit 1
        ;;
esac

echo -e "\n${GREEN}✓ Test suite completed successfully!${NC}\n"
