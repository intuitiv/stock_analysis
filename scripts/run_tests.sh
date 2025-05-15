#!/bin/bash

# Test execution script for CHAETRA
# Handles unit tests, integration tests, and performance tests

# Parse command line arguments
SKIP_UNIT=false
SKIP_INTEGRATION=false
SKIP_PERFORMANCE=false
COVERAGE=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-unit)
            SKIP_UNIT=true
            shift
            ;;
        --skip-integration)
            SKIP_INTEGRATION=true
            shift
            ;;
        --skip-performance)
            SKIP_PERFORMANCE=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set environment variables
export PYTHONPATH="$(pwd)"
export TEST_MODE=true
export TEST_DATABASE_URL="postgresql+asyncpg://localhost/test_naetra_db"
export TEST_REDIS_URL="redis://localhost:6379/1"

# Create test results directory
RESULTS_DIR="test_results"
mkdir -p "$RESULTS_DIR"
DATE_SUFFIX=$(date +%Y%m%d_%H%M%S)

# Function to run tests and capture results
run_tests() {
    local test_type=$1
    local test_path=$2
    local output_file="$RESULTS_DIR/${test_type}_results_${DATE_SUFFIX}.txt"
    local coverage_file="$RESULTS_DIR/${test_type}_coverage_${DATE_SUFFIX}.xml"
    
    echo "Running $test_type tests..."
    
    if [ "$COVERAGE" = true ]; then
        if [ "$VERBOSE" = true ]; then
            pytest "$test_path" -v --tb=short --cov=app --cov-report=xml:$coverage_file | tee "$output_file"
        else
            pytest "$test_path" --tb=short --cov=app --cov-report=xml:$coverage_file > "$output_file"
        fi
    else
        if [ "$VERBOSE" = true ]; then
            pytest "$test_path" -v --tb=short | tee "$output_file"
        else
            pytest "$test_path" --tb=short > "$output_file"
        fi
    fi
    
    local status=$?
    if [ $status -eq 0 ]; then
        echo "✅ $test_type tests passed"
    else
        echo "❌ $test_type tests failed"
        if [ "$VERBOSE" = false ]; then
            echo "See $output_file for details"
        fi
    fi
    return $status
}

# Function to run database migrations
setup_test_database() {
    echo "Setting up test database..."
    # Drop existing test database
    dropdb test_naetra_db --if-exists
    
    # Create fresh test database
    createdb test_naetra_db
    
    # Run migrations
    alembic upgrade head
}

# Function to clean up test resources
cleanup() {
    echo "Cleaning up test resources..."
    # Stop any running test containers/services
    docker-compose -f docker-compose.test.yml down 2>/dev/null || true
    
    # Clean up temporary files
    rm -rf .pytest_cache
    rm -f .coverage
}

# Register cleanup function to run on script exit
trap cleanup EXIT

# Initialize test environment
echo "Initializing test environment..."

# Start required services
docker-compose -f docker-compose.test.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 5

# Set up test database
setup_test_database

# Run tests based on flags
EXIT_CODE=0

# Unit tests
if [ "$SKIP_UNIT" = false ]; then
    echo -e "\n=== Running Unit Tests ===\n"
    run_tests "unit" "tests/unit" || EXIT_CODE=1
fi

# Integration tests
if [ "$SKIP_INTEGRATION" = false ]; then
    echo -e "\n=== Running Integration Tests ===\n"
    run_tests "integration" "tests/integration" || EXIT_CODE=1
fi

# Performance tests
if [ "$SKIP_PERFORMANCE" = false ]; then
    echo -e "\n=== Running Performance Tests ===\n"
    run_tests "performance" "tests/performance" -m "performance" || EXIT_CODE=1
fi

# Generate combined coverage report if enabled
if [ "$COVERAGE" = true ]; then
    echo -e "\n=== Generating Coverage Report ===\n"
    coverage combine
    coverage html -d "$RESULTS_DIR/coverage_html_${DATE_SUFFIX}"
    coverage report
fi

# Print test summary
echo -e "\n=== Test Summary ===\n"
echo "Test results saved in: $RESULTS_DIR"
if [ "$COVERAGE" = true ]; then
    echo "Coverage report: $RESULTS_DIR/coverage_html_${DATE_SUFFIX}/index.html"
fi

# Print final status
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n✅ All tests passed successfully!"
else
    echo -e "\n❌ Some tests failed. Check logs for details."
fi

exit $EXIT_CODE

# Usage examples:
# ./scripts/run_tests.sh                    # Run all tests
# ./scripts/run_tests.sh --coverage         # Run all tests with coverage
# ./scripts/run_tests.sh --skip-performance # Skip performance tests
# ./scripts/run_tests.sh -v                 # Run with verbose output
