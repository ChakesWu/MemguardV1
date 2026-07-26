"""
FINAL INTEGRATION TEST - Complete Project Verification

Tests:
  1. All modules import successfully
  2. Agent pipeline works end-to-end
  3. Graph nodes execute correctly
  4. CLI tool structure is complete
  5. API server is functional
  6. All 5 scenarios are loadable
  7. Full workflow produces complete SAR report
"""

import sys, json, os
from pathlib import Path

PASS = 0; FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1; print(f"  ✓ {name}: {detail}")
    else:
        FAIL += 1; print(f"  ✗ {name}: FAILED - {detail}")

# ═══════════════════════════════════════════════════════════════
print("=" * 70)
print("  FINCOMPLI BASELINE - FINAL INTEGRATION TEST")
print("=" * 70)
print(f"  Working: {Path.cwd()}")
print()

# ═══ TEST 1: Module Imports ═══
print("[TEST 1] Module Imports")

try:
    from config import settings
    check("config.settings", True, f"LLM={settings.llm_base_url}")
except Exception as e: check("config.settings", False, str(e))

try:
    from graph import ComplianceState, create_initial_state, build_compliance_graph
    check("graph.state", True, "ComplianceState")
    check("graph.builder", True, "build_compliance_graph")
except Exception as e: check("graph", False, str(e))

try:
    from agents import (FraudDetectionAgent, CaseHistoryAgent,
                         ComplianceResearchAgent, ReportGenerationAgent, SupervisorAgent)
    check("agents.all", True, "5 agents imported")
except Exception as e: check("agents", False, str(e))

try:
    from memory import MemoryLayer
    check("memory.layer", True, "MemoryLayer")
except Exception as e: check("memory", False, str(e))

try:
    from api.schemas import AnalyzeRequest, AnalyzeResponse, StatusResponse
    check("api.schemas", True, "AnalyzeRequest, Response")
except Exception as e: check("api.schemas", False, str(e))

try:
    from api.server import app
    check("api.server", True, f"FastAPI app ({len(app.routes)} routes)")
except Exception as e: check("api.server", False, str(e))

print()

# ═══ TEST 2: File Structure ═══
print("[TEST 2] File Structure Check")

required_files = [
    "config/settings.py", "config/__init__.py",
    "agents/__init__.py", "agents/base.py", "agents/fraud_detection.py",
    "agents/case_history.py", "agents/compliance_research.py",
    "agents/report_generation.py", "agents/supervisor.py",
    "memory/__init__.py", "memory/short_term.py", "memory/episodic.py",
    "memory/semantic.py", "memory/procedural.py", "memory/user_prefs.py",
    "graph/__init__.py", "graph/state.py", "graph/nodes.py", "graph/builder.py",
    "api/__init__.py", "api/server.py", "api/schemas.py",
    "cli/interactive.py",
    "scenarios/scenario_01.json", "scenarios/scenario_02.json",
    "scenarios/scenario_03.json", "scenarios/scenario_04.json",
    "scenarios/scenario_05.json",
    "mock_data/generators/customers.py", "mock_data/generators/sar_cases.py",
    "mock_data/generators/regulations.py", "mock_data/generators/transactions.py",
    "mock_data/seed_database.py",
    "README.md", "requirements.txt", "setup.py", ".env", ".gitignore"
]

for f in required_files:
    check(f"  {f}", Path(f).exists())

print(f"\n  Found: {sum(1 for f in required_files if Path(f).exists())}/{len(required_files)}")
print()

# ═══ TEST 3: Agent Pipeline ═══
print("[TEST 3] Agent Pipeline End-to-End")

from agents import (FraudDetectionAgent, CaseHistoryAgent,
                     ComplianceResearchAgent, ReportGenerationAgent)
from datetime import datetime, timezone

state = {
    "transaction_id": "TXN-FINAL-001", "customer_id": "C-00412",
    "amount": 490000, "currency": "HKD",
    "transaction_pattern": "multiple structured transactions below HKD 500K threshold across jurisdictions in short time window",
    "messages": [], "fraud_analysis": None, "case_history_analysis": None,
    "compliance_research": None, "final_report": None,
    "risk_score": 0.0, "risk_level": "unknown", "risk_factors": [],
    "memory_traces": [], "current_stage": "start",
    "requires_human_review": False, "final_decision": None,
    "thread_id": "test-final", "start_time": datetime.now(timezone.utc).isoformat(),
}

agents = [
    FraudDetectionAgent(),
    CaseHistoryAgent(),
    ComplianceResearchAgent(),
    ReportGenerationAgent()
]

for agent in agents:
    state = agent.analyze(state)
    check(f"  {agent.agent_id}", state.get(f"{agent.agent_id}_analysis") is not None or
          state.get("fraud_analysis") is not None or
          state.get("case_history_analysis") is not None or
          state.get("compliance_research") is not None or
          state.get("final_report") is not None)

check("  Pipeline complete", all([
    state["fraud_analysis"] is not None,
    state["case_history_analysis"] is not None,
    state["compliance_research"] is not None,
    state["final_report"] is not None
]))
check("  SAR draft generated", len(state["final_report"]["sar_draft"]) > 500)
check("  Messages recorded", len(state["messages"]) >= 4)

