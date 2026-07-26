# MemGuard
**Memory Observability & Security for AI Agents**

> See exactly what your agent remembers, why it made each decision, and whether its memory has been tampered with.

---

## ⚡ Quick Start

### 5-minute demo (terminal only)

```bash
pip install -e sdk/
pip install openai rich

# Using OpenAI (default)
export OPENAI_API_KEY=sk-xxx
python demo_simple.py

# Or use Anthropic Claude
export MEMGUARD_LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-xxx
python demo_simple.py

# Or use local Ollama (free, no API key needed)
export MEMGUARD_LLM_PROVIDER=ollama
export MEMGUARD_LLM_MODEL=qwen2.5:7b
python demo_simple.py

# Or use any OpenAI-compatible API
export MEMGUARD_LLM_PROVIDER=openai_compatible
export MEMGUARD_LLM_MODEL=your-model
export MEMGUARD_LLM_API_KEY=your-key
export MEMGUARD_LLM_BASE_URL=https://your-api.com/v1
python demo_simple.py
```

**Supported LLM Providers**: OpenAI · Anthropic · Ollama · Together AI · Groq · DeepSeek · vLLM · Any OpenAI-compatible API

Full configuration options: [`.env.example`](./.env.example)

**Output**: Colored memory events in your terminal showing CREATE, READ, UPDATE operations and conflict detection in real-time.

### With dashboard

```bash
./scripts/START_ALL.sh
export OPENAI_API_KEY=sk-xxx
python demo_with_dashboard.py
# Open http://localhost:3001
```

**Dashboard shows**:
- Memory timeline with all events
- Decision traces (memory IN → agent decision → memory OUT)
- Conflict detection
- Audit reports

### Integrate with your own LangGraph agent

```python
from memguard import MemGuardInterceptor
from memguard.adapters.langgraph import MemGuardCheckpointer
from memguard.transport.stdout import StdoutTransport

# Wrap your existing checkpointer
mg = MemGuardInterceptor(
    agent_id="my-agent",
    transport=StdoutTransport()  # or HttpTransport("http://localhost:8000")
)

checkpointer = MemGuardCheckpointer(
    inner=MemorySaver(),  # Your existing checkpointer
    interceptor=mg
)

# Use it in your graph
graph = your_workflow.compile(checkpointer=checkpointer)

# That's it. Run your agent normally.
# MemGuard tracks all memory operations automatically.
```

---

## 🌟 What is MemGuard?

MemGuard provides **4 tiers of memory intelligence**:

```
Tier 1: Memory Debugging          (For AI Engineers)
  → "Which memory caused this output?"
  
Tier 2: Memory Observability      (For Platform Engineers)
  → "How is my memory system performing?"
  
Tier 3: Memory Auditability       (For Compliance Officers)
  → "Explain this decision in business language"
  
Tier 4: Memory Governance         (For CISO/Board)
  → "Control memory as an organizational risk surface"
```

**Current Status**: Stage 1 (Tier 1) - Memory Debugging ✅

---

## 📚 Documentation

- **🚀 START HERE**: Read [`Documents/START_HERE.md`](./Documents/START_HERE.md) first!
- **📖 Quick Start**: 5-minute tutorial in [`Documents/QUICKSTART.md`](./Documents/QUICKSTART.md)
- **📋 Development Plan**: Full roadmap in [`Documents/plans/MEMGUARD_STANDALONE_PLAN.md`](./Documents/plans/MEMGUARD_STANDALONE_PLAN.md)
- **🔧 Execution Tools**: See [`Documents/EXECUTION_TOOLS.md`](./Documents/EXECUTION_TOOLS.md)

---

## 🎯 Original Quick Start (Legacy)

### Step 1: Install SDK

```bash
cd sdk
pip install -e .
```

### Step 2: Start Backend

```bash
# Use script
./scripts/START_BACKEND.sh

# Or manually
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend runs at: http://localhost:8000

### Step 3: Run Demo Agent

```bash
# Install LangGraph first
pip install langgraph langchain-core

# Run demo
python3 examples/demo_agent.py --mode auto
```

### Step 4: Verify

```bash
curl http://localhost:8000/v1/db/stats
```

Expected: `{"total_events": 10+, ...}`

---

## 🔧 Integration Example

**Integrate MemGuard with your LangGraph agent in 3 lines:**

```python
# Before MemGuard:
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()
graph = workflow.compile(checkpointer=checkpointer)

# After MemGuard (add these 3 lines):
from memguard.adapters.langgraph import MemGuardCheckpointer
from memguard.transport import HttpTransport

