#!/bin/bash
# Frontend Dashboard Quick Start Script

echo "======================================================================"
echo "  MemGuard Frontend Dashboard - Startup"
echo "======================================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../frontend"

# Load nvm for non-interactive shells
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 First run, installing dependencies..."
    echo ""
    npm install
    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ Dependency installation failed"
        echo ""
        echo "Please try:"
        echo "  cd frontend"
        echo "  rm -rf node_modules package-lock.json"
        echo "  npm install"
        exit 1
    fi
    echo ""
    echo "✅ Dependency installation complete"
    echo ""
fi

# Checking Backend status...
echo "🔍 Checking Backend status..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is running (http://localhost:8000)"
else
    echo "⚠️  Backend is not running"
    echo ""
    echo "Please start Backend first:"
    echo "  ./scripts/START_BACKEND.sh"
    echo ""
    echo "Or start manually:"
    echo "  cd backend && python3 -m uvicorn app.main:app --port 8000 --reload"
    echo ""
    read -p "Continue starting Frontend? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "🚀 Starting Frontend Dashboard..."
echo ""
echo "  URL: http://localhost:3001"
echo "  API: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop"
echo ""
echo "======================================================================"
echo ""

npm run dev
