# Agent Memory Visualization MVP and Pip SDK Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a demo-ready MVP that lets a developer install MemGuard with `pip`, record the memories retrieved for an agent response, and inspect a truthful visual explanation of why an incorrect response—such as saying the user is in Taipei when the current input says New York—was produced.

**Architecture:** Keep the existing SDK → HTTP ingestion → persisted event/trace → Next.js dashboard pipeline. Add a small public SDK facade, an explicit retrieval/output evidence contract, deterministic server-side explanation rules, and an output-first explanation panel. Store MVP provenance fields in the existing event and trace metadata JSON so this iteration does not require a database migration.

**Tech Stack:** Python 3.9+, dataclasses, standard-library HTTP transport, FastAPI, Pydantic 2, SQLite/Postgres-compatible persistence, Next.js 15, React 19, TypeScript, pytest, GitHub Actions, PyPI trusted publishing.

## Global Constraints

- Preserve tenant isolation on every `/v1/*` endpoint.
- Never describe recorded lineage as proof that a model internally relied on a memory.
- Label direct telemetry as **Observed** and deterministic comparisons as **Inferred**.
- Never fabricate an evidence item when a linked event is missing.
- Default SDK behavior remains privacy-first: raw memory content is omitted unless `capture_content=True`.
- Hash-only mode must still emit a stable, non-empty content hash.
- The golden demo must be deterministic and must not require an external LLM API key.
- The first-run path must work from a clean virtual environment with `pip install memguard`.
- Preserve backward compatibility for `MemGuardInterceptor.record()` and `trace_decision()` during the MVP.
- Do not expand this iteration into policy enforcement, prompt injection defense, automated memory correction, multi-framework parity, or causal attribution research.

---

## 1. Product Outcome

The MVP should answer one user question exceptionally well:

> “Why did this agent output Taipei when I just told it I am in New York?”

The dashboard answer must be based on a recorded chain:

```text
Current input: “I am currently in New York.”
        ↓
Observed retrieval: profile:current_location = “Taipei”
        ↓
Observed prompt inclusion: included_in_prompt = true
        ↓
Agent output: “You are currently in Taipei.”
        ↓
Inferred finding: retrieved memory conflicts with the current fact
```

The UI must also show:

- where the Taipei memory came from;
- when it was created and last verified;
- its retrieval rank and score, when supplied;
- whether it was actually included in the model context;
- which current fact conflicts with it;
- whether the record exceeded its declared freshness limit;
- whether any linked evidence is missing;
- the disclaimer that lineage is not proof of model causality.

This is the saleable wedge: MemGuard turns an agent's opaque memory behavior into inspectable evidence that a developer can use to debug a wrong answer.

## 2. Current-State Assessment

### What already works and should be retained

- `MemoryEvent` records memory operations, content hashes, context, tags, and upstream IDs.
- `DecisionTrace` links input event IDs, model output, and resulting memory writes.
- `HttpTransport` queues, batches, retries, and flushes SDK records.
- The backend persists SDK events and decision traces.
- The trace query resolves only persisted event IDs into `evidence_items` and explicitly returns `missing_evidence_event_ids`.
- The dashboard is already organized around selecting an output and inspecting its evidence lineage.
- The dashboard already includes the correct “not proof of model causality” disclaimer.
- A deterministic trace demo and contract tests already exist.

### Gaps blocking the MVP

1. `record()` removes raw content before `MemoryEvent` can hash it, so hash-only events can have an empty `content_hash`.
2. The SDK has no simple public method named around the user's intent: “record a retrieval” and “record an output.”
3. `DecisionTrace` does not explicitly carry `user_input` or `model`; the API substitutes placeholder values.
4. Provenance fields are generic, undocumented `context` keys rather than a stable visualization contract.
5. The API returns evidence records but does not return a deterministic explanation object.
6. The UI shows evidence lineage but does not clearly explain the New York/Taipei conflict.
7. Delivery failures are logged and swallowed, so a demo can print a trace ID even when evidence is incomplete.
8. The package metadata contains placeholder repository URLs, excludes some packages through a hard-coded package list, references a missing `py.typed`, and has no CLI.
9. The current demo requires running a repository script rather than proving that an installed package is enough.
10. The repository tracks local virtual-environment files, which makes packaging and release validation noisy and fragile.

## 3. MVP Scope and Non-Goals

### Included

- One event per retrieved memory that was available to the generation step.
- An explicit flag recording whether the retrieved memory was included in the prompt/context.
- An explicit current-facts map attached to the output trace.
- Deterministic conflict, staleness, combined stale-conflict, observed, and evidence-gap findings.
- An output-first “Why this output?” panel.
- A deterministic New York/Taipei golden demo.
- A public `MemGuard` Python facade and `memguard` CLI.
- Clean-wheel validation and an automated PyPI release workflow.

### Excluded from this MVP

- Token-level attribution, attention inspection, or claims about model internals.
- Automatic mutation or deletion of a customer's memory.
- A general-purpose memory database.
- Billing, subscriptions, organization administration, or a hosted onboarding wizard.
- Complete LangGraph semantic/vector store interception.
- CrewAI, AutoGen, or JavaScript SDK support.
- An LLM-generated explanation; deterministic rules are easier to test and defend in a demo.

## 4. Evidence Contract

### 4.1 Retrieval event

Record each memory selected by the application as a `MemoryOp.READ` event. The retrieved value is the event's `after_value` only when content capture is enabled. The following keys live in `MemoryEvent.context` and are persisted in `metadata_json`:

