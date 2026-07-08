from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .schemas import MemoryQueryRequest, MemoryWriteRequest, TimelineQueryRequest

_DEFAULT_DB = Path(__file__).parent.parent / "memguard.db" if __file__ else Path("memguard.db")
DB_PATH = Path(os.getenv("MEMGUARD_DB_PATH", _DEFAULT_DB))


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
        self.adapter = LocalLLMAdapter()
        self.events: list[MemoryEvent] = []           # In-memory cache
        self.decision_traces: list[DecisionTrace] = []  # In-memory cache
        self._lock = threading.Lock()
        self._init_db()

    # ── SQLite Persistence ──────────────────────────────────

    def _init_db(self) -> None:
        """Initialize SQLite database for persistent storage."""
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_events (
                    event_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    memory_id TEXT NOT NULL,
                    trace_id TEXT,
                    event_type TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    content TEXT,
                    content_hash TEXT,
                    policy_decision TEXT NOT NULL DEFAULT 'allow',
                    trust_score REAL NOT NULL DEFAULT 50.0,
                    created_at TEXT NOT NULL,
                    parent_event_id TEXT,
                    embedding_json TEXT DEFAULT '[]',
                    metadata_json TEXT DEFAULT '{}'
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS decision_traces (
                    trace_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    session_id TEXT,
                    timestamp TEXT NOT NULL,
                    input_memory_ids_json TEXT DEFAULT '[]',
                    input_memory_events_json TEXT DEFAULT '[]',
                    user_input TEXT,
                    llm_prompt_hash TEXT,
                    llm_output TEXT,
                    llm_output_hash TEXT,
                    llm_model TEXT,
                    output_memory_ids_json TEXT DEFAULT '[]',
                    output_memory_events_json TEXT DEFAULT '[]',
                    memory_influence_scores_json TEXT DEFAULT '{}',
                    total_influence_score REAL DEFAULT 0.0,
                    metadata_json TEXT DEFAULT '{}'
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_agent
                ON memory_events(tenant_id, agent_id, created_at DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_memory
                ON memory_events(memory_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_traces_agent
                ON decision_traces(tenant_id, agent_id)
            """)
            conn.commit()

        # Load existing events into memory cache
        self._load_from_db()

    def _load_from_db(self) -> None:
        """Load persisted events into memory cache on startup."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.row_factory = sqlite3.Row
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
        """Write a single event to SQLite."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO memory_events
                       (event_id, tenant_id, agent_id, memory_id, trace_id,
                        event_type, source_type, content, content_hash,
                        policy_decision, trust_score, created_at,
                        parent_event_id, embedding_json, metadata_json)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
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
                # 保存 before_value 和 after_value 到 metadata
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

    def detect_conflicts(self, window_seconds: float = 5.0) -> dict[str, Any]:
        """
        Detect concurrent writes to the same memory_key by different agents.

        Only reports the FIRST conflict per (memory_key, agent_pair) to avoid
        explosion when many events share a key within the window.
        """
        conflicts: list[dict] = []
        seen_pairs: set = set()  # dedup: (key, agent_a, agent_b)
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """SELECT event_id, agent_id, memory_id, event_type, created_at, content_hash
                       FROM memory_events
                       WHERE event_type IN ('update', 'create')
                       ORDER BY memory_id, created_at ASC"""
                ).fetchall()

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

                        # 去重：每个 (key, agent_a, agent_b) 组合只报一次
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
        self.decision_traces.append(trace)

    def _persist_trace(self, trace: DecisionTrace) -> None:
        """Write a decision trace to SQLite."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO decision_traces
                       (trace_id, tenant_id, agent_id, session_id, timestamp,
                        input_memory_ids_json, input_memory_events_json,
                        user_input, llm_prompt_hash, llm_output, llm_output_hash,
                        llm_model, output_memory_ids_json, output_memory_events_json,
                        memory_influence_scores_json, total_influence_score, metadata_json)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
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

    def get_decision_trace(self, trace_id: str) -> dict[str, Any] | None:
        """Get a specific decision trace by ID (from SQLite, survives restart)."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT * FROM decision_traces WHERE trace_id = ?", (trace_id,)
                ).fetchone()
                if row:
                    d = dict(row)
                    for k in ("input_memory_ids_json", "input_memory_events_json",
                              "output_memory_ids_json", "output_memory_events_json",
                              "memory_influence_scores_json", "metadata_json"):
                        if d.get(k):
                            try:
                                d[k.replace("_json", "")] = json.loads(d[k])
                            except Exception:
                                pass
                    return d
        except Exception:
            pass
        return None

    def get_decision_traces_by_agent(self, tenant_id: str, agent_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get all decision traces for a specific agent (from SQLite, survives restart)."""
        return self._query_traces("WHERE tenant_id = ? AND agent_id = ?", (tenant_id, agent_id), limit)

    def get_decision_traces_by_tenant(self, tenant_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Get all decision traces for a tenant across all agents (from SQLite)."""
        return self._query_traces("WHERE tenant_id = ?", (tenant_id,), limit)

    def _query_traces(self, where_clause: str, params: tuple, limit: int) -> list[dict[str, Any]]:
        """Shared SQLite query helper for decision traces. Enriches with event details."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.row_factory = sqlite3.Row
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
                    all_event_ids = d.get("input_memory_ids", []) + d.get("output_memory_ids", [])
                    if all_event_ids:
                        placeholders = ",".join("?" for _ in all_event_ids)
                        event_rows = conn.execute(
                            f"SELECT event_id, agent_id, memory_id, event_type FROM memory_events WHERE event_id IN ({placeholders})",
                            all_event_ids,
                        ).fetchall()
                        event_map = {}
                        for er in event_rows:
                            event_map[er["event_id"]] = {
                                "agent_id": er["agent_id"],
                                "memory_key": er["memory_id"],
                                "operation": er["event_type"],
                            }
                        # Enrich input side
                        d["input_memory_details"] = [event_map.get(eid, {"memory_key": eid[:12]+"..."}) for eid in d.get("input_memory_ids", [])]
                        # Enrich output side
                        d["output_memory_details"] = [event_map.get(eid, {"memory_key": eid[:12]+"..."}) for eid in d.get("output_memory_ids", [])]

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
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.row_factory = sqlite3.Row
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

    def get_sessions_list(self, limit: int = 50) -> dict[str, Any]:
        """Return distinct sessions with their event counts and latest timestamps."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """SELECT trace_id as session_id,
                              COUNT(*) as event_count,
                              MAX(created_at) as latest_event,
                              GROUP_CONCAT(DISTINCT agent_id) as agents
                       FROM memory_events
                       WHERE trace_id != '' AND trace_id IS NOT NULL
                       GROUP BY trace_id
                       ORDER BY latest_event DESC
                       LIMIT ?""",
                    (limit,)
                ).fetchall()

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

    def get_memory_influence_history(self, memory_id: str) -> dict[str, Any]:
        """Show all decisions this memory influenced."""
        influenced_decisions = []
        for trace in self.decision_traces:
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
