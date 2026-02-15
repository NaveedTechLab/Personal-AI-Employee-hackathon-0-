#!/bin/bash
# Start Personal AI Employee Dashboard
# Terminal 1: Python API backend (port 9001)
# Terminal 2: Next.js frontend (port 9000)

echo "Starting Personal AI Employee Dashboard..."
echo "============================================"

# Start Python backend in background
echo "Starting Python API backend on port 9001..."
python interactive_dashboard.py &
BACKEND_PID=$!

# Start Next.js frontend
echo "Starting Next.js frontend on port 9000..."
cd frontend && npm run dev &
FRONTEND_PID=$!

echo ""
echo "  Frontend: http://localhost:9000"
echo "  Backend:  http://localhost:9001"
echo ""
echo "Press Ctrl+C to stop both servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
