# MemGuard — Technical Design Document

**Version:** 0.1 (MVP Design)
**Status:** Draft
**Last Updated:** 2026-06-24

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Design](#2-architecture-design)
3. [Core Components](#3-core-components)
4. [Data Model & Schema](#4-data-model--schema)
5. [SDK Design](#5-sdk-design)
6. [Framework Adapters](#6-framework-adapters)
7. [API Layer](#7-api-layer)
8. [Storage Layer](#8-storage-layer)
9. [Analysis Engine](#9-analysis-engine)
10. [Dashboard & Visualization](#10-dashboard--visualization)
11. [Deployment Model](#11-deployment-model)
12. [MVP Scope & Roadmap](#12-mvp-scope--roadmap)
13. [Open Questions](#13-open-questions)

---

## 1. System Overview

MemGuard is a **Memory Observability and Governance infrastructure** that sits between AI agent systems and their memory backends. It intercepts, records, and analyzes every memory operation — providing developers with full visibility into what agents remember, why they behave the way they do, and how memory evolves over time.

### Core Design Principle

> Memory is state. State must be observable.

Current AI agent frameworks treat memory as a black box. MemGuard treats memory as a **first-class observable system**, following the same principle that made distributed tracing essential for microservices.

### What MemGuard Is NOT

- It is **not** a memory backend (it wraps existing ones: Mem0, Zep, MemGPT, Redis, vector DBs)
- It is **not** a prompt logging tool (it tracks semantic state, not raw text)
- It is **not** an LLM proxy (it only intercepts memory operations, not model calls)

---

## 2. Architecture Design

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AI Agent System                       │
│                                                         │
│  ┌─────────────┐    ┌──────────────────────────────┐   │
│  │  Agent Core  │───▶│     MemGuard SDK             │   │
│  │ (LLM calls) │    │  (Interceptor / Middleware)  │   │
│  └─────────────┘    └──────────┬───────────────────┘   │
│                                │ intercepts              │
│                    ┌───────────▼───────────┐            │
│                    │  Original Memory      │            │
│                    │  Backend (Mem0/Redis/ │            │
│                    │  Zep/VectorDB/etc.)   │            │
│                    └───────────────────────┘            │
└────────────────────────────────┬────────────────────────┘
                                 │ async events
                    ┌────────────▼────────────┐
                    │   MemGuard Control Plane │
                    │                         │
                    │  ┌──────────────────┐   │
                    │  │  Event Pipeline   │   │
                    │  │  (Redis Streams)  │   │
                    │  └────────┬─────────┘   │
                    │           │              │
                    │  ┌────────▼─────────┐   │
                    │  │  Storage Layer   │   │
                    │  │  - Event Store   │   │
                    │  │  - Graph Store   │   │
                    │  │  - Snapshot Store│   │
                    │  └────────┬─────────┘   │
                    │           │              │
                    │  ┌────────▼─────────┐   │
                    │  │  Analysis Engine │   │
                    │  │  - Tracer        │   │
                    │  │  - Diff Engine   │   │
                    │  │  - Conflict Det. │   │
                    │  └────────┬─────────┘   │
                    │           │              │
                    │  ┌────────▼─────────┐   │
                    │  │   REST / WS API  │   │
                    │  └────────┬─────────┘   │
                    └───────────┼─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │    MemGuard Dashboard    │
                    │  (Timeline / Trace / Diff│
                    └─────────────────────────┘
```

### 2.2 Integration Modes

MemGuard supports three integration modes, each with different tradeoffs:

| Mode | How It Works | Best For | Overhead |
|------|-------------|----------|----------|
| **Sidecar** | SDK fires async events to separate MemGuard process | Production systems | Near-zero (fire-and-forget) |
| **Inline** | SDK runs in-process, sync/async capture | Development, debugging | Low (~1-5ms per op) |
| **Proxy** | MemGuard wraps memory backend entirely | Governance use cases | Medium (adds network hop) |

**Recommended:** Start with Inline for development, migrate to Sidecar for production.

---

## 3. Core Components

### 3.1 Component Map

```
MemGuard
├── sdk/                    # Client-side interception
│   ├── core/               # Base interceptor & event emitter
│   ├── adapters/           # Framework-specific adapters
│   │   ├── langgraph.py
│   │   ├── autogen.py
│   │   ├── crewai.py
│   │   └── mem0.py
│   └── transport/          # Event delivery (HTTP / Redis / stdout)
│
├── server/                 # MemGuard Control Plane
│   ├── pipeline/           # Event ingestion & validation
│   ├── storage/            # Storage abstraction layer
│   ├── analysis/           # Analysis engine
│   └── api/                # REST + WebSocket API
│
└── dashboard/              # React frontend
    ├── timeline/            # Memory evolution view
    ├── trace/              # Decision trace replay
    └── diff/               # Memory diff viewer
```

---

## 4. Data Model & Schema

### 4.1 Core Entity: MemoryEvent

Every memory operation produces a `MemoryEvent`. This is the atomic unit of MemGuard.

```python
@dataclass
class MemoryEvent:
    # Identity
    event_id:       str         # UUID v4
    agent_id:       str         # Which agent
    session_id:     str         # Conversation/session
    trace_id:       str         # Links to an LLM call trace

    # What happened
    operation:      MemoryOp    # CREATE | READ | UPDATE | DELETE | QUERY | SEARCH
    timestamp:      datetime    # UTC, microsecond precision
    latency_ms:     float       # Time taken by underlying memory op

    # Memory target
    memory_key:     str         # Logical key / identifier
    namespace:      str         # Scoping (user_id, org_id, etc.)
    memory_type:    MemoryType  # EPISODIC | SEMANTIC | PROCEDURAL | WORKING

    # Content (hashed by default, raw if opted-in)
    before_value:   dict | None # State before op (for UPDATE/DELETE)
    after_value:    dict | None # State after op (for CREATE/UPDATE)
    content_hash:   str         # SHA-256 of content (for dedup/comparison)
    embedding_id:   str | None  # If vector memory

    # Causality
    caused_by:      str | None  # event_id of upstream event (lineage)
    llm_call_id:    str | None  # Which LLM completion triggered this
    user_message_id: str | None # Which user turn triggered this

    # Context
    context:        dict        # Framework-specific metadata
    tags:           list[str]   # Developer-defined labels
```

### 4.2 Memory Operation Types

```python
class MemoryOp(Enum):
    CREATE  = "create"   # New memory written
    READ    = "read"     # Memory retrieved by key
    UPDATE  = "update"   # Existing memory modified
    DELETE  = "delete"   # Memory removed
    QUERY   = "query"    # Structured search
    SEARCH  = "search"   # Semantic/vector search
```

### 4.3 Memory Types (Cognitive Model)

MemGuard adopts a cognitive science-inspired memory taxonomy:

| Type | Description | Example |
|------|-------------|---------|
| `EPISODIC` | Specific past events/interactions | "User mentioned their dog is named Max on 2024-01-05" |
| `SEMANTIC` | General facts about the world or user | "User is a software engineer in Singapore" |
| `PROCEDURAL` | How to do things, learned behaviors | "Always confirm before deleting files" |
| `WORKING` | Short-term, in-context state | "Current task: book a flight to Tokyo" |

### 4.4 Decision Trace Entity

Links memory reads to LLM outputs:

```python
@dataclass
class DecisionTrace:
    trace_id:           str
    agent_id:           str
    session_id:         str
    timestamp:          datetime
    
    # Input side
    input_memories:     list[str]   # event_ids of READ operations
    prompt_hash:        str         # Hash of the full prompt sent to LLM
    
    # Output side
    output_hash:        str         # Hash of LLM response
    output_summary:     str         # Optional: short description of decision
    
    # New memories produced
    output_memories:    list[str]   # event_ids of CREATE/UPDATE after this call
    
    # Analysis
    memory_influence_score: float   # 0-1: how much memory shaped the output
```

### 4.5 Lineage Graph Model

Represented as a directed acyclic graph (DAG):

```
Nodes:  MemoryEvent (each version of a memory)
Edges:  "derived_from", "updated_by", "conflicted_with", "merged_into"
```

Example lineage:
```
[CREATE: "user likes Python" @ t=0]
         │ updated_by
         ▼
[UPDATE: "user likes Python & Rust" @ t=100]
         │ conflicted_with
         ▼
[CREATE: "user prefers Go" @ t=200]  ← from different session
```

---

## 5. SDK Design

### 5.1 Core Interceptor (Python)

```python
# memguard/core/interceptor.py

from memguard.core.event import MemoryEvent, MemoryOp
from memguard.transport import Transport
import functools, time, hashlib, uuid

class MemGuardInterceptor:
    """
    Base class. Wraps any memory backend.
    Framework adapters subclass or compose this.
    """
    
    def __init__(
        self,
        agent_id: str,
        transport: Transport,
        capture_content: bool = False,  # opt-in for raw content
        namespace: str = "default",
    ):
        self.agent_id = agent_id
        self.transport = transport
        self.capture_content = capture_content
        self.namespace = namespace
        self._session_id: str | None = None

    def set_session(self, session_id: str):
        self._session_id = session_id

    def wrap_operation(
        self,
        operation: MemoryOp,
        key: str,
        before_value: dict | None = None,
        after_value: dict | None = None,
        **context,
    ) -> str:
        """Record a memory event. Returns event_id."""
        
        event = MemoryEvent(
            event_id=str(uuid.uuid4()),
            agent_id=self.agent_id,
            session_id=self._session_id or "unknown",
            trace_id=context.get("trace_id", ""),
            operation=operation,
            timestamp=datetime.utcnow(),
            memory_key=key,
            namespace=self.namespace,
            before_value=before_value if self.capture_content else None,
            after_value=after_value if self.capture_content else None,
            content_hash=self._hash(after_value or before_value),
            caused_by=context.get("caused_by"),
            llm_call_id=context.get("llm_call_id"),
            context=context,
        )
        
        # Fire-and-forget: never block the agent
        self.transport.emit_async(event)
        return event.event_id

    def _hash(self, value: dict | None) -> str:
        if not value:
            return ""
        return hashlib.sha256(
            str(sorted(value.items())).encode()
        ).hexdigest()[:16]
```

### 5.2 Context Manager for Tracing

```python
# memguard/core/trace.py

from contextvars import ContextVar

_current_trace_id: ContextVar[str | None] = ContextVar(
    "memguard_trace_id", default=None
)
_current_llm_call_id: ContextVar[str | None] = ContextVar(
    "memguard_llm_call_id", default=None
)

class MemGuardTrace:
    """
    Use as context manager around LLM calls.
    Automatically links subsequent memory ops to this trace.
    
    Example:
        with MemGuardTrace(trace_id="call-123") as trace:
            memories = agent.recall("user preferences")
            response = llm.complete(prompt)
            agent.remember(response)
    """
    
    def __init__(self, trace_id: str | None = None):
        self.trace_id = trace_id or str(uuid.uuid4())
        self._tokens = []

    def __enter__(self):
        self._tokens.append(
            _current_trace_id.set(self.trace_id)
        )
        return self

    def __exit__(self, *args):
        for token in self._tokens:
            _current_trace_id.reset(token)
```

### 5.3 Transport Layer

```python
# memguard/transport/base.py

class Transport(ABC):
    @abstractmethod
    async def emit(self, event: MemoryEvent): ...
    
    def emit_async(self, event: MemoryEvent):
        """Non-blocking: schedule on event loop, never raise."""
        try:
            asyncio.get_event_loop().create_task(
                self.emit(event)
            )
        except Exception:
            pass  # Observability must never break production

# Implementations:
# HttpTransport     → POST to MemGuard server
# RedisTransport    → XADD to Redis Stream
# StdoutTransport   → JSON to stdout (dev/testing)
# FileTransport     → Append to JSONL file (offline)
```

---

## 6. Framework Adapters

### 6.1 LangGraph Adapter

LangGraph uses a `Checkpointer` for state persistence. MemGuard wraps it:

```python
# memguard/adapters/langgraph.py

from langgraph.checkpoint.base import BaseCheckpointSaver
from memguard.core.interceptor import MemGuardInterceptor

class MemGuardCheckpointer(BaseCheckpointSaver):
    """Drop-in replacement for LangGraph's checkpointer."""

    def __init__(self, inner: BaseCheckpointSaver, interceptor: MemGuardInterceptor):
        self.inner = inner
        self.interceptor = interceptor

    def put(self, config, checkpoint, metadata, *args):
        # Capture BEFORE state
        existing = self.inner.get(config)
        
        # Delegate to real checkpointer
        result = self.inner.put(config, checkpoint, metadata, *args)
        
        # Record event
        self.interceptor.wrap_operation(
            operation=MemoryOp.UPDATE if existing else MemoryOp.CREATE,
            key=config["configurable"]["thread_id"],
            before_value=existing,
            after_value=checkpoint,
            source="langgraph_checkpoint",
        )
        return result

    def get(self, config, *args):
        result = self.inner.get(config, *args)
        if result:
            self.interceptor.wrap_operation(
                operation=MemoryOp.READ,
                key=config["configurable"]["thread_id"],
                after_value=result,
            )
        return result

# Usage:
# from langgraph.checkpoint.memory import MemorySaver
# inner = MemorySaver()
# checkpointer = MemGuardCheckpointer(inner, interceptor)
# graph = workflow.compile(checkpointer=checkpointer)
```

### 6.2 Mem0 Adapter

```python
# memguard/adapters/mem0.py

class MemGuardMem0(Memory):
    """Wraps Mem0's Memory class with observability."""

    def __init__(self, inner: Memory, interceptor: MemGuardInterceptor):
        self.inner = inner
        self.interceptor = interceptor

    def add(self, messages, user_id, **kwargs):
        result = self.inner.add(messages, user_id=user_id, **kwargs)
        for mem in result.get("results", []):
            self.interceptor.wrap_operation(
                operation=MemoryOp.CREATE,
                key=mem["id"],
                after_value={"text": mem["memory"]},
                user_id=user_id,
            )
        return result

    def search(self, query, user_id, **kwargs):
        result = self.inner.search(query, user_id=user_id, **kwargs)
        for mem in result.get("results", []):
            self.interceptor.wrap_operation(
                operation=MemoryOp.SEARCH,
                key=mem["id"],
                after_value={"text": mem["memory"], "score": mem.get("score")},
                query=query,
                user_id=user_id,
            )
        return result
```

### 6.3 AutoGen Adapter

```python
# memguard/adapters/autogen.py

class MemGuardAgent(ConversableAgent):
    """AutoGen agent with memory observability."""

    def __init__(self, *args, memguard: MemGuardInterceptor, **kwargs):
        super().__init__(*args, **kwargs)
        self._memguard = memguard

    def _process_received_message(self, message, sender, silent):
        # Intercept working memory updates
        before = dict(self.chat_messages)
        result = super()._process_received_message(message, sender, silent)
        self._memguard.wrap_operation(
            operation=MemoryOp.UPDATE,
            key=f"chat_history:{sender.name}",
            before_value=before.get(sender, []),
            after_value=self.chat_messages.get(sender, []),
        )
        return result
```

### 6.4 Adapter Support Matrix

| Framework | Memory Type | Adapter Status | Notes |
|-----------|------------|----------------|-------|
| LangGraph | State/Checkpoint | ✅ MVP | Wraps BaseCheckpointSaver |
| Mem0 | Semantic | ✅ MVP | Wraps Memory class |
| AutoGen | Working/Chat | 🔄 Beta | Hook into message processing |
| CrewAI | Entity/Short-term | 🔄 Beta | Monkey-patch memory methods |
| MemGPT/Letta | Archival/Recall | 📋 Planned | Intercept storage calls |
| Custom | Any | ✅ MVP | Use base interceptor directly |

---

## 7. API Layer

### 7.1 REST API Design

Base URL: `https://api.memguard.io/v1`

**Events**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/events` | POST | Ingest one or more memory events |
| `/events` | GET | Query events with filters |
| `/events/{event_id}` | GET | Fetch a single event |
| `/events/{event_id}/lineage` | GET | Get full lineage chain |

**Sessions**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sessions/{session_id}/timeline` | GET | Memory timeline for a session |
| `/sessions/{session_id}/trace` | GET | Decision traces for a session |
| `/sessions/{session_id}/replay` | POST | Replay memory state at a given time |

**Agents**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agents/{agent_id}/memory-state` | GET | Current memory snapshot |
| `/agents/{agent_id}/stats` | GET | Memory usage statistics |
| `/agents/{agent_id}/conflicts` | GET | Detected memory conflicts |

**Analysis**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analysis/diff` | POST | Diff two memory states |
| `/analysis/influence` | GET | Which memories influenced a decision |
| `/analysis/conflicts` | GET | All detected conflicts |
| `/analysis/stale` | GET | Memories flagged as stale |

### 7.2 Event Ingestion Endpoint

```
POST /v1/events
Authorization: Bearer <api_key>

Body:
{
  "events": [
    {
      "event_id": "uuid",
      "agent_id": "agent-001",
      "session_id": "session-abc",
      "operation": "create",
      "memory_key": "user_preference_lang",
      "namespace": "user:u_123",
      "memory_type": "semantic",
      "after_value": { "language": "Python" },
      "content_hash": "a3f4b2c1",
      "timestamp": "2026-06-24T10:00:00.000Z",
      "llm_call_id": "call-xyz"
    }
  ]
}

Response 202 Accepted:
{
  "accepted": 1,
  "rejected": 0,
  "event_ids": ["uuid"]
}
```

### 7.3 WebSocket: Real-Time Stream

```
WS wss://api.memguard.io/v1/stream

Subscribe:
{ "action": "subscribe", "agent_id": "agent-001" }

Event Push:
{
  "type": "memory_event",
  "event": { ...MemoryEvent... },
  "alerts": [
    { "type": "conflict", "conflicted_with": "event-id-xyz", "severity": "high" }
  ]
}
```

---

## 8. Storage Layer

### 8.1 Storage Architecture

MemGuard uses a **three-store architecture**:

```
┌─────────────────────────────────────────────────────────┐
│                    Storage Layer                         │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Event Store (PostgreSQL + TimescaleDB)          │   │
│  │  - Append-only log of all MemoryEvents           │   │
│  │  - Time-series partitioned by timestamp          │   │
│  │  - JSONB columns for flexible content            │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Lineage Graph (PostgreSQL recursive CTEs)       │   │
│  │  - memory_nodes: one row per event               │   │
│  │  - memory_edges: directed relationships          │   │
│  │  - Traversal via WITH RECURSIVE queries          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Snapshot Store (PostgreSQL JSONB)               │   │
│  │  - Periodic full memory state snapshots          │   │
│  │  - Enables fast point-in-time reconstruction     │   │
│  │  - Snapshot interval: configurable (default: 50  │   │
│  │    events or 1 hour, whichever comes first)      │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 8.2 Database Schema (PostgreSQL)

```sql
-- Core event table (TimescaleDB hypertable for time-series)
CREATE TABLE memory_events (
    event_id        UUID PRIMARY KEY,
    agent_id        TEXT NOT NULL,
    session_id      TEXT NOT NULL,
    trace_id        TEXT,
    llm_call_id     TEXT,
    
    operation       TEXT NOT NULL,   -- create/read/update/delete/query/search
    memory_type     TEXT,            -- episodic/semantic/procedural/working
    memory_key      TEXT NOT NULL,
    namespace       TEXT NOT NULL DEFAULT 'default',
    
    content_hash    TEXT,
    before_hash     TEXT,            -- Hash of before_value
    after_hash      TEXT,            -- Hash of after_value
    
    -- Raw content (optional, only if capture_content=True)
    before_value    JSONB,
    after_value     JSONB,
    
    context         JSONB DEFAULT '{}',
    tags            TEXT[],
    latency_ms      FLOAT,
    
    timestamp       TIMESTAMPTZ NOT NULL,
    ingested_at     TIMESTAMPTZ DEFAULT now(),
    
    caused_by       UUID REFERENCES memory_events(event_id)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('memory_events', 'timestamp');

-- Indexes
CREATE INDEX ON memory_events (agent_id, timestamp DESC);
CREATE INDEX ON memory_events (session_id, timestamp DESC);
CREATE INDEX ON memory_events (memory_key, namespace, timestamp DESC);
CREATE INDEX ON memory_events (llm_call_id) WHERE llm_call_id IS NOT NULL;

-- Lineage graph (adjacency list)
CREATE TABLE memory_edges (
    edge_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_event_id   UUID NOT NULL REFERENCES memory_events(event_id),
    to_event_id     UUID NOT NULL REFERENCES memory_events(event_id),
    edge_type       TEXT NOT NULL,  -- derived_from/updated_by/conflicted_with/merged_into
    confidence      FLOAT DEFAULT 1.0,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ON memory_edges (from_event_id);
CREATE INDEX ON memory_edges (to_event_id);

-- Snapshots
CREATE TABLE memory_snapshots (
    snapshot_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id        TEXT NOT NULL,
    session_id      TEXT,
    snapshot_time   TIMESTAMPTZ NOT NULL,
    last_event_id   UUID REFERENCES memory_events(event_id),
    memory_state    JSONB NOT NULL,  -- Full memory state at this point
    event_count     INT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- Decision traces
CREATE TABLE decision_traces (
    trace_id            UUID PRIMARY KEY,
    agent_id            TEXT NOT NULL,
    session_id          TEXT NOT NULL,
    timestamp           TIMESTAMPTZ NOT NULL,
    input_event_ids     UUID[],      -- READ events that preceded this LLM call
    output_event_ids    UUID[],      -- CREATE/UPDATE events that followed
    prompt_hash         TEXT,
    output_hash         TEXT,
    memory_influence_score FLOAT,
    metadata            JSONB DEFAULT '{}'
);
```

### 8.3 Point-in-Time Memory Reconstruction

```python
def reconstruct_memory_state(
    agent_id: str,
    at_time: datetime,
    session_id: str | None = None
) -> dict:
    """
    Reconstruct the exact memory state an agent had at `at_time`.
    Uses snapshot + event replay for efficiency.
    """
    
    # 1. Find nearest snapshot before at_time
    snapshot = db.query("""
        SELECT * FROM memory_snapshots
        WHERE agent_id = %s AND snapshot_time <= %s
        ORDER BY snapshot_time DESC LIMIT 1
    """, [agent_id, at_time])
    
    # 2. Replay events from snapshot forward
    events = db.query("""
        SELECT * FROM memory_events
        WHERE agent_id = %s
          AND timestamp > %s AND timestamp <= %s
          AND operation IN ('create', 'update', 'delete')
        ORDER BY timestamp ASC
    """, [agent_id, snapshot.snapshot_time if snapshot else epoch, at_time])
    
    # 3. Apply events to snapshot state
    state = snapshot.memory_state if snapshot else {}
    for event in events:
        key = f"{event.namespace}:{event.memory_key}"
        if event.operation == "delete":
            state.pop(key, None)
        else:
            state[key] = event.after_value
    
    return state
```

---

## 9. Analysis Engine

### 9.1 Conflict Detection

A conflict is detected when two memories for the same key contradict each other:

```python
class ConflictDetector:
    
    CONFLICT_TYPES = {
        "same_key_different_value":  # Same key, hash mismatch
        "semantic_contradiction":    # Different keys, but semantically opposite
        "temporal_inconsistency":    # Later memory contradicts factual claim from earlier
    }

    def detect_on_write(self, event: MemoryEvent) -> list[Conflict]:
        conflicts = []
        
        # Check 1: Same key, different hash
        existing = self._get_latest_for_key(event.memory_key, event.namespace)
        if existing and existing.content_hash != event.content_hash:
            conflicts.append(Conflict(
                type="same_key_different_value",
                event_a=existing.event_id,
                event_b=event.event_id,
                severity=self._severity(existing, event),
            ))
        
        # Check 2: Semantic contradiction (if embeddings enabled)
        if self.embedding_client:
            conflicts.extend(
                self._check_semantic_conflicts(event)
            )
        
        return conflicts

    def _severity(self, a: MemoryEvent, b: MemoryEvent) -> str:
        # Higher severity if the memories are far apart in time
        # or if they are of type SEMANTIC (facts, not episodic)
        if b.memory_type == MemoryType.SEMANTIC:
            return "high"
        age_hours = (b.timestamp - a.timestamp).total_seconds() / 3600
        return "high" if age_hours > 24 else "medium"
```

### 9.2 Staleness Detection

```python
class StalenessDetector:
    
    def flag_stale(
        self,
        agent_id: str,
        max_age_days: int = 30,
        min_read_recency_days: int = 7
    ) -> list[StaleMemory]:
        
        return db.query("""
            SELECT 
                memory_key,
                namespace,
                MAX(timestamp) FILTER (WHERE operation IN ('create','update')) AS last_written,
                MAX(timestamp) FILTER (WHERE operation = 'read') AS last_read,
                COUNT(*) FILTER (WHERE operation = 'read') AS read_count
            FROM memory_events
            WHERE agent_id = %s
            GROUP BY memory_key, namespace
            HAVING 
                MAX(timestamp) FILTER (WHERE operation IN ('create','update')) 
                    < NOW() - INTERVAL '%s days'
                OR MAX(timestamp) FILTER (WHERE operation = 'read') 
                    < NOW() - INTERVAL '%s days'
        """, [agent_id, max_age_days, min_read_recency_days])
```

### 9.3 Memory Influence Scoring

How much did memory influence a given LLM decision?

```python
def compute_influence_score(trace_id: str) -> float:
    """
    Score: 0 = memory had no influence, 1 = decision fully determined by memory
    
    Formula:
    - Base score from number of memories read before the LLM call
    - Weighted by how recent those memories were
    - Weighted by memory_type (SEMANTIC > PROCEDURAL > EPISODIC > WORKING)
    """
    trace = get_trace(trace_id)
    
    if not trace.input_event_ids:
        return 0.0
    
    type_weights = {
        MemoryType.SEMANTIC:    1.0,
        MemoryType.PROCEDURAL:  0.8,
        MemoryType.EPISODIC:    0.6,
        MemoryType.WORKING:     0.3,
    }
    
    scores = []
    for event_id in trace.input_event_ids:
        event = get_event(event_id)
        recency = _recency_score(event.timestamp, trace.timestamp)
        type_w  = type_weights.get(event.memory_type, 0.5)
        scores.append(recency * type_w)
    
    return min(1.0, sum(scores) / max(1, len(scores)))
```

### 9.4 Memory Diff Engine

```python
@dataclass
class MemoryDiff:
    added:    list[dict]  # Keys present in state_b but not state_a
    removed:  list[dict]  # Keys present in state_a but not state_b
    modified: list[dict]  # Keys present in both but with different content_hash
    unchanged: int        # Count of unchanged keys

def diff_states(state_a: dict, state_b: dict) -> MemoryDiff:
    keys_a = set(state_a.keys())
    keys_b = set(state_b.keys())
    
    added    = [{"key": k, "value": state_b[k]} for k in keys_b - keys_a]
    removed  = [{"key": k, "value": state_a[k]} for k in keys_a - keys_b]
    modified = [
        {"key": k, "before": state_a[k], "after": state_b[k]}
        for k in keys_a & keys_b
        if state_a[k] != state_b[k]
    ]
    unchanged = len([k for k in keys_a & keys_b if state_a[k] == state_b[k]])
    
    return MemoryDiff(added, removed, modified, unchanged)
```

---

## 10. Dashboard & Visualization

### 10.1 Core Views

**Memory Timeline View**
- X-axis: time
- Y-axis: memory keys (grouped by namespace)
- Events shown as colored dots (CREATE=green, UPDATE=yellow, DELETE=red, READ=blue)
- Click to inspect event details and lineage
- Playback mode: step through events at adjustable speed

**Decision Trace View**
- Given a specific LLM output, shows:
  - Which memories were READ before the call
  - The memory influence score
  - Which new memories were CREATED/UPDATED after
- Rendered as a flow diagram: `[Memory reads] → [LLM Call] → [Output] → [Memory writes]`

**Memory Diff View**
- Compare memory state at any two timestamps
- Shows added, removed, modified keys
- Side-by-side value diff for modified keys

**Conflict Dashboard**
- List of detected conflicts with severity
- Side-by-side comparison of conflicting memories
- Timeline showing when the conflict emerged

### 10.2 Frontend Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| Framework | React 18 | Ecosystem, component reuse |
| State | Zustand | Lightweight, no boilerplate |
| Timeline | D3.js | Custom temporal visualization |
| Graph/DAG | React Flow | Lineage & trace diagrams |
| Charts | Recharts | Stats and metrics |
| Diff View | react-diff-viewer | Side-by-side diffs |
| API Client | SWR + fetch | Caching, real-time |
| WebSocket | native WS | Real-time event stream |

---

## 11. Deployment Model

### 11.1 MVP: Self-Hosted (Docker Compose)

```yaml
# docker-compose.yml
services:
  postgres:
    image: timescale/timescaledb:latest-pg16
    environment:
      POSTGRES_DB: memguard
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    # Used for event pipeline in early stage

  memguard-server:
    image: memguard/server:latest
    depends_on: [postgres, redis]
    environment:
      DATABASE_URL: postgresql://...
      REDIS_URL: redis://redis:6379
      API_KEY_SALT: ${API_KEY_SALT}
    ports:
      - "8000:8000"   # REST API
      - "8001:8001"   # WebSocket

  memguard-dashboard:
    image: memguard/dashboard:latest
    depends_on: [memguard-server]
    ports:
      - "3000:3000"
```

### 11.2 Scaling Path

| Stage | Infra | Volume | Notes |
|-------|-------|--------|-------|
| MVP | Docker Compose, 1 server | < 10K events/day | Single developer or small team |
| Early | Kubernetes, 2-3 pods | < 1M events/day | Small production deployment |
| Growth | K8s + Kafka + read replicas | < 100M events/day | Multiple agents, multi-tenant |
| Enterprise | Multi-region, dedicated clusters | Unlimited | Compliance-grade SLAs |

### 11.3 Data Privacy Considerations

- **Content hashing by default**: Raw memory content is never stored unless `capture_content=True` is explicitly set
- **Namespace isolation**: Each user/org has isolated namespaces; no cross-contamination
- **Retention policies**: Configurable event TTL (default: 90 days for events, 30 days for raw content)
- **PII detection**: Optional pre-flight PII scanner on after_value before storage (uses regex + NER)
- **Encryption at rest**: PostgreSQL-level encryption; optional field-level encryption for after_value

---

## 12. MVP Scope & Roadmap

### Phase 1 — MVP (Weeks 1–6)

Goal: Working prototype that a developer can integrate in < 30 minutes.

- [ ] Core SDK (Python): Base interceptor + HttpTransport + StdoutTransport
- [ ] LangGraph adapter
- [ ] Mem0 adapter
- [ ] Event ingestion API (POST /v1/events)
- [ ] PostgreSQL event store (no TimescaleDB yet)
- [ ] Basic timeline query API
- [ ] Simple web dashboard: event log + basic timeline
- [ ] Docker Compose deployment
- [ ] README + quickstart guide

**Success metric:** 3 external developers successfully instrument their LangGraph agent.

### Phase 2 — Developer Experience (Weeks 7–12)

- [ ] AutoGen + CrewAI adapters
- [ ] Decision trace linking (llm_call_id → memories)
- [ ] Conflict detection (rule-based, same-key)
- [ ] Memory diff view in dashboard
- [ ] TypeScript SDK
- [ ] API key authentication
- [ ] TimescaleDB migration

**Success metric:** Dashboard shows a complete memory timeline + at least 1 detected conflict.

### Phase 3 — Analysis & Governance (Weeks 13–20)

- [ ] Memory influence scoring
- [ ] Staleness detection
- [ ] Semantic conflict detection (embedding-based)
- [ ] Point-in-time replay in dashboard
- [ ] Memory quarantine API (soft-delete with audit log)
- [ ] Alert webhooks (Slack, email)
- [ ] Multi-tenant support
- [ ] Compliance export (JSON/CSV audit log)

---

## 13. Open Questions

These are design decisions that require further research or external input:

| # | Question | Options | Priority |
|---|----------|---------|----------|
| 1 | Should content be stored by default or hashed? | (a) Hash only, opt-in for raw; (b) Store raw, opt-in for PII redaction | High |
| 2 | How to link memory events to LLM calls without requiring LLM instrumentation? | (a) Require trace_id injection; (b) Time-window heuristic; (c) Wrap LLM client too | High |
| 3 | Should MemGuard support synchronous governance (blocking writes)? | (a) Read-only observability (safe, simple); (b) Write interception (powerful, risky) | Medium |
| 4 | Embedding strategy for semantic conflict detection | (a) Use agent's existing embeddings; (b) Re-embed in MemGuard; (c) Skip for MVP | Medium |
| 5 | Multi-tenant data isolation model | (a) Schema-per-tenant (strong isolation, complex ops); (b) Row-level security (simpler, less isolated) | Low (post-MVP) |
| 6 | Should MemGuard be open-source core + cloud premium? | (a) Fully open source; (b) Open-core; (c) Closed source SaaS | Strategic |

---

## Appendix A: Key Design Decisions Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language for server | Python | Matches agent ecosystem; FastAPI is fast to iterate |
| DB for events | PostgreSQL | Proven reliability; TimescaleDB adds time-series power without a new system |
| Graph store | PostgreSQL recursive CTEs (MVP) | Avoids adding Neo4j dependency for MVP; migrate later if needed |
| Event pipeline | Redis Streams (MVP) → Kafka | Redis is operationally simple; Kafka when throughput demands it |
| Content storage default | Hash only | Privacy-first; trust is earned before storing raw data |
| SDK blocking behavior | Never block | Observability must have zero impact on agent reliability |

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| Memory Event | An atomic record of a single memory operation (create/read/update/delete) |
| Decision Trace | A record linking memory reads → LLM call → LLM output → memory writes |
| Memory Lineage | The chain of events showing how a piece of memory evolved over time |
| Memory Namespace | A logical scope for memory isolation (e.g., per-user, per-agent, per-org) |
| Content Hash | A short hash of memory value content, used for comparison without exposing raw data |
| Conflict | Two memories for the same key with inconsistent content |
| Stale Memory | A memory that has not been accessed or updated within a configured threshold |
| Snapshot | A full capture of an agent's memory state at a specific point in time |
| Influence Score | A 0–1 metric of how much memory shaped a specific LLM decision |

---

*MemGuard Technical Design Document — v0.1*
*All content is confidential and for internal / incubation use only.*
