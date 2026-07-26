#!/bin/bash
# One-click launch full system (Backend + Frontend)

echo "======================================================================"
echo "  MemGuard - Full System Startup"
echo "======================================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR/.."

# Load nvm for non-interactive shells
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "📋 Startup Plan:"
echo "  1. Backend API (port 8000)"
echo "  2. Frontend Dashboard (port 3001)"
echo ""

# Check if Backend is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Backend is already running (port 8000)${NC}"
else
    echo "🚀 Starting Backend..."
    cd "$ROOT_DIR/backend"
    nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
    BACKEND_PID=$!
    echo "   PID: $BACKEND_PID"

    # Wait for Backend to be ready
    echo "   Waiting for Backend to be ready..."
    for i in {1..15}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "   ${GREEN}✅ Backend ready${NC}"
            break
        fi
        if [ $i -eq 15 ]; then
            echo "   ❌ Backend startup timeout"
            echo "   Check logs: tail -f backend/backend.log"
            exit 1
        fi
        sleep 1
    done
fi

echo ""

# Check if Frontend is already running
if lsof -Pi :3001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Frontend is already running (port 3001)${NC}"
else
    echo "🚀 Starting Frontend..."
    cd "$ROOT_DIR/frontend"

    # Check dependencies
    if [ ! -d "node_modules" ]; then
        echo "   📦 Installing dependencies..."
        npm install > /dev/null 2>&1
    fi

    nohup npm run dev > frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "   PID: $FRONTEND_PID"

    # Wait for Frontend to be ready
    echo "   Waiting for Frontend to be ready..."
    for i in {1..20}; do
        if curl -s http://localhost:3001 > /dev/null 2>&1; then
            echo -e "   ${GREEN}✅ Frontend ready${NC}"
            break
        fi
        if [ $i -eq 20 ]; then
            echo "   ❌ Frontend startup timeout"
            echo "   Check logs: tail -f frontend/frontend.log"
            exit 1
        fi
        sleep 1
    done
fi

echo ""
echo "======================================================================"
echo -e "${GREEN}✅ System startup complete!${NC}"
echo "======================================================================"
echo ""
echo "🌐 Access URLs:"
echo "   Frontend Dashboard: http://localhost:3001"
echo "   Backend API:        http://localhost:8000"
echo "   API Documentation:  http://localhost:8000/docs"
echo ""
echo "📊 Check logs:"
echo "   Backend:  tail -f backend/backend.log"
echo "   Frontend: tail -f frontend/frontend.log"
echo ""
echo "🛑 Stop services:"
echo "   pkill -f 'uvicorn app.main:app'"
echo "   pkill -f 'next dev'"
echo ""
echo "======================================================================"
