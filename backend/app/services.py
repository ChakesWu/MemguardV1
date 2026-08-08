from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .schemas import MemoryQueryRequest, MemoryWriteRequest, TimelineQueryRequest
from .database import DatabaseConfig
from .migrations import apply_migrations

@dataclass
class MemoryEvent:
    event_id: str
    tenant_id: str
    agent_id: str
    memory_id: str
    trace_id: str
    event_type: str
    source_type: str
    content: str
    content_hash: str
    policy_decision: str
    trust_score: float
    created_at: str
    parent_event_id: str | None = None
    embedding: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionTrace:
    """Links memory reads to LLM decisions and resulting memory writes."""
    trace_id: str
    tenant_id: str
    agent_id: str
    session_id: str | None
    timestamp: str

    # Input: what memories were used
    input_memory_ids: list[str]
    input_memory_events: list[str]  # event_ids of READ operations

    # The decision
    user_input: str
    llm_prompt_hash: str
    llm_output: str
    llm_output_hash: str
    llm_model: str

    # Output: what memories were created
    output_memory_ids: list[str]
    output_memory_events: list[str]  # event_ids of CREATE/UPDATE operations

    # Analysis
    memory_influence_scores: dict[str, float]  # memory_id -> influence score (0-1)
    total_influence_score: float  # Overall: how much did memory shape this decision?

    metadata: dict[str, Any] = field(default_factory=dict)


class LocalLLMAdapter:
    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = base_url or "http://localhost:1234"
        self.model = model or "local-model"

    def embed(self, content: str) -> list[float]:
        digest = hashlib.sha256(content.encode("utf-8")).digest()
        return [round(b / 255.0, 6) for b in digest[:16]]


