#!/bin/bash
# Quick script to run MemGuard demo
#
# Usage: ./scripts/RUN_DEMO.sh

echo "======================================================================"
echo "  MemGuard Demo - Quick Run Script"
echo "======================================================================"
echo ""

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend already running"
else
    echo "❌ Backend not running. Please start it first:"
    echo "   ./scripts/START_BACKEND.sh"
    exit 1
fi

echo ""
echo "🚀 Running demo agent..."
echo ""

cd examples
python3 demo_agent.py --mode auto

echo ""
echo "======================================================================"
echo "  Demo Complete!"
echo "======================================================================"
echo ""
echo "📊 Check results:"
echo "   curl http://localhost:8000/v1/db/stats | python3 -m json.tool"
echo ""
