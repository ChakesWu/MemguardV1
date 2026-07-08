# FinCompli Baseline

**A production-grade multi-agent system simulating real enterprise financial compliance workflows.**

Built with LangGraph · Claude · ChromaDB · FastAPI

---

## What This Is

FinCompli Baseline is an open-source simulation of how a mid-sized bank's compliance team could automate suspicious transaction analysis using AI agents.

It is not a toy demo. It is designed to show — clearly and completely — what enterprise-grade agent architecture looks like when applied to a real business problem: Anti-Money Laundering (AML) compliance.

If you have ever wondered "what does a production multi-agent system actually do in a real company?", this is your answer.

---

## The Business Problem It Solves

Every bank is legally required to detect and report suspicious transactions to regulators (in Hong Kong: HKMA; Singapore: MAS; US: FinCEN).

Today, this process looks like this:

```
Compliance officer manually reviews flagged transactions
        ↓
Searches past cases for precedents (hours of work)
        ↓
Looks up relevant regulations (more hours)
        ↓
Writes a Suspicious Activity Report (SAR) from scratch
        ↓
Submits to regulator within 3 business days
```

A single compliance officer handles dozens of cases per week. The work is repetitive, time-sensitive, and high-stakes. A mistake means a regulatory fine. A delay means a missed deadline.

FinCompli Baseline shows how this entire process can be orchestrated by AI agents, with a human staying in control at the critical decision point.

---

## How It Works

Four specialist agents work together, each with a clear role:

```
Incoming suspicious transaction
           ↓
    ┌─────────────────┐
    │  Supervisor     │  ← Coordinates everything, decides routing
    └────────┬────────┘
         ↙       ↘
┌──────────┐  ┌──────────────┐
│  Fraud   │  │    Case      │  ← Run in parallel
│Detection │  │  History     │
└──────────┘  └──────────────┘
         ↘       ↙
    ┌─────────────────┐
    │  Supervisor     │  ← Aggregates results
    └────────┬────────┘
             ↓
    ┌─────────────────┐
    │   Compliance    │  ← Looks up applicable regulations
    │   Research      │
    └────────┬────────┘
             ↓
    ┌─────────────────┐
    │    Report       │  ← Drafts the SAR document
    │   Generator     │
    └────────┬────────┘
             ↓
    ┌─────────────────┐
    │  Human Review   │  ← Compliance officer approves (high risk only)
    │   (interrupt)   │
    └────────┬────────┘
             ↓
         Filed / Cleared
```

### The Four Agents

**Fraud Detection Agent**
Analyzes transaction data to identify suspicious patterns: structuring (splitting amounts to stay under reporting thresholds), geographic anomalies, behavioral deviations from customer history. Outputs a risk score from 0.0 to 1.0.

**Case History Agent**
Searches a database of 30 historical SAR cases to find similar precedents. "This transaction pattern matches SAR-2024-0033 (88% similarity) — that case was filed and referred to police." Uses vector similarity search on past case summaries.

**Compliance Research Agent**
Retrieves the relevant regulatory requirements based on the transaction type and jurisdictions involved. "This requires filing under HKMA AML Guideline §35 within 3 business days, and cross-notifying FinCEN under §103.18."

**Report Generator Agent**
Combines all inputs and drafts a complete, regulator-ready SAR document in proper format. The draft includes: factual description, suspicious indicators, regulatory citations, evidence trail, and recommended action.

---

## Memory Architecture

The system uses five distinct memory layers, each serving a different purpose:

| Memory Type | Storage | What It Stores | Example Query |
|------------|---------|---------------|---------------|
| Short-term | LangGraph Thread State | Current analysis context | "What customer are we analyzing?" |
| Episodic | ChromaDB | Past SAR cases (30 records) | "Find cases similar to this pattern" |
| Semantic | ChromaDB | Regulatory text (40 provisions) | "Which HKMA rules apply here?" |
| Procedural | SQLite | SOP workflow rules | "What's the escalation threshold?" |
| User Preferences | SQLite | Compliance officer settings | "Does Wang prefer Chinese reports?" |

Each memory retrieval is logged with: what was queried, which memories were retrieved, similarity scores, which agent retrieved them, and what output was influenced. This log is the foundation for memory auditability.

---

## Five Test Scenarios

The system ships with five complete test scenarios covering the realistic range of cases a compliance team encounters:

**Scenario 01 — Normal Cross-border Transfer**
A corporate client wires HKD 150,000 to a Singapore subsidiary with proper documentation. Expected outcome: cleared, no SAR filed.

**Scenario 02 — Structuring (Main Demo)**
Client C-00412 (Sunrise Global Holdings Ltd, Cayman Islands) transfers HKD 490,000 from three accounts in Hong Kong, Singapore, and Cayman Islands within 3 minutes — each amount just below the HKD 500,000 automatic reporting threshold. Total: HKD 1,470,000. Expected outcome: risk score 0.93, SAR filed.