```python
{
    "evidence_role": "retrieved_memory",
    "source_type": "conversation",
    "source_id": "trip-message-2026-07-01",
    "memory_created_at": "2026-07-01T09:00:00+00:00",
    "memory_last_verified_at": "2026-07-01T09:00:00+00:00",
    "retrieval_query": "Where is the user currently located?",
    "retrieval_score": 0.93,
    "retrieval_rank": 1,
    "included_in_prompt": True,
    "fact_key": "current_location",
    "max_age_seconds": 86400,
}
```

Field semantics:

| Field | Required | Meaning |
|---|---:|---|
| `evidence_role` | Yes | Always `retrieved_memory` for this helper. |
| `source_type` | Yes | Developer-supplied origin category such as `conversation`, `profile`, or `tool`. |
| `source_id` | No | Identifier in the developer's system. |
| `memory_created_at` | No | ISO-8601 creation timestamp from the source system. |
| `memory_last_verified_at` | No | ISO-8601 time when the fact was last confirmed. |
| `retrieval_query` | No | Query that produced this result. |
| `retrieval_score` | No | Backend/vector-store relevance score, passed through without reinterpretation. |
| `retrieval_rank` | No | One-based order returned to the agent application. |
| `included_in_prompt` | Yes | Whether the application actually included this record in model context. |
| `fact_key` | No | Key used to compare memory content with `current_facts`. |
| `max_age_seconds` | No | Developer-defined freshness limit for this fact. |

### 4.2 Output trace

Add explicit fields to the SDK `DecisionTrace`:

```python
user_input: str = ""
model: str = ""
```

Use the existing `context` field for this stable MVP trace metadata:

```python
{
    "current_facts": {"current_location": "New York"},
    "evidence_model": "recorded_lineage",
    "causality_claim": "not_proven",
}
```

### 4.3 Explanation response

The backend adds this object to every trace response:

```json
{
  "explanation": {
    "basis": "recorded_evidence",
    "causality_claim": "not_proven",
    "status": "stale_conflict",
    "summary": "The output repeated a retrieved Taipei memory that conflicted with the current New York fact and was older than its freshness limit.",
    "findings": [
      {
        "kind": "stale_conflict",
        "event_id": "retrieval-event-id",
        "memory_key": "profile:current_location",
        "fact_key": "current_location",
        "remembered_value": "Taipei",
        "current_value": "New York",
        "source_type": "conversation",
        "source_id": "trip-message-2026-07-01",
        "retrieval_rank": 1,
        "retrieval_score": 0.93,
        "included_in_prompt": true,
        "memory_created_at": "2026-07-01T09:00:00+00:00",
        "memory_last_verified_at": "2026-07-01T09:00:00+00:00",
        "max_age_seconds": 86400,
        "age_seconds": 2678400
      }
    ]
  }
}
```

Allowed top-level statuses are `observed`, `stale`, `conflict`, `stale_conflict`, and `evidence_gap`. If multiple findings exist, use this severity order:

```text
evidence_gap > stale_conflict > conflict > stale > observed
```

The explanation engine compares values only when all of these exist:

- `trace.metadata.current_facts[fact_key]`;
- evidence metadata `_after_value[fact_key]`;
- evidence metadata `fact_key`.

Absence of raw captured content is not an error. It means MemGuard can show provenance and a hash but cannot infer a value conflict.

---

## 5. Implementation Tasks

### Execution preflight

Run this once before Task 1 so every Python command below uses the same isolated environment rather than either tracked `myenv` directory:

```bash
python3 -m venv .venv-mvp
.venv-mvp/bin/python -m pip install --upgrade pip
.venv-mvp/bin/python -m pip install -e "sdk[dev]"
.venv-mvp/bin/python -m pip install -r backend/requirements.txt
```

Record the baseline before changing code:

```bash
git status --short
.venv-mvp/bin/python -m pytest -q
cd frontend && npm run build
```

If a baseline check fails, save the exact failure output and distinguish it from regressions introduced by the task. Do not modify unrelated user-owned changes while executing this plan.

### Task 1: Correct privacy-safe hashing and extend the SDK trace contract

**Files:**

- Modify: `sdk/memguard/core/event.py`
- Modify: `sdk/memguard/core/interceptor.py`
- Create: `tests/test_sdk_event_contract.py`

**Public behavior:**

- Equal dictionaries produce the same hash regardless of insertion order.
- Hash-only mode emits no raw values and emits a non-empty hash.
- Content-capture mode emits raw values and the same hash.
- `DecisionTrace` serializes `user_input` and `model`.

- [ ] Create a failing test for canonical hashes and interceptor redaction:

```python
import threading

from memguard.core.event import DecisionTrace
from memguard.core.interceptor import MemGuardInterceptor
from memguard.core.event import MemoryOp


class CaptureTransport:
    def __init__(self):
        self.event = None
        self.ready = threading.Event()

    def _emit_sync(self, event):
        self.event = event
        self.ready.set()


def test_hash_only_record_keeps_hash_but_removes_content():
    transport = CaptureTransport()
    guard = MemGuardInterceptor("agent", transport=transport, capture_content=False)
    guard.record(MemoryOp.READ, "profile:location", after_value={"city": "Taipei"})
    assert transport.ready.wait(1)
    assert transport.event.after_value is None
    assert transport.event.content_hash


def test_canonical_hash_ignores_mapping_insertion_order():
    first = MemGuardInterceptor._hash_content({"city": "Taipei", "country": "Taiwan"})
    second = MemGuardInterceptor._hash_content({"country": "Taiwan", "city": "Taipei"})
    assert first == second


def test_decision_trace_has_display_fields():
    trace = DecisionTrace(user_input="I am in New York", model="demo-model")
    assert trace.user_input == "I am in New York"
    assert trace.model == "demo-model"
```

- [ ] Run the test and confirm the new assertions fail before implementation:

```bash
.venv-mvp/bin/python -m pytest tests/test_sdk_event_contract.py -q
```