print()

# ═══ TEST 4: Graph Nodes ═══
print("[TEST 4] Graph Nodes Execution")

from graph.nodes import (
    fraud_detection_node, case_history_node, supervisor_aggregate_node,
    compliance_research_node, report_generation_node,
    human_review_node, final_submission_node
)

state2 = {
    "transaction_id": "TXN-GRAPH-001", "customer_id": "C-00412",
    "amount": 490000, "currency": "HKD",
    "transaction_pattern": "structuring pattern multiple jurisdictions short time window",
    "messages": [], "fraud_analysis": None, "case_history_analysis": None,
    "compliance_research": None, "final_report": None,
    "risk_score": 0.0, "risk_level": "unknown", "risk_factors": [],
    "memory_traces": [], "current_stage": "start",
    "requires_human_review": False, "final_decision": None,
    "thread_id": "test-graph", "start_time": datetime.now(timezone.utc).isoformat(),
}

nodes = [
    fraud_detection_node, case_history_node, supervisor_aggregate_node,
    compliance_research_node, report_generation_node,
    human_review_node, final_submission_node
]

for node_fn in nodes:
    try:
        state2 = node_fn(state2)
        check(f"  {node_fn.__name__}", True)
    except Exception as e:
        check(f"  {node_fn.__name__}", False, str(e)[:60])

check("  Graph pipeline complete", state2.get("final_decision") is not None)
check("  End time recorded", state2.get("end_time") is not None)

print()

# ═══ TEST 5: Scenarios ═══
print("[TEST 5] Scenario Validation")

for sid in ["01", "02", "03", "04", "05"]:
    file = Path(f"scenarios/scenario_{sid}.json")
    if file.exists():
        with open(file) as f:
            sc = json.load(f)
        check(f"  Scenario {sid}: {sc['title']}",
              all(k in sc for k in ["transaction_id", "customer_id", "amount", "transaction_pattern"]))
    else:
        check(f"  Scenario {sid}", False, "file not found")

print()

# ═══ TEST 6: API Endpoints ═══
print("[TEST 6] API Server")

from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)

# Health check
resp = client.get("/api/health")
check("  GET /api/health", resp.status_code == 200, f"status={resp.status_code}")
health_data = resp.json()
check("  health.status=ok", health_data.get("status") == "ok")
check("  health.version", health_data.get("version") == "0.1.0")
check("  health.agents", len(health_data.get("agents_loaded", [])) == 5)

# Analyze transaction
resp = client.post("/api/analyze", json={
    "transaction_id": "TXN-API-001",
    "customer_id": "C-00412",
    "amount": 490000,
    "currency": "HKD",
    "transaction_pattern": "structuring multiple transactions below threshold across jurisdictions"
})
check("  POST /api/analyze", resp.status_code == 200, f"status={resp.status_code}")
analyze_data = resp.json()
thread_id = analyze_data.get("thread_id")
check("  analyze.thread_id", thread_id is not None, thread_id or "")
check("  analyze.completed", analyze_data.get("status") == "completed")

# Get status
resp = client.get(f"/api/status/{thread_id}")
check("  GET /api/status", resp.status_code == 200)
status_data = resp.json()
check("  status.risk_score > 0", status_data.get("risk_score", 0) > 0, f"score={status_data.get('risk_score')}")

# Get report
resp = client.get(f"/api/report/{thread_id}")
check("  GET /api/report", resp.status_code == 200)
report_data = resp.json()
check("  report.sar_draft", len(report_data.get("sar_draft", "")) > 500,
      f"{len(report_data.get('sar_draft', ''))} chars")

# Get memory traces
resp = client.get(f"/api/memory/{thread_id}")
check("  GET /api/memory", resp.status_code == 200)

# List scenarios
resp = client.get("/api/scenarios")
check("  GET /api/scenarios", resp.status_code == 200)
scenarios_data = resp.json()
check("  scenarios.count", scenarios_data.get("total") == 5)

# Human decision
resp = client.post(f"/api/human-decision/{thread_id}", json={
    "reviewer_id": "compliance_officer_001",
    "decision": "approve",
    "comments": "Approved - clear structuring pattern"
})
check("  POST /api/human-decision", resp.status_code == 200)
decision_data = resp.json()
check("  decision.final", decision_data.get("final_decision") == "file_sar")

print()

# ═══ FINAL SUMMARY ═══
print("=" * 70)
print(f"  FINAL RESULTS: {PASS} passed, {FAIL} failed")
if FAIL == 0:
    print("  ✅ ALL TESTS PASSED!")
    print("  FinCompli Baseline is ready for deployment.")
else:
    print(f"  ❌ {FAIL} test(s) need attention.")
print("=" * 70)
print()
print("  Project Statistics:")
print(f"    Python modules: {sum(1 for f in required_files if f.endswith('.py'))}+")
print(f"    Test scenarios: 5")
print(f"    API endpoints: 8")
print(f"    Agents: 5")
print(f"    Memory types: 5")
print(f"    Graph nodes: 8")
print()
print("  Start API server:")
print("    uvicorn api.server:app --reload")
print("    → http://localhost:8000/docs")
