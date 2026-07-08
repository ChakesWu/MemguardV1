#!/bin/bash
# ============================================================================
# Stage 1: Run fincompli-baseline with real Qwen (no MemGuard)
#
# This demonstrates the FinCompli compliance pipeline end-to-end:
#   - Fraud Detection Agent analyzes the transaction
#   - Case History Agent retrieves similar SAR cases
#   - Compliance Research Agent queries regulations
#   - Report Generation Agent produces the SAR draft
#
# All agents use your local Qwen model for reasoning.
# If Qwen is unreachable, they fall back to heuristic mode.
#
# Prerequisites:
#   1. llama-server running: llama-server -m <model> --port 8080 --host 0.0.0.0
#   2. venv created: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
#   3. Mock data seeded: python mock_data/seed_database.py
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "  FinCompli Baseline — Stage 1 (Qwen)"
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

# Check Qwen is reachable
echo "🔍 Checking Qwen connectivity..."
if curl -s -m 3 http://localhost:8080/v1/models > /dev/null 2>&1; then
    echo "✅ Qwen (llama-server) is running on port 8080"
else
    echo "⚠️  Qwen not reachable at http://localhost:8080/v1/models"
    echo "   Start with: llama-server -m <model> --port 8080 --host 0.0.0.0"
    echo "   Continuing — agents will use heuristic fallback..."
fi

echo ""
echo "🚀 Running Scenario 02 (Structuring) with Qwen + domain memory..."
echo ""

python cli/interactive.py --scenario 02 --memory --llm

echo ""
echo "============================================"
echo "  Stage 1 Complete"
echo "============================================"
echo ""
echo "Next: Stage 2 — add MemGuard observability"
echo "  ./run_with_memguard.sh"
