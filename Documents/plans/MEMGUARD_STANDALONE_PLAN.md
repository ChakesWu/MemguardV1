# MemGuard Development Plan - Standalone Product
**Based on**: 02_memorylens_product_document.md  
**Approach**: Build MemGuard as a universal memory observability SDK  
**Date**: 2026-07-01

---

## 🎯 Product Vision

**MemGuard/MemoryLens** = Memory Intelligence Layer for AI Agents

### The 4-Tier Product Ladder

```
Tier 1: Memory Debugging          (For AI Engineers)
        ↓
Tier 2: Memory Observability      (For Platform Engineers)
        ↓
Tier 3: Memory Auditability       (For Compliance Officers)
        ↓
Tier 4: Memory Governance         (For CISO/CCO)
```

---

## 📋 Development Stages (Revised)

### Stage 1: Tier 1 - Memory Debugging (Weeks 1-3)
**Target User**: AI Engineer  
**Value Prop**: "Which memory caused this output?"

#### What to Build
1. **SDK Core** ✅ (Already done)
   - Event capture
   - Framework adapters (LangGraph ✅, Mem0, AutoGen, CrewAI)
   - Transport layer (HTTP, File, Stdout)

2. **Backend APIs**
   - Event ingestion: `POST /v1/events` ✅
   - Timeline query: `GET /v1/sessions/{session_id}/timeline`
   - Memory lineage: `GET /v1/memory/{memory_key}/lineage`
   - Memory diff: `POST /v1/analysis/diff`
   - Counterfactual query: "What if this memory didn't exist?"

3. **Frontend Dashboard**
   - **Memory Timeline View**
     - Horizontal time axis
     - Color-coded events (CREATE/READ/UPDATE/DELETE)
     - Click to inspect event details
     - Visual diff for UPDATE events
   
   - **Memory Conflict Detector**
     - Flag when two memories contradict
     - Show conflict resolution
   
   - **Counterfactual Query Tool**
     - "Remove memory X, show how output changes"

4. **Deliverables**
   - SDK package installable via `pip install memguard`
   - Backend Docker image
   - Dashboard accessible at `localhost:3000`
   - Documentation: "Integrate MemGuard in 5 minutes"

---

### Stage 2: Tier 2 - Memory Observability (Weeks 4-6)
**Target User**: Platform Engineer, ML Ops  
**Value Prop**: "How is my memory system performing?"

#### What to Build
1. **Retrieval Quality Tracking**
   - Track similarity score distributions over time
   - Alert when average relevance drops
   - Visualize: "Are retrieved memories actually relevant?"

2. **Memory Access Heatmaps**
   - Which memories are retrieved most frequently?
   - Which memories are never retrieved? (dead memories)
   - Hot/cold memory identification

3. **Cross-Agent Memory Flow**
   - Agent A writes → Agent B reads
   - Visualize memory sharing patterns
   - "How does memory flow through your system?"

4. **Drift Detection**
   - Track when long-term memories are updated
   - Trace update propagation through agent outputs
   - "Did this update have the intended effect?"

5. **Anomaly Alerting**
   - Statistical anomaly detection on access patterns
   - Spike alerts (unusual retrieval frequency)
   - Alert webhooks (Slack, email)

6. **Dashboard Views**
   - Agent health dashboard
   - Memory access heatmap
   - Stale memory list with recommendations
   - Cross-agent flow diagram (React Flow)
   - Time-series charts (Recharts)

---

### Stage 3: Tier 3 - Memory Auditability (Weeks 7-10)
**Target User**: Compliance Officer, Internal Audit  
**Value Prop**: "Explain this decision in business language"

#### What to Build - THE KILLER FEATURE ⭐

1. **Memory Audit Report Generator**
   - **Input**: Decision trace (memory reads → LLM call → output)
   - **Output**: Plain English audit report
   
   Example report structure:
   ```
   MemoryLens Audit Report
   Agent Output: SAR Recommendation — Client C-00412
   Generated: 2025-03-15 14:23:11 HKT
   
   Summary:
   The agent's recommendation to file a SAR was based on three 
   distinct memory sources, all verified as unmodified.
   
   Memory Sources Used:
   1. Historical Case SAR-2024-0033 (similarity: 88%)
   2. Historical Case SAR-2023-0171 (similarity: 82%)
   3. HKMA AML Guideline §35 (current, unmodified)
   
   Memory Integrity Verification:
   ✓ All sources passed integrity checks
   ✓ No modifications since indexing
   ✓ Authorized agent access
   
   What the Agent Did Not Use:
   Case SAR-2022-0089 (similarity: 71%) - dismissed due to 
   different transaction amounts
   ```