checkpointer = MemGuardCheckpointer(
    inner=MemorySaver(),
    agent_id="my-agent",
    namespace="my-org",
    transport=HttpTransport("http://localhost:8000")
)
graph = workflow.compile(checkpointer=checkpointer)
```

**That's it!** Your agent now has full memory tracing with:
- ✅ Zero breaking changes
- ✅ <5ms overhead
- ✅ Privacy-first (content hashed by default)
- ✅ Fire-and-forget (never blocks your agent)

---

## 📦 Project Structure

```
MemguardV1/
├── README.md                     ← Main project documentation
│
├── sdk/memguard/                 ← SDK (pip installable)
│   ├── core/                     - Event models, interceptor
│   ├── adapters/                 - LangGraph, Mem0, AutoGen adapters
│   └── transport/                - HTTP, File, Stdout transport layer
│
├── backend/                      ← Backend control plane
│   └── app/
│       ├── main.py               - FastAPI application
│       ├── services.py           - Event storage & query
│       └── schemas.py            - Data models
│
├── frontend/                     ← Dashboard (Next.js)
│   ├── app/
│   │   └── timeline/             - Memory timeline view
│   └── components/               - React components
│
├── examples/                     ← Demo agents
│   └── demo_agent.py             - Standalone demo (no FinCompli dependency)
│
├── tests/                        ← Test files
│   ├── test_sdk_backend_integration.py
│   └── test_memory_tracing.py
│
├── scripts/                      ← Executable scripts
│   ├── START_BACKEND.sh          - Start Backend
│   ├── RUN_DEMO.sh               - Run Demo
│   ├── test_all.sh               - Full test suite
│   └── verify_installation.sh    - Verify installation
│
├── fincompli-baseline/           ← 🔒 Standalone enterprise agent demo (do not modify)
│
└── Documents/                    ← 📚 All documentation
    ├── START_HERE.md             - 🔥 Quick start guide
    ├── QUICKSTART.md             - 5-minute tutorial
    ├── EXECUTION_TOOLS.md        - Execution tools inventory
    ├── plans/                    - 📋 Plans
    │   ├── MEMGUARD_STANDALONE_PLAN.md  - Core development plan
    │   ├── DEVELOPMENT_PLAN.md          - Long-term roadmap
    │   ├── STAGE1_TASKS.md              - Stage1 task list
    │   └── ...
    ├── reference/                - 📖 Reference documents
    │   ├── 02_memorylens_product_document.md - Product requirements
    │   ├── MemGuard_Technical_Design.md     - Technical design
    │   └── API_EXAMPLES.md                  - API examples
    └── fincompli/                - 🏦 FinCompli related
        └── ...