Expected result: failures for missing `_hash_content`, empty hash-only content hashes, and unsupported trace fields.

- [ ] Add a canonical helper to `MemGuardInterceptor`:

```python
@staticmethod
def _hash_content(value: dict[str, Any] | None) -> str:
    if value is None:
        return ""
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
```

- [ ] In `record()`, compute `content_hash` from `after_value` when it is not `None`, otherwise from `before_value`, before redacting either value.
- [ ] Pass the computed hash into `MemoryEvent(content_hash=...)` while preserving `capture_content` behavior.
- [ ] Update `MemoryEvent.__post_init__` to use the same canonical hash helper or move the helper to `event.py` and import it from the interceptor. Keep only one hashing implementation.
- [ ] Add `user_input` and `model` to `DecisionTrace` immediately before the hash/output fields so `dataclasses.asdict()` includes them.
- [ ] Extend `trace_decision()` with backward-compatible keyword arguments `user_input: str = ""` and `model: str = ""`.
- [ ] Run the focused tests:

```bash
.venv-mvp/bin/python -m pytest tests/test_sdk_event_contract.py -q
```

Expected result: all tests pass.

- [ ] Run the existing SDK and phase contract tests:

```bash
.venv-mvp/bin/python -m pytest tests/test_phase1a_contract.py tests/test_solo_validation_gate.py -q
```

- [ ] Commit:

```bash
git add sdk/memguard/core/event.py sdk/memguard/core/interceptor.py tests/test_sdk_event_contract.py
git commit -m "fix: preserve privacy-safe memory hashes"
```

### Task 2: Add intent-level SDK APIs and a public `MemGuard` facade

**Files:**

- Create: `sdk/memguard/client.py`
- Modify: `sdk/memguard/core/interceptor.py`
- Modify: `sdk/memguard/__init__.py`
- Create: `tests/test_sdk_client.py`

**Required public interface:**

```python
class MemGuard:
    def __init__(
        self,
        api_url: str,
        api_key: str,
        agent_id: str,
        namespace: str = "default",
        capture_content: bool = False,
    ) -> None: ...

    def set_session(self, session_id: str) -> None: ...
    def record_retrieval(...) -> str: ...
    def record_output(...) -> DecisionTrace: ...
    def flush(self, timeout: float = 5.0) -> bool: ...
    def delivery_status(self) -> TransportStats: ...
```

The interceptor methods must have these signatures:

```python
def record_retrieval(
    self,
    memory_key: str,
    value: dict[str, Any],
    *,
    memory_type: MemoryType = MemoryType.SEMANTIC,
    source_type: str,
    source_id: Optional[str] = None,
    memory_created_at: Optional[str] = None,
    memory_last_verified_at: Optional[str] = None,
    retrieval_query: str = "",
    retrieval_score: Optional[float] = None,
    retrieval_rank: Optional[int] = None,
    included_in_prompt: bool = True,
    fact_key: Optional[str] = None,
    max_age_seconds: Optional[int] = None,
) -> str: ...

def record_output(
    self,
    *,
    user_input: str,
    output_text: str,
    input_event_ids: list[str],
    output_event_ids: Optional[list[str]] = None,
    model: str = "",
    current_facts: Optional[dict[str, Any]] = None,
) -> DecisionTrace: ...
```

- [ ] Write failing unit tests using a synchronous capture transport. Verify:

```python
event_id = interceptor.record_retrieval(
    "profile:current_location",
    {"current_location": "Taipei"},
    source_type="conversation",
    source_id="trip-message-2026-07-01",
    retrieval_query="Where is the user?",
    retrieval_score=0.93,
    retrieval_rank=1,
    included_in_prompt=True,
    fact_key="current_location",
    max_age_seconds=86400,
)
trace = interceptor.record_output(
    user_input="I am currently in New York.",
    output_text="You are currently in Taipei.",
    input_event_ids=[event_id],
    model="deterministic-demo",
    current_facts={"current_location": "New York"},
)
```

Assert that the retrieval event has `operation == MemoryOp.READ`, every specified metadata key, and `evidence_role == "retrieved_memory"`. Assert that the trace has explicit `user_input`, `model`, empty output IDs by default, `evidence_model == "recorded_lineage"`, and `causality_claim == "not_proven"`.

- [ ] Run the focused test and confirm it fails because these APIs do not exist:

```bash
.venv-mvp/bin/python -m pytest tests/test_sdk_client.py -q
```

- [ ] Implement `MemGuardInterceptor.record_retrieval()` as a thin validated wrapper around `record()`.
- [ ] Reject `retrieval_rank < 1`, scores outside `0.0..1.0`, and negative `max_age_seconds` with `ValueError` before emitting an event.
- [ ] Implement `MemGuardInterceptor.record_output()` as a thin wrapper around `trace_decision()`.
- [ ] Set the three trace context keys exactly: `current_facts`, `evidence_model`, and `causality_claim`.
- [ ] Implement `MemGuard` by constructing one `HttpTransport` and one `MemGuardInterceptor`, then delegating the public calls.
- [ ] Export `MemGuard`, `MemoryType`, `MemoryOp`, `MemoryEvent`, and `DecisionTrace` from `sdk/memguard/__init__.py`.
- [ ] Keep the lower-level interceptor public for adapter authors.
- [ ] Run tests:

```bash
.venv-mvp/bin/python -m pytest tests/test_sdk_client.py tests/test_sdk_event_contract.py -q
```

- [ ] Commit:

```bash
git add sdk/memguard/client.py sdk/memguard/core/interceptor.py sdk/memguard/__init__.py tests/test_sdk_client.py
git commit -m "feat: add memory visualization SDK facade"
```

### Task 3: Make evidence delivery completeness observable

**Files:**

