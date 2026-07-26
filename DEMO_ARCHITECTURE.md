# MemGuard Demo Architecture Design

**Version:** 1.0  
**Date:** 2026-07-10  
**Status:** Design Complete - Ready for Implementation

---

## Executive Summary

This document defines a **three-layer demo architecture** that showcases MemGuard's core value: making AI agent memory observable, traceable, and explainable in real enterprise scenarios.

**Target Audiences:**
- **Non-technical** (Investors, Compliance Officers, Product Managers): See AI preventing a HKD 1.47M money laundering transaction with full explanation
- **Technical** (Engineers, Platform Teams): See a LangGraph multi-agent system with 5 memory layers tracked across 11+ memory operations

**Core Narrative:**
> "An AI Agent just blocked a HKD 1.47M structuring transaction. Do you know why it made that decision? MemGuard does."

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         LAYER 3: Dashboard                       │
│            (Claude-style UI, 3 views, English only)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Memory     │  │   Decision   │  │   Summary    │          │
│  │   Timeline   │  │    Trace     │  │     Card     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP API
┌────────────────────────────┴────────────────────────────────────┐
│                    MemGuard Backend (FastAPI)                    │
│  • Event ingestion       • Decision trace storage               │
│  • SQLite persistence    • Influence score calculation          │
│  • Audit report generation                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │ SDK Transport
┌────────────────────────────┴────────────────────────────────────┐
│                      MemGuard SDK Layer                          │
│  • Intercepts all memory operations                             │
│  • Calculates content hashes                                    │
│  • Fire-and-forget event emission                               │
└────────────────────────────┬────────────────────────────────────┘
                             │ Wraps
┌────────────────────────────┴────────────────────────────────────┐
│                   FinCompli Multi-Agent System                   │
│                    (Scenario 02: Structuring)                    │
│                                                                  │
│  Supervisor → [Fraud Detection ∥ Case History]                  │
│       ↓                                                          │
│  Compliance Research → Report Generation                         │
│       ↓                                                          │
│  Human Review → Final Submission                                 │
│                                                                  │
│  Memory Types Used:                                              │
│  • Episodic (Historical SAR cases in ChromaDB)                   │
│  • Semantic (Regulations in ChromaDB)                            │
│  • Procedural (SOP rules in SQLite)                              │
│  • Working (Thread state in LangGraph)                           │
│  • User Preferences (Officer settings in SQLite)                 │
└──────────────────────────────────────────────────────────────────┘
                             │
                   Local Qwen Model (llama.cpp)
                   http://localhost:8080
```

---

## Three-Layer Implementation Plan

### Layer 1: Terminal Demo (`python demo.py`)

**Goal:** One command runs complete FinCompli Scenario 02 with beautiful terminal output

**Features:**
- ✅ Runs entire Structuring scenario (HKD 1.47M case)
- ✅ Real-time colored memory event display
- ✅ Shows all 5 agents in action
- ✅ Displays decision trace with influence scores
- ✅ Works with local Qwen model
- ✅ Complete in ~60 seconds

**Terminal Output Structure:**
```
┌──────────────────────────────────────────────┐
│  MemGuard × FinCompli                        │
│  Enterprise Compliance Demo                  │
└──────────────────────────────────────────────┘

[Scenario] Structuring Detection
Customer splits HKD 1,470,000 into 3×490,000
to avoid HKD 500,000 reporting threshold

┌─ Stage 1: Parallel Analysis ─────────────────┐
│                                              │
│ [Fraud Detection Agent]                      │
│   🔵 READ    episodic:customer_history       │
│   🟢 CREATE  working:fraud_analysis          │
│   Risk Score: 0.89 (CRITICAL)                │
│                                              │
│ [Case History Agent]                         │
│   🔷 QUERY   episodic:sar_cases             │
│   Retrieved: SAR-2024-0033 (similarity=0.88) │
│   🟢 CREATE  working:case_history           │
│                                              │
└──────────────────────────────────────────────┘

