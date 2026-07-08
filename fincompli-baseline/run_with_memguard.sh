#!/bin/bash
# ============================================================================
# Stage 2: Run fincompli-baseline WITH MemGuard SDK → Full Observability
#
# This runs the SAME compliance pipeline as Stage 1, but now:
#   - Every memory read (episodic, semantic, procedural) is traced
#   - Every agent output is recorded
#   - DecisionTraces link memory → output for each agent
#   - The MemGuard Dashboard shows the complete memory-to-output chain
#
# Prerequisites:
#   1. llama-server running on port 8080
#   2. MemGuard backend: ./scripts/START_BACKEND.sh (or: uvicorn backend.app.main:app --port 8000)
#   3. MemGuard dashboard: ./scripts/START_FRONTEND.sh (or: cd frontend && npm run dev)
#   4. SDK installable: pip install -e ../sdk
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "  FinCompli + MemGuard — Stage 2 (Observability)"
echo "============================================"
echo ""

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "../myenv/bin/activate" ]; then
    source ../myenv/bin/activate
else
    echo "⚠️  No venv found — using system Python"
fi

# Install MemGuard SDK (idempotent, zero dependencies)
echo "📦 Installing MemGuard SDK..."
pip install -e "$REPO_ROOT/sdk" -q
echo "✅ SDK installed"

# Check Qwen
echo ""
echo "🔍 Checking Qwen connectivity..."
if curl -s -m 3 http://localhost:8080/v1/models > /dev/null 2>&1; then
    echo "✅ Qwen is running on port 8080"
else
    echo "⚠️  Qwen not reachable — agents will use heuristic fallback"
fi

# Check MemGuard backend
echo ""
echo "🔍 Checking MemGuard backend..."
BACKEND_RUNNING=false
if curl -s -m 2 http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ MemGuard backend is running on port 8000"
    BACKEND_RUNNING=true
else
    echo "⚠️  MemGuard backend not running — starting it..."
    cd "$REPO_ROOT/backend"
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd "$SCRIPT_DIR"
    sleep 2
    if curl -s -m 2 http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend started (PID: $BACKEND_PID)"
        BACKEND_RUNNING=true
    else
        echo "❌ Backend failed to start"
    fi
fi

echo ""
echo "🚀 Running Scenario 02 with Qwen + domain memory + MemGuard tracing..."
echo ""

python run_with_memguard.py --scenario 02

echo ""
echo "============================================"
echo "  Stage 2 Complete — Observability Data Ready"
echo "============================================"
echo ""
echo "📊 View the results:"
echo "   Dashboard:  http://localhost:3001"
echo "   API Docs:   http://localhost:8000/docs"
echo "   DB Stats:   curl http://localhost:8000/v1/db/stats"
echo "   Events:     curl 'http://localhost:8000/v1/events?limit=50'"
echo ""
echo "🔍 On the dashboard, you can see:"
echo "   ① What memory each agent read (episodic/semantic/procedural)"
echo "   ② What each agent output (risk scores, SAR reports)"
echo "   ③ DecisionTraces linking memory → agent decisions"
echo ""

# Keep backend running if we started it
if [ -n "${BACKEND_PID:-}" ]; then
    echo "Backend running (PID: $BACKEND_PID). Stop with: kill $BACKEND_PID"
fi
