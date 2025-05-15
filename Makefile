# CHAETRA Test Environment Makefile

# Variables
PYTHON = python3
PIP = pip3
PYTEST = pytest
COVERAGE = coverage
DOCKER_COMPOSE = docker-compose
TEST_COMPOSE_FILE = docker-compose.test.yml

# Directories
SRC_DIR = app
TEST_DIR = tests
RESULTS_DIR = test_results

# Test configuration
COVERAGE_MIN = 80
TIMEOUT = 300

.PHONY: help test setup clean lint coverage performance integration unit docker-test

help:
	@echo "CHAETRA Test Environment Commands:"
	@echo "make setup         - Set up test environment and install dependencies"
	@echo "make test         - Run all tests"
	@echo "make unit         - Run unit tests"
	@echo "make integration  - Run integration tests"
	@echo "make performance  - Run performance tests"
	@echo "make coverage     - Run tests with coverage report"
	@echo "make lint         - Run code quality checks"
	@echo "make clean        - Clean up test artifacts"
	@echo "make docker-test  - Run tests in Docker environment"

setup:
	@echo "Setting up test environment..."
	$(PIP) install -r requirements-test.txt
	$(DOCKER_COMPOSE) -f $(TEST_COMPOSE_FILE) pull
	@echo "Creating test results directory..."
	mkdir -p $(RESULTS_DIR)
	@echo "Setup complete"

test: clean setup
	@echo "Running all tests..."
	$(PYTEST) $(TEST_DIR) \
		--verbose \
		--tb=short \
		--maxfail=2 \
		--timeout=$(TIMEOUT) \
		--junitxml=$(RESULTS_DIR)/test-results.xml

unit: setup
	@echo "Running unit tests..."
	$(PYTEST) $(TEST_DIR)/unit \
		-v \
		--tb=short \
		-m "unit" \
		--junitxml=$(RESULTS_DIR)/unit-test-results.xml

integration: setup
	@echo "Running integration tests..."
	$(DOCKER_COMPOSE) -f $(TEST_COMPOSE_FILE) up -d
	$(PYTEST) $(TEST_DIR)/integration \
		-v \
		--tb=short \
		-m "integration" \
		--junitxml=$(RESULTS_DIR)/integration-test-results.xml
	$(DOCKER_COMPOSE) -f $(TEST_COMPOSE_FILE) down

performance: setup
	@echo "Running performance tests..."
	$(DOCKER_COMPOSE) -f $(TEST_COMPOSE_FILE) up -d
	$(PYTEST) $(TEST_DIR)/performance \
		-v \
		--tb=short \
		-m "performance" \
		--junitxml=$(RESULTS_DIR)/performance-test-results.xml
	$(DOCKER_COMPOSE) -f $(TEST_COMPOSE_FILE) down

coverage:
	@echo "Running tests with coverage..."
	$(COVERAGE) run -m pytest $(TEST_DIR) \
		--verbose \
		--tb=short \
		--cov=$(SRC_DIR) \
		--cov-report=term-missing \
		--cov-report=html:$(RESULTS_DIR)/coverage \
		--cov-fail-under=$(COVERAGE_MIN)
	$(COVERAGE) report
	@echo "Coverage report available at $(RESULTS_DIR)/coverage/index.html"

lint:
	@echo "Running code quality checks..."
	black --check $(SRC_DIR) $(TEST_DIR)
	flake8 $(SRC_DIR) $(TEST_DIR)
	mypy $(SRC_DIR)
	pylint $(SRC_DIR)
	bandit -r $(SRC_DIR)

clean:
	@echo "Cleaning up test artifacts..."
	$(DOCKER_COMPOSE) -f $(TEST_COMPOSE_FILE) down -v
	rm -rf $(RESULTS_DIR)/*
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +

docker-test:
	@echo "Running tests in Docker environment..."
	$(DOCKER_COMPOSE) -f $(TEST_COMPOSE_FILE) build
	$(DOCKER_COMPOSE) -f $(TEST_COMPOSE_FILE) run --rm test

# Additional utility targets

install-hooks:
	@echo "Installing git hooks..."
	cp hooks/* .git/hooks/
	chmod +x .git/hooks/*

validate-config:
	@echo "Validating test configuration..."
	$(PYTHON) -c "import yaml; yaml.safe_load(open('$(TEST_COMPOSE_FILE)'))"
	$(PYTHON) -c "import configparser; configparser.ConfigParser().read('pytest.ini')"

check-dependencies:
	@echo "Checking dependencies..."
	safety check
	pip-audit

init-db:
	@echo "Initializing test database..."
	$(PYTHON) scripts/init_test_db.py

seed-db:
	@echo "Seeding test database..."
	$(PYTHON) scripts/seed_test_data.py

generate-docs:
	@echo "Generating test documentation..."
	sphinx-build -b html docs/tests $(RESULTS_DIR)/docs

# Target for running specific test files
# Usage: make test-file TEST_FILE=path/to/test_file.py
test-file:
	@if [ -z "$(TEST_FILE)" ]; then \
		echo "Please specify TEST_FILE=path/to/test_file.py"; \
		exit 1; \
	fi
	$(PYTEST) $(TEST_FILE) -v --tb=short

# Target for running tests with specific markers
# Usage: make test-marked MARKER=slow
test-marked:
	@if [ -z "$(MARKER)" ]; then \
		echo "Please specify MARKER=marker_name"; \
		exit 1; \
	fi
	$(PYTEST) -v -m "$(MARKER)" --tb=short

.DEFAULT_GOAL := help
