# MemGuard/MemoryLens Development Plan
## Staged Implementation Roadmap

**Project Overview**: Memory Observability and Governance Infrastructure for AI Agents  
**Product**: MemoryLens (4-tier: Debugging → Observability → Auditability → Governance)  
**Created**: 2026-07-01

---

## 📊 Current State Assessment

### ✅ What's Complete
1. **FinCompli Baseline** (Tasks 1-8) - Demo multi-agent system
   - Multi-agent financial compliance workflow (LangGraph)
   - Memory layer with 5 types (short-term, episodic, semantic, procedural, user prefs)
   - ChromaDB + SQLite backend
   - CLI interface and test scenarios
   - Mock data generation

2. **Basic Infrastructure**
   - SDK structure (core, adapters, transport)
   - Backend FastAPI structure
   - Frontend Next.js scaffolding
   - Technical design document

### 🚧 What's In Progress
- Git modifications in `fincompli-baseline/graph/builder.py` and `nodes.py`
- Basic backend implementation exists but incomplete

### ❌ What's Missing
1. **SDK**: Incomplete adapters, missing instrumentation
2. **Backend**: Missing Tier 2-4 features, analysis engine incomplete
3. **Frontend**: Only scaffolding, no actual UI components
4. **Integration**: FinCompli → MemGuard integration not connected
5. **Documentation**: API docs, integration guides incomplete

---

## 🎯 Development Strategy

### Overall Approach
**Build vertically through all tiers with the FinCompli baseline as the reference implementation**

The plan follows a "vertical slice" approach:
- Each stage delivers end-to-end value (SDK → Backend → Frontend → Integration)
- FinCompli baseline serves as the **dogfooding testbed** for each tier
- Start with Tier 1 (Debugging) and progressively build to Tier 4 (Governance)

---

## 📋 Stage 1: Foundation & Tier 1 (Memory Debugging)
**Duration**: 2-3 weeks  
**Goal**: Working MVP with basic memory tracing for engineers

### 1.1 Complete SDK Core (Week 1)

**Tasks**:
- [ ] Finalize `MemoryEvent` data model with all fields
- [ ] Implement `MemGuardInterceptor` base class
- [ ] Implement context manager for trace linking (`MemGuardTrace`)
- [ ] Complete all three transports:
  - [ ] `FileTransport` (JSONL append)
  - [ ] `HttpTransport` (async POST to backend)
  - [ ] `StdoutTransport` (debug logging)
- [ ] Add event batching and retry logic to HttpTransport

**Deliverables**:
- `sdk/memguard/core/event.py` - complete data models
- `sdk/memguard/core/interceptor.py` - base interceptor
- `sdk/memguard/transport/*` - all three transports working
- Unit tests for core SDK

### 1.2 Complete LangGraph Adapter (Week 1)

**Tasks**:
- [ ] Implement `MemGuardCheckpointer` wrapper
- [ ] Hook into LangGraph state reads/writes
- [ ] Capture before/after states for diffs
- [ ] Link memory events to LangGraph execution traces
- [ ] Add metadata extraction (thread_id, step_name, agent_id)

**Deliverables**:
- `sdk/memguard/adapters/langgraph.py` - production-ready
- Integration example with FinCompli baseline
- Test suite covering all checkpointer operations

### 1.3 Backend Event Ingestion & Storage (Week 1-2)

**Tasks**:
- [ ] Complete `/v1/events` ingestion endpoint
- [ ] Implement SQLite event store schema (from technical design)
- [ ] Add event validation and deduplication
- [ ] Implement basic timeline query API
- [ ] Add filtering by agent_id, session_id, operation type
- [ ] Create database indexes for performance

**Deliverables**:
- `backend/app/ingestion.py` - event ingestion service
- `backend/app/storage.py` - SQLite persistence layer
- `backend/app/api/events.py` - query endpoints
- Database migration scripts

### 1.4 Basic Memory Timeline API (Week 2)