┌─ Stage 2: Compliance Research ───────────────┐
│                                              │
│ [Compliance Research Agent]                  │
│   🔷 QUERY   semantic:regulations           │
│   Retrieved: HKMA §35, FATF R.10            │
│   🟢 CREATE  working:compliance_findings    │
│                                              │
└──────────────────────────────────────────────┘

┌─ Stage 3: Report Generation ─────────────────┐
│                                              │
│ [Report Generation Agent]                    │
│   🔵 READ    working:fraud_analysis         │
│   🔵 READ    working:case_history           │
│   🔵 READ    working:compliance_findings    │
│   🟢 CREATE  working:sar_report             │
│                                              │
└──────────────────────────────────────────────┘

┌─ Decision Trace ─────────────────────────────┐
│                                              │
│ Memory IN (3 reads, influence=0.92):         │
│   • episodic:sar_cases → 0.88               │
│   • semantic:regulations → 0.76             │
│   • working:fraud_analysis → 0.89           │
│                    ↓                         │
│ Agent Decision: FILE SAR (High Risk)         │
│                    ↓                         │
│ Memory OUT (1 create):                       │
│   • working:sar_report                      │
│                                              │
└──────────────────────────────────────────────┘

✅ Scenario Complete
   Total Events: 11
   Decision Traces: 4
   Final Decision: FILE SAR (requires human review)

🔍 View full trace: http://localhost:3001
```

**Key Deliverables:**
- `demo.py` - Single entry point script
- Beautiful Rich-based terminal output
- Real FinCompli Scenario 02 execution
- Works with local Qwen model

---

### Layer 2: Decision Trace Enhancement

**Goal:** Make the causal chain crystal clear: "Memory X influenced Decision Y"

**Current Problem:**
- MemGuard tracks events ✅
- MemGuard stores decision traces ✅
- But the **causal link** between memory and decision is implicit

**Solution: Influence Score Visualization**

```
┌─ Decision Trace #3: Report Generation ───────────────────────────┐
│                                                                   │
│ Agent: report_generation                                          │
│ Timestamp: 2026-07-10 15:32:18                                    │
│                                                                   │
│ ┌─ MEMORY IN ────────────────────────────────────────────────┐   │
│ │                                                            │   │
│ │  🔵 READ  episodic:sar_cases                              │   │
│ │          ├─ SAR-2024-0033 (similarity: 0.88)              │   │
│ │          └─ Influence: ██████████████████░░ 0.88          │   │
│ │                                                            │   │
│ │  🔵 READ  semantic:regulations                            │   │
│ │          ├─ HKMA §35, FATF R.10                           │   │
│ │          └─ Influence: ███████████████░░░░░ 0.76          │   │
│ │                                                            │   │
│ │  🔵 READ  working:fraud_analysis                          │   │
│ │          ├─ Risk Score: 0.89                              │   │
│ │          └─ Influence: ██████████████████░░ 0.89          │   │
│ │                                                            │   │
│ │  Total Influence Score: 2.53                              │   │
│ └────────────────────────────────────────────────────────────┘   │
│                                                                   │
│                            ↓                                      │
│                                                                   │
│ ┌─ AGENT DECISION ───────────────────────────────────────────┐   │
│ │                                                            │   │
│ │  Decision: FILE SAR                                        │   │
│ │  Confidence: HIGH (0.92)                                   │   │
│ │                                                            │   │
│ │  Reasoning:                                                │   │
│ │  • Pattern matches SAR-2024-0033 (structuring)            │   │
│ │  • Violates HKMA §35 reporting threshold                  │   │
│ │  • Fraud score 0.89 exceeds critical threshold            │   │
│ │                                                            │   │
│ └────────────────────────────────────────────────────────────┘   │
│                                                                   │
│                            ↓                                      │
│                                                                   │
│ ┌─ MEMORY OUT ───────────────────────────────────────────────┐   │
│ │                                                            │   │
│ │  🟢 CREATE  working:sar_report                            │   │
│ │            Content Hash: 7f3a9b...                        │   │
│ │            Size: 2.4 KB                                    │   │
│ │                                                            │   │
│ └────────────────────────────────────────────────────────────┘   │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

