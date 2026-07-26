# FinCompli Baseline

**Enterprise Multi-Agent Financial Compliance System**

Version 0.1 - MVP Baseline

---

## Overview

FinCompli Baseline is a **runnable sandbox system** that simulates the compliance automation workflow of a mid-sized Hong Kong/Singapore bank. This baseline demonstrates how enterprise AI agents work together in real business scenarios — from suspicious transaction detection to multi-agent collaborative analysis to manual review to final compliance report submission.

**Core Value**: This system allows anyone to clearly understand "how enterprise agents work in real business scenarios" at first glance.

---

## System Architecture

```
User/System Input Suspicious Transaction
        ↓
  [Supervisor Agent]  ← Coordinates all analysis work
  ↙           ↘
[Fraud Detection]  [Case History]  ← Execute in parallel
  ↘           ↙
  [Supervisor Aggregate] ← Consolidate results
        ↓ (Medium/High Risk)
  [Compliance Research Agent]  ← Query applicable regulations
        ↓
  [Report Generation Agent]    ← Generate SAR draft
        ↓ (High Risk)
  [Human Review Node]          ← Compliance officer confirms
        ↓
  [Final Submission/Archive] ← Submit/archive
```

---

## Memory Layer Design

| Memory Type | Storage | Use Case | Visualization |
|------------|-------------|----------------------------|-----------|
| Short-term Memory | Thread State | Current conversation context | ✓ |
| Episodic Memory | ChromaDB | Historical SAR case retrieval | ✓ **Key** |
| Semantic Memory | ChromaDB | Regulatory text query | ✓ |
| Procedural Memory | SQLite | SOP rules | ✓ |
| User Preferences | SQLite | Compliance officer personalization | ✓ |

---

## Technology Stack

```
Language: Python 3.9+
Agent Framework: LangGraph >= 0.2.0
LLM: Local Qwen 3.6 (via llama.cpp)
Short-term Memory: LangGraph Thread State (built-in checkpointer)
Episodic Memory: ChromaDB (past SAR case vector database)
Semantic Memory: ChromaDB (regulatory text vector database)
Procedural Memory: SQLite (SOP workflow rules)
User Memory: SQLite (compliance officer preferences)
Embedding: sentence-transformers (all-MiniLM-L6-v2)
Audit Log: SQLite (structured, with reserved fields for future product integration)
API Service: FastAPI + uvicorn
Mock Data Generation: Faker (all English)
Test Interface: CLI interactive script
Language: English
```

---

## Quick Start

### 1. Environment Setup

```bash
# Clone or navigate to project directory
cd fincompli-baseline

# Run one-click setup script
python setup.py

# Install dependencies (recommended: use virtual environment)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Verify installation
python -c "import langgraph; import chromadb; print('✓ OK')"
```

### 2. Configure LLM

Edit `.env` file and configure your local Qwen endpoint:

```env
LLM_BASE_URL=http://localhost:8080
LLM_MODEL=Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ3_M.gguf
```

### 3. Generate Mock Data

```bash
python mock_data/seed_database.py
```

This will generate:
- 100 virtual customers (60 low-risk, 30 medium-risk, 10 high-risk)
- 30 historical SAR cases
- 40 regulatory text segments
- 25 test transaction scenarios

### 4. Run Test Scenario

```bash
# Interactive CLI mode
python cli/interactive.py --scenario 02

# Scenario 02: Structuring (most complete demo scenario)
```

### 5. Start API Server

```bash
uvicorn api.server:app --reload

# API will be available at: http://localhost:8000
# API Documentation: http://localhost:8000/docs
```

---

## Test Scenarios

| Scenario | Type | Risk Level | Description |
|----------|------|------------|-------------|
| 01 | Normal Transfer | Low | Standard cross-border remittance with clear business purpose |
| 02 | **Structuring** | **Critical** | Customer splits HKD 1.47M into 3×490K to avoid reporting threshold |
| 03 | High-Risk KYC | High | Large transaction with expired KYC documentation |
| 04 | Cross-Border | Medium | Unusual destination country pattern |
| 05 | False Positive | Low | Appears suspicious but has valid business explanation |

**Scenario 02 (Structuring)** is the **primary demonstration scenario** with the most complete workflow including human review.

---

## Directory Structure

```
fincompli-baseline/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── .env                         # Environment config (created by setup.py)
├── setup.py                     # One-click initialization
│
├── config/                      # Global configuration
├── agents/                      # All agent definitions
├── graph/                       # LangGraph state and builder
├── memory/                      # Memory layer (tiered design)
├── tools/                       # Enterprise tools mock
├── mock_data/                   # Simulated enterprise data
│   ├── generators/              # Data generators
│   └── seeds/                   # Generated data files
├── api/                         # FastAPI service
├── cli/                         # Interactive CLI
├── scenarios/                   # Complete test scenarios
├── audit_logs/                  # Audit log output
└── data/                        # Runtime data
    ├── chroma/                  # ChromaDB persistence
    └── sqlite/                  # SQLite databases
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze` | POST | Submit transaction for analysis |
| `/api/status/{thread_id}` | GET | Get analysis status |
| `/api/human-decision/{thread_id}` | POST | Submit human review decision |
| `/api/report/{thread_id}` | GET | Get SAR report and execution trace |
| `/api/memory-traces/{thread_id}` | GET | **Get memory traces (for visualization products)** |
| `/api/audit-log` | GET | Get audit log |
| `/api/health` | GET | System health check |

**Key Integration Point for Downstream Products:**  
`GET /api/memory-traces/{thread_id}` - This endpoint provides complete memory trace data including similarity scores, which is the primary data source for memory visualization products.

---

## Future Product Integration Points

The following hook points are **reserved but not implemented** in this baseline:

1. **Memory Call Hooks** (`memory/*.py` modules)
   - Current: Only writes to audit log
   - Future: Replace with WebSocket push for real-time visualization

2. **State `memory_traces` List** (`graph/state.py`)
   - Downstream products read this for visualization
   - Contains: memory_type, agent_id, query, similarity_scores

3. **`GET /api/memory-traces/{thread_id}` Endpoint**
   - Primary data source for visualization products
   - Returns structured memory trace data

4. **`GET /api/audit-log` Endpoint**
   - Data source for security audit products
   - Structured SQLite format with reserved security_flag field

---

## Development Status

- [x] TASK 1: Project initialization and environment setup
- [ ] TASK 2: Mock enterprise data generation
- [ ] TASK 3: Memory layer implementation
- [ ] TASK 4: Graph state schema definition
- [ ] TASK 5: Four sub-agent implementation
- [ ] TASK 6: Supervisor and graph assembly
- [ ] TASK 7: CLI test interface and scenario scripts
- [ ] TASK 8: FastAPI service + final integration testing

---

## License

This is a baseline demonstration system for internal development and testing purposes.

---

## Contact

For questions or issues, please refer to the project documentation.

---

**Last Updated:** 2026-06-26  
**Version:** 0.1.0-baseline
