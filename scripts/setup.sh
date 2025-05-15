#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print step message
print_step() {
    echo -e "${YELLOW}[SETUP] $1${NC}"
}

# Print success message
print_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# Print error message
print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Print warning message
print_warning() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

print_step "Starting NAETRA Setup..."

# 1. Check for Python and Poetry
print_step "Checking for Python 3.8+ and Poetry..."
if ! command -v python3 &> /dev/null || ! python3 -c "import sys; assert sys.version_info >= (3,8)" &> /dev/null; then
    print_error "Python 3.8 or higher is required. Please install it."
    exit 1
fi
print_success "Python 3.8+ found."

if ! command -v poetry &> /dev/null; then
    print_error "Poetry is not installed. Please install Poetry: https://python-poetry.org/docs/#installation"
    exit 1
fi
print_success "Poetry found."

# 2. Setup Python environment and install dependencies using Poetry
print_step "Setting up Python environment and installing dependencies with Poetry..."
if poetry install; then
    print_success "Python dependencies installed successfully."
else
    print_error "Poetry install failed. Check error messages above."
    print_warning "If you encounter issues with talib-binary installation:"
    print_warning "1. Try installing pandas-ta as an alternative: poetry add pandas-ta"
    print_warning "2. Or try ta-lib from a different source: poetry add -e git+https://github.com/TA-Lib/ta-lib-python.git#egg=TA-Lib"
    exit 1
fi

# 3. Setup Node.js environment for frontend
print_step "Setting up Node.js environment for frontend..."
if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
    print_warning "Node.js or npm not found. Frontend setup might require manual installation of Node.js (LTS recommended)."
    print_warning "Visit https://nodejs.org/ to download and install Node.js LTS."
else
    print_success "Node.js and npm found."
    print_step "Installing frontend dependencies..."
    if (cd frontend && npm install); then
        print_success "Frontend dependencies installed successfully."
    else
        print_error "npm install for frontend failed. Check error messages."
        # Not exiting, as backend might still be usable
    fi
fi

# 4. Setup .env file
print_step "Setting up .env file..."
if [ -f ".env" ]; then
    print_success ".env file already exists."
else
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success ".env file created from .env.example. Please review and update .env with your settings."
    else
        print_error ".env.example not found. Cannot create .env file. Please create it manually."
    fi
fi

# Check for custom environment overrides
if [ -f ".env.custom.example" ] && [ ! -f ".env.custom" ]; then
    print_warning "Optional .env.custom.example found. If you use custom environment overrides, copy it to .env.custom and configure."
fi

# 5. Initialize database with Alembic
print_step "Initializing database with Alembic migrations..."
DB_URL_SET=$(grep '^DATABASE_URL=' .env 2>/dev/null || grep '^DATABASE_URL=' .env.example 2>/dev/null)
if [ -z "$DB_URL_SET" ]; then
    print_error "DATABASE_URL not found in .env or .env.example. Cannot run migrations. Please set it up."
else
    if poetry run alembic upgrade head; then
        print_success "Database migrations applied successfully."
    else
        print_error "Alembic migrations failed. Check error messages and database connection in .env."
    fi
fi

print_step "-----------------------------------------------------"
print_success "NAETRA Setup Complete!"
echo -e "
Next Steps:
1. ${YELLOW}Review and update your .env file${NC} with appropriate settings:
   - Database credentials
   - API keys (Alpha Vantage, etc.)
   - Redis configuration
   - Other service-specific settings

2. Ensure required services are running:
   - PostgreSQL (database)
   - Redis (caching, message broker)

3. Start the application:
   All components:    ${GREEN}./scripts/start.sh${NC}
   Backend only:      ${GREEN}./scripts/start.sh backend${NC}
   Frontend only:     ${GREEN}./scripts/start.sh frontend${NC}

4. Access the application:
   - Backend API docs: http://localhost:8000/api/v1/docs
   - Frontend: http://localhost:3000

Notes:
- Technical Analysis features use talib-binary. If you experience issues:
  * Try pandas-ta as an alternative (poetry add pandas-ta)
  * Or install ta-lib from source (see technical_analysis.md in docs)
- For development tools and guidelines, see docs/DEVELOPMENT.md
"
print_step "-----------------------------------------------------"

exit 0