- Modify: `sdk/memguard/transport/http.py`
- Modify: `sdk/memguard/client.py`
- Create: `tests/test_http_transport_status.py`

**Required type:**

```python
@dataclass(frozen=True)
class TransportStats:
    queued: int
    delivered: int
    dropped: int
    failed: int
    pending: int

    @property
    def evidence_complete(self) -> bool:
        return self.pending == 0 and self.dropped == 0 and self.failed == 0
```

Counters are record counts, not request counts. A successful batch of five events increments `delivered` by five.

- [ ] Write failing tests that monkeypatch `_post()` for these cases:

  - successful event batch increments `queued` and `delivered`;
  - a final retry failure increments `failed` by batch length;
  - queue overflow increments `dropped`;
  - `flush(timeout)` returns `False` if records remain pending;
  - a completed successful flush produces `evidence_complete is True`.

- [ ] Run the focused tests and confirm failure:

```bash
.venv-mvp/bin/python -m pytest tests/test_http_transport_status.py -q
```

- [ ] Guard all counters with the existing condition lock.
- [ ] Increment `queued` only after `_pending` is incremented for a submitted record.
- [ ] Increment `dropped` if `put_nowait()` raises `queue.Full`.
- [ ] Change `_deliver()` and `_deliver_batch()` to return `True` or `False`; increment `delivered` or `failed` in `_drain()` after the final outcome.
- [ ] Add `stats() -> TransportStats` to `HttpTransport` and delegate it through `MemGuard.delivery_status()`.
- [ ] Keep production instrumentation non-raising. The CLI and demo will inspect the status and fail loudly when completeness is false.
- [ ] Run tests:

```bash
.venv-mvp/bin/python -m pytest tests/test_http_transport_status.py tests/test_sdk_client.py -q
```

- [ ] Commit:

```bash
git add sdk/memguard/transport/http.py sdk/memguard/client.py tests/test_http_transport_status.py
git commit -m "feat: expose evidence delivery status"
```

### Task 4: Accept and persist explicit output context

**Files:**

- Modify: `backend/app/schemas.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/services.py`
- Create: `tests/test_trace_ingestion_contract.py`

**Data decision:** No database migration is required. The existing `decision_traces` table already has `user_input`, `llm_model`, and `metadata_json` columns.

- [ ] Add a Pydantic `SDKDecisionTrace` schema with the same fields as the SDK dataclass, including explicit `user_input`, `model`, and default factories for ID lists/context.
- [ ] Change `create_decision_trace` from `payload: dict` to `payload: SDKDecisionTrace`.
- [ ] Write a failing authenticated API test that posts:

```json
{
  "trace_id": "trace-location-demo",
  "agent_id": "location-agent",
  "session_id": "location-demo-run",
  "namespace": "acme-dev",
  "timestamp": "2026-08-01T12:00:00+00:00",
  "input_event_ids": ["retrieval-location-taipei"],
  "output_event_ids": [],
  "prompt_hash": "prompt-hash",
  "output_hash": "output-hash",
  "output_summary": "You are currently in Taipei.",
  "user_input": "I am currently in New York.",
  "model": "deterministic-demo",
  "memory_influence_score": 0.0,
  "context": {
    "current_facts": {"current_location": "New York"},
    "evidence_model": "recorded_lineage",
    "causality_claim": "not_proven"
  }
}
```

Assert that `GET /v1/trace/trace-location-demo` returns the exact `user_input`, `llm_model == "deterministic-demo"`, and the current facts under `metadata`.

- [ ] Run the focused test and confirm it fails because placeholder values are persisted:

```bash
.venv-mvp/bin/python -m pytest tests/test_trace_ingestion_contract.py -q
```

- [ ] Map `payload.user_input` to `DecisionTrace.user_input`.
- [ ] Map `payload.model` to `DecisionTrace.llm_model`.
- [ ] Map `payload.context` to `DecisionTrace.metadata` without silently adding an `analysis_type` substitute.
- [ ] Preserve aliases `/v1/trace` and `/v1/traces`.
- [ ] Keep tenant ID derived through `request_tenant()` and never trust an unauthenticated namespace.
- [ ] Make `MemoryGateway.create_decision_trace()` the single public storage operation: calculate influence scores, update the in-memory cache, and call `_persist_trace()` exactly once.
- [ ] Remove the route's direct `gateway._persist_trace(trace)` call after the service owns persistence.
- [ ] Extend the API test to query the database for `trace-location-demo` and assert one row exists.
- [ ] Run tests:

```bash
.venv-mvp/bin/python -m pytest tests/test_trace_ingestion_contract.py tests/test_phase1a_contract.py -q
```

- [ ] Commit:

```bash
git add backend/app/schemas.py backend/app/main.py backend/app/services.py tests/test_trace_ingestion_contract.py
git commit -m "feat: persist explicit agent output context"
```

### Task 5: Add a deterministic explanation engine

**Files:**

- Create: `backend/app/explanation.py`
- Modify: `backend/app/services.py`
- Create: `tests/test_explanation_engine.py`

**Pure function:**

```python
def explain_trace(
    trace: dict[str, Any],
    evidence_items: list[dict[str, Any]],
    missing_evidence_event_ids: list[str],
) -> dict[str, Any]:
    """Build a truthful explanation from persisted trace evidence only."""
```

**Deterministic rules:**

1. Return `evidence_gap` if any linked evidence ID is missing. Include the missing IDs but do not create findings for nonexistent records.
2. Consider only input-side items whose metadata has `evidence_role == "retrieved_memory"`.
3. Read the remembered value from `metadata["_after_value"][fact_key]`; never parse the display string stored in `content`.
4. A conflict exists when remembered and current values are both present and unequal after trimming strings. Do not lowercase values because case may be meaningful outside location names.
5. A stale record exists when `memory_last_verified_at` is parseable, `max_age_seconds` is present, and trace time minus verification time is greater than the limit.
6. A future verification timestamp is not stale and produces `age_seconds = 0`.
7. Unparseable timestamps skip the stale inference; retain the observed evidence.
8. `included_in_prompt=False` remains visible but the summary must say the memory was retrieved and excluded, not that it shaped the output.
9. If no comparison can be made, return `observed` with a provenance-only summary.

