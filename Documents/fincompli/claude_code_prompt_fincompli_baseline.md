## Project Overview

You will build an enterprise-grade financial compliance multi-agent system for me, named **FinCompli Baseline**.

This is a **runnable sandbox system** that simulates the compliance automation workflow of a mid-sized Hong Kong/Singapore bank. The goal is to establish an architecturally realistic, end-to-end Baseline. Afterwards, I will insert independent memory visualization and security layer products on top of it for testing, **but this iteration does not include any visualization or monitoring functionality**.

**Core value of this system**: To allow anyone seeing this system for the first time to clearly understand "how enterprise Agents work in real business scenarios" — from suspicious transaction triggering, to multi-agent collaborative analysis, to human review, to final compliance report submission.

---

## Strict Execution Rules

1. **Execute by Task**: I will list 8 tasks. After completing each task, output a summary and pause, waiting for me to input `continue` before executing the next task.
2. **After each task is completed**, list: the files created, the verifiable validation commands, and a preview of the next task.
3. **If you encounter dependency conflicts or environment issues**, tell me directly and provide two solutions. Do not make assumptions and continue on your own.
4. **All Mock data must be realistic and credible**: Customer names, amounts, regions, and case descriptions must reflect the real appearance of the financial industry. Do not use placeholders like `foo`, `test`, `example`.
5. **Code must have bilingual (Chinese/English) comments**: This system will later be shown to non-technical personnel. Comments should explain "what business operation this code is performing," not just technical descriptions.

---

## Tech Stack

```
Language: Python 3.11+
Agent Framework: langgraph >= 0.2.0
LLM: Locally deployed qwen3.6
Short-Term Memory: LangGraph Thread State (built-in checkpointer)
Episodic Memory: ChromaDB (past SAR case vector database)
Semantic Memory: ChromaDB (regulatory provision vector database)
Procedural Memory: SQLite (SOP workflow rules)
Long-Term User Memory: SQLite (compliance officer preference settings)
Embedding: sentence-transformers (all-MiniLM-L6-v2)
Audit Log: SQLite (structured, with reserved fields for future product integration)
API Service: FastAPI + uvicorn
Mock Data Generation: Faker (all English)
Test Entry: CLI interactive script
Language: English
```

**All dependency versions are fixed in requirements.txt to ensure reproducibility.**

---

## Complete Directory Structure

Create the following complete directory structure (create structure first, then fill in content):

```
fincompli-baseline/
│
├── README.md                         # System description (bilingual Chinese/English)
├── requirements.txt                  # Fixed-version dependencies
├── .env.example                      # Environment variable template
├── .gitignore
├── setup.py                          # One-click initialization script
│
├── config/
│   ├── __init__.py
│   └── settings.py                   # Global configuration (reads from .env)
│
├── agents/                           # All Agent definitions
│   ├── __init__.py
│   ├── supervisor.py                 # Main Supervisor Agent (LangGraph entry point)
│   ├── fraud_detection.py            # Sub-Agent 1: Transaction fraud detection
│   ├── compliance_research.py        # Sub-Agent 2: Regulatory provision research
│   ├── case_history.py               # Sub-Agent 3: Historical case retrieval
│   └── report_generator.py           # Sub-Agent 4: SAR report generation
│
├── graph/
│   ├── __init__.py
│   ├── state.py                      # LangGraph State Schema definition
│   ├── builder.py                    # Graph construction and compilation
│   └── nodes.py                      # All Graph Node functions
│
├── memory/                           # Memory layer (layered design)
│   ├── __init__.py
│   ├── short_term.py                 # Short-term: Thread State encapsulation
│   ├── episodic.py                   # Episodic: SAR case vector database
│   ├── semantic.py                   # Semantic: Regulatory knowledge vector database
│   ├── procedural.py                 # Procedural: SOP rules SQLite
│   └── user_prefs.py                 # User: Compliance officer preferences SQLite
│
├── tools/                            # Enterprise tool Mock implementations
│   ├── __init__.py
│   ├── transaction_monitor.py        # Transaction stream monitoring tool
│   ├── customer_database.py          # Customer database query tool
│   ├── risk_scorer.py                # Risk score calculation tool
│   ├── regulatory_lookup.py          # Regulatory provision query tool
│   ├── sar_submission.py             # SAR submission simulation tool
│   └── audit_logger.py              # Audit log recording (reserved interface)
│
├── mock_data/                        # Simulated enterprise data
│   ├── __init__.py
│   ├── generators/
│   │   ├── customers.py              # Generate 100 virtual customers
│   │   ├── transactions.py           # Generate transaction scenarios (normal/abnormal/borderline)
│   │   ├── sar_cases.py             # Generate 30 historical SAR cases
│   │   └── regulations.py            # Generate regulatory provision snippets
│   ├── seeds/
│   │   ├── customers.json            # Generated customer data
│   │   ├── sar_cases.json           # Generated historical cases
│   │   ├── regulations.json          # Regulatory provisions
│   │   └── transaction_scenarios.json # Test scenarios
│   └── seed_database.py              # Import seeds into all memory layers
│
├── api/
│   ├── __init__.py
│   ├── server.py                     # FastAPI main service
│   ├── routes/
│   │   ├── transactions.py           # /api/transactions endpoint
│   │   ├── analysis.py               # /api/analyze endpoint
│   │   └── reports.py                # /api/reports endpoint
│   └── schemas.py                    # Pydantic request/response models
│
├── cli/
│   ├── __init__.py
│   ├── interactive.py                # Interactive test CLI
│   └── batch_test.py                 # Batch scenario test
│
├── scenarios/                        # Complete test scenario scripts
│   ├── scenario_01_normal_transfer.py
│   ├── scenario_02_structuring.py    # Structuring (primary demo scenario)
│   ├── scenario_03_high_risk_kyc.py
│   ├── scenario_04_cross_border.py
│   └── scenario_05_false_positive.py
│
├── audit_logs/                       # Audit log output directory (git ignore)
│   └── .gitkeep
│
└── data/                             # Runtime data (git ignore)
    ├── chroma/                       # ChromaDB persistence directory
    └── sqlite/                       # SQLite database directory
```

