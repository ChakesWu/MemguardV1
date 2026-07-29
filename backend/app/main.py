from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .agent import MemoryAwareAgent
from .llm import LLMClient
from .schemas import (
    AgentRunRequest, MemoryQueryRequest, MemoryWriteRequest,
    TimelineQueryRequest, EventsIngestRequest
)
from .services import MemoryGateway
from .audit import AuditReportGenerator, export_to_markdown
from .auth import AuthenticationError, TenantAccessError, authenticate_bearer_token, enforce_tenant

app = FastAPI(title="MemGuard v1", version="0.1.0")

# Allow frontend and SDK to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("MEMGUARD_CORS_ORIGINS", "http://localhost:3001").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

gateway = MemoryGateway()
agent = MemoryAwareAgent(gateway=gateway, llm=LLMClient())
audit_generator = AuditReportGenerator()


@app.middleware("http")
async def authenticate_evidence_api(request: Request, call_next):
    """Require a Keycloak bearer token for every evidence API endpoint."""
    # Browser CORS preflights do not carry bearer tokens. Let CORSMiddleware
    # answer them before enforcing authentication on the real request.
    if request.method != "OPTIONS" and request.url.path.startswith("/v1/"):
        try:
            request.state.principal = authenticate_bearer_token(request.headers.get("Authorization"))
        except AuthenticationError as exc:
            return JSONResponse(status_code=401, content={"detail": str(exc)})
    return await call_next(request)


def request_tenant(request: Request, requested_tenant_id: str | None = None) -> str:
    try:
        return enforce_tenant(request.state.principal.tenant_id, requested_tenant_id)
    except TenantAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@app.get("/health")
def health():
    return {"status": "ok", "llm_model": agent.llm.model, "llm_base_url": agent.llm.base_url}


@app.post("/v1/memory/write")
def write_memory(payload: MemoryWriteRequest, request: Request):
    tenant_id = request_tenant(request, payload.tenant_id)
    return gateway.write_memory(payload.model_copy(update={"tenant_id": tenant_id}))


@app.post("/v1/memory/query")
def query_memory(payload: MemoryQueryRequest, request: Request):
    tenant_id = request_tenant(request, payload.tenant_id)
    return gateway.query_memory(payload.model_copy(update={"tenant_id": tenant_id}))


@app.post("/v1/memory/timeline")
def timeline(payload: TimelineQueryRequest, request: Request):
    tenant_id = request_tenant(request, payload.tenant_id)
    return gateway.timeline(payload.model_copy(update={"tenant_id": tenant_id}))


@app.post("/v1/agent/run")
def run_agent(payload: AgentRunRequest, request: Request):
    tenant_id = request_tenant(request, payload.tenant_id)
    return agent.run(tenant_id, payload.agent_id, payload.input, payload.session_id).__dict__


@app.get("/v1/memory/{memory_id}/trace")
def trace_memory(memory_id: str, request: Request):
    tenant_id = request_tenant(request)
    trace = gateway.trace_memory(memory_id)
    trace["events"] = [event for event in trace["events"] if event["tenant_id"] == tenant_id]
    return trace


@app.get("/v1/memory/observability/{tenant_id}/{agent_id}")
def observability_summary(tenant_id: str, agent_id: str, request: Request):
    return gateway.observability_summary(request_tenant(request, tenant_id), agent_id)