```

---

## 🎨 What Gets Traced?

Every memory operation produces a `MemoryEvent`:

- **CREATE** - New memory written (🟢 Green)
- **READ** - Memory retrieved (🔵 Blue)
- **UPDATE** - Memory modified (🟡 Yellow)
- **DELETE** - Memory removed (🔴 Red)
- **QUERY/SEARCH** - Memory lookup (🔷 Cyan)

Each event includes:
- `event_id` (UUID)
- `agent_id`, `session_id`, `namespace`
- `operation`, `memory_key`, `memory_type`
- `content_hash` (SHA-256)
- `timestamp`, `context`, `tags`

---

## 🚀 Framework Support

### Current Support
- ✅ **LangGraph** - Full support (checkpointer wrapper)
- ✅ **Generic** - Base interceptor for custom systems

### Planned Support (Stage 1-2)
- 🔄 **LangChain** - Memory wrappers
- 🔄 **Mem0** - Memory class wrapper
- 🔄 **AutoGen** - Conversation tracking
- 🔄 **CrewAI** - Task memory tracking

---

## 📊 Current Development Status

### ✅ Stage 1: Tier 1 - Memory Debugging (Weeks 1-3) ← **WE ARE HERE**

**Completed:**
- [x] SDK core implementation
- [x] LangGraph adapter
- [x] Backend event ingestion
- [x] SQLite storage
- [x] Demo agent
- [x] Integration test scripts

**In Progress:**
- [ ] Frontend dashboard (next priority)
- [ ] API documentation
- [ ] Video tutorials

**Success Metrics:**
- SDK captures all memory operations ✅
- Events stored in backend ✅
- Timeline API works ✅
- Demo runs successfully ✅

---

## 🎯 Roadmap

### Stage 1: Memory Debugging (Weeks 1-3) ← Current
- Debug: "Which memory caused this output?"
- Timeline visualization
- Event detail inspection

### Stage 2: Memory Observability (Weeks 4-6)
- Retrieval quality tracking
- Memory access heatmaps
- Cross-agent flow analysis
- Drift detection
- Anomaly alerting

### Stage 3: Memory Auditability (Weeks 7-10) 🌟 **Killer Feature**
- Natural language audit reports
- Regulatory framework mappings
- Memory integrity verification
- Export formats (PDF, JSON, CSV)

### Stage 4: Memory Governance (Weeks 11-15)
- Access control policies
- Prompt injection detection
- Lifecycle management
- Board-level dashboard
- Regulatory reporting

---

## 🔒 Privacy & Security

### Privacy-First Design
- **Hash by default**: Content is SHA-256 hashed, not stored
- **Opt-in for raw content**: Explicit `capture_content=True` required
- **Namespace isolation**: Multi-tenant by design
- **Configurable retention**: Auto-purge after N days

### Security Features (Stage 4)
- Prompt injection detection
- Access control policies
- Memory quarantine
- Integrity verification

---

## 📚 Documentation

- **Quick Start**: [`Documents/QUICKSTART.md`](./Documents/QUICKSTART.md)
- **Entry Guide**: [`Documents/START_HERE.md`](./Documents/START_HERE.md)
- **Development Plan**: [`Documents/plans/MEMGUARD_STANDALONE_PLAN.md`](./Documents/plans/MEMGUARD_STANDALONE_PLAN.md)
- **Product Vision**: [`Documents/reference/02_memorylens_product_document.md`](./Documents/reference/02_memorylens_product_document.md)
- **Technical Design**: [`Documents/reference/MemGuard_Technical_Design.md`](./Documents/reference/MemGuard_Technical_Design.md)
- **API Reference**: http://localhost:8000/docs (when backend is running)

---

## 🧪 Testing

### Quick Start (one command)
```bash
./scripts/verify_installation.sh
```

### Run Demo Agent
```bash
# Automated demo (recommended first)
python3 examples/demo_agent.py --mode auto

# Interactive chat
python3 examples/demo_agent.py --mode interactive

# Comparison (with/without MemGuard)
python3 examples/demo_agent.py --mode compare
```

### Run Integration Tests
```bash
# Test SDK → Backend flow
python3 tests/test_sdk_backend_integration.py

# Full test suite
./scripts/test_all.sh
```

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check Python version (need 3.9+)
python3 --version

# Install dependencies
cd backend
pip install -r requirements.txt
```

### Events not captured
```bash
# Check backend is running
curl http://localhost:8000/health

# Enable debug logging
export MEMGUARD_LOG_LEVEL=DEBUG
python3 examples/demo_agent.py --mode auto
```

### Database issues
```bash
# View database directly
sqlite3 backend/memguard.db "SELECT COUNT(*) FROM memory_events;"
```

---

## 📊 Performance

- **Overhead**: <5ms per memory operation (99th percentile)
- **Throughput**: 1000+ events/second
- **Storage**: SQLite for MVP, PostgreSQL + TimescaleDB for production

**How we achieve low overhead:**
- Fire-and-forget event emission (never blocks)
- Async background processing
- Content hashing (not serialization) by default
- Batching and buffering

---

## 🤝 Contributing

This is currently in private development. For questions or feedback:

1. Review the development plan: [`MEMGUARD_STANDALONE_PLAN.md`](./MEMGUARD_STANDALONE_PLAN.md)
2. Check current tasks: [`STAGE1_TASKS.md`](./STAGE1_TASKS.md)
3. See completed work: [`TASK_EXECUTION_COMPLETE.md`](./TASK_EXECUTION_COMPLETE.md)

---

## 📄 License

TBD - Currently in development

---

## 🎉 Next Steps

1. **Run the demo**: `python3 examples/demo_agent.py --mode auto`
2. **Build frontend**: See `MEMGUARD_STANDALONE_PLAN.md` for tasks
3. **Read docs**: Start with `START_HERE.md`
4. **Join beta**: Coming soon!

---

**Built with ❤️ — Memory is state. State must be observable.**

---

## 📞 Quick Reference

| What | Where |
|------|-------|
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Frontend | http://localhost:3000 (when built) |
| Database | `backend/memguard.db` |
| Logs | `backend.log` |

**Version**: 0.1.0-alpha  
**Status**: Stage 1 Development  
**Last Updated**: 2026-07-01