---

## Task List (Execute in Order)

---

### TASK 1: Project Initialization and Environment Setup

**Objective**: Create the complete directory structure, configure all dependencies, and ensure the environment is runnable.

**Execution Steps**:

1. Create the complete directory structure (all directories and empty `__init__.py` files)

2. Create `requirements.txt` with the following content (fixed versions). Add more if needed:
```
langgraph==0.2.35
langchain==0.3.7
langchain-community==0.3.7
langchain-chroma==0.1.4
chromadb==0.5.15
sentence-transformers==3.2.1
fastapi==0.115.5
uvicorn==0.32.1
sqlalchemy==2.0.36
pydantic==2.10.1
pydantic-settings==2.6.1
faker==33.1.0
python-dotenv==1.0.1
rich==13.9.4
typer==0.13.1
httpx==0.28.0
pytest==8.3.3
pytest-asyncio==0.24.0
```

3. Create `.env.example`:
```env
# LLM Configuration
# LLM Configuration (local Qwen via llama.cpp llama-server)
LLM_BASE_URL=http://localhost:8080
LLM_MODEL=Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ3_M.gguf
LLM_API_KEY=not-needed-for-local

# Database Paths
CHROMA_DB_PATH=./data/chroma
SQLITE_DB_PATH=./data/sqlite/fincompli.db

# System Configuration
LOG_LEVEL=INFO
ENVIRONMENT=development
MAX_RISK_SCORE=0.85          # Above this score triggers human review
AUTO_APPROVE_THRESHOLD=0.30  # Below this score auto-clears

# Mock Settings
ENABLE_MOCK_DATA=true
TRANSACTION_STREAM_DELAY=0   # Seconds, 0 means instant

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
```

4. Create `config/settings.py` (use Pydantic Settings to read from environment variables)

5. Create `.gitignore` (exclude `data/`, `audit_logs/*.db`, `.env`, `__pycache__`, etc.)

6. Create `setup.py` one-click initialization script:
   - Auto-create `data/chroma`, `data/sqlite`, `audit_logs` directories
   - Copy `.env.example` to `.env` (if not already present)
   - Install dependencies
   - Output next-step instructions

**Completion Criteria**: Run `python setup.py` without errors, and `python -c "import langgraph; import chromadb; print('OK')"` passes.

---

### TASK 2: Mock Enterprise Data Generation

**Objective**: Generate all realistic, credible simulated enterprise data. This is the foundation of the entire system's credibility.

**Important**: Data must match real financial industry scenarios. Below are the specific requirements for each data category.

**2a. Customer Data (`mock_data/generators/customers.py`)**

Generate 100 customers, categorized by risk level:
- **Low Risk (60 people)**: Local residents/businesses, long-term stable transaction history, complete KYC
- **Medium Risk (30 people)**: Offshore companies or recently opened accounts, partially incomplete data
- **High Risk (10 people)**: PEP (Politically Exposed Persons) or involving FATF high-risk list countries

Each customer includes:
```json
{
  "customer_id": "C-XXXXX",
  "name": "Real person name or company name (use Faker to generate in English)",
  "type": "individual | corporate",
  "kyc_status": "verified | pending | expired",
  "risk_level": "low | medium | high",
  "country": "HK | SG | CN | KY | BVI | UK | US",
  "account_number": "HKXX XXXX XXXX XXXX",
  "account_open_date": "ISO date",
  "typical_transaction_range": {"min": 10000, "max": 500000},
  "typical_countries": ["HK", "SG"],
  "monthly_transaction_count": 5,
  "notes": "Customer notes (business description)"
}
```

**2b. Historical SAR Cases (`mock_data/generators/sar_cases.py`)**

Generate 30 historical SAR cases. These are the core of episodic memory.

Each case includes:
```json
{
  "sar_id": "SAR-2023-XXXX",
  "filed_date": "ISO date",
  "customer_id": "Associated customer",
  "case_type": "structuring | money_laundering | fraud | terrorist_financing | other",
  "transaction_pattern": "Detailed description of transaction pattern (2-3 sentences)",
  "amount_total": 1470000,
  "jurisdictions_involved": ["HK", "SG", "KY"],
  "suspicious_indicators": ["indicator_1", "indicator_2"],
  "regulations_cited": ["HKMA AML § 35", "FSTB Notice 2024-01"],
  "outcome": "filed | dismissed | referred_to_police",
  "case_summary": "Complete case summary (100-200 chars, for RAG retrieval)",
  "lessons_learned": "What was learned from this case"
}
```

