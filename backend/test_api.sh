#!/bin/bash
# Quick API test to verify endpoints work

echo "Testing MemGuard API..."
echo ""

# Test health endpoint
echo "1. Health Check:"
curl -s http://localhost:8000/health | python3 -m json.tool
echo -e "\n"

# Test memory write
echo "2. Write Memory:"
curl -s -X POST http://localhost:8000/v1/memory/write \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "test",
    "agent_id": "agent1",
    "content": "User prefers Python",
    "source_type": "system"
  }' | python3 -m json.tool
echo -e "\n"

echo "Test script created. Run './test_api.sh' after starting the server."
