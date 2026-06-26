from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .agent import MemoryAwareAgent
from .llm import LLMClient
from .schemas import (
    AgentRunRequest, MemoryQueryRequest, MemoryWriteRequest,
    TimelineQueryRequest, EventsIngestRequest
)
from .services import MemoryGateway

app = FastAPI(title="MemGuard v1", version="0.1.0")

# Allow frontend and SDK to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

gateway = MemoryGateway()
agent = MemoryAwareAgent(gateway=gateway, llm=LLMClient())


@app.get("/health")
def health():
    return {"status": "ok", "llm_model": agent.llm.model, "llm_base_url": agent.llm.base_url}


@app.post("/v1/memory/write")
def write_memory(payload: MemoryWriteRequest):
    return gateway.write_memory(payload)


@app.post("/v1/memory/query")
def query_memory(payload: MemoryQueryRequest):
    return gateway.query_memory(payload)


@app.post("/v1/memory/timeline")
def timeline(payload: TimelineQueryRequest):
    return gateway.timeline(payload)


@app.post("/v1/agent/run")
def run_agent(payload: AgentRunRequest):
    return agent.run(payload.tenant_id, payload.agent_id, payload.input, payload.session_id).__dict__


@app.get("/v1/memory/{memory_id}/trace")
def trace_memory(memory_id: str):
    return gateway.trace_memory(memory_id)


@app.get("/v1/memory/observability/{tenant_id}/{agent_id}")
def observability_summary(tenant_id: str, agent_id: str):
    return gateway.observability_summary(tenant_id, agent_id)


# Decision Trace Endpoints
@app.get("/v1/trace/{trace_id}")
def get_decision_trace(trace_id: str):
    """Get a specific decision trace showing which memories influenced a decision."""
    trace = gateway.get_decision_trace(trace_id)
    if not trace:
        return {"error": "Trace not found"}, 404
    return trace


@app.get("/v1/trace/agent/{tenant_id}/{agent_id}")
def get_agent_decision_traces(tenant_id: str, agent_id: str, limit: int = 50):
    """Get all decision traces for an agent."""
    return {
        "tenant_id": tenant_id,
        "agent_id": agent_id,
        "traces": gateway.get_decision_traces_by_agent(tenant_id, agent_id, limit)
    }


@app.get("/v1/memory/{memory_id}/influence")
def get_memory_influence(memory_id: str):
    """Show all decisions this memory has influenced."""
    return gateway.get_memory_influence_history(memory_id)


# ── SDK Ingestion (used by LangGraph adapter, etc.) ──────────

@app.post("/v1/events")
def ingest_events(payload: EventsIngestRequest):
    """
    Ingest memory events from the MemGuard SDK.

    This is the endpoint the SDK's HttpTransport sends events to.
    Accepts events from any framework adapter (LangGraph, CrewAI, etc.)
    """
    raw_events = [e.model_dump() for e in payload.events]
    return gateway.ingest_sdk_events(raw_events)


@app.get("/v1/db/stats")
def db_stats():
    """Get database statistics."""
    import sqlite3
    from .services import DB_PATH
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            event_count = conn.execute("SELECT COUNT(*) FROM memory_events").fetchone()[0]
            trace_count = conn.execute("SELECT COUNT(*) FROM decision_traces").fetchone()[0]
        return {
            "db_path": str(DB_PATH),
            "total_events": event_count,
            "total_decision_traces": trace_count,
            "persisted": True
        }
    except Exception as e:
        return {"error": str(e)}