**Tasks**:
- [ ] `GET /v1/sessions/{session_id}/timeline` - chronological events
- [ ] `GET /v1/memory/{memory_key}/lineage` - evolution of one memory
- [ ] `GET /v1/agents/{agent_id}/memory-state` - current snapshot
- [ ] Add pagination and time-range filtering
- [ ] Return memory influence metadata

**Deliverables**:
- REST API endpoints documented in OpenAPI/Swagger
- Postman collection for testing

### 1.5 Frontend: Memory Timeline View (Week 2-3)

**Tasks**:
- [ ] Design timeline component (horizontal time axis)
- [ ] Visualize events as colored dots (CREATE=green, READ=blue, UPDATE=yellow, DELETE=red)
- [ ] Implement event detail modal (click to inspect)
- [ ] Add filtering controls (agent, operation type, time range)
- [ ] Show before/after diff for UPDATE events
- [ ] Add session selector

**Tech Stack**:
- React + TypeScript
- D3.js for timeline visualization
- Tailwind CSS for styling
- SWR for data fetching

**Deliverables**:
- `frontend/components/MemoryTimeline.tsx`
- `frontend/components/EventDetailModal.tsx`
- `frontend/app/timeline/[sessionId]/page.tsx`

### 1.6 Integration: FinCompli → MemGuard (Week 3)

**Tasks**:
- [ ] Wrap FinCompli checkpointer with MemGuardCheckpointer
- [ ] Instrument all memory layer calls (episodic, semantic, procedural)
- [ ] Add trace_id linking between LLM calls and memory ops
- [ ] Configure HttpTransport to backend
- [ ] Run complete SAR scenario with memory tracing

**Deliverables**:
- Modified `fincompli-baseline/graph/builder.py` with MemGuard integration
- Example run showing complete memory trace
- Documentation: "Integrating MemGuard with LangGraph"

### 1.7 Stage 1 Testing & Documentation (Week 3)

**Tasks**:
- [ ] End-to-end test: FinCompli run → events in backend → visible in dashboard
- [ ] Performance test: measure overhead (target: <5ms per event)
- [ ] Write integration guide
- [ ] Create demo video

**Success Criteria**:
- ✅ Run FinCompli scenario 02 (structuring case)
- ✅ All memory operations visible in timeline
- ✅ Can click any event and see before/after state
- ✅ Can trace lineage of any memory key
- ✅ Backend handles 1000+ events/second

---

## 📋 Stage 2: Tier 2 (Memory Observability)
**Duration**: 2-3 weeks  
**Goal**: Operational monitoring of memory system health

### 2.1 Memory Health Metrics (Week 4)

**Tasks**:
- [ ] Implement metrics aggregation service
- [ ] Track retrieval quality (similarity score distributions)
- [ ] Memory access frequency heatmaps
- [ ] Stale memory detection (unused for N days)
- [ ] Cross-agent memory flow tracking
- [ ] Anomaly detection (unusual access patterns)

**Deliverables**:
- `backend/app/analysis/metrics.py`
- `GET /v1/agents/{agent_id}/stats` endpoint
- `GET /v1/memory/observability/{tenant}/{agent}` dashboard API

### 2.2 Memory Access Heatmap (Week 4)

**Tasks**:
- [ ] Aggregate READ events by memory_key
- [ ] Calculate access frequency and recency
- [ ] Identify hot vs cold memories
- [ ] Flag memories never retrieved

**Deliverables**:
- `GET /v1/memory/heatmap` API
- SQL queries for efficient aggregation

### 2.3 Cross-Agent Memory Flow Analysis (Week 5)

**Tasks**:
- [ ] Track memory writes by agent A → reads by agent B
- [ ] Build memory flow graph (agent → memory → agent)
- [ ] Detect memory sharing patterns
- [ ] Calculate memory influence across agents

**Deliverables**:
- `backend/app/analysis/flow.py`
- `GET /v1/analysis/memory-flow` API

### 2.4 Drift Detection (Week 5)

**Tasks**:
- [ ] Track memory updates over time
- [ ] Compare before/after content hashes
- [ ] Measure drift magnitude
- [ ] Trace propagation of updates through system

**Deliverables**:
- `backend/app/analysis/drift.py`
- `GET /v1/memory/{id}/drift-history` API