- [ ] Write table-driven tests for:

  - fresh matching memory → `observed`;
  - fresh conflicting memory → `conflict`;
  - stale matching memory → `stale`;
  - stale conflicting memory → `stale_conflict`;
  - content not captured → `observed` with no remembered/current value claim;
  - missing linked event → `evidence_gap`;
  - excluded memory → finding preserves `included_in_prompt=False` and uses exclusion wording;
  - malformed timestamps → no exception and no stale claim;
  - tenant-unrelated evidence never reaches the function because service resolution is tenant-scoped.

- [ ] Run the focused tests and confirm failure because the module does not exist:

```bash
.venv-mvp/bin/python -m pytest tests/test_explanation_engine.py -q
```

- [ ] Implement ISO-8601 parsing with `datetime.fromisoformat(value.replace("Z", "+00:00"))` and normalize naive timestamps to UTC.
- [ ] Build finding dictionaries with the exact fields defined in Section 4.3.
- [ ] Build summaries from fixed templates; do not send event content to an LLM.
- [ ] In `MemoryGateway._query_traces()`, call `explain_trace()` after `evidence_items` and `missing_evidence_event_ids` are finalized.
- [ ] Ensure traces with no linked IDs still receive an `observed` explanation with an empty findings list.
- [ ] Run tests:

```bash
.venv-mvp/bin/python -m pytest tests/test_explanation_engine.py tests/test_solo_validation_gate.py tests/test_phase1a_contract.py -q
```

- [ ] Commit:

```bash
git add backend/app/explanation.py backend/app/services.py tests/test_explanation_engine.py
git commit -m "feat: explain memory-backed agent outputs"
```

### Task 6: Ship the New York/Taipei golden demo inside the package

**Files:**

- Create: `sdk/memguard/demo.py`
- Create: `sdk/memguard/cli.py`
- Create: `examples/location_memory_demo.py`
- Create: `tests/test_location_demo.py`
- Modify: `sdk/memguard/__init__.py`

**Demo fixture:**

```python
CURRENT_INPUT = "I am currently in New York. Where am I?"
CURRENT_FACTS = {"current_location": "New York"}
RETRIEVED_MEMORY = {"current_location": "Taipei"}
AGENT_OUTPUT = "You are currently in Taipei."
MEMORY_CREATED_AT = "2026-06-15T09:00:00+00:00"
MEMORY_LAST_VERIFIED_AT = "2026-06-15T09:00:00+00:00"
TRACE_TIMESTAMP = "2026-08-01T12:00:00+00:00"
```

The stale result must be deterministic. Add an optional `timestamp` parameter to `record_output()`/`trace_decision()` or construct the trace timestamp through an injectable clock. Do not monkeypatch global time in production code.

- [ ] Write a failing test with a fake transport that captures records and asserts:

  - exactly one retrieval event is recorded;
  - its source, rank, score, prompt-inclusion flag, fact key, and freshness limit are present;
  - the trace explicitly contains the current input, current facts, output, and model;
  - the returned result includes the trace ID and dashboard URL;
  - the demo does not import LangGraph, OpenAI, or any external model client.

- [ ] Run the focused test and confirm failure:

```bash
.venv-mvp/bin/python -m pytest tests/test_location_demo.py -q
```

- [ ] Implement `run_location_demo(client: MemGuard, dashboard_url: str = "http://localhost:3001") -> dict[str, Any]` in `sdk/memguard/demo.py`.
- [ ] Construct the intentionally wrong output directly from the stale retrieved memory so the demo is repeatable.
- [ ] Call `client.flush(timeout=5.0)` and then inspect `client.delivery_status()`.
- [ ] Raise `RuntimeError` with queued/delivered/dropped/failed counts if flush times out or evidence is incomplete.
- [ ] Return JSON-serializable fields: tenant, agent, session, input, retrieved value, output, trace ID, and `dashboard_url/?trace=<trace-id>`.
- [ ] Make `examples/location_memory_demo.py` a thin import-and-run wrapper, proving the logic lives in the installed package.
- [ ] Implement CLI commands with `argparse`:

```text
memguard doctor --api-url http://localhost:8000 --api-token TOKEN
memguard demo --api-url http://localhost:8000 --api-token TOKEN --tenant-id acme-dev
```

- [ ] `doctor` must call `/health` without a bearer token and report API reachability, then call an authenticated trace-list endpoint and report authentication/tenant access. Exit `0` only if both checks succeed.
- [ ] `demo` must instantiate `MemGuard(capture_content=True)`, run the location demo, print formatted JSON, and exit nonzero on incomplete delivery.
- [ ] Do not print the API token in success or error output.
- [ ] Run tests:

```bash
.venv-mvp/bin/python -m pytest tests/test_location_demo.py tests/test_sdk_client.py -q
```

- [ ] Commit:

```bash
git add sdk/memguard/demo.py sdk/memguard/cli.py sdk/memguard/__init__.py examples/location_memory_demo.py tests/test_location_demo.py
git commit -m "feat: add deterministic location memory demo"
```

### Task 7: Render a clear “Why this output?” explanation

**Files:**

- Modify: `frontend/lib/dashboard.ts`
- Create: `frontend/components/WhyThisOutput.tsx`
- Modify: `frontend/components/EvidenceWorkspace.tsx`
- Modify: `frontend/app/globals.css`