# Decision Trace Endpoints
@app.post("/v1/trace")
@app.post("/v1/traces")  # alias for SDK backward compatibility
def create_decision_trace(payload: dict, request: Request):
    """
    Receive a DecisionTrace from the SDK.

    Links memory READ events → LLM decision → memory WRITE events.
    """
    from .services import DecisionTrace as DTrace

    tenant_id = request_tenant(request, payload.get("namespace", payload.get("tenant_id")))
    trace = DTrace(
        trace_id=payload.get("trace_id", ""),
        tenant_id=tenant_id,
        agent_id=payload.get("agent_id", "unknown"),
        session_id=payload.get("session_id"),
        timestamp=payload.get("timestamp", ""),
        input_memory_ids=payload.get("input_event_ids", []),
        input_memory_events=payload.get("input_event_ids", []),
        user_input="(see prompt_hash for traceability)",
        llm_prompt_hash=payload.get("prompt_hash", ""),
        llm_output=payload.get("output_summary", ""),
        llm_output_hash=payload.get("output_hash", ""),
        llm_model=payload.get("context", {}).get("analysis_type", "fincompli-agent"),
        output_memory_ids=payload.get("output_event_ids", []),
        output_memory_events=payload.get("output_event_ids", []),
        memory_influence_scores=payload.get("memory_influence_scores", {}),
        total_influence_score=payload.get("memory_influence_score", 0.0),
        metadata=payload.get("context", {}),
    )
    gateway.create_decision_trace(trace)
    # Also persist to DB
    gateway._persist_trace(trace)
    return {"status": "ok", "trace_id": trace.trace_id}


@app.get("/v1/trace/{trace_id}")
def get_decision_trace(trace_id: str, request: Request):
    """Get a specific decision trace showing which memories influenced a decision."""
    trace = gateway.get_decision_trace(trace_id)
    if not trace or trace.get("tenant_id") != request_tenant(request):
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace


@app.get("/v1/decision-traces/{trace_id}")
def get_decision_trace_detail(trace_id: str, request: Request):
    """
    Get detailed decision trace with causal chain and influence scores.

    Returns enhanced trace showing:
    - Input memory influences (with similarity scores)
    - Decision reasoning (extracted from LLM output)
    - Output memory operations
    - Full causal chain: Memory IN → Decision → Memory OUT
    """
    trace = gateway.get_decision_trace(trace_id)
    if not trace or trace.get("tenant_id") != request_tenant(request):
        raise HTTPException(status_code=404, detail="Trace not found")
    detail = gateway.get_decision_trace_detail(trace_id)
    if detail.get("error") == "Trace not found":
        raise HTTPException(status_code=404, detail="Trace not found")
    return detail


@app.get("/v1/trace/agent/{tenant_id}/{agent_id}")
def get_agent_decision_traces(tenant_id: str, agent_id: str, request: Request, limit: int = 50):
    """Get all decision traces for an agent."""
    return {
        "tenant_id": request_tenant(request, tenant_id),
        "agent_id": agent_id,
        "traces": gateway.get_decision_traces_by_agent(request_tenant(request, tenant_id), agent_id, limit)
    }


@app.get("/v1/trace/tenant/{tenant_id}")
def get_tenant_traces(tenant_id: str, request: Request, limit: int = 100):
    """Get all decision traces for a tenant (all agents)."""
    return gateway.get_decision_traces_by_tenant(request_tenant(request, tenant_id), limit)


@app.get("/v1/memory/{memory_id}/influence")
def get_memory_influence(memory_id: str, request: Request):
    """Show all decisions this memory has influenced."""
    return gateway.get_memory_influence_history(memory_id, request_tenant(request))


# ── SDK Ingestion (used by LangGraph adapter, etc.) ──────────

@app.post("/v1/events")
def ingest_events(payload: EventsIngestRequest, request: Request):
    """
    Ingest memory events from the MemGuard SDK.

    This is the endpoint the SDK's HttpTransport sends events to.
    Accepts events from any framework adapter (LangGraph, CrewAI, etc.)
    """
    tenant_id = request_tenant(request)
    raw_events = [{**e.model_dump(), "namespace": tenant_id} for e in payload.events]
    return gateway.ingest_sdk_events(raw_events)


# ── Analysis APIs ──────────────────────────────────────

