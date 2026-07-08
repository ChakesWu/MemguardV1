# MemGuard — Product Specification for Claude Code
# Version: MVP (v0.1)
# Scope: Build only what is marked [MVP]. 
#        Do NOT build anything marked [LATER].

---

## What This Product Does (One Paragraph)

MemGuard is a memory observability and security layer 
for AI agents. It wraps any agent's memory backend, 
intercepts every read/write operation, records a 
structured event log, detects memory poisoning attempts, 
and surfaces all of this through a terminal output and 
a minimal web dashboard.

The core loop is:
  Agent writes/reads memory
  → MemGuard SDK intercepts
  → MemoryEvent recorded
  → Terminal shows what happened in real time
  → Dashboard shows timeline + conflicts

---

## MVP Scope (Build This First)

### 1. SDK Core [MVP]

File: memguard/core/interceptor.py

The SDK wraps any memory client. 
It intercepts operations without blocking the agent.

Required operations to intercept:
  - write (CREATE / UPDATE)
  - read (READ)
  - delete (DELETE)
  - search (SEARCH / QUERY)

For each operation, record a MemoryEvent:

  event_id:       uuid4
  agent_id:       string (passed by developer)
  session_id:     string (passed by developer)
  operation:      "create" | "read" | "update" | 
                  "delete" | "search"
  memory_key:     string
  namespace:      string (default: "default")
  before_hash:    sha256[:16] of before_value
  after_hash:     sha256[:16] of after_value
  timestamp:      UTC datetime
  latency_ms:     float
  caused_by:      event_id | null
  llm_call_id:    string | null
  context:        dict (any extra metadata)

CRITICAL: The SDK must NEVER block the agent.
All event emission must be fire-and-forget async.
If MemGuard fails, the agent continues normally.
Use try/except everywhere. Swallow all errors silently.

Usage pattern the developer writes:
  from memguard import MemGuard
  mg = MemGuard(api_key="xxx")
  memory = mg.watch(existing_mem0_client)
  # Nothing else changes in their code

---

### 2. Terminal Output [MVP]

When events are captured, print to terminal immediately.
This is the first thing a developer sees. Make it clear.

Format:
  [MemGuard] {operation.upper()}  {memory_key}
             value: {after_hash}
             session: {session_id}

For CONFLICT (same key, different hash written twice):
  [MemGuard] ⚠️  CONFLICT  {memory_key}
             was:  {before_hash}
             now:  {after_hash}
             session: {session_id}

For READ that follows a recent CONFLICT on same key:
  [MemGuard] ⚠️  READ AFTER CONFLICT  {memory_key}
             agent read the conflicted value
             this may have affected LLM output

Color coding (use colorama or rich):
  CREATE  → green
  READ    → blue  
  UPDATE  → yellow
  DELETE  → red
  CONFLICT → red + bold
  SEARCH  → cyan

---

### 3. Adapters [MVP: LangGraph + Mem0 only]

File: memguard/adapters/langgraph.py
File: memguard/adapters/mem0.py

LangGraph adapter:
  Wrap BaseCheckpointSaver
  Intercept put() and get()
  Record CREATE on first put, UPDATE on subsequent puts
  Record READ on get

Mem0 adapter:
  Wrap Memory class
  Intercept add(), search(), get_all(), delete()
  Record appropriate operation for each

[LATER] AutoGen adapter
[LATER] CrewAI adapter
[LATER] Zep adapter

---

### 4. Transport Layer [MVP: two options only]

File: memguard/transport/stdout.py   ← default for dev
File: memguard/transport/http.py     ← for production

StdoutTransport:
  Print MemoryEvent as formatted JSON to stdout
  Used when no api_key is provided
  Good for local development and testing

HttpTransport:
  POST events to MemGuard server as JSON batch
  Batch size: 10 events or 2 seconds, whichever first
  Retry: 3 times with exponential backoff
  If all retries fail: drop event, log warning, continue

[LATER] RedisTransport
[LATER] FileTransport

---

### 5. Event Storage [MVP]

File: server/storage/postgres.py

Use PostgreSQL only. No TimescaleDB yet.