### 2.5 Frontend: Observability Dashboard (Week 5-6)

**Tasks**:
- [ ] Agent health overview page
- [ ] Memory access heatmap visualization
- [ ] Stale memory list with recommendations
- [ ] Cross-agent flow diagram (React Flow)
- [ ] Anomaly alerts feed
- [ ] Time-series charts (Recharts)

**Deliverables**:
- `frontend/app/observability/page.tsx`
- `frontend/components/MemoryHeatmap.tsx`
- `frontend/components/AgentFlowDiagram.tsx`

### 2.6 Alerting System (Week 6)

**Tasks**:
- [ ] Define alert rules (stale memory, anomaly threshold, conflict detected)
- [ ] Implement alert evaluation engine
- [ ] Store alerts in database
- [ ] Add webhook notifications (Slack, email)
- [ ] Frontend alert center

**Deliverables**:
- `backend/app/alerts/engine.py`
- `POST /v1/alerts/webhook` configuration API
- Alert notification templates

---

## 📋 Stage 3: Tier 3 (Memory Auditability)
**Duration**: 3-4 weeks  
**Goal**: Human-readable audit trails for compliance officers

### 3.1 Decision Trace Linking (Week 7)

**Tasks**:
- [ ] Complete `DecisionTrace` data model
- [ ] Link memory READ events → LLM call → memory WRITE events
- [ ] Calculate memory influence scores
- [ ] Store decision traces in database

**Deliverables**:
- `backend/app/models/decision_trace.py`
- `POST /v1/trace` - create decision trace
- `GET /v1/trace/{trace_id}` - retrieve trace

### 3.2 Memory Influence Scoring (Week 7)

**Tasks**:
- [ ] Implement influence score algorithm
- [ ] Weight by memory type (semantic > procedural > episodic)
- [ ] Weight by recency
- [ ] Weight by similarity score (for vector retrievals)
- [ ] Aggregate influence across multiple memories

**Deliverables**:
- `backend/app/analysis/influence.py`
- Influence scores in decision traces

### 3.3 Natural Language Audit Report Generator (Week 8-9)

**Core Feature of Tier 3**

**Tasks**:
- [ ] Design audit report template structure
- [ ] Implement LLM-based narrative generator
- [ ] Input: Decision trace + memory events
- [ ] Output: Plain English explanation
- [ ] Include:
  - Summary of decision
  - Memory sources used (with citations)
  - Influence percentages
  - Memory integrity verification
  - What the agent did NOT use (and why)
- [ ] Support bilingual output (English + Chinese)

**Deliverables**:
- `backend/app/audit/report_generator.py`
- `POST /v1/audit/generate-report` API
- Report templates for different decision types
- Example report for FinCompli SAR recommendation

### 3.4 Regulatory Framework Mappings (Week 9)

**Tasks**:
- [ ] Define framework schema (EU AI Act, HKMA, MAS, FCA, NIST)
- [ ] Map audit report sections to regulatory requirements
- [ ] Add framework-specific export formats
- [ ] Include regulatory citation tracking

**Deliverables**:
- `backend/app/compliance/frameworks.py`
- Framework templates
- Export formatters (PDF, JSON, CSV)

### 3.5 Memory Integrity Verification (Week 9-10)

**Tasks**:
- [ ] Implement content hash verification
- [ ] Track memory modification history
- [ ] Detect unauthorized changes
- [ ] Flag tampering attempts
- [ ] Verification status in audit reports

**Deliverables**:
- `backend/app/security/integrity.py`
- `GET /v1/memory/{id}/verify-integrity` API

### 3.6 Frontend: Audit Report Viewer (Week 10)

**Tasks**:
- [ ] Audit report list page
- [ ] Report detail view (structured, human-readable)
- [ ] PDF export functionality
- [ ] Regulatory framework selector
- [ ] Citation links to source memories
- [ ] Print-friendly layout

**Deliverables**:
- `frontend/app/audit/reports/page.tsx`
- `frontend/components/AuditReport.tsx`
- PDF generation service

### 3.7 FinCompli Integration: SAR Audit Report (Week 10)