**Key Enhancements:**
1. **Visual causal flow** (Memory IN → Decision → Memory OUT)
2. **Influence score bars** (quantitative + visual)
3. **Decision reasoning extraction** (from LLM output)
4. **Content preview** (first 100 chars of retrieved memory)

**Implementation:**
- Enhance backend `decision_traces` table with reasoning field
- Add influence score calculation in SDK
- Create rich terminal formatter for decision traces
- Add decision trace API endpoint with full details

---

### Layer 3: Dashboard (Claude-style)

**Goal:** Three-view dashboard with Claude.ai aesthetic - minimal, fast, beautiful

**Design Principles:**
- **Simplicity**: Only 3 views, no feature bloat
- **Speed**: Instant load, real-time updates
- **Beauty**: Claude.ai inspired - lots of white space, soft shadows, purple accents
- **Clarity**: Business story first, technical details on click

**View 1: Memory Timeline**

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Memory Timeline                                                │
│  Scenario 02: Structuring Detection                             │
│                                                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                 │
│  15:32:10  🔵 READ     episodic        fraud_detection         │
│            customer_history                                     │
│                                                                 │
│  15:32:11  🔷 QUERY    episodic        case_history           │
│            sar_cases → 3 matches                               │
│                                                                 │
│  15:32:12  🟢 CREATE   working         fraud_detection         │
│            fraud_analysis                                       │
│                                                                 │
│  15:32:13  🟢 CREATE   working         case_history           │
│            case_history_analysis                               │
│                                                                 │
│  15:32:15  🔷 QUERY    semantic        compliance_research     │
│            regulations → 2 matches                              │
│                                                                 │
│  15:32:17  🔵 READ     working         report_generation       │
│            fraud_analysis                                       │
│                                                                 │
│  15:32:17  🔵 READ     working         report_generation       │
│            case_history_analysis                               │
│                                                                 │
│  15:32:18  🟢 CREATE   working         report_generation       │
│            sar_report                                           │
│                                                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                 │
│  11 events • 8 seconds • 4 agents                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**View 2: Decision Trace (Interactive)**

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Decision Trace                                                 │
│  Why did the AI flag this transaction?                          │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                                                           │ │
│  │  Memory Evidence                                          │ │
│  │                                                           │ │
│  │  SAR-2024-0033 (88% match)                               │ │
│  │  "Customer structured HKD 1.2M across multiple branches  │ │
│  │   to avoid reporting threshold..."                       │ │
│  │                                                           │ │
│  │  Influence: ██████████████████░░ 0.88                    │ │
│  │                                                           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│                           ↓                                     │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                                                           │ │
│  │  Regulatory Violation                                     │ │
│  │                                                           │ │
│  │  HKMA §35: Reporting Threshold HKD 500,000              │ │
│  │  "Financial institutions must file STR for transactions │ │
│  │   exceeding HKD 500,000..."                             │ │
│  │                                                           │ │
│  │  Influence: ███████████████░░░░░ 0.76                    │ │
│  │                                                           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│                           ↓                                     │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                                                           │ │
│  │  AI Decision: FILE SAR                                    │ │
│  │                                                           │ │
│  │  This transaction exhibits structuring behavior matching │ │
│  │  historical case SAR-2024-0033 and violates HKMA §35.   │ │
│  │  Requires immediate human review.                         │ │
│  │                                                           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**View 3: Summary Card (Business View)**

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Compliance Case Summary                                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                         │   │
│  │  Case ID: TXN-2024-071001                              │   │
│  │  Amount: HKD 1,470,000                                  │   │
│  │  Pattern: Structuring (3 transactions)                 │   │
│  │                                                         │   │
│  │  Risk Assessment: CRITICAL (0.93)                       │   │
│  │                                                         │   │
│  │  Decision: FILE SAR                                     │   │
│  │  Status: Awaiting Human Review                          │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Key Findings                                                   │
│                                                                 │
│  • Customer split large amount to avoid threshold              │
│  • Pattern matches historical SAR case (88% similarity)        │
│  • Violates HKMA §35 reporting requirements                   │
│  • Multiple rapid transactions across branches                 │
│                                                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                 │
│  AI System Performance                                          │
│                                                                 │
│  • 11 memory operations traced                                 │
│  • 4 agents coordinated                                        │
│  • 5 memory types accessed                                     │
│  • 8 second analysis time                                      │
│  • 100% decision transparency                                  │
│                                                                 │
│  [Download Full Report] [View Memory Timeline]                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Technical Stack:**
- Next.js 14 (App Router)
- Tailwind CSS
- Real-time updates via polling (1s interval during demo)
- Claude.ai color palette:
  - Primary: `#7C3AED` (purple-600)
  - Background: `#FFFFFF`
  - Cards: `#F9FAFB` with `shadow-sm`
  - Text: `#111827` (gray-900) / `#6B7280` (gray-500)
  - Accents: `#8B5CF6` (purple-500)