Table: memory_events
  event_id      UUID PRIMARY KEY
  agent_id      TEXT NOT NULL
  session_id    TEXT NOT NULL
  operation     TEXT NOT NULL
  memory_key    TEXT NOT NULL
  namespace     TEXT DEFAULT 'default'
  before_hash   TEXT
  after_hash    TEXT
  before_value  JSONB  -- null unless capture_content=True
  after_value   JSONB  -- null unless capture_content=True
  llm_call_id   TEXT
  caused_by     UUID
  context       JSONB DEFAULT '{}'
  latency_ms    FLOAT
  timestamp     TIMESTAMPTZ NOT NULL
  ingested_at   TIMESTAMPTZ DEFAULT now()

Indexes:
  (agent_id, timestamp DESC)
  (session_id, timestamp DESC)
  (memory_key, namespace, timestamp DESC)

[LATER] TimescaleDB hypertable conversion
[LATER] Lineage graph table (memory_edges)
[LATER] Snapshot table

---

### 6. Conflict Detection [MVP: rule-based only]

File: server/analysis/conflict_detector.py

Simple rule: 
  If a WRITE event comes in for a key that already 
  has a value (different hash), flag as CONFLICT.

On conflict:
  1. Store conflict metadata in memory_events context field
  2. Push to terminal output immediately
  3. Store in conflicts table for dashboard

Table: memory_conflicts
  conflict_id   UUID PRIMARY KEY
  agent_id      TEXT
  session_id    TEXT
  memory_key    TEXT
  event_a_id    UUID  -- original
  event_b_id    UUID  -- conflicting write
  severity      TEXT  -- "high" | "medium" | "low"
  detected_at   TIMESTAMPTZ DEFAULT now()

Severity logic:
  high   → same key, value completely different
  medium → same key, value partially overlaps
  low    → same key, hash different but similar length

[LATER] Semantic conflict detection (embedding-based)
[LATER] Cross-session conflict detection

---

### 7. REST API [MVP: minimal]

File: server/api/routes.py
Framework: FastAPI

Endpoints to build:

  POST /v1/events
    Accept batch of MemoryEvents
    Validate schema
    Store to postgres
    Run conflict detection
    Return 202 Accepted

  GET /v1/sessions/{session_id}/timeline
    Return all events for session ordered by timestamp
    Include conflict flags

  GET /v1/agents/{agent_id}/conflicts
    Return list of detected conflicts
    Filter by: severity, time range

  GET /health
    Return 200 OK
    Used by Docker health check

[LATER] GET /v1/analysis/diff
[LATER] GET /v1/analysis/influence  
[LATER] WebSocket real-time stream
[LATER] Authentication (API keys)

---

### 8. Dashboard [MVP: minimal, functional]

File: dashboard/

Stack: React + Tailwind only. No complex libraries yet.
Single page app. Three views accessible by tab.

View 1: Event Log (default view)
  Table with columns:
    Time | Session | Operation | Memory Key | Hash | Conflict?
  Color code operations (match terminal colors)
  Click row → expand to show full event details
  Filter by: agent_id, session_id, operation type

View 2: Timeline
  For a selected session_id:
  Show events as a vertical list ordered by time
  Group by memory_key
  Highlight conflicts in red
  This is NOT a fancy D3 chart yet.
  Just a well-formatted list.

View 3: Conflicts
  List all detected conflicts
  Show: key / was / now / session / severity / time
  Click → show both conflicting events side by side

[LATER] D3 visualization
[LATER] Decision trace view
[LATER] Memory diff view
[LATER] Point-in-time replay

---

### 9. Security Layer [MVP: write-time scanner only]

File: server/security/scanner.py

This is the Memory Poisoning detection.
MVP only needs the fast-path (no LLM calls).

On every WRITE event, run these checks:

  Check 1: Instruction pattern detection
    If after_value contains phrases like:
      "ignore previous", "disregard", "new instruction",
      "you are now", "forget everything", "system prompt"
    → Flag as SUSPICIOUS, severity HIGH

  Check 2: Anomalous specificity
    If after_value contains explicit references to
    agent behavior, model instructions, or role overrides
    → Flag as SUSPICIOUS, severity HIGH

  Check 3: Rapid write anomaly
    If same session writes to same key more than
    5 times in 60 seconds
    → Flag as SUSPICIOUS, severity MEDIUM

