from __future__ import annotations

from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .agent import MemoryAwareAgent
from .llm import LLMClient
from .schemas import (
    AgentRunRequest, MemoryQueryRequest, MemoryWriteRequest,
    TimelineQueryRequest, EventsIngestRequest
)
from .services import MemoryGateway
from .audit import AuditReportGenerator, export_to_markdown

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
audit_generator = AuditReportGenerator()


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
@app.post("/v1/trace")
@app.post("/v1/traces")  # alias for SDK backward compatibility
def create_decision_trace(payload: dict):
    """
    Receive a DecisionTrace from the SDK.

    Links memory READ events → LLM decision → memory WRITE events.
    """
    from .services import DecisionTrace as DTrace

    trace = DTrace(
        trace_id=payload.get("trace_id", ""),
        tenant_id=payload.get("namespace", payload.get("tenant_id", "default")),
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


@app.get("/v1/trace/tenant/{tenant_id}")
def get_tenant_traces(tenant_id: str, limit: int = 100):
    """Get all decision traces for a tenant (all agents)."""
    return gateway.get_decision_traces_by_tenant(tenant_id, limit)


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


# ── Analysis APIs ──────────────────────────────────────

@app.get("/v1/analysis/conflicts")
def get_conflicts(window_seconds: Optional[float] = 5.0):
    """
    检测内存冲突 — 同一 memory_key 被不同 agent 在短时间内修改。

    参数:
    - window_seconds: 冲突检测窗口 (默认 5 秒)
    """
    return gateway.detect_conflicts(window_seconds=window_seconds or 5.0)


@app.get("/v1/analysis/audit/{session_id}")
def generate_audit_report(
    session_id: str,
    style: str = "compliance",
    format: str = "json",
):
    """
    生成会话审计报告 — 将技术事件转换为自然语言报告。

    参数:
    - session_id: 会话 ID
    - style: 报告风格 (compliance / debug / business)
    - format: 输出格式 (json / markdown)
    """
    # 通过 memory_id LIKE 匹配 session_id
    events_data = gateway.get_events_list(limit=5000, memory_key_pattern=session_id)
    events = events_data.get("events", [])

    # 获取决策追踪
    traces = []
    try:
        # Extract agent_id from first event
        if events:
            agent_id = events[0].get("agent_id")
            traces_data = gateway.get_traces_by_agent("default", agent_id)
            traces = [t for t in traces_data.get("traces", []) if t.get("session_id") == session_id]
    except Exception:
        pass

    # 获取冲突
    conflicts_data = gateway.detect_conflicts(window_seconds=60.0)
    conflicts = [
        c for c in conflicts_data.get("conflicts", [])
        if any(e.get("event_id") in [c["event_a"], c["event_b"]] for e in events)
    ]

    # 生成报告
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


# ── Dashboard APIs (事件列表 & Session 列表) ──────────

@app.get("/v1/events")
def get_events(
    limit: int = 100,
    offset: int = 0,
    operation: Optional[str] = None,
    agent_id: Optional[str] = None,
    session_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
):
    """
    获取内存事件列表 (Dashboard 核心 API)

    参数:
    - limit: 返回数量 (默认 100, 最大 500)
    - offset: 偏移量 (分页)
    - operation: 按操作类型过滤 (create/read/update/delete/query)
    - agent_id: 按 agent 过滤
    - session_id: 按 session 过滤
    - tenant_id: 按 namespace/tenant 过滤
    """
    return gateway.get_events_list(
        limit=min(limit, 500),
        offset=offset,
        operation=operation,
        agent_id=agent_id,
        session_id=session_id,
        tenant_id=tenant_id,
    )


@app.get("/v1/sessions")
def get_sessions(limit: int = 50):
    """
    获取所有 session 列表

    返回每个 session 的:
    - session_id
    - event_count (事件数量)
    - latest_event (最新事件时间)
    - agents (参与的 agent 列表)
    """
    return gateway.get_sessions_list(limit=limit)


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