**TypeScript contract:**

```typescript
export type ExplanationStatus =
  | 'observed'
  | 'stale'
  | 'conflict'
  | 'stale_conflict'
  | 'evidence_gap'

export interface ExplanationFinding {
  kind: ExplanationStatus
  event_id: string
  memory_key: string
  fact_key?: string
  remembered_value?: unknown
  current_value?: unknown
  source_type?: string
  source_id?: string
  retrieval_rank?: number
  retrieval_score?: number
  included_in_prompt?: boolean
  memory_created_at?: string
  memory_last_verified_at?: string
  max_age_seconds?: number
  age_seconds?: number
}

export interface TraceExplanation {
  basis: 'recorded_evidence'
  causality_claim: 'not_proven'
  status: ExplanationStatus
  summary: string
  findings: ExplanationFinding[]
  missing_evidence_event_ids?: string[]
}
```

- [ ] Add `explanation?: TraceExplanation` to `DecisionTrace` for backward compatibility with old persisted traces.
- [ ] Build `WhyThisOutput` with this information hierarchy:

  1. **Current input** — `trace.user_input`.
  2. **Agent output** — existing `traceOutput(trace)`.
  3. **Explanation summary** — status badge plus server summary.
  4. **Memory finding cards** — remembered value versus current value.
  5. **Observed provenance** — source, record ID, retrieval rank/score, timestamps, prompt inclusion.
  6. **Evidence limits** — causality disclaimer and missing event IDs.

- [ ] Use visible labels, not color alone:

```text
OBSERVED · Retrieved and included in context
INFERRED · Conflicts with current input
LIMIT · Recorded lineage is not proof of model causality
```

- [ ] Show “Content hidden by privacy mode” when a finding has no remembered value but its evidence item has a content hash.
- [ ] Show “Retrieved but not included in context” when `included_in_prompt` is false.
- [ ] Format age as a readable duration and preserve the exact timestamp in a `title` attribute.
- [ ] Add `WhyThisOutput` below the workspace trace header and above the lower-level three-stage lineage.
- [ ] Keep the existing evidence lineage view; it remains the technical drill-down.
- [ ] Update the empty-state command to use `memguard demo` rather than the repository-only generic script.
- [ ] Add responsive CSS for a two-column remembered/current comparison that collapses to one column below 720px.
- [ ] Ensure status semantics do not depend on red/green alone and meet keyboard/screen-reader basics with headings, lists, `aria-labelledby`, and `role="status"` only for evidence gaps.
- [ ] Build the frontend:

```bash
cd frontend
npm run build
```

Expected result: Next.js production build succeeds with no TypeScript errors.

- [ ] Manually inspect these five states using API fixtures or persisted traces:

  - stale conflict with captured content;
  - conflict-only;
  - privacy mode with hash only;
  - excluded-from-prompt memory;
  - missing evidence.

- [ ] Commit:

```bash
git add frontend/lib/dashboard.ts frontend/components/WhyThisOutput.tsx frontend/components/EvidenceWorkspace.tsx frontend/app/globals.css
git commit -m "feat: visualize why an agent produced an output"
```

### Task 8: Make the SDK installable and usable from PyPI

**Files:**

- Modify: `sdk/pyproject.toml`
- Delete: `sdk/setup.py`
- Create: `sdk/memguard/py.typed`
- Modify: `sdk/README.md`
- Modify: `sdk/memguard/__init__.py`
- Create: `tests/test_sdk_distribution.py`

**Packaging decisions:**

- Distribution name: `memguard` for MVP, subject to a final registry/name availability check before first publish.
- Import package: `memguard`.
- Version: `0.2.0`.
- `pyproject.toml` is the only build configuration.
- Use setuptools package discovery so `memguard.display`, `memguard.demo`, and future subpackages are included.

- [ ] Update metadata:

```toml
[project]
name = "memguard"
version = "0.2.0"
description = "Explain how retrieved agent memory relates to an AI output"

[project.scripts]
memguard = "memguard.cli:main"

[project.urls]
Homepage = "https://github.com/ChakesWu/MemguardV1"
Documentation = "https://github.com/ChakesWu/MemguardV1#readme"
Repository = "https://github.com/ChakesWu/MemguardV1"
Issues = "https://github.com/ChakesWu/MemguardV1/issues"

[tool.setuptools.packages.find]
where = ["."]
include = ["memguard*"]
```

- [ ] Add `build>=1.2` and `twine>=5.0` to the `dev` extra.
- [ ] Delete the duplicate legacy `setup.py` only after confirming all metadata is represented in `pyproject.toml`.
- [ ] Add the empty `py.typed` marker.
- [ ] Keep `__version__` synchronized at `0.2.0`; add a release test comparing it with `pyproject.toml`.
- [ ] Write `sdk/README.md` around the first useful result, not around all infrastructure:

```python
from memguard import MemGuard

guard = MemGuard(
    api_url="http://localhost:8000",
    api_key="<token>",
    agent_id="travel-agent",
    namespace="acme-dev",
    capture_content=True,
)
guard.set_session("user-42-run-7")

memory_event_id = guard.record_retrieval(
    "profile:current_location",
    {"current_location": "Taipei"},
    source_type="conversation",
    retrieval_rank=1,
    included_in_prompt=True,
    fact_key="current_location",
)

guard.record_output(
    user_input="I am currently in New York.",
    output_text="You are currently in Taipei.",
    input_event_ids=[memory_event_id],
    model="my-agent-model",
    current_facts={"current_location": "New York"},
)
guard.flush()
```

- [ ] Document that `capture_content=True` is required for value-level conflict visualization and should only be enabled with the developer's privacy approval.
- [ ] Build both distribution artifacts:

