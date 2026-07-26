"""
FinCompli Baseline - API Server

Main FastAPI application providing REST endpoints for the compliance workflow.

Endpoints:
  POST /api/analyze          - Submit transaction for analysis
  GET  /api/status/{id}      - Get analysis status
  POST /api/human-decision   - Submit human review decision
  GET  /api/report/{id}      - Get SAR report and execution trace
  GET  /api/memory/{id}      - Get memory traces (for visualization products)
  GET  /api/scenarios         - List available scenarios
  GET  /api/health            - System health check
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

from api.schemas import (
    AnalyzeRequest, AnalyzeResponse, StatusResponse,
    HumanDecisionRequest, HumanDecisionResponse,
    MemoryTracesResponse, ReportResponse, HealthResponse
)
from graph import create_initial_state, build_compliance_graph

app = FastAPI(
    title="FinCompli Baseline",
    version="0.1.0",
    description="Enterprise Multi-Agent Financial Compliance System API"
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# In-memory store for workflow states
_store: dict = {}

# Build graph once at startup
_graph = build_compliance_graph()


@app.on_event("startup")
async def startup():
    """Initialize system on startup"""
    print(f"[FinCompli API] Starting up...")
    print(f"[FinCompli API] Graph compiled with {len(_graph.nodes)} nodes")
    print(f"[FinCompli API] Ready at http://0.0.0.0:8000")


@app.get("/api/health", response_model=HealthResponse)
async def health():
    """System health check"""
    return {
        "status": "ok",
        "version": "0.1.0",
        "agents_loaded": [
            "fraud_detection", "case_history",
            "compliance_research", "report_generation", "supervisor"
        ],
        "scenarios_available": ["01", "02", "03", "04", "05"],
        "memory_status": {"store_entries": len(_store)}
    }


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_transaction(request: AnalyzeRequest):
    """
    Submit a transaction for compliance analysis

    Triggers the full multi-agent compliance workflow.
    """
    thread_id = request.thread_id or f"api-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Create initial state
    state = create_initial_state(
        transaction_id=request.transaction_id,
        customer_id=request.customer_id,
        amount=request.amount,
        currency=request.currency,
        transaction_pattern=request.transaction_pattern,
        thread_id=thread_id,
        from_account=request.from_account,
        to_account=request.to_account,
        to_country=request.to_country
    )

    # Run the workflow
    try:
        config = {"configurable": {"thread_id": thread_id}}
        final_state = _graph.invoke(state, config)

        # Store for later queries
        _store[thread_id] = final_state

        return {
            "thread_id": thread_id,
            "transaction_id": request.transaction_id,
            "status": "completed",
            "current_stage": final_state.get("current_stage", "completed")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow error: {str(e)}")


@app.get("/api/status/{thread_id}", response_model=StatusResponse)
async def get_status(thread_id: str):
    """
    Get analysis status for a thread
    """
    state = _store.get(thread_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    return {
        "thread_id": thread_id,
        "transaction_id": state.get("transaction_id", ""),
        "status": "completed" if state.get("end_time") else "in_progress",
        "current_stage": state.get("current_stage", "unknown"),
        "risk_score": state.get("risk_score", 0),
        "risk_level": state.get("risk_level", "unknown"),
        "requires_human_review": state.get("requires_human_review", False),
        "final_decision": state.get("final_decision"),
        "memory_traces_count": len(state.get("memory_traces", [])),
        "messages_count": len(state.get("messages", []))
    }


@app.post("/api/human-decision/{thread_id}", response_model=HumanDecisionResponse)
async def submit_human_decision(thread_id: str, request: HumanDecisionRequest):
    """
    Submit human review decision for a high-risk case
    """
    state = _store.get(thread_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    from agents.supervisor import SupervisorAgent
    from graph.nodes import human_review_node, final_submission_node

    # Set human decision
    state["human_decision"] = request.decision
    state["human_comments"] = request.comments or ""

    # Re-run human review and final submission
    state = human_review_node(state)
    state = final_submission_node(state)

    _store[thread_id] = state

    return {
        "thread_id": thread_id,
        "final_decision": state.get("final_decision", "unknown"),
        "status": "completed"
    }


@app.get("/api/report/{thread_id}", response_model=ReportResponse)
async def get_report(thread_id: str):
    """
    Get SAR report and complete execution trace
    """
    state = _store.get(thread_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    return {
        "thread_id": thread_id,
        "transaction_id": state.get("transaction_id", ""),
        "risk_score": state.get("risk_score", 0),
        "risk_level": state.get("risk_level", "unknown"),
        "final_decision": state.get("final_decision"),
        "sar_draft": state.get("final_report", {}).get("sar_draft", ""),
        "memory_traces": state.get("memory_traces", []),
        "execution_summary": {
            "start_time": state.get("start_time"),
            "end_time": state.get("end_time"),
            "stages_completed": [
                s for s in ["fraud_detection", "case_history", "compliance_research",
                           "report_generation", "human_review", "final_submission"]
                if state.get(s.replace("_", "") + "_analysis") or s == "final_submission"
            ],
            "messages_count": len(state.get("messages", []))
        }
    }


@app.get("/api/memory/{thread_id}", response_model=MemoryTracesResponse)
async def get_memory_traces(thread_id: str):
    """
    Get memory traces for visualization products

    [PRODUCT HOOK POINT]
    This is the primary data source for memory visualization products.
    """
    state = _store.get(thread_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    return {
        "thread_id": thread_id,
        "total_traces": len(state.get("memory_traces", [])),
        "traces": state.get("memory_traces", [])
    }


@app.get("/api/scenarios")
async def list_scenarios():
    """List all available test scenarios"""
    import json
    scenarios_dir = Path(__file__).parent.parent / "scenarios"
    scenarios = []

    for file in sorted(scenarios_dir.glob("scenario_*.json")):
        with open(file, 'r') as f:
            sc = json.load(f)
        scenarios.append({
            "scenario_id": sc["scenario_id"],
            "title": sc["title"],
            "type": sc["type"],
            "expected_risk_level": sc["expected_risk_level"]
        })

    return {"total": len(scenarios), "scenarios": scenarios}


@app.get("/api/scenarios/{scenario_id}")
async def run_scenario(scenario_id: str):
    """
    Run a predefined scenario via API
    """
    import json
    scenario_file = Path(__file__).parent.parent / "scenarios" / f"scenario_{scenario_id}.json"

    if not scenario_file.exists():
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")

    with open(scenario_file, 'r') as f:
        sc = json.load(f)

    request = AnalyzeRequest(
        transaction_id=sc["transaction_id"],
        customer_id=sc["customer_id"],
        amount=sc["amount"],
        currency=sc.get("currency", "HKD"),
        transaction_pattern=sc["transaction_pattern"],
        from_account=sc.get("from_account"),
        to_account=sc.get("to_account"),
        to_country=sc.get("to_country"),
        thread_id=f"scenario-{scenario_id}-{datetime.now().strftime('%H%M%S')}"
    )

    return await analyze_transaction(request)