**Tasks**:
- [ ] Generate audit report for Scenario 02 SAR recommendation
- [ ] Show which case histories influenced decision
- [ ] Show which regulations were cited
- [ ] Demonstrate integrity verification
- [ ] Export as PDF for compliance review

**Deliverables**:
- Example audit report document
- Integration documentation
- Demo video for compliance officers

---

## 📋 Stage 4: Tier 4 (Memory Governance)
**Duration**: 4-5 weeks  
**Goal**: Enterprise-grade security, access control, and policy enforcement

### 4.1 Access Control Policy Engine (Week 11-12)

**Tasks**:
- [ ] Define policy schema (who can access what, when)
- [ ] Implement policy evaluation engine
- [ ] Policy types:
  - Agent-based (agent X can only read memory type Y)
  - Context-based (only within same session/user)
  - Time-based (regulatory memory older than N months flagged)
  - Risk-based (high-risk data requires supervisor approval)
- [ ] Policy enforcement at read/write time
- [ ] Audit log for policy violations

**Deliverables**:
- `backend/app/governance/policy_engine.py`
- `POST /v1/policies` - create policy
- `GET /v1/policies` - list policies
- `DELETE /v1/policies/{id}` - delete policy
- Policy enforcement middleware

### 4.2 Memory Contamination Detection (Week 12-13)

**Prompt Injection Defense**

**Tasks**:
- [ ] Implement write-time content scanner
- [ ] Detection patterns:
  - Instruction-like language in factual memory
  - System prompt override attempts
  - Anomalous specificity about agent behavior
  - Known injection signatures
- [ ] Quarantine suspicious writes
- [ ] Alert on contamination attempts
- [ ] Review queue for quarantined memories

**Deliverables**:
- `backend/app/security/contamination.py`
- Quarantine database table
- `GET /v1/security/quarantine` API
- `POST /v1/security/quarantine/{id}/review` - approve/reject

### 4.3 Memory Lifecycle Management (Week 13)

**Tasks**:
- [ ] Define retention policies by memory type
- [ ] Implement auto-purge for expired memories
- [ ] Versioning and immutable snapshots
- [ ] Provenance chain tracking
- [ ] Regulatory compliance (7-year retention for financial)

**Deliverables**:
- `backend/app/governance/lifecycle.py`
- `POST /v1/governance/retention-policy` API
- Scheduled cleanup jobs

### 4.4 Governance Dashboard (Week 14)

**Board-Level View**

**Tasks**:
- [ ] Executive summary metrics:
  - Total memory operations over period
  - Access policy violations
  - Contamination attempts blocked
  - Memory integrity check status
  - % of outputs with complete audit trails
- [ ] Trend charts
- [ ] Risk indicators
- [ ] Compliance posture score

**Deliverables**:
- `frontend/app/governance/page.tsx`
- Executive dashboard components
- Export to PowerPoint/PDF for board meetings

### 4.5 Regulatory Reporting Package (Week 14-15)

**Tasks**:
- [ ] Structure export for regulatory submission
- [ ] Pre-formatted for:
  - HKMA Supervisory Policy Manual
  - MAS Notice 626
  - FCA CP23/32
  - EU AI Act Article 13/14
  - NIST AI RMF
  - SEC AI disclosure
- [ ] Include:
  - Memory governance framework documentation
  - Policy coverage reports
  - Exception reports
  - Sample audit trails
- [ ] ZIP package generator

**Deliverables**:
- `backend/app/compliance/regulatory_export.py`
- Export templates for each framework
- `POST /v1/compliance/export` API

### 4.6 Multi-Tenant Architecture (Week 15)

**Tasks**:
- [ ] Implement tenant isolation (namespace-based)
- [ ] Tenant-specific databases or row-level security
- [ ] Tenant admin roles and permissions
- [ ] Tenant-specific policy management
- [ ] Billing and usage tracking per tenant

**Deliverables**:
- Tenant management service
- `POST /v1/tenants` - create tenant
- `GET /v1/tenants/{id}/usage` - usage metrics
- Updated database schema with tenant_id everywhere