**Scenario 03 — High-risk KYC Anomaly**
A client with an expired KYC suddenly initiates a large transaction to a FATF high-risk country. Expected outcome: escalated to human review.

**Scenario 04 — Cross-border Chain**
A complex multi-hop transaction through four jurisdictions that individually look normal but form a suspicious pattern when analyzed together.

**Scenario 05 — False Positive**
A listed company's finance department sends quarterly payments to five subsidiary countries. Looks suspicious at first glance but has full documentation. Expected outcome: cleared. This scenario tests that the system does not over-flag.

---

## What Gets Logged

Every run of the system produces a structured audit trail:

```json
{
  "thread_id": "thread-20250315-88411",
  "scenario": "structuring",
  "execution_timeline": [
    { "t": "14:23:01", "agent": "supervisor", "action": "routed to fraud_detection + case_history" },
    { "t": "14:23:03", "agent": "fraud_detection", "action": "risk_score=0.93, pattern=structuring" },
    { "t": "14:23:04", "agent": "case_history", "action": "retrieved 3 similar cases" },
    { "t": "14:23:06", "agent": "supervisor", "action": "aggregated, requires_human_review=true" },
    { "t": "14:23:08", "agent": "compliance_research", "action": "found 2 applicable regulations" },
    { "t": "14:23:11", "agent": "report_generator", "action": "SAR draft generated" },
    { "t": "14:25:44", "agent": "human_review", "action": "approved by compliance officer Wang" }
  ],
  "memory_traces": [
    {
      "agent": "case_history",
      "memory_type": "episodic",
      "query": "multi-jurisdiction rapid transfer structuring pattern",
      "retrieved": [
        { "id": "SAR-2024-0033", "similarity": 0.88 },
        { "id": "SAR-2023-0171", "similarity": 0.82 },
        { "id": "SAR-2022-0089", "similarity": 0.71 }
      ]
    },
    {
      "agent": "compliance_research",
      "memory_type": "semantic",
      "query": "cross-border structuring HK SG reporting obligation",
      "retrieved": [
        { "id": "HKMA-AML-2023-§35", "similarity": 0.96 },
        { "id": "FINCEN-BSA-§103.18", "similarity": 0.91 }
      ]
    }
  ]
}
```

This log structure is the primary data source for memory observability tooling.

---

## Tech Stack

```
Agent Framework    LangGraph 0.2+
LLM                Anthropic Claude (claude-sonnet-4-6)
Vector Database    ChromaDB
Relational DB      SQLite
API                FastAPI
CLI                Typer + Rich
Mock Data          Faker
```

---

## Getting Started

```bash
# Clone and install
git clone https://github.com/your-org/fincompli-baseline
cd fincompli-baseline
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Initialize and seed data
python setup.py
python mock_data/seed_database.py

# Run the main demo scenario (structuring)
python cli/interactive.py --scenario 02

# Or start the API server
uvicorn api.server:app --reload
# Then POST to http://localhost:8000/api/analyze
```

---

## Project Structure

```
fincompli-baseline/
├── agents/           # Four specialist agents
├── graph/            # LangGraph state, builder, nodes
├── memory/           # Five memory layer implementations
├── tools/            # Mock enterprise tools (transaction DB, customer DB, etc.)
├── mock_data/        # Seed data generators and pre-generated datasets
├── scenarios/        # Five complete test scenarios
├── api/              # FastAPI server and routes
├── cli/              # Interactive terminal interface
└── data/             # Runtime data (ChromaDB, SQLite — gitignored)
```

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze` | POST | Submit a transaction for analysis |
| `/api/status/{thread_id}` | GET | Check current agent and status |
| `/api/human-decision/{thread_id}` | POST | Submit compliance officer decision |
| `/api/report/{thread_id}` | GET | Retrieve final SAR report |
| `/api/memory-traces/{thread_id}` | GET | Retrieve all memory access records |
| `/api/audit-log` | GET | Query the full audit event log |
| `/api/health` | GET | System health check |

---

## What This Is Not

This is a simulation. It uses realistic structure and real regulatory framework names, but the regulatory text is simplified for demonstration purposes. It is not a licensed compliance system and should not be used for actual regulatory filings.

---

## Why We Built This

Enterprise AI agent deployments are still largely invisible. Most public examples are chatbots or simple pipelines. This project exists to show what a real multi-agent system looks like when applied to a business-critical workflow — with proper memory architecture, human oversight, audit logging, and realistic test data.

We also built it as a testing ground for memory observability tooling. The `memory_traces` structure and `/api/memory-traces` endpoint are designed as clean integration points for tools that want to visualize or audit what an agent remembers and why it makes the decisions it makes.

---

## License

MIT

## Contributing

Issues and PRs welcome. See `CONTRIBUTING.md`.
