#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print step message
print_step() {
    echo -e "${YELLOW}[STOP] $1${NC}"
}

# Print success message
print_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# Print error message
print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Function to stop process by PID if PID file exists, with pkill fallback
stop_process() {
    local pid_file=$1
    local friendly_name=$2
    local pkill_pattern=$3 

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if [ -z "$pid" ]; then
            print_error "$friendly_name PID file ($pid_file) is empty. Attempting to stop by pattern."
        elif ps -p "$pid" > /dev/null; then
            print_step "Stopping $friendly_name (PID: $pid)..."
            if kill "$pid" > /dev/null 2>&1; then
                sleep 1 
                if ! ps -p "$pid" > /dev/null; then
                    print_success "$friendly_name stopped (PID: $pid)"
                    rm "$pid_file"
                    return 0
                else
                    print_step "$friendly_name (PID: $pid) did not stop with SIGTERM, trying SIGKILL..."
                    kill -9 "$pid" > /dev/null 2>&1
                    sleep 1
                    if ! ps -p "$pid" > /dev/null; then
                        print_success "$friendly_name stopped with SIGKILL (PID: $pid)"
                        rm "$pid_file"
                        return 0
                    else
                        print_error "Failed to stop $friendly_name (PID: $pid) even with SIGKILL."
                        # Don't remove PID file if kill failed, it might be a different process with same PID later
                        return 1
                    fi
                fi
            else
                print_error "Failed to send SIGTERM to $friendly_name (PID: $pid). It might already be stopped or have issues."
                if ! ps -p "$pid" > /dev/null; then # Check if it's actually running
                    print_step "$friendly_name (PID: $pid) is not running. Cleaning up PID file."
                    rm "$pid_file"
                    return 0
                fi
                return 1
            fi
        else # PID in file is not a running process
            print_step "$friendly_name (PID: $pid from $pid_file) not found running. Cleaning up PID file."
            rm "$pid_file"
            # Fall through to pkill as a safety measure if pattern is provided
        fi
    else
        print_step "$friendly_name PID file ($pid_file) not found."
        # Fall through to pkill
    fi

    # Fallback to pkill if PID file method wasn't fully successful or PID file missing
    if [ -n "$pkill_pattern" ]; then
        print_step "Attempting to stop $friendly_name by pattern: '$pkill_pattern'..."
        if pgrep -f "$pkill_pattern" > /dev/null; then
            pkill -f "$pkill_pattern"
            sleep 1 # Give pkill a moment
            if ! pgrep -f "$pkill_pattern" > /dev/null; then
                print_success "$friendly_name stopped using pkill."
                # Clean up PID file if it exists and pkill was successful for this pattern
                if [ -f "$pid_file" ]; then rm "$pid_file"; fi
                return 0
            else
                print_error "Failed to stop $friendly_name using pkill (pattern: '$pkill_pattern')."
                return 1
            fi
        else
            print_step "$friendly_name (matching '$pkill_pattern') not found running."
            return 0 # Not an error if it wasn't running by pattern
        fi
    fi
    # If PID file was not found and no pkill pattern, consider it "not running"
    print_step "$friendly_name was not running (no PID file and no pkill pattern attempted)."
    return 0 
}

# Default action
ACTION="all"

# Parse arguments
if [ "$#" -gt 0 ]; then
    ACTION="$1"
fi

print_step "NAETRA System Stop Script (Action: $ACTION)"

STOPPED_BACKEND_SUCCESS=false
STOPPED_FRONTEND_SUCCESS=false

if [[ "$ACTION" == "all" || "$ACTION" == "backend" ]]; then
    if stop_process "logs/backend.pid" "Backend server" "uvicorn app.main:app"; then
        STOPPED_BACKEND_SUCCESS=true
    fi
fi

if [[ "$ACTION" == "all" || "$ACTION" == "frontend" ]]; then
    # Adjusted pkill pattern for typical react-scripts/vite dev server process name
    if stop_process "logs/frontend.pid" "Frontend server" "node.*(react-scripts start|vite)"; then
        STOPPED_FRONTEND_SUCCESS=true
    fi
fi

# Optional: Stop Redis (uncomment if needed and if started by start.sh)
# if [[ "$ACTION" == "all" ]]; then
#     # ... (Redis stop logic from previous version) ...
# fi

if [[ "$ACTION" == "all" ]]; then
    if [ "$STOPPED_BACKEND_SUCCESS" = true ] && [ "$STOPPED_FRONTEND_SUCCESS" = true ]; then
        print_success "NAETRA system components stopped successfully!"
    else
        print_error "One or more NAETRA system components may not have stopped cleanly. Please check processes."
    fi
elif [[ "$ACTION" == "backend" ]]; then
    if [ "$STOPPED_BACKEND_SUCCESS" = true ]; then
        print_success "Backend stopped successfully!"
    else
        print_error "Backend may not have stopped cleanly."
    fi
elif [[ "$ACTION" == "frontend" ]]; then
    if [ "$STOPPED_FRONTEND_SUCCESS" = true ]; then
        print_success "Frontend stopped successfully!"
    else
        print_error "Frontend may not have stopped cleanly."
    fi
elif [[ "$ACTION" != "all" && "$ACTION" != "backend" && "$ACTION" != "frontend" ]]; then
    print_error "Invalid action: $ACTION. Use 'backend', 'frontend', or 'all'."
    echo "Usage: ./scripts/stop.sh [all|backend|frontend]"
    exit 1
fi

echo -e "\nTo start the system again, use: ${YELLOW}./scripts/start.sh [all|backend|frontend]${NC}"