---

## Integration Points

### 1. MemGuard SDK → FinCompli

**File:** `fincompli-baseline/run_with_memguard.py` (already exists, needs enhancement)

**What it does:**
- Wraps FinCompli's memory operations with MemGuard interceptor
- Captures all 5 memory types
- Associates memory ops with agent decisions
- Calculates influence scores

**Key code:**
```python
from memguard import MemGuardInterceptor
from memguard.adapters.langgraph import MemGuardCheckpointer
from memguard.transport.http import HttpTransport

# Wrap all memory layers
interceptor = MemGuardInterceptor(
    agent_id="fincompli",
    namespace="enterprise-demo",
    transport=HttpTransport("http://localhost:8000"),
    capture_content=True,  # For demo only
)

# Wrap episodic memory (ChromaDB)
episodic_memory = MemGuardEpisodicWrapper(
    inner=ChromaDBStore(...),
    interceptor=interceptor,
    memory_type="episodic"
)

# Wrap semantic memory (ChromaDB)
semantic_memory = MemGuardSemanticWrapper(
    inner=ChromaDBStore(...),
    interceptor=interceptor,
    memory_type="semantic"
)

# Wrap procedural memory (SQLite)
procedural_memory = MemGuardProceduralWrapper(
    inner=SQLiteStore(...),
    interceptor=interceptor,
    memory_type="procedural"
)

# Run scenario
run_scenario_02(
    episodic=episodic_memory,
    semantic=semantic_memory,
    procedural=procedural_memory,
)
```

### 2. Backend → Dashboard

**API Endpoints:**

```
GET /v1/events
  → Returns memory events for timeline view

GET /v1/decision-traces
  → Returns decision traces with influence scores

GET /v1/summary/{session_id}
  → Returns business summary for summary card

GET /v1/db/stats
  → Returns system statistics
```

### 3. Local Qwen Model

**Configuration:**
- Model: Qwen 3.6 (via llama.cpp server)
- Endpoint: `http://localhost:8080/v1/chat/completions`
- API compatible with OpenAI format
- Used by all FinCompli agents for analysis

---

## Execution Workflow

### Demo Flow (60 seconds)

