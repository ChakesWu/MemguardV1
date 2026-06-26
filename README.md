# MemGuard v1 — Memory Observability for AI Agents

**Trace which memories make your agent output each decision.**

MemGuard is a **middleware layer** that sits between AI agent frameworks and their memory backends. It intercepts every memory operation (read/write/update) — without requiring changes to your agent code — and provides full traceability into which memories influenced each decision.

## 🎯 Why MemGuard?

```
❌ BEFORE: Memory is a black box
   "Why did my agent say THAT?"
   "Which memory caused this decision?"
   "Is this memory being used or stale?"

✅ AFTER: Full memory observability
   "Decision was 87% influenced by memory X"
   "This memory has been read 12 times in 3 sessions"
   "Stale memory Y hasn't been accessed in 30 days"
```

## 🏗️ Architecture

```
Your LangGraph Agent (ZERO code changes)
        │
        │  graph.compile(checkpointer=MemGuardCheckpointer(...))
        ▼
┌──────────────────────────────────────┐
│  MemGuard Checkpointer (SDK)         │  ← Transparent wrapper
│  - Intercepts all state reads/writes │
│  - Records MemoryEvents async        │
│  - Never blocks your agent           │
└──────────────┬───────────────────────┘
               │ delegates to original
               ▼
┌──────────────────────────────────────┐
│  Original Checkpointer               │
│  (MemorySaver / SqliteSaver / etc.)  │
└──────────────────────────────────────┘
               │ events (fire-and-forget)
               ▼
┌──────────────────────────────────────┐
│  MemGuard Control Plane (FastAPI)    │
│  - Event ingestion API               │
│  - SQLite persistence                │
│  - Decision tracing & analysis       │
│  - Governance (quarantine, policy)   │
└──────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Install the SDK

```bash
cd sdk
pip install -e .
```

### 2. Start the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Server runs at `http://localhost:8000`

### 3. Use in Your LangGraph Agent

Your agent code needs **ONE LINE changed** — just wrap your checkpointer:

```python
from langgraph.checkpoint.memory import MemorySaver
from memguard.adapters.langgraph import MemGuardCheckpointer
from memguard.transport import HttpTransport, FileTransport

# Before MemGuard:
# checkpointer = MemorySaver()

# After MemGuard (add these 3 lines):
checkpointer = MemGuardCheckpointer(
    inner=MemorySaver(),                    # Original checkpointer
    agent_id="my-agent",                    # Identify this agent
    namespace="my-org",                     # Tenant/org namespace
    transport=FileTransport("events.jsonl"), # Record events to file
)

# Everything else is IDENTICAL
graph = workflow.compile(checkpointer=checkpointer)
result = graph.invoke({"messages": [...]}, config)
```

**That's it.** Every state read/write is now being recorded.

### 4. See What Happened

```bash
# Read the recorded events
cat events.jsonl | python3 -m json.tool

# Or query the backend API
curl http://localhost:8000/v1/db/stats
curl http://localhost:8000/v1/memory/observability/my-org/my-agent
```

---

## 📦 SDK: Three Transports

Choose how events are delivered:

| Transport | Use Case | Setup |
|-----------|----------|-------|
| `FileTransport("events.jsonl")` | Development, offline | Zero deps |
| `HttpTransport("http://localhost:8000")` | Production with server | Zero deps |
| `StdoutTransport()` | Debugging | Zero deps |

```python
from memguard.transport import FileTransport, HttpTransport, StdoutTransport

# Development: write to local file
transport = FileTransport("memguard_events.jsonl")

# Production: send to MemGuard server
transport = HttpTransport("http://localhost:8000", api_key="...")

# Debugging: print to stdout
transport = StdoutTransport()
```

## 📚 API Reference

### Backend Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check with LLM config |
| `/v1/memory/write` | POST | Write a memory event |
| `/v1/memory/query` | POST | Query memories for an agent |
| `/v1/memory/timeline` | POST | Get memory timeline |
| `/v1/memory/{id}/trace` | GET | Get memory's event lineage |
| `/v1/memory/{id}/influence` | GET | Show all decisions this memory influenced |
| `/v1/memory/observability/{tenant}/{agent}` | GET | Get observability summary |
| `/v1/agent/run` | POST | Run built-in agent with tracing |
| `/v1/events` | POST | **SDK ingestion** — receive events from adapters |
| `/v1/trace/{trace_id}` | GET | Get decision trace |
| `/v1/trace/agent/{tenant}/{agent}` | GET | Get all traces for agent |
| `/v1/db/stats` | GET | Database statistics |

### SDK Ingestion (used by adapters)

