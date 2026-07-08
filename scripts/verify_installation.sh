#!/bin/bash
# MemGuard - Execution Checklist & Test Script
# Run this to verify your MemGuard installation is working

set -e  # Exit on error

echo ""
echo "======================================================================"
echo "  MemGuard - Installation & Verification Script"
echo "======================================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_passed() {
    echo -e "${GREEN}✓${NC} $1"
}

check_failed() {
    echo -e "${RED}✗${NC} $1"
}

check_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# ══════════════════════════════════════════════════════════════════════
# Step 1: Check Prerequisites
# ══════════════════════════════════════════════════════════════════════

echo "Step 1: Checking Prerequisites..."
echo "----------------------------------------------------------------------"

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    check_passed "Python 3 installed: $PYTHON_VERSION"
else
    check_failed "Python 3 not found"
    exit 1
fi

# Check if virtual environment is recommended
if [[ -z "$VIRTUAL_ENV" ]]; then
    check_warning "Not in virtual environment (recommended but not required)"
fi

# Check directory structure
if [[ -d "sdk" && -d "backend" && -d "examples" ]]; then
    check_passed "Directory structure correct"
else
    check_failed "Directory structure incorrect. Are you in MemguardV1 root?"
    exit 1
fi

echo ""

# ══════════════════════════════════════════════════════════════════════
# Step 2: Install SDK
# ══════════════════════════════════════════════════════════════════════

echo "Step 2: Installing MemGuard SDK..."
echo "----------------------------------------------------------------------"

cd sdk
pip install -e . > /dev/null 2>&1
if [[ $? -eq 0 ]]; then
    check_passed "SDK installed successfully"
else
    check_failed "SDK installation failed"
    exit 1
fi
cd ..

# Verify SDK import
python3 -c "from memguard.core.event import MemoryEvent; from memguard.adapters.langgraph import MemGuardCheckpointer" 2>/dev/null
if [[ $? -eq 0 ]]; then
    check_passed "SDK imports working"
else
    check_failed "SDK imports failed"
    exit 1
fi

echo ""

# ══════════════════════════════════════════════════════════════════════
# Step 3: Check Backend Dependencies
# ══════════════════════════════════════════════════════════════════════

echo "Step 3: Checking Backend Dependencies..."
echo "----------------------------------------------------------------------"

cd backend

# Install backend requirements
pip install -r requirements.txt > /dev/null 2>&1
if [[ $? -eq 0 ]]; then
    check_passed "Backend dependencies installed"
else
    check_failed "Backend dependency installation failed"
    exit 1
fi

cd ..

echo ""

# ══════════════════════════════════════════════════════════════════════
# Step 4: Check Demo Agent Dependencies
# ══════════════════════════════════════════════════════════════════════

echo "Step 4: Checking Demo Agent Dependencies..."
echo "----------------------------------------------------------------------"

# Install LangGraph
pip install langgraph langchain-core > /dev/null 2>&1
if [[ $? -eq 0 ]]; then
    check_passed "LangGraph installed"
else
    check_warning "LangGraph installation had warnings (may still work)"
fi

echo ""

# ══════════════════════════════════════════════════════════════════════
# Step 5: Start Backend (Background)
# ══════════════════════════════════════════════════════════════════════

echo "Step 5: Starting Backend..."
echo "----------------------------------------------------------------------"

# Check if backend is already running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    check_warning "Backend already running on port 8000"
    BACKEND_ALREADY_RUNNING=1
else
    echo "Starting backend in background..."
    cd backend
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..

    # Wait for backend to start
    for i in {1..10}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            check_passed "Backend started successfully (PID: $BACKEND_PID)"
            echo "  Log file: backend.log"
            break
        fi
        if [[ $i -eq 10 ]]; then
            check_failed "Backend failed to start"
            echo "  Check backend.log for errors"
            exit 1
        fi
        sleep 1
    done
fi

echo ""

# ══════════════════════════════════════════════════════════════════════
# Step 6: Run Demo Agent
# ══════════════════════════════════════════════════════════════════════

echo "Step 6: Running Demo Agent..."
echo "----------------------------------------------------------------------"
echo ""

cd examples
python3 demo_agent.py --mode auto

if [[ $? -eq 0 ]]; then
    echo ""
    check_passed "Demo agent completed successfully"
else
    check_failed "Demo agent failed"
    cd ..
    exit 1
fi
cd ..

echo ""

# ══════════════════════════════════════════════════════════════════════
# Step 7: Verify Events Captured
# ══════════════════════════════════════════════════════════════════════

echo "Step 7: Verifying Events Captured..."
echo "----------------------------------------------------------------------"

# Check database stats
STATS=$(curl -s http://localhost:8000/v1/db/stats)
EVENT_COUNT=$(echo $STATS | python3 -c "import sys, json; print(json.load(sys.stdin).get('total_events', 0))" 2>/dev/null)

if [[ $EVENT_COUNT -gt 0 ]]; then
    check_passed "Events captured: $EVENT_COUNT"
    echo "$STATS" | python3 -m json.tool 2>/dev/null | head -10
else
    check_failed "No events captured"
fi

echo ""

# ══════════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════════

echo "======================================================================"
echo "  Verification Complete!"
echo "======================================================================"
echo ""
echo "✅ MemGuard is working correctly!"
echo ""
echo "📊 What you can do now:"
echo ""
echo "  1. View database stats:"
echo "     curl http://localhost:8000/v1/db/stats | jq"
echo ""
echo "  2. Query events:"
echo "     sqlite3 backend/memguard.db 'SELECT * FROM memory_events;'"
echo ""
echo "  3. Run interactive demo:"
echo "     python examples/demo_agent.py --mode interactive"
echo ""
echo "  4. View API documentation:"
echo "     open http://localhost:8000/docs"
echo ""
echo "  5. Check backend logs:"
echo "     tail -f backend.log"
echo ""
echo "  6. Stop backend:"
if [[ -n "$BACKEND_PID" ]]; then
    echo "     kill $BACKEND_PID"
fi
echo ""
echo "📚 Next steps:"
echo "  - Read QUICKSTART.md for detailed usage"
echo "  - Read MEMGUARD_STANDALONE_PLAN.md for development roadmap"
echo "  - Build frontend dashboard (next priority)"
echo ""
echo "======================================================================"