2. **Natural Language Generation**
   - Use LLM to convert technical traces → business narrative
   - Bilingual support (English + Chinese)
   - Templates for different decision types

3. **Regulation-Linked Citations**
   - Link retrieved regulations to specific versions
   - Hash verification (regulation unchanged since retrieval)
   - Temporal audit: "Which version was current at decision time?"

4. **Export Formats**
   - PDF (for regulatory submission)
   - JSON (for internal systems)
   - CSV (for bulk audit review)

5. **Regulatory Framework Mappings**
   - EU AI Act Article 13/14
   - HKMA Supervisory Policy Manual
   - MAS Notice 626
   - FCA CP23/32
   - NIST AI RMF
   - SEC AI disclosure

---

### Stage 4: Tier 4 - Memory Governance (Weeks 11-15)
**Target User**: CISO, Chief Compliance Officer, Board  
**Value Prop**: "Control memory as an organizational risk surface"

#### What to Build

1. **Access Control Policy Engine**
   - Define policies: who can access what, when
   - Examples:
     - "Customer PII only within same session"
     - "High-risk data requires supervisor approval"
     - "Regulatory memory >12 months flagged as stale"
   - Enforce at memory layer (not in agent code)
   - Alert on policy violations

2. **Memory Contamination Detection** 🛡️
   - **Prompt injection defense at write time**
   - Detection patterns:
     - "ignore previous instructions"
     - "forget above"
     - "system prompt override"
     - Instruction-like language in factual memory
   - Quarantine suspicious writes
   - Review queue for flagged memories

3. **Memory Lifecycle Management**
   - Retention policies by memory type
   - Auto-purge expired memories
   - Versioning and immutable snapshots
   - Provenance chain tracking
   - 7-year retention for financial (regulatory compliance)

4. **Governance Dashboard** (Board-Level)
   - Executive metrics:
     - Total memory operations over period
     - Access policy violations
     - Contamination attempts blocked
     - Memory integrity check status
     - % of outputs with complete audit trails
   - Trend charts
   - Compliance posture score

5. **Regulatory Reporting Package**
   - Structured export for regulators
   - Pre-formatted for each framework
   - Include:
     - Memory governance framework docs
     - Policy coverage reports
     - Exception reports
     - Sample audit trails
   - ZIP package generator

---

## 🚀 Execution Plan - Stage 1 (This Week)

### Goals for Week 1
1. ✅ SDK working end-to-end
2. ✅ Backend ingestion working
3. ⭐ Create **standalone demo** (not using FinCompli)
4. ⭐ Build basic dashboard

---

### Task 1: Create Standalone Demo Agent (Day 1)
**File**: `examples/demo_agent.py`

Build a simple LangGraph agent that:
- Has a conversation
- Uses checkpointer for state
- Wrapped with MemGuardCheckpointer
- Shows memory tracing in action

```python
"""
Demo Agent - Shows MemGuard in action

A simple conversational agent that:
1. Remembers user preferences
2. Uses LangGraph for state management
3. Wrapped with MemGuard for full memory tracing

Run:
    python examples/demo_agent.py
    
Then view timeline at:
    http://localhost:3000/timeline/<session_id>
"""
```

---

### Task 2: Complete Backend Timeline API (Day 1-2)
**Files**: `backend/app/api/timeline.py`

Implement:
- `GET /v1/sessions/{session_id}/timeline`
  - Return all events for a session
  - Order by timestamp
  - Pagination support
  
- `GET /v1/agents/{agent_id}/timeline`
  - All events for an agent across sessions
  
- `GET /v1/memory/{memory_key}/lineage`
  - Show evolution: CREATE → UPDATE → UPDATE
  - Include before/after diffs

---

### Task 3: Build Dashboard - Timeline View (Day 3-5)
**Files**: `frontend/app/timeline/[sessionId]/page.tsx`

**Features** (in priority order):
1. **Simple table view**
   - Fetch events from API
   - Display: timestamp, operation, agent, memory_key
   - Color-code operations