```bash
cd sdk
../.venv-mvp/bin/python -m build
../.venv-mvp/bin/python -m twine check dist/*
```

Expected result: one source archive, one wheel, and `PASSED` for both artifacts.

- [ ] Verify contents:

```bash
unzip -l sdk/dist/memguard-0.2.0-py3-none-any.whl
```

Expected result: the wheel contains `client.py`, `cli.py`, `demo.py`, `display/`, and `py.typed`.

- [ ] Install the wheel into a clean temporary environment and test public imports and the CLI:

```bash
python3 -m venv /tmp/memguard-wheel-test
/tmp/memguard-wheel-test/bin/python -m pip install sdk/dist/memguard-0.2.0-py3-none-any.whl
/tmp/memguard-wheel-test/bin/python -c "from memguard import MemGuard; print('import ok')"
/tmp/memguard-wheel-test/bin/memguard --help
```

- [ ] Run the distribution test:

```bash
.venv-mvp/bin/python -m pytest tests/test_sdk_distribution.py -q
```

- [ ] Commit:

```bash
git add sdk/pyproject.toml sdk/memguard/py.typed sdk/README.md sdk/memguard/__init__.py tests/test_sdk_distribution.py
git rm sdk/setup.py
git commit -m "build: prepare memguard Python distribution"
```

### Task 9: Add clean CI, release automation, and repository hygiene

**Files:**

- Modify: `.gitignore`
- Create: `.github/workflows/sdk.yml`
- Create: `.github/workflows/publish-sdk.yml`
- Create: `LICENSE`
- Modify: `README.md`

**Important:** The existing metadata declares MIT. Confirm the repository owner's licensing decision before publishing. If MIT is confirmed, add the standard MIT text with the correct copyright holder and year. Do not publish a package claiming MIT while omitting the license file.

- [ ] Add ignore rules:

```gitignore
.venv*/
myenv/
backend/myenv/
dist/
build/
*.egg-info/
__pycache__/
.pytest_cache/
```

- [ ] Stop tracking the virtual environments while leaving local files intact:

```bash
git rm -r --cached backend/myenv myenv
```

- [ ] Verify no source file lives only inside either environment before committing the removal.
- [ ] Create `sdk.yml` triggered by pull requests and pushes to the default branch with Python 3.9, 3.10, 3.11, and 3.12.
- [ ] In each Python job, install `-e "sdk[dev]"` and `backend/requirements.txt`, then run all root tests.
- [ ] Add a package job on Python 3.11 that runs `python -m build`, `python -m twine check sdk/dist/*`, installs the produced wheel, imports `MemGuard`, and runs `memguard --help`.
- [ ] Add a frontend job using the Node version supported by Next.js 15, `npm ci`, and `npm run build`.
- [ ] Create `publish-sdk.yml` triggered by tags matching `sdk-v*`.
- [ ] Use PyPI trusted publishing with `id-token: write`; do not store an API token in repository files.
- [ ] Make the publish job depend on tests and package validation, then use `pypa/gh-action-pypi-publish`.
- [ ] Add a manual TestPyPI dispatch input for the first release rehearsal.
- [ ] Add a root README quickstart with exactly these steps:

  1. start the local stack;
  2. obtain a Keycloak development token;
  3. `pip install memguard`;
  4. `memguard doctor`;
  5. `memguard demo`;
  6. open the returned trace URL.

- [ ] Document the local development token command:

```bash
curl -s -X POST http://localhost:8180/realms/memguard/protocol/openid-connect/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'client_id=memguard-frontend' \
  -d 'username=demo@memguard.local' \
  -d 'password=demo-password' \
  -d 'grant_type=password'
```

- [ ] Explicitly label those credentials as local-development-only.
- [ ] Confirm the `memguard` distribution name is available in the intended registry immediately before the first publish. If unavailable, change only the distribution name and CLI release documentation; keep `import memguard` stable.
- [ ] Run local equivalents of CI:

```bash
.venv-mvp/bin/python -m pytest -q
cd frontend && npm run build
cd ../sdk && ../.venv-mvp/bin/python -m build && ../.venv-mvp/bin/python -m twine check dist/*
```

- [ ] Commit hygiene separately from product code so the large index removal is reviewable:

```bash
git add .gitignore .github/workflows/sdk.yml .github/workflows/publish-sdk.yml LICENSE README.md
git commit -m "ci: validate and publish the Python SDK"
git commit -m "chore: stop tracking local environments"
```

### Task 10: Run the end-to-end MVP acceptance gate

**Files:**

- Create: `tests/test_location_mvp_e2e.py`
- Modify only if the gate exposes a defect: files from Tasks 1–9

**Environment setup:**

- [ ] Create a clean repository-local environment and install real package dependencies:

```bash
python3 -m venv .venv-mvp-acceptance
.venv-mvp-acceptance/bin/python -m pip install --upgrade pip
.venv-mvp-acceptance/bin/python -m pip install -e "sdk[dev]"
.venv-mvp-acceptance/bin/python -m pip install -r backend/requirements.txt
```

- [ ] Start the local services using the repository's documented Docker Compose command.
- [ ] Confirm service health:

```bash
curl -s http://localhost:8000/health
docker compose config --quiet
```

- [ ] Obtain the local development token and export it only in the active shell as `MEMGUARD_API_TOKEN`.
- [ ] Run the installed-package checks:

```bash
.venv-mvp-acceptance/bin/memguard doctor \
  --api-url http://localhost:8000 \
  --api-token "$MEMGUARD_API_TOKEN" \
  --tenant-id acme-dev

.venv-mvp-acceptance/bin/memguard demo \
  --api-url http://localhost:8000 \
  --api-token "$MEMGUARD_API_TOKEN" \
  --tenant-id acme-dev
```

