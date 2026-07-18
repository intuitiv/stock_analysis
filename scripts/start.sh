#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print step message
print_step() {
    echo -e "${YELLOW}[START] $1${NC}"
}

# Print success message
print_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# Print error message
print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Function to check if process is running
check_process() {
    pgrep -f "$1" > /dev/null
    return $?
}

# Function to start backend
start_backend() {
    local in_background=$1 # true or false

    print_step "Starting backend server..."
    if check_process "uvicorn app.main:app"; then
        print_step "Backend is already running"
        return 0
    fi

    mkdir -p logs
    if [ "$in_background" = true ]; then
        print_step "Starting backend in background. Logs: logs/backend.log"
        poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
        BACKEND_PID=$!
        echo $BACKEND_PID > logs/backend.pid
        sleep 3
        if check_process "uvicorn app.main:app"; then
            print_success "Backend started successfully (PID: $BACKEND_PID)."
            return 0
        else
            print_error "Failed to start backend. Check logs/backend.log"
            return 1
        fi
    else
        print_step "Starting backend in foreground. Press Ctrl+C to stop."
        # Ensure logs directory exists even for foreground for consistency if uvicorn logs there by default
        poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
        # Script will block here until uvicorn is stopped
        print_success "Backend stopped."
        return 0 
    fi
}

# Function to start frontend
start_frontend() {
    local in_background=$1 # true or false

    print_step "Starting frontend development server..."
    # Adjusted for typical react-scripts/vite dev server process name
    if check_process "node.*(react-scripts start|vite)"; then
        print_step "Frontend is already running"
        return 0
    fi
    
    mkdir -p logs
    cd frontend
    if [ "$in_background" = true ]; then
        print_step "Starting frontend in background. Logs: ../logs/frontend.log"
        npm run dev > ../logs/frontend.log 2>&1 &
        FRONTEND_PID=$!
        cd ..
        echo $FRONTEND_PID > logs/frontend.pid
        sleep 5 
        if lsof -i:3000 -t >/dev/null || check_process "node.*(react-scripts start|vite)"; then
            print_success "Frontend started successfully (PID: $FRONTEND_PID)."
            return 0
        else
            cd .. # Ensure we are back in project root on failure
            print_error "Failed to start frontend. Check logs/frontend.log"
            return 1
        fi
    else
        print_step "Starting frontend in foreground. Press Ctrl+C to stop."
        npm run dev
        # Script will block here
        cd ..
        print_success "Frontend stopped."
        return 0
    fi
}

# Function to check Redis (remains the same)
check_redis() {
    print_step "Checking Redis..."
    if ! redis-cli ping > /dev/null 2>&1; then
        print_error "Redis is not running or not accessible. Please ensure Redis is running."
        return 1
    fi
    print_success "Redis is running"
    return 0
}

# Function to check PostgreSQL (remains the same)
check_postgres() {
    print_step "Checking PostgreSQL..."
    if ! pg_isready -q; then
        print_error "PostgreSQL is not running or not accessible. Please ensure PostgreSQL is running."
        return 1
    fi
    print_success "PostgreSQL is running"
    return 0
}

# Default action
ACTION="all"

# Parse arguments
if [ "$#" -gt 0 ]; then
    ACTION="$1"
fi

print_step "NAETRA System Start Script (Action: $ACTION)"

if [[ "$ACTION" == "all" || "$ACTION" == "backend" || "$ACTION" == "frontend" ]]; then
    if ! check_redis; then exit 1; fi
    if ! check_postgres; then exit 1; fi
fi

if [[ "$ACTION" == "backend" ]]; then
    start_backend false # Start in foreground
elif [[ "$ACTION" == "frontend" ]]; then
    start_frontend false # Start in foreground
elif [[ "$ACTION" == "all" ]]; then
    print_step "Starting all components in background..."
    start_backend true & # Start backend in background
    BACKEND_BG_PID=$!
    start_frontend true & # Start frontend in background
    FRONTEND_BG_PID=$!
    
    wait $BACKEND_BG_PID
    BACKEND_EXIT_CODE=$?
    wait $FRONTEND_BG_PID
    FRONTEND_EXIT_CODE=$?

    if [ $BACKEND_EXIT_CODE -eq 0 ] && [ $FRONTEND_EXIT_CODE -eq 0 ]; then
        print_success "All components started successfully in background."
        echo -e "
Backend logs: logs/backend.log (PID: $(cat logs/backend.pid 2>/dev/null || echo N/A))
Frontend logs: logs/frontend.log (PID: $(cat logs/frontend.pid 2>/dev/null || echo N/A))
View with: tail -f logs/backend.log or tail -f logs/frontend.log

Backend available at: ${GREEN}http://localhost:8000${NC}
Frontend available at: ${GREEN}http://localhost:3000${NC}
API Docs: ${GREEN}http://localhost:8000/api/v1/docs${NC}
"
    else
        print_error "One or more components failed to start in background. Check logs."
    fi
else
    print_error "Invalid action: $ACTION. Use 'backend', 'frontend', or 'all'."
    echo "Usage: ./scripts/start.sh [all|backend|frontend]"
    exit 1
fi