```
POST /v1/events
Content-Type: application/json

{
  "events": [
    {
      "agent_id": "my-agent",
      "operation": "create",
      "memory_key": "checkpoint:session-001",
      "namespace": "my-org",
      "timestamp": "2026-06-25T10:30:00.000000+00:00",
      "after_value": {"messages": [...]},
      "content_hash": "a3f4b2c1",
      "context": {"thread_id": "session-001"}
    }
  ]
}

Response 200:
{
  "accepted": 1,
  "rejected": 0,
  "event_ids": ["uuid-here"]
}
```

---

## 🧪 Running the Example

```bash
# Install LangGraph (required for the example)
pip install langgraph langgraph-checkpoint

# Install the SDK
cd sdk && pip install -e . && cd ..

# Run the LangGraph example
cd examples
python langgraph_agent.py
```

The example shows:
1. A LangGraph agent running **without** MemGuard (baseline — no observability)
2. The **same** agent running **with** MemGuard (3-line change — full observability)
3. The recorded memory events (timeline of reads/writes)
4. What questions MemGuard can answer about your agent's behavior

---

## 🛡️ Memory Governance

### Prompt Injection Detection

MemGuard detects and quarantines suspicious content:

```python
# These patterns trigger quarantine:
- "ignore previous instructions"
- "forget above"
- "system prompt override"
- "instruction override"
```

Quarantined memories get `trust_score < 20` and are excluded from agent decisions.

### Trust Scoring

| Source | Base Score | Modifier |
|--------|-----------|----------|
| `system` | 50 | +30 (most trusted) |
| `tool` | 50 | +20 |
| `user` | 50 | -10 (least trusted) |
| Quarantined | — | -40 penalty |

---

## 🔍 Use Cases

### 1. Debug: "Why did my agent give this answer?"

```bash
# Run the agent
curl -X POST http://localhost:8000/v1/agent/run \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"t","agent_id":"a","input":"What tech stack?"}'

# Get the decision trace
curl http://localhost:8000/v1/trace/{trace_id} | jq '.memory_influence_scores'
```

### 2. Audit: "How often is this memory used?"

```bash
curl http://localhost:8000/v1/memory/{memory_id}/influence
# Shows every decision this memory influenced, with scores
```

### 3. Monitor: "Is my agent's memory healthy?"

```bash
curl http://localhost:8000/v1/memory/observability/my-org/my-agent
# Returns: total events, quarantined, avg trust score, staleness
```

### 4. LangGraph: "What state changes happened in my graph?"

```bash
# With MemGuardCheckpointer, every state read/write is recorded
cat events.jsonl | jq 'select(.operation=="create" or .operation=="update")'
```

---

## 📁 Project Structure

```
MemguardV1/
├── sdk/memguard/               # Python SDK (pip install)
│   ├── core/
│   │   ├── event.py            # MemoryEvent, DecisionTrace models
│   │   └── interceptor.py      # Base interceptor + Transport ABC
│   ├── adapters/
│   │   └── langgraph.py        # LangGraph Checkpointer wrapper
│   ├── transport/
│   │   ├── http.py             # HTTP → MemGuard server
│   │   ├── file.py             # JSONL file (dev/offline)
│   │   └── stdout.py           # Print to stdout (debug)
│   └── setup.py
├── backend/app/                # MemGuard Control Plane
│   ├── main.py                 # FastAPI routes
│   ├── services.py             # MemoryGateway + SQLite storage
│   ├── agent.py                # Built-in agent + influence scoring
│   ├── llm.py                  # LLM client (DeepSeek default)
│   └── schemas.py              # Pydantic models
├── examples/
│   └── langgraph_agent.py      # LangGraph + MemGuard demo
└── MemGuard_Technical_Design.md
```

---

## 🚧 Roadmap

### ✅ Phase 1 — Core SDK (Current)
- ✅ Base interceptor pattern
- ✅ LangGraph checkpointer adapter
- ✅ File/HTTP/Stdout transports
- ✅ SQLite persistence
- ✅ Decision tracing & influence scoring
- ✅ Prompt injection quarantine

### Phase 2 — More Adapters
- [ ] Mem0 adapter
- [ ] CrewAI adapter
- [ ] AutoGen adapter
- [ ] Generic OpenAI-compatible adapter

### Phase 3 — Advanced Analysis
- [ ] Semantic conflict detection
- [ ] Staleness detection & alerts
- [ ] Point-in-time memory replay
- [ ] PostgreSQL + TimescaleDB migration

### Phase 4 — Dashboard
- [ ] React timeline visualization
- [ ] Decision trace flow diagrams
- [ ] Memory diff viewer

---

## 🤝 Contributing

This is an early-stage MVP. PRs welcome!

## 📖 Technical Design

See [MemGuard_Technical_Design.md](./MemGuard_Technical_Design.md) for the complete architecture specification.

---

**Built with ❤️ — Memory is state. State must be observable.**
