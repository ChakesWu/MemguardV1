#!/bin/bash
# Start MemGuard backend
#
# Usage: ./scripts/START_BACKEND.sh

echo "======================================================================"
echo "  Starting MemGuard Backend"
echo "======================================================================"
echo ""

# Navigate to project root (scripts/ → ../)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../backend"

# Check if port 8000 is in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8000 is already in use"
    echo ""
    echo "Existing process:"
    lsof -Pi :8000 -sTCP:LISTEN
    echo ""
    read -p "Kill existing process and restart? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill -9 $(lsof -t -i:8000)
        echo "✅ Killed existing process"
    else
        echo "❌ Exiting..."
        exit 1
    fi
fi

echo "🚀 Starting backend on port 8000..."
echo ""
echo "  API: http://localhost:8000"
echo "  Docs: http://localhost:8000/docs"
echo "  Health: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
