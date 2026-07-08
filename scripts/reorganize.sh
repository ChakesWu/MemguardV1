#!/bin/bash
# 文件整理脚本 - 将所有文件归类到正确位置
set -e

echo "======================================================================"
echo "  MemGuard - 文件结构整理"
echo "======================================================================"
echo ""

ROOT="/Users/chakeswu/cursor/MemguardV1"

# ── 1. 创建目标目录结构 ──
echo "📁 创建目录结构..."

mkdir -p "$ROOT/Documents/plans"
mkdir -p "$ROOT/Documents/fincompli"
mkdir -p "$ROOT/Documents/reference"
mkdir -p "$ROOT/scripts"
mkdir -p "$ROOT/tests"

echo "  ✅ Documents/plans/     - 计划书"
echo "  ✅ Documents/fincompli/  - FinCompli 相关文档"
echo "  ✅ Documents/reference/  - 参考文档"
echo "  ✅ scripts/              - 可执行脚本"
echo "  ✅ tests/                - 测试文件"

# ── 2. 移动计划书到 Documents/plans/ ──
echo ""
echo "📋 移动计划书..."

mv "$ROOT/MEMGUARD_STANDALONE_PLAN.md"  "$ROOT/Documents/plans/"
mv "$ROOT/DEVELOPMENT_PLAN.md"          "$ROOT/Documents/plans/"
mv "$ROOT/STAGE1_TASKS.md"              "$ROOT/Documents/plans/"
mv "$ROOT/EXECUTION_SUMMARY.md"         "$ROOT/Documents/plans/"
mv "$ROOT/TASK_EXECUTION_COMPLETE.md"   "$ROOT/Documents/plans/"
mv "$ROOT/FINAL_REPORT.md"              "$ROOT/Documents/plans/"

echo "  ✅ MEMGUARD_STANDALONE_PLAN.md"
echo "  ✅ DEVELOPEMENT_PLAN.md"
echo "  ✅ STAGE1_TASKS.md"
echo "  ✅ EXECUTION_SUMMARY.md"
echo "  ✅ TASK_EXECUTION_COMPLETE.md"
echo "  ✅ FINAL_REPORT.md"

# ── 3. 移动使用指南到 Documents/ ──
echo ""
echo "📖 移动使用指南..."

mv "$ROOT/START_HERE.md"      "$ROOT/Documents/"
mv "$ROOT/QUICKSTART.md"       "$ROOT/Documents/"
mv "$ROOT/EXECUTION_TOOLS.md"  "$ROOT/Documents/"

echo "  ✅ START_HERE.md"
echo "  ✅ QUICKSTART.md"
echo "  ✅ EXECUTION_TOOLS.md"

# ── 4. 移动 FinCompli 相关文档 ──
echo ""
echo "🏦 移动 FinCompli 文档..."

mv "$ROOT/Documents/01_fincompli_baseline_README.md"  "$ROOT/Documents/fincompli/"
mv "$ROOT/Documents/claude_code_prompt_fincompli_baseline (1).md"  "$ROOT/Documents/fincompli/claude_code_prompt_fincompli_baseline.md"

echo "  ✅ 01_fincompli_baseline_README.md"
echo "  ✅ claude_code_prompt_fincompli_baseline.md"

# ── 5. 移动参考文档 ──
echo ""
echo "📚 移动参考文档..."

mv "$ROOT/Documents/02_memorylens_product_document.md"  "$ROOT/Documents/reference/"
mv "$ROOT/Documents/MemGuard_Technical_Design.md"        "$ROOT/Documents/reference/"
mv "$ROOT/Documents/API_EXAMPLES.md"                      "$ROOT/Documents/reference/"

echo "  ✅ 02_memorylens_product_document.md"
echo "  ✅ MemGuard_Technical_Design.md"
echo "  ✅ API_EXAMPLES.md"

# ── 6. 移动脚本到 scripts/ ──
echo ""
echo "🔧 移动脚本文件..."

mv "$ROOT/START_BACKEND.sh"     "$ROOT/scripts/"
mv "$ROOT/RUN_DEMO.sh"          "$ROOT/scripts/"
mv "$ROOT/test_all.sh"          "$ROOT/scripts/"
mv "$ROOT/verify_installation.sh" "$ROOT/scripts/"

echo "  ✅ START_BACKEND.sh"
echo "  ✅ RUN_DEMO.sh"
echo "  ✅ test_all.sh"
echo "  ✅ verify_installation.sh"

# ── 7. 移动测试文件到 tests/ ──
echo ""
echo "🧪 移动测试文件..."

mv "$ROOT/test_sdk_backend_integration.py"  "$ROOT/tests/"
mv "$ROOT/test_memory_tracing.py"           "$ROOT/tests/"

echo "  ✅ test_sdk_backend_integration.py"
echo "  ✅ test_memory_tracing.py"

# ── 8. 清理其他文件 ──
echo ""
echo "🧹 清理临时文件..."

# 移动 backend.log 到 backend/
if [ -f "$ROOT/backend.log" ]; then
    mv "$ROOT/backend.log" "$ROOT/backend/"
    echo "  ✅ backend.log → backend/"
fi

# 删除空 docs 目录(如果有 Documents/ 就不需要)
if [ -d "$ROOT/docs" ] && [ -z "$(ls -A $ROOT/docs 2>/dev/null)" ]; then
    rmdir "$ROOT/docs"
    echo "  ✅ 删除空 docs/ 目录"
fi

echo ""
echo "======================================================================"
echo "  ✅ 文件整理完成！"
echo "======================================================================"
