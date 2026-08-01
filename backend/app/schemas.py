from typing import Any, Optional

from pydantic import BaseModel, Field


class MemoryWriteRequest(BaseModel):
    tenant_id: str
    agent_id: str
    content: str
    source_type: str = Field(default="user")
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    source_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryQueryRequest(BaseModel):
    tenant_id: str
    agent_id: str
    query: str
    filters: dict[str, Any] = Field(default_factory=dict)


class TimelineQueryRequest(BaseModel):
    tenant_id: str
    agent_id: str
    limit: int = Field(default=25, ge=1, le=200)


class ObservabilitySummaryResponse(BaseModel):
    tenant_id: str
    agent_id: str
    total_events: int
    active_memories: int
    quarantined_events: int
    avg_trust_score: float
    latest_event_at: Optional[str] = None


class AgentRunRequest(BaseModel):
    tenant_id: str
    agent_id: str
    input: str
    session_id: Optional[str] = None


# SDK Event Ingestion (used by HttpTransport)
class SDKEvent(BaseModel):
    event_id: Optional[str] = None
    agent_id: str = "unknown"
    operation: str = "create"
    memory_key: str = ""
    memory_type: str = "working"
    namespace: str = "default"
    session_id: Optional[str] = None
    llm_call_id: Optional[str] = None
    timestamp: Optional[str] = None
    before_value: Optional[dict] = None
    after_value: Optional[dict] = None
    content_hash: Optional[str] = None
    context: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    caused_by: Optional[str] = None


class EventsIngestRequest(BaseModel):
    events: list[SDKEvent]


class SDKDecisionTrace(BaseModel):
    trace_id: str = ""
    agent_id: str = "unknown"
    session_id: Optional[str] = None
    namespace: str = "default"
    timestamp: str = ""
    input_event_ids: list[str] = Field(default_factory=list)
    prompt_hash: str = ""
    user_input: str = ""
    model: str = ""
    output_hash: str = ""
    output_summary: str = ""
    output_event_ids: list[str] = Field(default_factory=list)
    memory_influence_score: float = 0.0
    context: dict[str, Any] = Field(default_factory=dict)
