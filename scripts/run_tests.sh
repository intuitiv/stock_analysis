#!/bin/bash

# Set environment variables for testing
export APP_NAME="Naetra Test"
export DEBUG=true
export APP_SECRET_KEY="test-secret-key-do-not-use-in-production"
export DATABASE_URL="sqlite+aiosqlite:///./test.db"
export DATABASE_ECHO=true
export ALPHA_VANTAGE_API_KEY="test-key"
export FINNHUB_API_KEY="test-key"
export YAHOO_FINANCE_API_KEY="test-key"

# Create test directory if it doesn't exist
mkdir -p tests/coverage

# Clean up any previous test databases
rm -f test.db

# Run the tests with coverage
pytest \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html:tests/coverage/html \
    --cov-branch \
    -v \
    -s \
    "$@"

# Clean up test database
rm -f test.db
