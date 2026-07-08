#!/bin/bash
# Complete test suite for MemGuard

echo ""
echo "======================================================================"
echo "  MemGuard - Complete Test Suite"
echo "======================================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -n "Testing: $test_name... "

    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "Step 1: Environment Checks"
echo "----------------------------------------------------------------------"

run_test "Python 3.9+" "python3 -c 'import sys; exit(0 if sys.version_info >= (3, 9) else 1)'"
run_test "SDK installed" "python3 -c 'import memguard'"
run_test "Backend dependencies" "python3 -c 'import fastapi; import uvicorn'"

echo ""
echo "Step 2: Backend Checks"
echo "----------------------------------------------------------------------"

run_test "Backend reachable" "curl -s http://localhost:8000/health"
run_test "Database exists" "test -f backend/memguard.db"
run_test "Health endpoint" "curl -s http://localhost:8000/health | grep -q status"

echo ""
echo "Step 3: API Endpoint Tests"
echo "----------------------------------------------------------------------"

run_test "GET /health" "curl -s http://localhost:8000/health"
run_test "GET /v1/db/stats" "curl -s http://localhost:8000/v1/db/stats"
run_test "GET /docs (Swagger)" "curl -s http://localhost:8000/docs | grep -q OpenAPI"

echo ""
echo "Step 4: SDK Tests"
echo "----------------------------------------------------------------------"

run_test "Import SDK core" "python3 -c 'from memguard.core.event import MemoryEvent'"
run_test "Import LangGraph adapter" "python3 -c 'from memguard.adapters.langgraph import MemGuardCheckpointer'"
run_test "Import transports" "python3 -c 'from memguard.transport import HttpTransport, FileTransport, StdoutTransport'"

echo ""
echo "======================================================================"
echo "  Test Results"
echo "======================================================================"
echo ""
echo -e "  ${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "  ${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run demo: ./RUN_DEMO.sh"
    echo "  2. View events: curl http://localhost:8000/v1/db/stats"
    echo "  3. Build frontend: cd frontend && npm run dev"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  - Backend not running? Run: ./START_BACKEND.sh"
    echo "  - Dependencies missing? Run: cd sdk && pip install -e ."
    echo "  - Check logs: cat backend.log"
    exit 1
fi