Case type distribution:
- structuring: 10 cases
- money_laundering: 8 cases
- fraud: 7 cases
- terrorist_financing: 3 cases
- other: 2 cases

**2c. Regulatory Provisions (`mock_data/generators/regulations.py`)**

Generate simulated provision snippets for the following real regulatory frameworks (**do not fabricate regulation names; use real existing frameworks; content can be simplified**):

- HKMA Anti-Money Laundering Guidelines (AML Guideline 2023): 15 provisions
- MAS Monetary Authority of Singapore Notice MAS 626: 10 provisions
- FinCEN BSA/AML Requirements: 10 provisions
- FATF 40 Recommendations related provisions: 5 provisions

Each provision:
```json
{
  "regulation_id": "HKMA-AML-2023-§35",
  "jurisdiction": "HK | SG | US | INT",
  "authority": "HKMA | MAS | FinCEN | FATF",
  "section": "§ 35",
  "title": "Suspicious Transaction Reporting Obligation",
  "content": "Complete provision content (within 200 words)",
  "applicability": "Under what circumstances it applies",
  "deadline": "Report within 3 business days",
  "penalty": "Maximum fine amount or description"
}
```

**2d. Transaction Test Scenarios (`mock_data/generators/transactions.py`)**

Generate 5 categories of transaction scenarios, 5 transactions per category, totaling 25 test transactions:

1. **Normal Cross-Border Remittance**: Customer A transfers $150,000 from Hong Kong to Singapore, with clear business purpose
2. **Structuring (High Risk)**: Customer B transfers $490,000 each from HK, SG, and KY accounts within 3 minutes
3. **Abnormal Geographic Combination (Medium Risk)**: Customer C suddenly transfers to a FATF high-risk country, deviating from historical patterns
4. **KYC Expired High-Value Transaction (Medium Risk)**: Customer D has expired KYC but is still conducting large transactions
5. **False Positive Scenario**: Transactions that look suspicious but have reasonable explanations (tests system does not over-alert)

Each transaction:
```json
{
  "transaction_id": "TXN-YYYYMMDD-XXXXX",
  "timestamp": "ISO datetime",
  "customer_id": "C-XXXXX",
  "from_account": "Account number",
  "to_account": "Account number",
  "to_country": "Destination country code",
  "amount": 490000,
  "currency": "HKD | USD | SGD",
  "purpose_code": "Transaction purpose code",
  "channel": "swift | local_transfer | online",
  "ip_address": "If online transaction",
  "device_fingerprint": "Device ID",
  "scenario_type": "normal | structuring | geo_anomaly | kyc_expired | false_positive",
  "expected_risk_score": 0.93,
  "expected_outcome": "flag | clear | human_review"
}
```

**2e. Create `mock_data/seed_database.py`**

Read all seeds JSON files and complete:
1. Store customer data in SQLite
2. Vectorize SAR case `case_summary` and store in ChromaDB `episodic_memory` collection
3. Vectorize regulatory provision `content` and store in ChromaDB `semantic_memory` collection
4. Store transaction scenarios in SQLite
5. Output: `Imported X customers, X SAR cases, X regulations, X transaction scenarios`

**Completion Criteria**: `python mock_data/seed_database.py` succeeds, ChromaDB and SQLite have data, query test passes.

---

### TASK 3: Memory Layer Implementation

**Objective**: Implement a layered memory system with clear read/write interfaces for each layer, reserving standard hook points for future visualization product integration.

**Key Design**: Every memory operation must be recorded in the audit log with a fixed format. Future products only need to read this log to visualize.

**3a. `memory/short_term.py`**

Encapsulate LangGraph Thread State, providing:
```python
class ShortTermMemory:
    """
    Short-term memory: context state of the current conversation
    Stored in LangGraph Thread State, automatically cleared after conversation ends
    
    [Business Purpose] Allows all sub-agents to share the context of the current analysis task
    """
    def get_thread_state(self, thread_id: str) -> dict: ...
    def update_context(self, thread_id: str, key: str, value: Any) -> None: ...
```

**3b. `memory/episodic.py`**

Encapsulate ChromaDB `episodic_memory` collection:
```python
class EpisodicMemory:
    """
    Episodic memory: complete records of past SAR cases
    Used for: "Which past cases are similar to this transaction?"
    
    [Business Purpose] Allows the Agent to learn judgment patterns from historical cases
    """
    def retrieve_similar_cases(
        self, 
        query: str, 
        n_results: int = 5
    ) -> list[SARCaseResult]:
        """
        Returns format includes: case_id, similarity_score, case_summary, outcome
        similarity_score is key data for future visualization products and must be preserved
        """
        ...
    
    def add_case(self, case: SARCase) -> str: ...
```

**3c. `memory/semantic.py`**

Encapsulate ChromaDB `semantic_memory` collection:
```python
class SemanticMemory:
    """
    Semantic memory: regulatory provision knowledge base
    Used for: "Which regulatory provisions apply to this case?"
    
    [Business Purpose] Allows the Agent to automatically cite correct regulatory references, ensuring compliance reports are auditable
    """
    def retrieve_relevant_regulations(
        self, 
        context: str, 
        jurisdiction: str | None = None,
        n_results: int = 3
    ) -> list[RegulationResult]: ...
```