2. **Event detail modal**
   - Click row → show full event
   - Show before/after diff
   - Show causality (caused_by link)

3. **Filtering**
   - By operation type
   - By agent_id
   - Time range

4. **Session selector**
   - Dropdown of recent sessions
   - Quick jump between sessions

5. **(Optional) Timeline visualization**
   - D3.js horizontal timeline
   - Zoom and pan
   - Visual diff

---

### Task 4: Documentation (Day 6-7)
**Files**: 
- `docs/quickstart.md`
- `docs/api-reference.md`
- `docs/integrations/langgraph.md`

**Content**:
1. **Quickstart Guide** (5 minutes to integrate)
   ```python
   # Step 1: Install
   pip install memguard
   
   # Step 2: Wrap your checkpointer
   from memguard.adapters.langgraph import MemGuardCheckpointer
   checkpointer = MemGuardCheckpointer(inner=your_checkpointer, ...)
   
   # Step 3: Start backend
   docker run -p 8000:8000 memguard/backend
   
   # Step 4: View dashboard
   open http://localhost:3000
   ```

2. **API Reference**
   - All endpoints documented
   - Request/response examples
   - Authentication (if applicable)

3. **Integration Guides**
   - LangGraph (complete)
   - LangChain (TODO)
   - Mem0 (TODO)
   - AutoGen (TODO)
   - CrewAI (TODO)

---

## 📊 Deliverables for Stage 1

### Code
- [ ] SDK package ready: `pip install memguard`
- [ ] Backend Docker image: `docker pull memguard/backend`
- [ ] Dashboard Docker image: `docker pull memguard/dashboard`
- [ ] Demo agent: `examples/demo_agent.py`
- [ ] Test suite

### Documentation
- [ ] Quickstart guide (5-minute integration)
- [ ] API reference (Swagger UI)
- [ ] LangGraph integration guide
- [ ] Architecture documentation

### Demo
- [ ] Video: "Memory debugging in 5 minutes"
- [ ] Live demo site (optional)

---

## 🎯 Success Criteria - Stage 1

### Functional
- ✅ Capture all memory operations from any LangGraph agent
- ✅ Store events in backend
- ✅ Query timeline via API
- ✅ Display timeline in dashboard
- ✅ See before/after diffs
- ✅ Trace memory lineage

### Non-Functional
- ✅ <5ms overhead per operation
- ✅ Handle 1000+ events/second
- ✅ Privacy-first (hash by default)
- ✅ Zero breaking changes to existing agents

### Adoption
- ✅ 3+ external developers integrate successfully
- ✅ Integration takes <30 minutes
- ✅ Clear value demonstrated

---

## 📝 Key Principles

### 1. Universal Compatibility
MemGuard must work with ANY agent system:
- LangGraph ✅
- LangChain
- Mem0
- AutoGen
- CrewAI
- Custom systems

### 2. Zero Breaking Changes
Integrating MemGuard should NEVER break existing agent logic.
It's pure observability - read-only by default.

### 3. Privacy-First
- Hash content by default
- Opt-in for raw content capture
- Clear documentation on data handling

### 4. Production-Ready
- Fire-and-forget (never block agents)
- Graceful degradation (observability failure ≠ agent failure)
- Low overhead (<5ms per operation)

---

## 🚀 This Week's Action Plan

### Monday (Today)
1. ✅ Review current SDK implementation
2. ✅ Create development plan
3. [ ] **Create standalone demo agent** (`examples/demo_agent.py`)
4. [ ] **Test SDK → Backend flow**

### Tuesday
5. [ ] **Complete timeline API** (backend)
6. [ ] **Test API with demo agent**

### Wednesday-Thursday
7. [ ] **Build frontend timeline view** (simple table first)
8. [ ] **Add event detail modal**
9. [ ] **Add filtering controls**

### Friday
10. [ ] **Write quickstart documentation**
11. [ ] **Create demo video**
12. [ ] **Package for distribution**

---

## 📦 Next Immediate Task

**Create `examples/demo_agent.py`** - A standalone demo showing MemGuard in action

This will:
- Show how to integrate MemGuard
- Provide a test case for the dashboard
- Serve as documentation
- Prove the value proposition

Ready to execute? 🚀