---

## 📋 Stage 5: Production Readiness & Scale
**Duration**: 3-4 weeks  
**Goal**: Deploy-ready system with enterprise features

### 5.1 PostgreSQL + TimescaleDB Migration (Week 16)

**Tasks**:
- [ ] Design PostgreSQL schema (from technical design)
- [ ] Implement TimescaleDB hypertables for events
- [ ] Migration script from SQLite
- [ ] Update all backend services to use PostgreSQL
- [ ] Performance testing and index optimization

**Deliverables**:
- PostgreSQL database schema
- Migration scripts
- Updated `backend/app/storage/postgres.py`

### 5.2 Additional Framework Adapters (Week 16-17)

**Tasks**:
- [ ] Mem0 adapter (wraps Memory class)
- [ ] AutoGen adapter (intercepts message processing)
- [ ] CrewAI adapter (hook into memory methods)
- [ ] Generic adapter for custom memory backends

**Deliverables**:
- `sdk/memguard/adapters/mem0.py`
- `sdk/memguard/adapters/autogen.py`
- `sdk/memguard/adapters/crewai.py`
- `sdk/memguard/adapters/generic.py`
- Integration examples for each

### 5.3 Performance Optimization (Week 17)

**Tasks**:
- [ ] Event batching in SDK (reduce HTTP calls)
- [ ] Database query optimization
- [ ] Redis cache for hot data
- [ ] Async processing for heavy operations (report generation)
- [ ] Load testing (target: 100K events/day)

**Deliverables**:
- Performance benchmark report
- Optimized backend services
- Redis integration

### 5.4 Security Hardening (Week 18)

**Tasks**:
- [ ] API key authentication
- [ ] Rate limiting
- [ ] Input validation and sanitization
- [ ] Encryption at rest for sensitive data
- [ ] HTTPS enforcement
- [ ] Security audit and penetration testing

**Deliverables**:
- Auth middleware
- Security documentation
- Penetration test report

### 5.5 Deployment & DevOps (Week 18-19)

**Tasks**:
- [ ] Docker Compose for local development
- [ ] Kubernetes manifests for production
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Monitoring and logging (Prometheus, Grafana)
- [ ] Backup and disaster recovery
- [ ] Environment-specific configs (dev, staging, prod)

**Deliverables**:
- `docker-compose.yml`
- `k8s/` directory with manifests
- `.github/workflows/` CI/CD configs
- Deployment guide

### 5.6 Documentation & Developer Experience (Week 19)

**Tasks**:
- [ ] Complete API reference (OpenAPI/Swagger)
- [ ] SDK documentation (docstrings + Sphinx)
- [ ] Integration guides for each framework
- [ ] Quick start tutorial
- [ ] Video tutorials
- [ ] FAQ and troubleshooting guide
- [ ] Architecture deep-dive docs

**Deliverables**:
- `docs/` directory with complete documentation
- Interactive API docs at `/docs` endpoint
- SDK reference site
- YouTube tutorial series

---

## 📋 Stage 6: Go-to-Market & Beta
**Duration**: Ongoing
**Goal**: Launch private beta and gather feedback

### 6.1 Beta Partner Onboarding

**Tasks**:
- [ ] Identify 5-10 beta partners (financial services, healthcare)
- [ ] Provide white-glove onboarding
- [ ] Gather feedback and iterate
- [ ] Case studies and testimonials

### 6.2 Pricing Model Implementation

**Tasks**:
- [ ] Define pricing tiers (Debugging, Observability, Enterprise, Governance)
- [ ] Usage-based billing (events per month)
- [ ] Implement billing integration (Stripe)
- [ ] Trial period management

### 6.3 Marketing Assets

**Tasks**:
- [ ] Product landing page
- [ ] Demo videos for each tier
- [ ] White papers on memory observability
- [ ] Blog posts on use cases
- [ ] Conference presentations

---

## 🎯 Success Metrics by Stage

### Stage 1 (Tier 1 - Debugging)
- ✅ 3+ external developers successfully integrate
- ✅ <5ms overhead per memory operation
- ✅ 100% of memory ops captured in timeline