**3d. `memory/procedural.py`**

SQLite storage for SOP workflows:
```python
class ProceduralMemory:
    """
    Procedural memory: standard compliance operating procedures (SOP)
    Fixed rules, e.g.: "Score > 0.85 must submit SAR"
    
    [Business Purpose] Ensures all Agent behavior aligns with the bank's internal compliance processes
    """
    def get_workflow_rules(self, scenario_type: str) -> list[WorkflowRule]: ...
    def get_escalation_threshold(self) -> float: ...
```

**3e. `memory/user_prefs.py`**

SQLite storage for compliance officer preferences:
```python
class UserPrefsMemory:
    """
    User memory: compliance officer's personal preference settings
    e.g.: prefer Chinese reports, pay special attention to certain risk types
    
    [Business Purpose] Personalize the compliance officer's work interface to improve efficiency
    """
    def get_user_preferences(self, user_id: str) -> UserPreferences: ...
    def update_preference(self, user_id: str, key: str, value: Any) -> None: ...
```

**3f. Unified `MemoryAuditLog` (in `tools/audit_logger.py`)**

**This is the key interface for future product integration and must be implemented strictly according to this format:**

```python
class MemoryAuditLog:
    """
    Audit log: records all memory layer operations
    
    [Future Product Integration Point] Visualization products only need to subscribe to this log to obtain complete memory tracking data
    """
    def log_memory_event(self, event: MemoryEvent) -> None:
        """
        Write format (SQLite `memory_events` table):
        - event_id: UUID
        - timestamp: ISO datetime
        - event_type: "retrieve" | "write" | "delete" | "access_denied"
        - memory_type: "episodic" | "semantic" | "procedural" | "user_prefs"
        - agent_id: which agent triggered this operation
        - thread_id: current conversation thread
        - query: query content (for retrieve)
        - memory_ids: list of memory IDs involved (JSON)
        - similarity_scores: list of similarity scores (for retrieve, JSON)
        - output_snippet: memory content summary (first 200 characters)
        - security_flag: null | "unauthorized_access" | "suspicious_write" | "pii_leak"
        """
        ...
```

**Completion Criteria**:
```python
# The following test script should run successfully
from memory.episodic import EpisodicMemory
em = EpisodicMemory()
results = em.retrieve_similar_cases("Customer makes rapid consecutive transfers across three jurisdictions")
assert len(results) > 0
assert hasattr(results[0], 'similarity_score')
print(f"Found {len(results)} similar cases, highest similarity: {results[0].similarity_score:.2f}")
```

---

### TASK 4: Graph State Schema Definition

**Objective**: Define the core state schema for LangGraph. This is the "shared workbench" of the entire Agent system.

**`graph/state.py`**

```python
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import operator

class TransactionData(TypedDict):
    """A transaction pending analysis"""
    transaction_id: str
    customer_id: str
    amount: float
    currency: str
    from_country: str
    to_country: str
    timestamp: str
    channel: str
    # For batch analysis (e.g., structuring), includes related transactions
    related_transactions: list[dict]

class RiskAnalysis(TypedDict):
    """Fraud detection Agent's analysis result"""
    risk_score: float                    # 0.0 - 1.0
    risk_level: str                      # "low" | "medium" | "high" | "critical"
    suspicious_indicators: list[str]     # List of specific anomaly indicators
    pattern_type: str                    # "structuring" | "geo_anomaly" | "normal" | ...
    analysis_reasoning: str             # Agent's analysis explanation (in business language)

class ComplianceResearch(TypedDict):
    """Regulatory research Agent's output"""
    applicable_regulations: list[dict]  # List of applicable regulations (with citation sources)
    filing_deadline: str                # Reporting deadline
    required_actions: list[str]         # List of required actions
    jurisdiction: list[str]            # Jurisdictions involved

class HistoricalContext(TypedDict):
    """Case history Agent's output"""
    similar_cases: list[dict]           # Similar historical cases (with similarity scores)
    historical_pattern: str            # Pattern inferred from historical cases
    precedent_outcomes: list[str]       # Past outcomes of similar cases

class SARReport(TypedDict):
    """SAR report generation Agent's output"""
    report_id: str
    status: str                         # "draft" | "approved" | "submitted" | "dismissed"
    report_content: str                # Complete SAR report body (in business language, submittable format)
    evidence_trail: list[dict]         # Evidence trail (with memory sources for each basis)
    submission_deadline: str

class MemoryTrace(TypedDict):
    """
    Memory trace: complete record of each memory call
    [Future Product Integration Point] This is the core data structure for visualization products
    """
    event_id: str
    memory_type: str                    # "episodic" | "semantic" | "procedural" | "user_prefs"
    agent_id: str                       # Which agent called this memory
    query: str                         # Query content
    retrieved_memory_ids: list[str]    # Retrieved memory IDs
    similarity_scores: list[float]     # Corresponding similarity scores
    influenced_output: str             # Which part of the output this memory influenced
    timestamp: str

class HumanDecision(TypedDict):
    """Input for the human review node"""
    reviewer_id: str
    decision: str                       # "approve" | "reject" | "modify"
    comments: str
    timestamp: str

class ComplianceState(TypedDict):
    """
    Shared state for the entire analysis workflow
    
    [Business Purpose] This is the "shared workbench" for all Agents
    Any Agent can read the work results of other Agents, ensuring information consistency
    """
    # Conversation message history (automatically managed by LangGraph)
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Currently analyzed transaction
    transaction_data: TransactionData | None
    
    # Analysis results from each Agent
    risk_analysis: RiskAnalysis | None
    compliance_research: ComplianceResearch | None
    historical_context: HistoricalContext | None
    sar_report: SARReport | None
    
    # Flow control
    current_agent: str                  # Currently executing Agent
    next_agents: list[str]             # List of next Agents to execute
    requires_human_review: bool        # Whether human review is required
    human_decision: HumanDecision | None
    
    # Memory traces (all Agent memory calls accumulate here)
    memory_traces: Annotated[list[MemoryTrace], operator.add]
    
    # Security events (reserved; detection logic not implemented this iteration, only structure reserved)
    security_events: list[dict]
    
    # Final output
    final_outcome: str | None          # "sar_filed" | "cleared" | "pending_review"
    execution_timeline: list[dict]     # Complete execution timeline (for auditing)
```

