#!/bin/bash
# Personal AI Employee - Platinum Tier Startup Script

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "🚀 Starting Personal AI Employee - Platinum Tier"

# Check if required environment variables are set
if [[ -z "$ANTHROPIC_API_KEY" ]]; then
    echo "❌ Error: ANTHROPIC_API_KEY environment variable not set"
    echo "Please set your Claude API key:"
    echo "export ANTHROPIC_API_KEY='your-api-key-here'"
    exit 1
fi

# Set default environment if not set
export ENVIRONMENT=${ENVIRONMENT:-production}
export LOG_LEVEL=${LOG_LEVEL:-INFO}

echo "⚙️  Environment: $ENVIRONMENT"
echo "☁️  Starting in 24/7 mode..."

# Create required directories
mkdir -p logs data vault

# Start the process supervisor (manages all other processes)
echo "🔄 Starting process supervisor..."
python -m phase_4.process_supervisor &

SUPERVISOR_PID=$!

# Set up signal handling for graceful shutdown
trap "echo '🛑 Shutting down...'; kill $SUPERVISOR_PID; wait $SUPERVISOR_PID; echo '✅ Shutdown complete.'" SIGTERM SIGINT

# Wait for supervisor to exit
wait $SUPERVISOR_PID