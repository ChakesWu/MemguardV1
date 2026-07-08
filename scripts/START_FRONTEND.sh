#!/bin/bash
# Frontend Dashboard 快速启动脚本

echo "======================================================================"
echo "  MemGuard Frontend Dashboard - 启动"
echo "======================================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../frontend"

# 检查 node_modules 是否存在
if [ ! -d "node_modules" ]; then
    echo "📦 首次运行，安装依赖..."
    echo ""
    npm install
    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ 依赖安装失败"
        echo ""
        echo "请尝试："
        echo "  cd frontend"
        echo "  rm -rf node_modules package-lock.json"
        echo "  npm install"
        exit 1
    fi
    echo ""
    echo "✅ 依赖安装完成"
    echo ""
fi

# 检查 Backend 是否运行
echo "🔍 检查 Backend 状态..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend 运行中 (http://localhost:8000)"
else
    echo "⚠️  Backend 未运行"
    echo ""
    echo "请先启动 Backend:"
    echo "  ./scripts/START_BACKEND.sh"
    echo ""
    echo "或手动启动:"
    echo "  cd backend && python3 -m uvicorn app.main:app --port 8000 --reload"
    echo ""
    read -p "是否继续启动 Frontend? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "🚀 启动 Frontend Dashboard..."
echo ""
echo "  URL: http://localhost:3001"
echo "  API: http://localhost:8000"
echo ""
echo "按 Ctrl+C 停止"
echo ""
echo "======================================================================"
echo ""

npm run dev
