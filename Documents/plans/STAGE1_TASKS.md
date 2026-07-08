# Stage 1: Foundation & Tier 1 (Memory Debugging)
## Task Tracking - Week 1-3

**Goal**: Working MVP with basic memory tracing for engineers  
**Status**: In Progress  
**Started**: 2026-07-01

---

## ✅ Already Complete (From Code Review)

### SDK Core
- ✅ `MemoryEvent` data model (`sdk/memguard/core/event.py`)
- ✅ `DecisionTrace` data model (`sdk/memguard/core/event.py`)
- ✅ `MemGuardInterceptor` base class (`sdk/memguard/core/interceptor.py`)
- ✅ `Transport` abstract base class (`sdk/memguard/core/interceptor.py`)
- ✅ `FileTransport` - JSONL append (`sdk/memguard/transport/file.py`)
- ✅ `HttpTransport` - async POST to backend (`sdk/memguard/transport/http.py`)
- ✅ `MemGuardCheckpointer` - LangGraph adapter (`sdk/memguard/adapters/langgraph.py`)
  - Wraps any BaseCheckpointSaver
  - Intercepts get_tuple(), put(), list()
  - Supports both sync and async APIs
  - Privacy-first with content hashing

### What Works
- Event creation with unique IDs
- Content hashing for privacy
- Fire-and-forget event emission
- Thread-safe async event delivery
- LangGraph state tracking

---

## 🚧 Tasks In Progress

### 1. Complete Missing Transports
- [ ] **StdoutTransport** - Debug logging transport
  - File: `sdk/memguard/transport/stdout.py`
  - Pretty-print events to console
  - Color-coded by operation type

### 2. Backend Event Ingestion
- [ ] **Event Ingestion Endpoint** - `POST /v1/events`
  - File: `backend/app/api/events.py`
  - Batch event ingestion (multiple events per request)
  - Validation using Pydantic schemas
  - Deduplication by event_id
  - Return accepted/rejected counts

### 3. Backend Storage Layer
- [ ] **SQLite Event Store Schema**
  - File: `backend/app/storage/event_store.py`
  - Table: `memory_events` with all MemoryEvent fields
  - Table: `decision_traces` with all DecisionTrace fields
  - Indexes for fast queries (agent_id, session_id, timestamp)
  - Migration scripts

- [ ] **Event Persistence Service**
  - File: `backend/app/services/event_service.py`
  - Insert events into database
  - Handle batch inserts efficiently
  - Query events with filters

### 4. Backend Query APIs
- [ ] **Timeline API**
  - `GET /v1/sessions/{session_id}/timeline` - chronological events
  - `GET /v1/agents/{agent_id}/timeline` - all events for agent
  - Pagination support
  - Time-range filtering

- [ ] **Memory Lineage API**
  - `GET /v1/memory/{memory_key}/lineage` - evolution of one memory
  - Show CREATE → UPDATE → UPDATE chain
  - Include before/after diffs

- [ ] **Agent State API**
  - `GET /v1/agents/{agent_id}/memory-state` - current snapshot
  - Reconstruct current state from events

### 5. Frontend Timeline View
- [ ] **Timeline Component**
  - File: `frontend/components/MemoryTimeline.tsx`
  - D3.js horizontal timeline
  - Color-coded dots (CREATE=green, READ=blue, UPDATE=yellow, DELETE=red)
  - Zoom and pan
  - Click to see details

- [ ] **Event Detail Modal**
  - File: `frontend/components/EventDetailModal.tsx`
  - Show full event data
  - Before/after diff for UPDATEs
  - Link to related events (caused_by)

- [ ] **Timeline Page**
  - File: `frontend/app/timeline/[sessionId]/page.tsx`
  - Session selector dropdown
  - Filtering controls (agent, operation, time range)
  - Real-time updates via polling/WebSocket

### 6. FinCompli Integration
- [ ] **Wrap FinCompli with MemGuard**
  - File: `fincompli-baseline/graph/builder.py` (modify)
  - Replace checkpointer with MemGuardCheckpointer
  - Configure HttpTransport
  - Keep original functionality intact