### Stage 2 (Tier 2 - Observability)
- ✅ Detect 95%+ of stale memories
- ✅ Memory health dashboard used by 10+ platform engineers
- ✅ 5+ actionable anomaly alerts per week

### Stage 3 (Tier 3 - Auditability)
- ✅ Generate audit report for any agent decision in <5 seconds
- ✅ 3+ compliance officers review and approve reports
- ✅ Export to 3+ regulatory frameworks

### Stage 4 (Tier 4 - Governance)
- ✅ Block 100% of access policy violations
- ✅ Detect and quarantine 90%+ of prompt injection attempts
- ✅ Board-level dashboard adopted by 2+ enterprises

### Stage 5 (Production)
- ✅ Handle 100K+ events/day
- ✅ 99.9% uptime SLA
- ✅ <100ms p95 API latency

### Stage 6 (GTM)
- ✅ 10+ beta partners
- ✅ 3+ paid customers
- ✅ $10K+ MRR

---

## 🛠️ Technology Stack Summary

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL + TimescaleDB (SQLite for MVP)
- **Cache**: Redis
- **LLM**: OpenAI API / Local model for report generation
- **Search**: PostgreSQL full-text search (pgvector for semantic)

### Frontend
- **Framework**: Next.js 14 + React 18
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Charts**: D3.js, Recharts, React Flow
- **State**: Zustand
- **Data Fetching**: SWR

### SDK
- **Language**: Python 3.9+
- **Async**: asyncio
- **HTTP**: httpx
- **Serialization**: Pydantic

### DevOps
- **Container**: Docker
- **Orchestration**: Kubernetes
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack

---

## 📅 Timeline Overview

```
Week 1-3   │ Stage 1: Tier 1 (Memory Debugging) MVP
Week 4-6   │ Stage 2: Tier 2 (Memory Observability)
Week 7-10  │ Stage 3: Tier 3 (Memory Auditability)
Week 11-15 │ Stage 4: Tier 4 (Memory Governance)
Week 16-19 │ Stage 5: Production Readiness
Week 20+   │ Stage 6: Beta Launch & GTM
```

**Total MVP to Beta**: ~20 weeks (5 months)

---

## 🚀 Next Immediate Actions

### This Week (Week 1 - Days 1-3)
1. ✅ Review and approve this development plan
2. [ ] Set up project management (GitHub Projects / Linear / Jira)
3. [ ] Create milestone issues for Stage 1
4. [ ] Complete SDK core implementation
5. [ ] Start LangGraph adapter development

### This Week (Days 4-7)
6. [ ] Backend event ingestion API
7. [ ] SQLite schema and storage layer
8. [ ] Basic timeline query API
9. [ ] First integration test: FinCompli → MemGuard

---

## 📝 Open Questions & Decisions Needed

1. **Content Storage Strategy**
   - [ ] Decision: Hash only by default, or store raw content?
   - Recommendation: Hash only (privacy-first), opt-in for raw

2. **Deployment Model for Beta**
   - [ ] Decision: Cloud SaaS, on-premise, or both?
   - Recommendation: Start with cloud SaaS, add on-premise for enterprise

3. **Open Source Strategy**
   - [ ] Decision: Fully open source, open-core, or closed?
   - Recommendation: Open-core (SDK + Tier 1 open, Tier 2-4 commercial)

4. **LLM for Audit Reports**
   - [ ] Decision: OpenAI API, local model, or both?
   - Recommendation: OpenAI API for SaaS, local model option for on-premise

5. **Pricing Model**
   - [ ] Decision: Per-event, per-agent, or tiered subscription?
   - Recommendation: Hybrid (base tier + usage-based for events >100K/month)

---

## 📚 References

- [Product Document](./Documents/02_memorylens_product_document.md)
- [Technical Design](./Documents/MemGuard_Technical_Design.md)
- [FinCompli Baseline](./fincompli-baseline/README.md)
- [Project README](./README.md)

---

**Document Owner**: Development Team  
**Last Updated**: 2026-07-01  
**Status**: Draft - Awaiting Approval