Expected result: the demo prints a trace ID, complete delivery counts, and a dashboard URL.

- [ ] Add an API-level end-to-end test that records the golden event/trace, fetches the trace, and asserts:

```python
assert trace["user_input"] == "I am currently in New York. Where am I?"
assert trace["llm_output"] == "You are currently in Taipei."
assert trace["explanation"]["status"] == "stale_conflict"
assert trace["explanation"]["causality_claim"] == "not_proven"
assert trace["missing_evidence_event_ids"] == []
assert trace["explanation"]["findings"][0]["remembered_value"] == "Taipei"
assert trace["explanation"]["findings"][0]["current_value"] == "New York"
assert trace["explanation"]["findings"][0]["included_in_prompt"] is True
```

- [ ] Run the complete Python suite:

```bash
.venv-mvp-acceptance/bin/python -m pytest -q
```

- [ ] Run the frontend production build:

```bash
cd frontend
npm run build
```

- [ ] Build and validate the wheel:

```bash
cd ../sdk
../.venv-mvp-acceptance/bin/python -m build
../.venv-mvp-acceptance/bin/python -m twine check dist/*
```

- [ ] Open the returned dashboard trace URL and verify the visible acceptance criteria below.
- [ ] Commit the end-to-end gate:

```bash
git add tests/test_location_mvp_e2e.py
git commit -m "test: verify location memory visualization MVP"
```

---

## 6. Demo Acceptance Criteria

The MVP is demo-ready only when all statements below are true.

### SDK and delivery

- [ ] A clean virtual environment can install the built wheel.
- [ ] `from memguard import MemGuard` succeeds.
- [ ] `memguard doctor` verifies API connectivity, authentication, and tenant access.
- [ ] `memguard demo` emits one retrieved memory and one decision trace.
- [ ] The demo exits nonzero if any evidence was dropped or permanently failed.
- [ ] Hash-only mode captures no raw value and emits a stable content hash.

### API and evidence truthfulness

- [ ] The trace API returns the real user input rather than a prompt-hash placeholder.
- [ ] The trace API returns the supplied model name.
- [ ] Every displayed evidence item resolves to a persisted event in the same tenant.
- [ ] Missing event IDs are returned explicitly and are never replaced with inferred records.
- [ ] The explanation declares `basis=recorded_evidence` and `causality_claim=not_proven`.
- [ ] Conflict and staleness findings are deterministic and covered by unit tests.

### Dashboard

- [ ] The page shows the current New York input.
- [ ] The page shows the incorrect Taipei output.
- [ ] The page shows the retrieved Taipei memory.
- [ ] The page shows its source and source ID.
- [ ] The page shows creation and verification timestamps.
- [ ] The page shows retrieval rank/score when present.
- [ ] The page shows whether the memory was included in context.
- [ ] The page labels retrieval/prompt inclusion as observed evidence.
- [ ] The page labels the New York/Taipei comparison as an inferred conflict.
- [ ] The page retains the “not proof of model causality” limitation.
- [ ] The lower-level evidence lineage remains available for technical inspection.

### Packaging and release

- [ ] `python -m build` creates a source archive and wheel.
- [ ] `twine check` passes for both artifacts.
- [ ] The wheel contains every runtime module and `py.typed`.
- [ ] CI covers supported Python versions and the frontend production build.
- [ ] A TestPyPI rehearsal succeeds before the production PyPI release.

## 7. Suggested Delivery Schedule

| Day | Outcome |
|---:|---|
| 1 | Tasks 1–2: trustworthy event contract and public SDK facade. |
| 2 | Task 3: observable transport completeness. |
| 3 | Task 4: explicit trace ingestion and persistence. |
| 4–5 | Task 5: deterministic explanation engine and edge-case tests. |
| 6 | Task 6: packaged New York/Taipei demo and CLI. |
| 7–8 | Task 7: explanation UI and responsive polish. |
| 9 | Task 8: wheel packaging and clean-install validation. |
| 10 | Task 9: CI, release workflow, license, and repository hygiene. |
| 11 | Task 10: end-to-end gate and demo rehearsal. |
| 12–14 | Buffer for authentication, packaging, browser, and deployment defects found by the acceptance gate. |

## 8. Commercial Demo Script

Keep the live presentation under three minutes:

1. State the pain: “Agent memory makes wrong answers hard to debug because developers cannot see which prior fact was available at generation time.”
2. Run `memguard demo` from an environment where the SDK was installed with pip.
3. Open the returned trace URL.
4. Point to the current input: New York.
5. Point to the selected output: Taipei.
6. Point to the observed retrieval: the old Taipei record, its source, rank, timestamps, and context-inclusion status.
7. Point to the inferred finding: the memory is stale and conflicts with the current fact.
8. Point to the evidence limitation: MemGuard records lineage; it does not claim access to the model's internal reasoning.
9. Close with the developer outcome: “Instead of reproducing the agent blindly, you now have the exact memory record to fix, expire, or exclude in your own application.”

The commercial proof is not the dashboard alone. It is the complete first-run loop:

```text
pip install → instrument two calls → reproduce wrong answer → inspect exact stale memory
```

## 9. Post-MVP Decisions Triggered by Real Usage

Do not implement these before the MVP has been demonstrated to at least five agent developers. Capture them as interview questions instead:

- Which memory frameworks must be instrumented automatically first?
- Do developers prefer per-output debugging, session timelines, or alerting as the daily entry point?
- Is content capture acceptable, or must most customers use hashes and customer-hosted redaction?
- Which correction action is most valuable: expire, supersede, quarantine, or exclude from prompt?
- What latency and delivery guarantees are required in production?
- Is the paying buyer the agent engineer, platform team, support team, or compliance team?

The next commercial build should be chosen from observed buyer behavior, not from adding more dashboard surface area.
