#!/bin/bash
# File reorganization script - organize all files to correct locations
set -e

echo "======================================================================"
echo "  MemGuard - File Structure Reorganization"
echo "======================================================================"
echo ""

ROOT="/Users/chakeswu/cursor/MemguardV1"

# ── 1. Creating target directory structure ──
echo "📁 Creating directory structure..."

mkdir -p "$ROOT/Documents/plans"
mkdir -p "$ROOT/Documents/fincompli"
mkdir -p "$ROOT/Documents/reference"
mkdir -p "$ROOT/scripts"
mkdir -p "$ROOT/tests"

echo "  ✅ Documents/plans/     - Planning documents"
echo "  ✅ Documents/fincompli/  - FinCompli related documents"
echo "  ✅ Documents/reference/  - Reference documents"
echo "  ✅ scripts/              - Executable scripts"
echo "  ✅ tests/                - Test files"

# ── 2. Moving planning documents to Documents/plans/ ──
echo ""
echo "📋 Moving planning documents..."

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

# ── 3. Moving user guides to Documents/ ──
echo ""
echo "📖 Moving user guides..."

mv "$ROOT/START_HERE.md"      "$ROOT/Documents/"
mv "$ROOT/QUICKSTART.md"       "$ROOT/Documents/"
mv "$ROOT/EXECUTION_TOOLS.md"  "$ROOT/Documents/"

echo "  ✅ START_HERE.md"
echo "  ✅ QUICKSTART.md"
echo "  ✅ EXECUTION_TOOLS.md"

# ── 4. Moving FinCompli documents ──
echo ""
echo "🏦 Moving FinCompli documents..."

mv "$ROOT/Documents/01_fincompli_baseline_README.md"  "$ROOT/Documents/fincompli/"
mv "$ROOT/Documents/claude_code_prompt_fincompli_baseline (1).md"  "$ROOT/Documents/fincompli/claude_code_prompt_fincompli_baseline.md"

echo "  ✅ 01_fincompli_baseline_README.md"
echo "  ✅ claude_code_prompt_fincompli_baseline.md"

# ── 5. Moving reference documents ──
echo ""
echo "📚 Moving reference documents..."

mv "$ROOT/Documents/02_memorylens_product_document.md"  "$ROOT/Documents/reference/"
mv "$ROOT/Documents/MemGuard_Technical_Design.md"        "$ROOT/Documents/reference/"
mv "$ROOT/Documents/API_EXAMPLES.md"                      "$ROOT/Documents/reference/"

echo "  ✅ 02_memorylens_product_document.md"
echo "  ✅ MemGuard_Technical_Design.md"
echo "  ✅ API_EXAMPLES.md"

# ── 6. Moving scripts to scripts/ ──
echo ""
echo "🔧 Moving script files..."

mv "$ROOT/START_BACKEND.sh"     "$ROOT/scripts/"
mv "$ROOT/RUN_DEMO.sh"          "$ROOT/scripts/"
mv "$ROOT/test_all.sh"          "$ROOT/scripts/"
mv "$ROOT/verify_installation.sh" "$ROOT/scripts/"

echo "  ✅ START_BACKEND.sh"
echo "  ✅ RUN_DEMO.sh"
echo "  ✅ test_all.sh"
echo "  ✅ verify_installation.sh"

# ── 7. Moving test files to tests/ ──
echo ""
echo "🧪 Moving test files..."

mv "$ROOT/test_sdk_backend_integration.py"  "$ROOT/tests/"
mv "$ROOT/test_memory_tracing.py"           "$ROOT/tests/"

echo "  ✅ test_sdk_backend_integration.py"
echo "  ✅ test_memory_tracing.py"

# ── 8. Cleaning up other files ──
echo ""
echo "🧹 Cleaning up temporary files..."

# Move backend.log to backend/
if [ -f "$ROOT/backend.log" ]; then
    mv "$ROOT/backend.log" "$ROOT/backend/"
    echo "  ✅ backend.log → backend/"
fi

# Remove empty docs directory (not needed if Documents/ exists)
if [ -d "$ROOT/docs" ] && [ -z "$(ls -A $ROOT/docs 2>/dev/null)" ]; then
    rmdir "$ROOT/docs"
    echo "  ✅ Removing empty docs/ directory"
fi

echo ""
echo "======================================================================"
echo "  ✅ File reorganization complete!"
echo "======================================================================"