Decision:
  SUSPICIOUS → quarantine (store in quarantine table,
                do NOT write to main memory store,
                alert in terminal)
  CLEAN      → allow write, proceed normally

Table: memory_quarantine
  quarantine_id   UUID PRIMARY KEY
  event_id        UUID
  reason          TEXT
  severity        TEXT
  detected_at     TIMESTAMPTZ DEFAULT now()
  reviewed        BOOLEAN DEFAULT false

[LATER] LLM deep validation (1% traffic fallback)
[LATER] Trust scoring system
[LATER] 7-layer full pipeline
[LATER] Immutable audit chain (Ed25519)

---

## File Structure

memguard/
├── sdk/
│   ├── __init__.py          ← exports MemGuard class
│   ├── core/
│   │   ├── interceptor.py   ← base interceptor
│   │   ├── event.py         ← MemoryEvent dataclass
│   │   └── trace.py         ← context var for trace_id
│   ├── adapters/
│   │   ├── langgraph.py
│   │   └── mem0.py
│   └── transport/
│       ├── base.py
│       ├── stdout.py
│       └── http.py
│
├── server/
│   ├── main.py              ← FastAPI app entrypoint
│   ├── api/
│   │   └── routes.py
│   ├── storage/
│   │   └── postgres.py
│   ├── analysis/
│   │   └── conflict_detector.py
│   └── security/
│       └── scanner.py
│
├── dashboard/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── views/
│   │   │   ├── EventLog.jsx
│   │   │   ├── Timeline.jsx
│   │   │   └── Conflicts.jsx
│   │   └── api/
│   │       └── client.js
│   └── package.json
│
├── docker-compose.yml
├── requirements.txt
└── README.md

---

## docker-compose.yml structure

Services:
  postgres:
    image: postgres:16
    env: POSTGRES_DB=memguard

  memguard-server:
    build: ./server
    depends_on: postgres
    ports: 8000:8000
    env: DATABASE_URL=postgresql://...

  memguard-dashboard:
    build: ./dashboard
    depends_on: memguard-server
    ports: 3000:3000

---

## Definition of Done for MVP

Claude Code should stop and show me a demo when:

  1. I can run: pip install memguard
  
  2. I can write:
       from memguard import MemGuard
       mg = MemGuard()
       memory = mg.watch(my_mem0_client)
     and see terminal output when my agent reads/writes
  
  3. I can open localhost:3000 and see:
       - a list of memory events
       - conflicts highlighted in red
       - ability to filter by session_id
  
  4. If I send a write containing "ignore previous instructions"
     it gets quarantined and does NOT enter the memory store
  
  5. docker-compose up starts everything with one command

These five things = MVP complete.
Do not build anything else until these five work.

---

## What NOT to Build in MVP

DO NOT build:
  - Memory Audit Reports (Tier 3 in MemoryLens doc)
  - Natural language explanation of decisions
  - Regulatory compliance report generation
  - Ed25519 immutable audit chain
  - LLM-based deep validation
  - Trust scoring system
  - Multi-agent cross-agent tracking
  - Point-in-time replay
  - WebSocket real-time streaming
  - Authentication / API keys
  - TimescaleDB
  - Neo4j or graph database
  - Embedding-based semantic analysis
  - Any enterprise features

These are [LATER]. Build them after MVP is validated.

---

## Build Order for Claude Code

Follow this exact sequence:

  Step 1: MemoryEvent dataclass + schema validation
  Step 2: Base interceptor + StdoutTransport
  Step 3: Mem0 adapter (simpler than LangGraph)
  Step 4: Test: wrap a real Mem0 client, see terminal output
  Step 5: PostgreSQL storage + migration script
  Step 6: FastAPI server + POST /v1/events endpoint
  Step 7: Conflict detector
  Step 8: Security scanner (fast path only)
  Step 9: GET endpoints for timeline + conflicts
  Step 10: React dashboard (Event Log view first)
  Step 11: LangGraph adapter
  Step 12: docker-compose
  Step 13: README with quickstart

At each step: write a simple test before moving on.
Do not skip to the next step if the current one is broken.