**`graph/builder.py`** — Define the complete LangGraph workflow:

```python
"""
FinCompli Agent Workflow

Workflow Design:
1. Entry: Receive transaction → Supervisor routing
2. Parallel Analysis: Fraud detection + Case history run simultaneously
3. Aggregation: Supervisor aggregates results, decides whether regulatory research is needed
4. Regulatory Research: Query relevant regulations based on risk type
5. Report Generation: Aggregate all inputs, generate SAR draft
6. Human Review (triggered for high risk): interrupt() waits for compliance officer confirmation
7. Final Submission / Archival

Graph Structure:
START
  ↓
[supervisor_route]          ← Analyze intent, decide routing
  ↓
[fraud_detection] ←→ [case_history_retrieval]   ← Parallel execution
  ↓
[supervisor_aggregate]      ← Aggregate analysis results
  ↓ (if risk > threshold)
[compliance_research]       ← Query regulations
  ↓
[report_generation]         ← Generate SAR draft
  ↓ (if risk > MAX_RISK)
[human_review_interrupt]    ← Pause, wait for human
  ↓
[final_submission]          ← Submit / Archive
  ↓
END
"""
```

**Completion Criteria**: `from graph.state import ComplianceState` succeeds, all State fields have correct type annotations.

---

### TASK 5: Four Sub-Agent Implementation

**Objective**: Implement the core logic of each Sub-Agent, ensuring each Agent has clear responsibility boundaries and memory calls.

**Design Principles**:
- Each Agent does only one thing; inputs and outputs are clearly defined
- Every memory layer call must simultaneously write `MemoryTrace` to State
- System Prompts describe the Agent's role in business language, not technical terminology

**5a. `agents/fraud_detection.py`**

```python
"""
Fraud Detection Agent

Business Responsibilities:
- Analyze individual or multiple related transactions
- Identify suspicious transaction patterns (structuring, geographic anomalies, behavioral deviations, etc.)
- Output risk score (0.0-1.0) and specific suspicious indicators

Memory Used:
- Procedural memory: Fraud detection rules (e.g., "Same customer, 3 transactions within 30 minutes = suspicious")
- Short-term memory: Customer information in the current thread

Does NOT use: Historical cases (handled by case_history agent)
"""

FRAUD_DETECTION_SYSTEM_PROMPT = """
You are a senior Anti-Money Laundering (AML) analyst with 15 years of experience.

Your job is to analyze submitted transaction data and identify possible suspicious transaction patterns.

## Patterns You Should Identify

**Structuring**
- Multiple transactions with amounts just below the statutory reporting threshold (e.g., $499,000 each)
- Multi-jurisdictional operations within a short time window
- Purpose is to evade automatic reporting

**Geographic Anomaly**
- Destination country inconsistent with the customer's historical pattern
- Involving FATF high-risk list countries (e.g., Iran, North Korea, Myanmar)

**Behavioral Deviation**
- Transaction amount exceeding the customer's historical range by more than 3x
- Sudden change in transaction frequency or channel

## Output Format Requirements

Explain your analysis in business language that a compliance officer can understand.
Do not use technical terminology.
Every suspicious indicator must be supported by specific data.
"""
```

Implement `detect_fraud(state: ComplianceState) -> ComplianceState`:
1. Read `state["transaction_data"]`
2. Query ProceduralMemory for detection rules, record to `memory_traces`
3. Call LLM analysis (with customer historical data as context)
4. Output `RiskAnalysis` and update State

**5b. `agents/case_history.py`**

```python
"""
Historical Case Retrieval Agent

Business Responsibilities:
- Find the most similar cases in the historical SAR case database that match the current transaction
- Extract the handling methods and outcomes of historical cases
- Provide "reference precedents" for report generation

Memory Used:
- Episodic memory (ChromaDB): 30 historical SAR cases

The similarity scores output are core display data for visualization products
"""
```