```
T=0s    User runs: python demo.py --scenario 02
        ├─ Initialize MemGuard SDK
        ├─ Connect to local Qwen
        ├─ Connect to MemGuard backend
        └─ Load Scenario 02 data

T=5s    [Supervisor] Initial routing
        ├─ Decision: Run fraud_detection + case_history in parallel
        └─ 🟢 CREATE working:routing_decision

T=10s   [Fraud Detection] Analyze transaction pattern
        ├─ 🔵 READ episodic:customer_history
        ├─ Call Qwen for fraud analysis
        └─ 🟢 CREATE working:fraud_analysis (score=0.89)

T=10s   [Case History] (parallel) Find similar cases
        ├─ 🔷 QUERY episodic:sar_cases
        ├─ ChromaDB returns 3 matches (best: 0.88)
        └─ 🟢 CREATE working:case_history_analysis

T=20s   [Supervisor] Aggregate results
        ├─ 🔵 READ working:fraud_analysis
        ├─ 🔵 READ working:case_history_analysis
        ├─ Calculate aggregated risk: 0.93 (CRITICAL)
        └─ Decision: Run compliance_research

T=30s   [Compliance Research] Query regulations
        ├─ 🔷 QUERY semantic:regulations
        ├─ ChromaDB returns HKMA §35, FATF R.10
        └─ 🟢 CREATE working:compliance_findings

T=40s   [Report Generation] Generate SAR
        ├─ 🔵 READ working:fraud_analysis
        ├─ 🔵 READ working:case_history_analysis
        ├─ 🔵 READ working:compliance_findings
        ├─ Call Qwen to generate report
        └─ 🟢 CREATE working:sar_report

T=50s   [Supervisor] Route to human review
        └─ Decision: requires_human_review=True

T=60s   Demo complete, display summary
        ├─ Total events: 11
        ├─ Decision traces: 4
        ├─ Final decision: FILE SAR
        └─ Show dashboard URL
```

---

## Success Metrics

### Layer 1 (Terminal Demo)
- ✅ One command starts demo
- ✅ Complete in <60 seconds
- ✅ All 11+ memory events displayed
- ✅ Beautiful colored output
- ✅ Works with local Qwen
- ✅ Clear business narrative

### Layer 2 (Decision Trace)
- ✅ Causal chain visible (Memory → Decision → Memory)
- ✅ Influence scores calculated and displayed
- ✅ Decision reasoning extracted
- ✅ Terminal + API both have rich format

### Layer 3 (Dashboard)
- ✅ Loads in <2 seconds
- ✅ Claude-style aesthetic
- ✅ 3 views working perfectly
- ✅ Real-time updates during demo
- ✅ Non-technical person understands the story
- ✅ Technical person sees full trace

---

## Open Source Package Structure

```
memguard-demo/
├── README.md                          # Story-first narrative
├── demo.py                            # One-command demo (Layer 1)
├── .env.example                       # Configuration template
│
├── sdk/                               # MemGuard SDK
│   └── memguard/
│       ├── core/
│       ├── adapters/
│       └── transport/
│
├── backend/                           # MemGuard backend (minimal)
│   └── app/
│       ├── main.py
│       ├── services.py
│       └── schemas.py
│
├── dashboard/                         # Layer 3 (3 views only)
│   ├── app/
│   │   └── page.tsx                  # Single-page app
│   └── components/
│       ├── MemoryTimeline.tsx
│       ├── DecisionTrace.tsx
│       └── SummaryCard.tsx
│
├── fincompli/                         # Simplified FinCompli
│   ├── scenario_02.json              # Structuring case only
│   ├── agents/                       # 4 agents (minimal)
│   ├── memory/                       # 5 memory types
│   └── run.py                        # Scenario runner
│
└── docs/
    ├── ARCHITECTURE.md               # This file
    ├── LAYER1_GUIDE.md               # Implementation guide
    ├── LAYER2_GUIDE.md
    └── LAYER3_GUIDE.md
```

**NOT included:**
- FinCompli scenarios 01, 03, 04, 05
- MemGuard Stage 2+ features
- Unused agents or memory types
- Complex configuration options

---

## Next Steps

1. **Implement Layer 1** (Priority 1)
   - Create `demo.py` entry point
   - Integrate MemGuard SDK with FinCompli Scenario 02
   - Build beautiful terminal output with Rich
   - Test with local Qwen

2. **Implement Layer 2** (Priority 2)
   - Enhance decision trace output format
   - Add influence score visualization
   - Extract decision reasoning from LLM output
   - Create terminal formatter

3. **Implement Layer 3** (Priority 3)
   - Redesign dashboard with Claude aesthetic
   - Build 3 views (Timeline, Trace, Summary)
   - Add real-time updates
   - Polish and test

4. **Polish Demo** (Priority 4)
   - Record demo video
   - Write story-first README
   - Test with real users
   - Prepare for open source

---

**End of Architecture Document**