@app.get("/v1/analysis/conflicts")
def get_conflicts(request: Request, window_seconds: Optional[float] = 5.0):
    """
    Detect memory conflicts — same memory_key modified by different agents within a short time window.

    Parameters:
    - window_seconds: Conflict detection window (default 5 seconds)
    """
    return gateway.detect_conflicts(
        window_seconds=window_seconds or 5.0,
        tenant_id=request_tenant(request),
    )


@app.get("/v1/analysis/audit/{session_id}")
def generate_audit_report(
    session_id: str,
    request: Request,
    style: str = "compliance",
    format: str = "json",
):
    """
    Generate a session audit report — converting technical events into a natural language report.

    Parameters:
    - session_id: Session ID
    - style: Report style (compliance / debug / business)
    - format: Output format (json / markdown)
    """
    # Session IDs are persisted on the event trace_id column. Do not search
    # memory keys: that can silently return an empty report for a real run.
    tenant_id = request_tenant(request)
    events_data = gateway.get_events_list(limit=5000, session_id=session_id, tenant_id=tenant_id)
    events = events_data.get("events", [])

    # Get decision traces
    traces = []
    try:
        # Extract agent_id from first event
        if events:
            agent_id = events[0].get("agent_id")
            traces = [
                trace
                for trace in gateway.get_decision_traces_by_agent(tenant_id, agent_id, limit=5000)
                if trace.get("session_id") == session_id
            ]
    except Exception:
        pass

    # Get conflicts
    conflicts_data = gateway.detect_conflicts(window_seconds=60.0, tenant_id=tenant_id)
    conflicts = [
        c for c in conflicts_data.get("conflicts", [])
        if any(e.get("event_id") in [c["event_a"], c["event_b"]] for e in events)
    ]

    # Generate report
    report = audit_generator.generate_session_report(
        session_id=session_id,
        events=events,
        traces=traces,
        conflicts=conflicts,
        style=style,
    )

    if format == "markdown":
        from fastapi.responses import PlainTextResponse
        md = export_to_markdown(report)
        return PlainTextResponse(md, media_type="text/markdown")

    return report


# ── Dashboard APIs (Event List & Session List) ──────────

@app.get("/v1/events")
def get_events(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    operation: Optional[str] = None,
    agent_id: Optional[str] = None,
    session_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
):
    """
    Get memory event list (Dashboard core API)

    Parameters:
    - limit: Number of results (default 100, max 500)
    - offset: Offset for pagination
    - operation: Filter by operation type (create/read/update/delete/query)
    - agent_id: Filter by agent
    - session_id: Filter by session
    - tenant_id: Filter by namespace/tenant
    """
    return gateway.get_events_list(
        limit=min(limit, 500),
        offset=offset,
        operation=operation,
        agent_id=agent_id,
        session_id=session_id,
        tenant_id=request_tenant(request, tenant_id),
    )


@app.get("/v1/sessions")
def get_sessions(request: Request, limit: int = 50):
    """
    Get all session list

    Returns for each session:
    - session_id
    - event_count (number of events)
    - latest_event (latest event timestamp)
    - agents (list of participating agents)
    """
    return gateway.get_sessions_list(limit=limit, tenant_id=request_tenant(request))


@app.get("/v1/db/stats")
def db_stats(request: Request):
    """Get database statistics."""
    try:
        with gateway.database.connect() as conn:
            tenant_id = request_tenant(request)
            event_count = conn.execute(
                "SELECT COUNT(*) AS total FROM memory_events WHERE tenant_id = ?", (tenant_id,)
            ).fetchone()["total"]
            trace_count = conn.execute(
                "SELECT COUNT(*) AS total FROM decision_traces WHERE tenant_id = ?", (tenant_id,)
            ).fetchone()["total"]
        stats = {
            "database_driver": gateway.database.driver,
            "total_events": event_count,
            "total_decision_traces": trace_count,
            "persisted": True,
        }
        if gateway.database.driver == "sqlite":
            stats["db_path"] = gateway.database.url.removeprefix("sqlite:///")
        return stats
    except Exception as e:
        return {"error": str(e)}