Implement `retrieve_case_history(state: ComplianceState) -> ComplianceState`:
1. Extract transaction feature descriptions from `state["risk_analysis"]` as query
2. Query EpisodicMemory, retrieve top-5 similar cases
3. **Key**: Record complete `memory_trace` to State, including similarity scores
4. Output `HistoricalContext`

**5c. `agents/compliance_research.py`**

```python
"""
Regulatory Research Agent

Business Responsibilities:
- Based on transaction characteristics and jurisdictions involved, find applicable regulatory provisions
- Determine reporting deadlines and required actions
- Cite specific regulatory provisions (for SAR report)

Memory Used:
- Semantic memory (ChromaDB): HKMA/MAS/FinCEN regulatory provision database

The output of this Agent directly determines the legal basis quality of the SAR report
"""
```

**5d. `agents/report_generator.py`**

```python
"""
SAR Report Generation Agent

Business Responsibilities:
- Aggregate the analysis results of the three preceding Agents
- Generate a SAR report draft that meets regulatory requirements
- Report must include: factual statements, suspicious indicators, regulatory basis, evidence trail

Memory Used:
- Procedural memory: SAR report format template (HKMA standard format)
- User preference memory: Compliance officer's report language preference (Chinese/English)
- Short-term memory: All analysis results from the current conversation

This is the final output of the entire workflow; quality directly affects the compliance of regulatory filings
"""

SAR_REPORT_FORMAT = """
## Suspicious Transaction Report Draft
**Filing Institution**: [Institution Name]
**Filing Date**: [Date]
**Case Number**: [SAR-XXXX-XXXX]

### I. Suspicious Customer / Transaction Overview
[Customer basic information + Summary of involved transactions]

### II. Description of Suspicious Behavior
[Specific suspicious behavior, in business language, timeline format]

### III. Basis for Suspicion Determination
[Combined with historical case precedents + fraud analysis results]

### IV. Applicable Regulations
[Cite specific regulatory provisions]

### V. Recommended Actions
[Reporting deadline + Next steps]

### VI. Memory Citation Trail
[All memory sources this report is based on, including memory IDs and similarity scores]
"""
```

**Completion Criteria**:
```bash
python -c "
from agents.fraud_detection import FraudDetectionAgent
agent = FraudDetectionAgent()
print('FraudDetectionAgent initialized successfully')
"
```

---

### TASK 6: Supervisor and Graph Assembly

**Objective**: Use LangGraph to connect all Agents into a complete workflow, implementing parallel execution, conditional routing, and Human-in-the-loop.

**`agents/supervisor.py`**

Supervisor Responsibilities:
1. **Receive Task**: Analyze user input, extract transaction information
2. **Routing Decision**: Determine which Sub-Agents need to run
3. **Aggregate Results**: Wait for parallel Agents to complete, integrate outputs
4. **Risk Gating**: Determine whether human review is needed
5. **Final Decision**: Execute final action after human review

```python
SUPERVISOR_SYSTEM_PROMPT = """
You are the supervisor coordinator of the FinCompli system.

Your job is to coordinate the work of four expert analysts:
1. Fraud Detection Analyst: Evaluate transaction risk
2. Case History Researcher: Look up historical precedents
3. Regulatory Compliance Advisor: Determine applicable regulations
4. Report Writer: Generate SAR reports

You are responsible for:
- Deciding which analysts need to participate based on transaction type
- Aggregating all analysis results to form a unified determination
- When risk score exceeds {threshold}, pausing and requesting compliance officer review

You do not do analysis directly; you are the coordinator.
"""
```

**`graph/builder.py`** — Complete Graph Construction:

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Send, interrupt

def build_compliance_graph(memory_saver):
    """
    Build the complete compliance analysis Graph
    
    Parallel execution design:
    fraud_detection and case_history_retrieval run simultaneously
    After both complete, the supervisor aggregates results before continuing
    """
    
    builder = StateGraph(ComplianceState)
    
    # Add all nodes
    builder.add_node("supervisor_route", supervisor_route_node)
    builder.add_node("fraud_detection", fraud_detection_node)
    builder.add_node("case_history_retrieval", case_history_node)
    builder.add_node("supervisor_aggregate", supervisor_aggregate_node)
    builder.add_node("compliance_research", compliance_research_node)
    builder.add_node("report_generation", report_generation_node)
    builder.add_node("human_review", human_review_node)   # interrupt is here
    builder.add_node("final_submission", final_submission_node)
    
    # Define flow
    builder.add_edge(START, "supervisor_route")
    
    # Route to parallel execution
    builder.add_conditional_edges(
        "supervisor_route",
        lambda state: ["fraud_detection", "case_history_retrieval"],
        ["fraud_detection", "case_history_retrieval"]
    )
    
    # Aggregate after parallel completion
    builder.add_edge("fraud_detection", "supervisor_aggregate")
    builder.add_edge("case_history_retrieval", "supervisor_aggregate")
    
    # Conditional routing: risk level determines subsequent path
    builder.add_conditional_edges(
        "supervisor_aggregate",
        route_by_risk_level,
        {
            "low_risk": "final_submission",
            "needs_research": "compliance_research",
        }
    )
    
    builder.add_edge("compliance_research", "report_generation")
    
    # Conditional routing: high risk requires human review
    builder.add_conditional_edges(
        "report_generation",
        route_by_human_required,
        {
            "human_required": "human_review",
            "auto_approve": "final_submission"
        }
    )
    
    builder.add_edge("human_review", "final_submission")
    builder.add_edge("final_submission", END)
    
    # Compile, using SQLite checkpointer for state persistence
    return builder.compile(checkpointer=memory_saver)

