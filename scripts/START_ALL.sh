#!/bin/bash
# 一键启动完整系统 (Backend + Frontend)

echo "======================================================================"
echo "  MemGuard - 完整系统启动"
echo "======================================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR/.."

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "📋 启动计划:"
echo "  1. Backend API (port 8000)"
echo "  2. Frontend Dashboard (port 3001)"
echo ""

# 检查 Backend 是否已运行
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Backend 已在运行 (port 8000)${NC}"
else
    echo "🚀 启动 Backend..."
    cd "$ROOT_DIR/backend"
    nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
    BACKEND_PID=$!
    echo "   PID: $BACKEND_PID"

    # 等待 Backend 启动
    echo "   等待 Backend 就绪..."
    for i in {1..15}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "   ${GREEN}✅ Backend 就绪${NC}"
            break
        fi
        if [ $i -eq 15 ]; then
            echo "   ❌ Backend 启动超时"
            echo "   查看日志: tail -f backend/backend.log"
            exit 1
        fi
        sleep 1
    done
fi

echo ""

# 检查 Frontend 是否已运行
if lsof -Pi :3001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Frontend 已在运行 (port 3001)${NC}"
else
    echo "🚀 启动 Frontend..."
    cd "$ROOT_DIR/frontend"

    # 检查依赖
    if [ ! -d "node_modules" ]; then
        echo "   📦 安装依赖..."
        npm install > /dev/null 2>&1
    fi

    nohup npm run dev > frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "   PID: $FRONTEND_PID"

    # 等待 Frontend 启动
    echo "   等待 Frontend 就绪..."
    for i in {1..20}; do
        if curl -s http://localhost:3001 > /dev/null 2>&1; then
            echo -e "   ${GREEN}✅ Frontend 就绪${NC}"
            break
        fi
        if [ $i -eq 20 ]; then
            echo "   ❌ Frontend 启动超时"
            echo "   查看日志: tail -f frontend/frontend.log"
            exit 1
        fi
        sleep 1
    done
fi

echo ""
echo "======================================================================"
echo -e "${GREEN}✅ 系统启动完成！${NC}"
echo "======================================================================"
echo ""
echo "🌐 访问地址:"
echo "   Frontend Dashboard: http://localhost:3001"
echo "   Backend API:        http://localhost:8000"
echo "   API Documentation:  http://localhost:8000/docs"
echo ""
echo "📊 查看日志:"
echo "   Backend:  tail -f backend/backend.log"
echo "   Frontend: tail -f frontend/frontend.log"
echo ""
echo "🛑 停止服务:"
echo "   pkill -f 'uvicorn app.main:app'"
echo "   pkill -f 'next dev'"
echo ""
echo "======================================================================"