- [ ] **Instrument Memory Layer**
  - Files: `fincompli-baseline/memory/*.py` (modify)
  - Wrap episodic memory (ChromaDB) reads/writes
  - Wrap semantic memory (ChromaDB) reads/writes
  - Wrap procedural memory (SQLite) reads/writes
  - Add MemGuard interceptor calls

- [ ] **Add Trace Linking**
  - Link LLM calls to memory events
  - Use context manager for trace_id
  - Calculate influence scores

### 7. Testing & Documentation
- [ ] **End-to-End Test**
  - Run FinCompli Scenario 02 (Structuring)
  - Verify all events captured
  - Verify events visible in backend API
  - Verify timeline renders correctly

- [ ] **Performance Testing**
  - Measure overhead per event (target: <5ms)
  - Load test with 1000+ events/second
  - Memory usage profiling

- [ ] **Documentation**
  - Integration guide: "Using MemGuard with LangGraph"
  - API documentation (OpenAPI/Swagger)
  - SDK reference docs
  - Demo video

---

## 📋 Implementation Order (Week 1)

### Day 1-2: Backend Foundation
1. Create `StdoutTransport` for debugging
2. Implement SQLite event store schema
3. Implement event ingestion endpoint
4. Test: SDK → Backend → Database flow

### Day 3-4: Query APIs
5. Implement timeline query endpoint
6. Implement memory lineage endpoint
7. Implement agent state endpoint
8. Test: Query APIs return correct data

### Day 5-7: Frontend Basics
9. Create timeline visualization component
10. Create event detail modal
11. Create timeline page
12. Test: Frontend displays backend data

---

## 📋 Week 2: Integration & Polish

### Day 8-10: FinCompli Integration
13. Wrap FinCompli checkpointer
14. Instrument memory layer
15. Add trace linking
16. Test: Complete scenario with tracing

### Day 11-14: Testing & Docs
17. End-to-end testing
18. Performance testing
19. Write documentation
20. Create demo video

---

## 📋 Week 3: Buffer & Refinement
- Bug fixes
- Performance optimization
- Documentation improvements
- User testing with beta partners

---

## 🎯 Success Criteria for Stage 1

### Functional Requirements
- ✅ SDK captures all memory operations
- ✅ Events stored in backend database
- ✅ Timeline API returns filtered events
- ✅ Frontend displays interactive timeline
- ✅ FinCompli integration works end-to-end
- ✅ Can trace lineage of any memory key
- ✅ Can see before/after diffs

### Non-Functional Requirements
- ✅ <5ms overhead per memory operation
- ✅ Handle 1000+ events/second
- ✅ Zero breaking changes to FinCompli
- ✅ Privacy-first (content hashed by default)
- ✅ Fire-and-forget (never blocks agent)

### Documentation Requirements
- ✅ API documentation (Swagger)
- ✅ Integration guide
- ✅ Demo video
- ✅ Quick start tutorial

---

## 🚀 Next Immediate Actions (Today)

1. [ ] Create `StdoutTransport` for debugging
2. [ ] Implement SQLite event store schema
3. [ ] Implement event ingestion endpoint (`POST /v1/events`)
4. [ ] Test: Send event from SDK to backend

**Time Estimate**: 4-6 hours for these 4 tasks

---

## 📝 Notes

### Key Decisions Made
- SQLite for MVP (PostgreSQL in Stage 5)
- Hash content by default (privacy-first)
- Fire-and-forget event emission (non-blocking)
- FinCompli as dogfooding testbed

### Open Questions
- [ ] Should we support WebSocket for real-time timeline updates?
- [ ] What's the event retention policy for SQLite? (default: 90 days)
- [ ] Do we need event batching in SDK? (combine multiple events per HTTP call)

### Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| SDK overhead too high | Agents slow down | Profile and optimize; add batching |
| Backend can't handle load | Events dropped | Add Redis queue; implement backpressure |
| FinCompli integration breaks | Demo fails | Keep changes minimal; extensive testing |
| Frontend performance issues | Timeline sluggish | Use virtualization for large datasets |

---

**Last Updated**: 2026-07-01  
**Status**: Ready to execute