class MemoryGateway:
    def __init__(self) -> None:
        self.database = DatabaseConfig.from_env()
        self.adapter = LocalLLMAdapter()
        self.events: list[MemoryEvent] = []           # In-memory cache
        self.decision_traces: list[DecisionTrace] = []  # In-memory cache
        self._lock = threading.Lock()
        self._init_db()

    # ── SQLite Persistence ──────────────────────────────────

    def _init_db(self) -> None:
        """Initialize the selected persistence database."""
        if self.database.driver == "sqlite":
            Path(self.database.url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
        apply_migrations(self.database)

        # Load existing events into memory cache
        self._load_from_db()

    def _load_from_db(self) -> None:
        """Load persisted events into memory cache on startup."""
        try:
            with self.database.connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM memory_events ORDER BY created_at"
                ).fetchall()
                for row in rows:
                    event = MemoryEvent(
                        event_id=row["event_id"],
                        tenant_id=row["tenant_id"],
                        agent_id=row["agent_id"],
                        memory_id=row["memory_id"],
                        trace_id=row["trace_id"] or "",
                        event_type=row["event_type"],
                        source_type=row["source_type"],
                        content=row["content"] or "",
                        content_hash=row["content_hash"] or "",
                        policy_decision=row["policy_decision"],
                        trust_score=row["trust_score"],
                        created_at=row["created_at"],
                        parent_event_id=row["parent_event_id"],
                        embedding=json.loads(row["embedding_json"] or "[]"),
                        metadata=json.loads(row["metadata_json"] or "{}"),
                    )
                    self.events.append(event)
        except Exception:
            pass  # DB might not exist yet

    def _persist_event(self, event: MemoryEvent) -> None:
        """Write a single event to the selected persistence database."""
        try:
            with self.database.connect() as conn:
                conn.execute(
                    self._event_upsert_statement(),
                    (
                        event.event_id, event.tenant_id, event.agent_id,
                        event.memory_id, event.trace_id, event.event_type,
                        event.source_type, event.content, event.content_hash,
                        event.policy_decision, event.trust_score, event.created_at,
                        event.parent_event_id,
                        json.dumps(event.embedding),
                        json.dumps(event.metadata),
                    )
                )
                conn.commit()
        except Exception:
            pass  # Best-effort persistence

    def _event_upsert_statement(self) -> str:
        if self.database.driver == "postgres":
            return """INSERT INTO memory_events
                       (event_id, tenant_id, agent_id, memory_id, trace_id,
                        event_type, source_type, content, content_hash,
                        policy_decision, trust_score, created_at,
                        parent_event_id, embedding_json, metadata_json)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT (event_id) DO UPDATE SET
                         tenant_id = EXCLUDED.tenant_id,
                         agent_id = EXCLUDED.agent_id,
                         memory_id = EXCLUDED.memory_id,
                         trace_id = EXCLUDED.trace_id,
                         event_type = EXCLUDED.event_type,
                         source_type = EXCLUDED.source_type,
                         content = EXCLUDED.content,
                         content_hash = EXCLUDED.content_hash,
                         policy_decision = EXCLUDED.policy_decision,
                         trust_score = EXCLUDED.trust_score,
                         created_at = EXCLUDED.created_at,
                         parent_event_id = EXCLUDED.parent_event_id,
                         embedding_json = EXCLUDED.embedding_json,
                         metadata_json = EXCLUDED.metadata_json"""
        return """INSERT OR REPLACE INTO memory_events
                       (event_id, tenant_id, agent_id, memory_id, trace_id,
                        event_type, source_type, content, content_hash,
                        policy_decision, trust_score, created_at,
                        parent_event_id, embedding_json, metadata_json)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""

    def ingest_sdk_events(self, events_payload: list[dict]) -> dict[str, Any]:
        """
        Ingest events from the MemGuard SDK (LangGraph adapter, etc.).

        This is the endpoint the SDK's HttpTransport sends to.
        Accepts raw MemoryEvent dicts from any framework adapter.
        """
        accepted = []
        rejected = []

        for raw in events_payload:
            try:
                # Save before_value and after_value to metadata
                meta = raw.get("context", {})
                if raw.get("before_value") is not None:
                    meta["_before_value"] = raw["before_value"]
                if raw.get("after_value") is not None:
                    meta["_after_value"] = raw["after_value"]

                event = MemoryEvent(
                    event_id=raw.get("event_id", str(uuid4())),
                    tenant_id=raw.get("namespace", raw.get("tenant_id", "default")),
                    agent_id=raw.get("agent_id", "unknown"),
                    memory_id=raw.get("memory_key", str(uuid4())),
                    trace_id=raw.get("session_id") or raw.get("caused_by") or str(uuid4()),
                    event_type=raw.get("operation", "unknown"),
                    source_type=raw.get("memory_type") or raw.get("context", {}).get("source", "sdk"),
                    content=str(raw.get("after_value") or raw.get("content_hash", "")),
                    content_hash=raw.get("content_hash", ""),
                    policy_decision="allow",
                    trust_score=80.0,
                    created_at=raw.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    metadata=meta,
                )

                with self._lock:
                    self.events.append(event)
                self._persist_event(event)

                accepted.append(event.event_id)
            except Exception:
                rejected.append(raw.get("event_id", "unknown"))

        return {"accepted": len(accepted), "rejected": len(rejected), "event_ids": accepted}

    def _policy_check(self, content: str, source_type: str) -> str:
        lowered = content.lower()
        if source_type == "system":
            return "allow"
        risky = ["ignore previous", "forget above", "system prompt override", "instruction override"]
        if any(pattern in lowered for pattern in risky):
            return "quarantine"
        return "allow"

    def _trust_score(self, source_type: str, policy_decision: str) -> float:
        score = 50.0
        if source_type == "system":
            score += 30
        if source_type == "tool":
            score += 20
        if source_type == "user":
            score -= 10
        if policy_decision == "quarantine":
            score -= 40
        return max(0.0, min(100.0, score))

    def _serialize(self, event: MemoryEvent) -> dict[str, Any]:
        return asdict(event)

    def write_memory(self, payload: MemoryWriteRequest) -> dict[str, Any]:
        policy_decision = self._policy_check(payload.content, payload.source_type)
        memory_id = str(uuid4())
        trace_id = str(uuid4())
        event = MemoryEvent(
            event_id=str(uuid4()),
            tenant_id=payload.tenant_id,
            agent_id=payload.agent_id,
            memory_id=memory_id,
            trace_id=trace_id,
            event_type="write",
            source_type=payload.source_type,
            content=payload.content,
            content_hash=hashlib.sha256(payload.content.encode("utf-8")).hexdigest(),
            policy_decision=policy_decision,
            trust_score=self._trust_score(payload.source_type, policy_decision),
            created_at=datetime.now(timezone.utc).isoformat(),
            embedding=self.adapter.embed(payload.content),
            metadata=payload.metadata,
        )
        with self._lock:
            self.events.append(event)
        self._persist_event(event)
        return {"memory_id": memory_id, "trace_id": trace_id, "event": self._serialize(event)}

    def query_memory(self, payload: MemoryQueryRequest) -> dict[str, Any]:
        filtered = [
            event for event in self.events
            if event.tenant_id == payload.tenant_id and event.agent_id == payload.agent_id
        ]
        ranked = sorted(
            filtered,
            key=lambda event: (event.policy_decision == "quarantine", abs(len(event.content) - len(payload.query))),
        )
        results = [self._serialize(event) for event in ranked]
        return {"query": payload.query, "count": len(results), "results": results}

    def trace_memory(self, memory_id: str) -> dict[str, Any]:
        trace = [self._serialize(event) for event in self.events if event.memory_id == memory_id]
        return {"memory_id": memory_id, "events": trace}

    def timeline(self, payload: TimelineQueryRequest) -> dict[str, Any]:
        items = [
            self._serialize(event)
            for event in self.events
            if event.tenant_id == payload.tenant_id and event.agent_id == payload.agent_id
        ]
        items.sort(key=lambda item: item["created_at"], reverse=True)
        return {"items": items[: payload.limit]}

    def observability_summary(self, tenant_id: str, agent_id: str) -> dict[str, Any]:
        items = [event for event in self.events if event.tenant_id == tenant_id and event.agent_id == agent_id]
        total_events = len(items)
        quarantined_events = sum(1 for event in items if event.policy_decision == "quarantine")
        active_memories = len({event.memory_id for event in items if event.policy_decision == "allow"})
        avg_trust_score = round(sum(event.trust_score for event in items) / total_events, 2) if total_events else 0.0
        latest_event_at = max((event.created_at for event in items), default=None)
        return {
            "tenant_id": tenant_id,
            "agent_id": agent_id,
            "total_events": total_events,
            "active_memories": active_memories,
            "quarantined_events": quarantined_events,
            "avg_trust_score": avg_trust_score,
            "latest_event_at": latest_event_at,
        }

    # ── Conflict Detection ────────────────────────────────────

    def _calculate_influence_scores(self, trace: DecisionTrace) -> tuple[dict[str, float], float]:
        """
        Auto-calculate influence scores for each input memory event.

        Returns:
            (per_memory_scores, overall_score)

        Formula:
            influence_score = type_weight × recency_weight

        Type weights:
            semantic=1.0, episodic=0.8, procedural=0.6, working=0.4, sdk/unknown=0.5

        Recency weights:
            <60s=1.0, <5min=0.9, <1hr=0.7, <24hr=0.5, >24hr=0.3
        """
        from datetime import datetime, timezone

        per_memory_scores: dict[str, float] = {}

        # Parse decision timestamp
        try:
            decision_time = datetime.fromisoformat(trace.timestamp.replace("Z", "+00:00"))
        except Exception:
            decision_time = datetime.now(timezone.utc)

        # Look up each input event and calculate its score
        for event_id in trace.input_memory_events:
            # Find event in SQLite (most reliable) or in-memory cache
            event_data = None
            try:
                with self.database.connect() as conn:
                    row = conn.execute(
                        "SELECT source_type, created_at FROM memory_events WHERE event_id = ?",
                        (event_id,)
                    ).fetchone()
                    if row:
                        event_data = dict(row)
            except Exception:
                pass

            # Fallback to in-memory cache
            if not event_data:
                for event in self.events:
                    if event.event_id == event_id:
                        event_data = {
                            "source_type": event.source_type,
                            "created_at": event.created_at
                        }
                        break

            if not event_data:
                # Event not found, skip
                continue

            # Calculate type_weight
            memory_type = event_data.get("source_type", "sdk").lower()
            type_weight = {
                "semantic": 1.0,
                "episodic": 0.8,
                "procedural": 0.6,
                "working": 0.4,
            }.get(memory_type, 0.5)  # Default for 'sdk' or unknown

            # Calculate recency_weight
            try:
                memory_time = datetime.fromisoformat(event_data["created_at"].replace("Z", "+00:00"))
                delta_seconds = (decision_time - memory_time).total_seconds()

                if delta_seconds < 60:
                    recency_weight = 1.0
                elif delta_seconds < 300:  # 5 minutes
                    recency_weight = 0.9
                elif delta_seconds < 3600:  # 1 hour
                    recency_weight = 0.7
                elif delta_seconds < 86400:  # 24 hours
                    recency_weight = 0.5
                else:
                    recency_weight = 0.3
            except Exception:
                recency_weight = 0.5  # Default if timestamp parsing fails

            # Combined score
            influence_score = min(1.0, type_weight * recency_weight)
            per_memory_scores[event_id] = influence_score

        # Overall score = average of individual scores, capped at 1.0
        if per_memory_scores:
            overall_score = min(1.0, sum(per_memory_scores.values()) / len(per_memory_scores))
        else:
            overall_score = 0.0

        return per_memory_scores, overall_score

    def detect_conflicts(
        self, window_seconds: float = 5.0, tenant_id: str | None = None
    ) -> dict[str, Any]:
        """
        Detect concurrent writes to the same memory_key by different agents.

        Only reports the FIRST conflict per (memory_key, agent_pair) to avoid
        explosion when many events share a key within the window.
        """
        conflicts: list[dict] = []
        seen_pairs: set = set()  # dedup: (key, agent_a, agent_b)
        try:
            with self.database.connect() as conn:
                query = """SELECT event_id, agent_id, memory_id, event_type, created_at, content_hash
                       FROM memory_events
                       WHERE event_type IN ('update', 'create')
                """
                params: list[Any] = []
                if tenant_id:
                    query += " AND tenant_id = ?"
                    params.append(tenant_id)
                query += " ORDER BY memory_id, created_at ASC"
                rows = conn.execute(query, params).fetchall()

            groups: dict[str, list] = {}
            for row in rows:
                key = row["memory_id"]
                if key not in groups:
                    groups[key] = []
                groups[key].append(dict(row))

            for mem_key, events_list in groups.items():
                if len(events_list) < 2:
                    continue
                for i in range(len(events_list)):
                    a = events_list[i]
                    for j in range(i + 1, len(events_list)):
                        b = events_list[j]
                        if a["agent_id"] == b["agent_id"]:
                            continue

                        # Dedup: only report each (key, agent_a, agent_b) combination once
                        pair_key = tuple(sorted([a["agent_id"], b["agent_id"]]))
                        full_key = (mem_key, pair_key[0], pair_key[1])
                        if full_key in seen_pairs:
                            continue

                        try:
                            ta = datetime.fromisoformat(a["created_at"].replace("Z", "+00:00"))
                            tb = datetime.fromisoformat(b["created_at"].replace("Z", "+00:00"))
                            delta = abs((tb - ta).total_seconds())
                        except Exception:
                            continue

                        if delta <= window_seconds:
                            seen_pairs.add(full_key)
                            severity = "critical" if delta < 0.5 else "high" if delta < 2.0 else "medium"
                            conflicts.append({
                                "memory_key": mem_key,
                                "agent_a": a["agent_id"],
                                "agent_b": b["agent_id"],
                                "event_a": a["event_id"],
                                "event_b": b["event_id"],
                                "time_a": a["created_at"],
                                "time_b": b["created_at"],
                                "delta_seconds": round(delta, 3),
                                "severity": severity,
                                "hash_a": a["content_hash"],
                                "hash_b": b["content_hash"],
                                "same_content": a["content_hash"] == b["content_hash"],
                            })

        except Exception as e:
            return {"conflicts": [], "total": 0, "error": str(e)}

        severity_order = {"critical": 0, "high": 1, "medium": 2}
        conflicts.sort(key=lambda c: severity_order.get(c["severity"], 3))

        return {"conflicts": conflicts, "total": len(conflicts)}

    def create_decision_trace(self, trace: DecisionTrace) -> None:
        """Store a decision trace linking memories to LLM decisions."""
        # Auto-calculate influence scores if not provided
        if not trace.memory_influence_scores or trace.total_influence_score == 0.0:
            trace.memory_influence_scores, trace.total_influence_score = self._calculate_influence_scores(trace)
        self.decision_traces.append(trace)

    def _persist_trace(self, trace: DecisionTrace) -> None:
        """Write a decision trace to the selected persistence database."""
        try:
            with self.database.connect() as conn:
                conn.execute(
                    self._trace_upsert_statement(),
                    (
                        trace.trace_id, trace.tenant_id, trace.agent_id,
                        trace.session_id, trace.timestamp,
                        json.dumps(trace.input_memory_ids),
                        json.dumps(trace.input_memory_events),
                        trace.user_input, trace.llm_prompt_hash,
                        trace.llm_output, trace.llm_output_hash,
                        trace.llm_model,
                        json.dumps(trace.output_memory_ids),
                        json.dumps(trace.output_memory_events),
                        json.dumps(trace.memory_influence_scores),
                        trace.total_influence_score,
                        json.dumps(trace.metadata),
                    )
                )
                conn.commit()
        except Exception:
            pass

    def _trace_upsert_statement(self) -> str:
        if self.database.driver == "postgres":
            return """INSERT INTO decision_traces
                       (trace_id, tenant_id, agent_id, session_id, timestamp,
                        input_memory_ids_json, input_memory_events_json,
                        user_input, llm_prompt_hash, llm_output, llm_output_hash,
                        llm_model, output_memory_ids_json, output_memory_events_json,
                        memory_influence_scores_json, total_influence_score, metadata_json)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT (trace_id) DO UPDATE SET
                         tenant_id = EXCLUDED.tenant_id,
                         agent_id = EXCLUDED.agent_id,
                         session_id = EXCLUDED.session_id,
                         timestamp = EXCLUDED.timestamp,
                         input_memory_ids_json = EXCLUDED.input_memory_ids_json,
                         input_memory_events_json = EXCLUDED.input_memory_events_json,
                         user_input = EXCLUDED.user_input,
                         llm_prompt_hash = EXCLUDED.llm_prompt_hash,
                         llm_output = EXCLUDED.llm_output,
                         llm_output_hash = EXCLUDED.llm_output_hash,
                         llm_model = EXCLUDED.llm_model,
                         output_memory_ids_json = EXCLUDED.output_memory_ids_json,
                         output_memory_events_json = EXCLUDED.output_memory_events_json,
                         memory_influence_scores_json = EXCLUDED.memory_influence_scores_json,
                         total_influence_score = EXCLUDED.total_influence_score,
                         metadata_json = EXCLUDED.metadata_json"""
        return """INSERT OR REPLACE INTO decision_traces
                       (trace_id, tenant_id, agent_id, session_id, timestamp,
                        input_memory_ids_json, input_memory_events_json,
                        user_input, llm_prompt_hash, llm_output, llm_output_hash,
                        llm_model, output_memory_ids_json, output_memory_events_json,
                        memory_influence_scores_json, total_influence_score, metadata_json)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""

    def get_decision_trace(self, trace_id: str) -> dict[str, Any] | None:
        """Get a specific decision trace by ID (from SQLite, survives restart)."""
        traces = self._query_traces("WHERE trace_id = ?", (trace_id,), 1)
        return traces[0] if traces else None

    def get_decision_traces_by_agent(self, tenant_id: str, agent_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get all decision traces for a specific agent (from SQLite, survives restart)."""
        return self._query_traces("WHERE tenant_id = ? AND agent_id = ?", (tenant_id, agent_id), limit)

    def get_decision_traces_by_tenant(self, tenant_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Get all decision traces for a tenant across all agents (from SQLite)."""
        return self._query_traces("WHERE tenant_id = ?", (tenant_id,), limit)

    def _query_traces(self, where_clause: str, params: tuple, limit: int) -> list[dict[str, Any]]:
        """Shared SQLite query helper for decision traces. Enriches with event details."""
        try:
            with self.database.connect() as conn:
                rows = conn.execute(
                    f"SELECT * FROM decision_traces {where_clause} ORDER BY timestamp DESC LIMIT ?",
                    (*params, limit),
                ).fetchall()
                results = []
                for row in rows:
                    d = dict(row)
                    json_fields = {
                        "input_memory_ids_json": "input_memory_ids",
                        "input_memory_events_json": "input_memory_events",
                        "output_memory_ids_json": "output_memory_ids",
                        "output_memory_events_json": "output_memory_events",
                        "memory_influence_scores_json": "memory_influence_scores",
                        "metadata_json": "metadata",
                    }
                    for db_key, api_key in json_fields.items():
                        if d.get(db_key):
                            try:
                                d[api_key] = json.loads(d.pop(db_key))
                            except Exception:
                                d.pop(db_key, None)

                    # ── Resolve event IDs → human-readable memory details ──
                    # `*_memory_events` are persisted event IDs. The parallel
                    # `*_memory_ids` fields are logical memory keys and cannot
                    # safely be used to resolve evidence rows.
                    input_event_ids = d.get("input_memory_events", d.get("input_memory_ids", []))
                    output_event_ids = d.get("output_memory_events", d.get("output_memory_ids", []))
                    all_event_ids = input_event_ids + output_event_ids
                    d["input_memory_details"] = []
                    d["output_memory_details"] = []
                    d["evidence_items"] = []
                    d["missing_evidence_event_ids"] = []
                    if all_event_ids:
                        placeholders = ",".join("?" for _ in all_event_ids)
                        event_rows = conn.execute(
                            f"""SELECT event_id, agent_id, memory_id, event_type, source_type,
                                       created_at, content_hash, metadata_json
                                FROM memory_events
                                WHERE event_id IN ({placeholders}) AND tenant_id = ?""",
                            (*all_event_ids, d["tenant_id"]),
                        ).fetchall()
                        event_map = {}
                        for er in event_rows:
                            try:
                                metadata = json.loads(er["metadata_json"] or "{}")
                            except Exception:
                                metadata = {}
                            event_map[er["event_id"]] = {
                                "event_id": er["event_id"],
                                "agent_id": er["agent_id"],
                                "memory_key": er["memory_id"],
                                "operation": er["event_type"],
                                "memory_type": er["source_type"],
                                "timestamp": er["created_at"],
                                "content_hash": er["content_hash"] or "",
                                "metadata": metadata,
                            }
                        # Enrich input side
                        input_ids = input_event_ids
                        output_ids = output_event_ids
                        d["missing_evidence_event_ids"] = [
                            eid for eid in all_event_ids if eid not in event_map
                        ]
                        input_details = [event_map[eid] for eid in input_ids if eid in event_map]
                        d["input_memory_details"] = input_details
                        # Enrich output side
                        output_details = [event_map[eid] for eid in output_ids if eid in event_map]
                        d["output_memory_details"] = output_details
                        # Canonical Phase 1A evidence contract. Every item is
                        # an event actually persisted in memory_events, with an
                        # explicit side describing how it relates to the output.
                        d["evidence_items"] = [
                            {**item, "side": "input"} for item in input_details
                        ] + [
                            {**item, "side": "output"} for item in output_details
                        ]

                    results.append(d)
                return results
        except Exception:
            pass
        return []

    # ── Event List & Session Queries ─────────────────────────

    def get_events_list(
        self,
        limit: int = 100,
        offset: int = 0,
        operation: str | None = None,
        agent_id: str | None = None,
        session_id: str | None = None,
        tenant_id: str | None = None,
        memory_key_pattern: str | None = None,
    ) -> dict[str, Any]:
        """Query events from SQLite with optional filters."""
        try:
            with self.database.connect() as conn:
                query = "SELECT * FROM memory_events"
                params: list[Any] = []
                conditions: list[str] = []

                if operation:
                    conditions.append("event_type = ?")
                    params.append(operation)
                if agent_id:
                    conditions.append("agent_id = ?")
                    params.append(agent_id)
                if session_id:
                    conditions.append("trace_id = ?")
                    params.append(session_id)
                if tenant_id:
                    conditions.append("tenant_id = ?")
                    params.append(tenant_id)
                if memory_key_pattern:
                    conditions.append("memory_id LIKE ?")
                    params.append(f"%{memory_key_pattern}%")

                if conditions:
                    query += " WHERE " + " AND ".join(conditions)

                query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])

                cursor = conn.execute(query, params)
                rows = cursor.fetchall()

                events = []
                for row in rows:
                    meta = json.loads(row["metadata_json"] or "{}")
                    before_val = meta.pop("_before_value", None)
                    after_val = meta.pop("_after_value", None)
                    events.append({
                        "event_id": row["event_id"],
                        "agent_id": row["agent_id"],
                        "session_id": row["trace_id"] or "",
                        "operation": row["event_type"],
                        "memory_key": row["memory_id"],
                        "namespace": row["tenant_id"],
                        "memory_type": row["source_type"],
                        "content_hash": row["content_hash"] or "",
                        "timestamp": row["created_at"],
                        "context": meta,
                        "before_value": before_val,
                        "after_value": after_val,
                    })

                count_query = "SELECT COUNT(*) as cnt FROM memory_events"
                if conditions:
                    count_query += " WHERE " + " AND ".join(conditions)
                count_row = conn.execute(count_query, params[:-2] if conditions else []).fetchone()
                total = count_row["cnt"] if count_row else 0

                return {"events": events, "total": total}
        except Exception as e:
            return {"events": [], "total": 0, "error": str(e)}

    def governed_memory_inventory(self, tenant_id: str) -> list[dict[str, Any]]:
        """Return the support agent's current memory sources for audit display only."""
        try:
            with self.database.connect() as conn:
                orders = conn.execute("SELECT * FROM support_orders WHERE tenant_id = ? ORDER BY order_id", (tenant_id,)).fetchall()
                policies = conn.execute("SELECT * FROM support_policies WHERE tenant_id = ? ORDER BY document_id, version", (tenant_id,)).fetchall()
                memories = conn.execute("SELECT * FROM support_memories WHERE tenant_id = ? ORDER BY memory_id, version_id", (tenant_id,)).fetchall()
        except Exception:
            return []

        items: list[dict[str, Any]] = []
        for row in orders:
            data = dict(row)
            items.append({
                "memory_id": f"order:{data['order_id']}", "kind": "support_order",
                "summary": f"{data['order_id']} · {data['product']} · {data['status']} · {data['payment_status']}",
                "source_type": data.get("source_type") or "support_order_db", "source_id": data.get("source_id") or data["order_id"],
                "writer_id": data.get("writer_id") or "unknown", "verified_at": data.get("verified_at"),
                "updated_at": data.get("source_updated_at"), "conflict_status": data.get("conflict_status") or "unknown",
                "trust_score": 92.0, "policy_status": "allow", "prompt_eligible": True,
            })
        for row in policies:
            data = dict(row)
            items.append({
                "memory_id": f"policy:{data['document_id']}:{data['version']}", "kind": "policy_document",
                "summary": f"{data['document_id']} {data['version']} · {data['status']}",
                "source_type": "support_policy_db", "source_id": data["document_id"], "writer_id": "policy-administration",
                "verified_at": data["effective_from"], "updated_at": data["effective_from"], "conflict_status": "none",
                "trust_score": 90.0, "policy_status": "allow" if data["status"] == "active" else "review_required", "prompt_eligible": data["status"] == "active",
            })
        trust_by_level = {"high": 85.0, "medium": 70.0, "low": 55.0}
        for row in memories:
            data = dict(row)
            active = data["status"] == "active" and (not data.get("valid_until") or data["valid_until"] >= datetime.now(timezone.utc).isoformat())
            items.append({
                "memory_id": data["memory_id"], "kind": data["kind"], "summary": str(json.loads(data["value_json"])),
                "source_type": data["source_type"], "source_id": data.get("source_id"), "writer_id": "support-agent-memory",
                "verified_at": data.get("valid_from"), "updated_at": data.get("valid_from"), "conflict_status": "none",
                "trust_score": trust_by_level.get(data["trust_level"], 50.0), "policy_status": "allow" if active else "review_required", "prompt_eligible": active,
            })
        return items

    def get_sessions_list(self, limit: int = 50, tenant_id: str | None = None) -> dict[str, Any]:
        """Return distinct sessions with their event counts and latest timestamps."""
        try:
            with self.database.connect() as conn:
                agent_aggregation = (
                    "STRING_AGG(DISTINCT agent_id, ',')"
                    if self.database.driver == "postgres"
                    else "GROUP_CONCAT(DISTINCT agent_id)"
                )
                query = f"""SELECT trace_id as session_id,
                              COUNT(*) as event_count,
                              MAX(created_at) as latest_event,
                              {agent_aggregation} as agents
                       FROM memory_events
                       WHERE trace_id != '' AND trace_id IS NOT NULL"""
                params: list[Any] = []
                if tenant_id:
                    query += " AND tenant_id = ?"
                    params.append(tenant_id)
                query += """
                       GROUP BY trace_id
                       ORDER BY latest_event DESC
                       LIMIT ?"""
                params.append(limit)
                rows = conn.execute(query, params).fetchall()

                sessions = []
                for row in rows:
                    sessions.append({
                        "session_id": row["session_id"],
                        "event_count": row["event_count"],
                        "latest_event": row["latest_event"],
                        "agents": row["agents"].split(",") if row["agents"] else [],
                    })

                return {"sessions": sessions, "total": len(sessions)}
        except Exception as e:
            return {"sessions": [], "total": 0, "error": str(e)}

    def get_memory_influence_history(
        self, memory_id: str, tenant_id: str | None = None
    ) -> dict[str, Any]:
        """Show all decisions this memory influenced."""
        influenced_decisions = []
        for trace in self.decision_traces:
            if tenant_id and trace.tenant_id != tenant_id:
                continue
            if memory_id in trace.input_memory_ids:
                influenced_decisions.append({
                    "trace_id": trace.trace_id,
                    "timestamp": trace.timestamp,
                    "user_input": trace.user_input,
                    "llm_output_preview": trace.llm_output[:200] + "..." if len(trace.llm_output) > 200 else trace.llm_output,
                    "influence_score": trace.memory_influence_scores.get(memory_id, 0.0),
                    "total_memories_used": len(trace.input_memory_ids)
                })

        influenced_decisions.sort(key=lambda d: d["timestamp"], reverse=True)

        return {
            "memory_id": memory_id,
            "total_influences": len(influenced_decisions),
            "decisions": influenced_decisions
        }

    def get_decision_trace_detail(self, trace_id: str) -> dict[str, Any]:
        """
        Get detailed decision trace with causal chain and influence scores.

        Returns enhanced trace with:
        - Input memory influences (sorted by score)
        - Decision reasoning (extracted from LLM output)
        - Output memory operations
        """
        try:
            # Import reasoning extractor
            from .reasoning_extractor import ReasoningExtractor

            with self.database.connect() as conn:

                # Get decision trace
                trace = conn.execute(
                    "SELECT * FROM decision_traces WHERE trace_id = ?",
                    (trace_id,)
                ).fetchone()

                if not trace:
                    return {"error": "Trace not found"}

                trace_dict = dict(trace)

                # Parse JSON fields
                input_event_ids = json.loads(trace_dict.get("input_memory_events_json", "[]"))
                output_event_ids = json.loads(trace_dict.get("output_memory_events_json", "[]"))

                # Get input memory events with details
                input_influences = []
                if input_event_ids:
                    placeholders = ",".join("?" for _ in input_event_ids)
                    input_events = conn.execute(
                        f"""SELECT event_id, agent_id, memory_id, event_type, source_type,
                                  created_at, content_hash, metadata_json
                           FROM memory_events
                           WHERE event_id IN ({placeholders}) AND tenant_id = ?
                           ORDER BY created_at ASC""",
                        (*input_event_ids, trace_dict["tenant_id"])
                    ).fetchall()

                    # Calculate influence scores
                    decision_time = datetime.fromisoformat(trace_dict["timestamp"].replace("Z", "+00:00"))

                    for event in input_events:
                        event_dict = dict(event)
                        metadata = json.loads(event_dict.get("metadata_json", "{}"))

                        # Get similarity score if available
                        similarity = None
                        similarities = metadata.get("similarities", [])
                        if similarities:
                            similarity = max(similarities)

                        # Calculate influence (simple version)
                        influence_score = self._calculate_single_influence(
                            event_dict, decision_time, similarity
                        )

                        # Get content preview
                        content_preview = ""
                        after_val = metadata.get("_after_value")
                        if after_val:
                            content_str = str(after_val)
                            content_preview = content_str[:100] + "..." if len(content_str) > 100 else content_str

                        input_influences.append({
                            "event_id": event_dict["event_id"],
                            "memory_key": event_dict["memory_id"],
                            "memory_type": event_dict["source_type"],
                            "operation": event_dict["event_type"],
                            "influence_score": influence_score,
                            "content_preview": content_preview,
                            "similarity_score": similarity,
                            "timestamp": event_dict["created_at"],
                        })

                    # Sort by influence score
                    input_influences.sort(key=lambda x: x["influence_score"], reverse=True)

                # Get output memory events
                output_influences = []
                if output_event_ids:
                    placeholders = ",".join("?" for _ in output_event_ids)
                    output_events = conn.execute(
                        f"""SELECT event_id, agent_id, memory_id, event_type, source_type,
                                  created_at, content_hash
                           FROM memory_events
                           WHERE event_id IN ({placeholders}) AND tenant_id = ?
                           ORDER BY created_at ASC""",
                        (*output_event_ids, trace_dict["tenant_id"])
                    ).fetchall()

                    for event in output_events:
                        event_dict = dict(event)
                        output_influences.append({
                            "event_id": event_dict["event_id"],
                            "memory_key": event_dict["memory_id"],
                            "memory_type": event_dict["source_type"],
                            "operation": event_dict["event_type"],
                            "content_hash": event_dict.get("content_hash", ""),
                            "timestamp": event_dict["created_at"],
                        })

                # Extract reasoning from LLM output
                llm_output = trace_dict.get("llm_output", "")
                reasoning_data = ReasoningExtractor.extract_full_reasoning(llm_output)

                # Calculate total influence
                total_input_influence = sum(
                    inf["influence_score"] for inf in input_influences
                )

                return {
                    "trace_id": trace_dict["trace_id"],
                    "agent_id": trace_dict["agent_id"],
                    "session_id": trace_dict.get("session_id", ""),
                    "timestamp": trace_dict["timestamp"],

                    # Memory IN
                    "input_memory_influences": input_influences[:5],  # Top 5
                    "total_input_influence": round(total_input_influence, 2),

                    # Decision
                    "decision_type": reasoning_data["decision_type"],
                    "decision_confidence": reasoning_data["confidence"],
                    "decision_reasoning": reasoning_data["reasoning"],
                    "key_factors": reasoning_data.get("key_factors", []),
                    "llm_output": llm_output,

                    # Memory OUT
                    "output_memory_influences": output_influences,

                    # Metadata
                    "user_input": trace_dict.get("user_input", ""),
                    "metadata": json.loads(trace_dict.get("metadata_json", "{}")),
                }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def _calculate_single_influence(
        self,
        event: dict,
        decision_time: datetime,
        similarity: float = None
    ) -> float:
        """Calculate influence score for a single memory event"""
        # Base score
        base = 1.0

        # Similarity boost
        similarity_boost = similarity if similarity else 0.0

        # Recency boost
        try:
            event_time = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
            hours_diff = (decision_time - event_time).total_seconds() / 3600
            recency = 1.0 / (1.0 + hours_diff)
        except Exception:
            recency = 1.0

        # Memory type weight
        type_weights = {
            "episodic": 1.2,
            "semantic": 1.1,
            "procedural": 1.0,
            "working": 0.9,
            "user_preferences": 0.8,
        }
        memory_type = event.get("source_type", "working")
        type_weight = type_weights.get(memory_type, 1.0)

        # Calculate final score
        influence = base * (1.0 + similarity_boost) * recency * type_weight

        # Normalize to [0, 1]
        normalized = min(influence, 1.0)

        return round(normalized, 2)