def human_review_node(state: ComplianceState):
    """
    Human review node
    
    [Business Purpose] When the risk score exceeds the threshold, the system pauses and waits for compliance officer confirmation
    The compliance officer sees in this node: complete SAR draft + all analysis bases + memory call traces
    """
    # Use LangGraph interrupt to pause execution, waiting for external input
    decision = interrupt({
        "message": "Compliance officer review required",
        "risk_score": state["risk_analysis"]["risk_score"],
        "sar_draft": state["sar_report"],
        "memory_traces": state["memory_traces"],  # Pass memory traces to review interface
        "required_action": "Please review the SAR draft and choose: approve / reject / modify"
    })
    
    return {"human_decision": decision}
```

**Completion Criteria**:
```python
# The following should execute successfully (no LLM needed, only tests Graph structure)
from graph.builder import build_compliance_graph
from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string("./data/sqlite/test.db") as saver:
    graph = build_compliance_graph(saver)
    print("Graph compiled successfully")
    print("Nodes:", list(graph.nodes.keys()))
```

---

### TASK 7: CLI Test Interface and Complete Scenario Scripts

**Objective**: Create clear test entry points so anyone can conveniently run demo scenarios and understand what the system is doing.

**`cli/interactive.py`**

Use the `rich` library to achieve beautiful terminal output, allowing non-technical personnel to understand the system's operation process:

```python
"""
Interactive CLI

When each Agent executes, display in terminal:
- Agent name and responsibilities (with bilingual description)
- Memory type being queried
- Query result summary
- Output conclusion

Memory call display format:
┌─────────────────────────────────────┐
│  🧠 Memory Call: Episodic Memory     │
│  Query: "Rapid consecutive transfers across three jurisdictions" │
│  Found 3 similar cases:            │
│  ├ SAR-2024-0033 Similarity: 88%   │
│  ├ SAR-2023-0171 Similarity: 82%   │
│  └ SAR-2022-0089 Similarity: 71%   │
└─────────────────────────────────────┘

Human review node display:
┌─────────────────────────────────────┐
│  ⚠️  Human Review Required          │
│  Risk Score: 0.93 (Critical)       │
│  Enter decision [approve/reject/modify]: │
└─────────────────────────────────────┘
"""
```

**`scenarios/scenario_02_structuring.py`** (The most important demo scenario; needs to be most complete)

```python
"""
Scenario 02: Structuring

[Business Background]
Customer C-00412 (Sunrise Global Holdings Ltd, Cayman Islands offshore company)
Within 3 minutes, transfers HKD 490,000 each from three accounts in Hong Kong, Singapore, and Cayman Islands
Total: HKD 1,470,000, each transaction just below the HKD 500,000 automatic reporting threshold

[Expected Workflow]
1. Supervisor receives transaction → Routes to parallel analysis
2. Fraud detection: Identifies structuring pattern, risk score 0.93
3. Case history: Finds SAR-2024-0033 (similarity 88%) and SAR-2023-0171 (similarity 82%)
4. Supervisor aggregates: High risk, regulatory research needed
5. Regulatory research: HKMA §35 (3 business day reporting), FinCEN §103.18
6. Report generation: Generates SAR draft
7. Human review: Compliance officer reviews and approves
8. Final submission: SAR file archived

[Expected Output]
- Complete SAR draft (bilingual Chinese/English)
- 5 memory call records (with similarity scores)
- Complete execution timeline
- Compliance officer decision record
"""

SCENARIO_TRANSACTION = {
    "transaction_id": "TXN-20250315-88411",
    "timestamp": "2025-03-15T14:23:00+08:00",
    "customer_id": "C-00412",
    "customer_name": "Sunrise Global Holdings Ltd",
    "transactions": [
        {
            "sub_id": "TXN-88411-A",
            "timestamp": "2025-03-15T14:23:00+08:00",
            "from_account": "HK82 0012 3456 7890",
            "to_account": "KY1-9999-0001",
            "amount": 490000,
            "currency": "HKD",
            "to_country": "KY",  # Cayman Islands
            "channel": "swift"
        },
        {
            "sub_id": "TXN-88411-B",
            "timestamp": "2025-03-15T14:24:30+08:00",
            "from_account": "SG29 DBS9 0000 0001",
            "to_account": "KY1-9999-0002",
            "amount": 490000,
            "currency": "HKD",
            "to_country": "KY",
            "channel": "swift"
        },
        {
            "sub_id": "TXN-88411-C",
            "timestamp": "2025-03-15T14:26:00+08:00",
            "from_account": "KY2-8888-0001",
            "to_account": "BVI-0000-7777",
            "amount": 490000,
            "currency": "HKD",
            "to_country": "VG",  # British Virgin Islands
            "channel": "swift"
        }
    ]
}
```

**All 5 scenarios need to be created with consistent format, but scenario_02 needs the most detail.**

**`scenarios/scenario_05_false_positive.py`** (False positive scenario; tests system precision)

```python
"""
Scenario 05: False Positive

[Business Background]
Customer C-00088 (Finance department of a legitimate listed company)
Transfers large amounts to subsidiaries in 5 countries at quarter-end
Appears abnormal on the surface but has complete business documentation support

[Expected Workflow]
Fraud detection: Initial score 0.60 (medium risk)
Case history: Similar cases found all ended up as "normal business"
Supervisor: Medium risk, proceed with regulatory research
Compliance research: Confirms no filing needed if business documents exist
Report generation: Issues a "no filing required" explanation document
Final outcome: cleared, no SAR submitted

[Test Purpose]
Verify that the system is not overly sensitive and can correctly identify false positives
"""
```

**Completion Criteria**:
```bash
# Demo scenario should run completely
python cli/interactive.py --scenario 02
# System should complete the full workflow and output a SAR draft
```

---

### TASK 8: FastAPI Service + README + Final Integration Test

**Objective**: Provide API endpoints, improve documentation, and conduct end-to-end integration testing.

**`api/server.py`**

Provide the following API endpoints:

```
POST /api/analyze
  Body: { transaction_data: {...} }
  Response: { thread_id: "xxx", status: "started" }

GET /api/status/{thread_id}
  Response: { status, current_agent, risk_score, requires_human_review }

POST /api/human-decision/{thread_id}
  Body: { reviewer_id, decision, comments }
  Response: { status, final_outcome }

GET /api/report/{thread_id}
  Response: { sar_report, memory_traces, execution_timeline }

GET /api/memory-traces/{thread_id}
  Response: { traces: [{ memory_type, agent_id, query, memories, similarity_scores }] }
  [Future Product Integration Point] This endpoint is the primary data source for visualization products

GET /api/audit-log
  Query: ?limit=50&memory_type=episodic
  Response: { events: [...] }

GET /api/health
  Response: { status: "ok", version, agents_loaded, memory_collections }
```

**`README.md`** — Complete system documentation (bilingual Chinese/English):

```markdown
# FinCompli Baseline

An enterprise-grade Multi-Agent system simulating real financial institution compliance automation workflows.

## System Architecture Diagram (Text Version)

User/System inputs suspicious transaction
        ↓
  [Supervisor Agent]  ← Coordinates all analysis work
  ↙           ↘
[Fraud Detection]  [Case History]  ← Parallel execution
  ↘           ↙
  [Supervisor Aggregation]
        ↓ (Risk medium/high)
  [Regulatory Research Agent]    ← Query applicable regulations
        ↓
  [Report Generation Agent]    ← Generate SAR draft
        ↓ (High risk)
  [Human Review Node]      ← Compliance officer confirmation
        ↓
  [Final Submit / Archive]

## Memory Layer Design

| Memory Type     | Storage      | Use Case                         | Future Visualization |
|----------------|--------------|----------------------------------|---------------------|
| Short-Term     | Thread State | Current conversation context     | ✓                   |
| Episodic       | ChromaDB     | Historical SAR case retrieval    | ✓ Key Focus         |
| Semantic       | ChromaDB     | Regulatory provision lookup      | ✓                   |
| Procedural     | SQLite       | SOP rules                        | ✓                   |
| User Preferences | SQLite     | Compliance officer personalization | ✓                   |

## Quick Start

[Detailed installation and running steps]

## Test Scenario Descriptions

[Business descriptions of the 5 scenarios]

## Future Product Integration Points

[Explain which hook points are reserved for memory visualization products]
```

**Final Integration Test**:

```bash
# 1. Initialize
python setup.py

# 2. Generate and import Mock data
python mock_data/seed_database.py

# 3. Verify memory layer
python -m pytest tests/ -v

# 4. Run core demo scenario
python cli/interactive.py --scenario 02

# 5. Start API service
uvicorn api.server:app --reload

# 6. API test
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d @scenarios/scenario_02_data.json
```

**Final Completion Criteria**:
- [ ] All 5 scenarios run completely
- [ ] Scenario 02 (Structuring) complete output: SAR draft + Memory traces + Execution timeline
- [ ] `GET /api/memory-traces/{thread_id}` returns complete memory records including similarity scores
- [ ] `GET /api/audit-log` returns all memory operation logs
- [ ] README enables a compliance officer with no AI knowledge to understand what the system does

---

## Future Product Integration Notes (Not implemented this iteration, but interfaces must be preserved)

The following interface points in the Baseline only need to record data, no display:

```python
# 1. Memory call hooks (in each memory/ module)
def _log_memory_event(self, event_type, query, results):
    """
    [PRODUCT HOOK POINT]
    Future memory visualization products integrate here
    Expected integration: replace this method with a version that includes WebSocket push
    """
    audit_logger.log_memory_event(...)  # Currently only writes logs

# 2. The memory_traces list in State
# Future products read this list for visualization

# 3. GET /api/memory-traces/{thread_id}
# Primary data source for future products

# 4. GET /api/audit-log
# Data source for future security audit products
```

---

## Start Execution

Please start from **TASK 1**. After completing each task, list all created files and validation commands, then wait for me to input `continue` before executing the next task.

If you encounter any issues during execution, first describe the problem and two possible solutions, then wait for my confirmation before continuing.
