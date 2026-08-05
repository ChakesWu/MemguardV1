# Customer-Support Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver an authenticated `/agent` page where a user can have a persistent, streamed DeepSeek conversation with a real LangGraph customer-support agent backed by PostgreSQL and protected by approval-gated business actions.

**Architecture:** Add an `agent-server/` LangGraph application that owns customer-support graph behavior, typed business tools, PostgreSQL business data, and LangSmith tracing. The existing FastAPI backend remains the browser-facing Keycloak enforcement point and reverse-proxies the Agent Server protocol while injecting tenant and actor context. Adapt selected official Agent Chat UI components inside the existing Next.js frontend instead of running a second frontend.

**Tech Stack:** Python 3.11, LangGraph, LangChain, ChatDeepSeek, langgraph-cli, PostgreSQL 16, FastAPI, httpx, Keycloak OIDC, LangSmith, Next.js 15, React 19, TypeScript, `@langchain/langgraph-sdk`, Vitest, Testing Library, Docker Compose.

## Global Constraints

- The browser never receives `DEEPSEEK_API_KEY` or `LANGSMITH_API_KEY`.
- `agent-server` is Docker-network-only; only the existing backend exposes an agent-proxy route.
- The proxy must derive `tenant_id` and `actor_id` from the Keycloak token and overwrite client-supplied values.
- All business repository queries must include `tenant_id`.
- Read tools run automatically; `create_refund_request`, `create_support_ticket`, `update_shipping_address`, and `cancel_order` require a LangGraph interrupt.
- Every approved write revalidates current data and uses an idempotency key.
- Use `deepseek-v4-flash` by default; do not add new references to legacy `deepseek-chat` or `deepseek-reasoner` model names.
- Enable LangSmith only through server-side environment variables; `LANGSMITH_TRACING` remains opt-in.
- Do not connect this baseline to MemGuard SDK ingestion, traces, or dashboard evidence APIs.
- Preserve existing `/` evidence-console behavior and tests.
- Do not reset, delete, stage, or commit unrelated dirty worktree files.

---

## File Structure

```text
agent-server/
  Dockerfile                         LangGraph Agent Server image
  requirements.txt                   Isolated graph dependencies
  langgraph.json                     Graph registration and server config
  support_agent/
    __init__.py
    config.py                        Server-only settings and secret validation
    domain.py                        Typed customer/order/policy/action models
    migrations.py                    Support-business schema migration runner
    repository.py                    Tenant-scoped PostgreSQL access
    policy.py                        Pure refund-policy validation
    tools.py                         LangChain tools and interrupt-gated writers
    graph.py                         Compiled customer_support_agent graph
    seed.py                          Idempotent canonical local data seed
tests/support_agent/
  test_config.py
  test_repository.py
  test_policy.py
  test_tools.py
  test_graph.py
backend/app/
  agent_proxy.py                     Keycloak-authenticated Agent Server proxy
  main.py                            Proxy route registration
tests/
  test_agent_proxy.py
  test_agent_compose.py
frontend/
  app/agent/page.tsx                 Authenticated support-agent route
  components/agent/
    AgentProviders.tsx               Adapted thread/stream providers
    SupportAgentChat.tsx             Conversation, composer, and thread UI
    ToolActivityCard.tsx             Read-tool state and result renderer
    ApprovalCard.tsx                 Approve/edit/reject interrupt renderer
  lib/agent-client.ts                Typed Agent Server URL/header helpers
  test/agent-client.test.ts
  test/support-agent-chat.test.tsx
  vitest.config.ts
  package.json
  package-lock.json
  app/globals.css
docker-compose.yml
.env.example
THIRD_PARTY_NOTICES.md
```

## Task 1: Create the isolated LangGraph Agent Server and local configuration

**Files:**

- Create: `agent-server/requirements.txt`
- Create: `agent-server/langgraph.json`
- Create: `agent-server/Dockerfile`
- Create: `agent-server/support_agent/__init__.py`
- Create: `agent-server/support_agent/config.py`
- Create: `tests/support_agent/test_config.py`
- Modify: `docker-compose.yml`
- Modify: `.env.example`
- Test: `tests/test_agent_compose.py`

**Interfaces:**

- Produces `SupportAgentSettings.from_env() -> SupportAgentSettings`.
- Produces a LangGraph graph registration named `customer_support_agent`.
- Produces Docker service `agent-server` listening on internal port `2024` only.

- [ ] **Step 1: Write the failing settings and Compose contract tests**

```python
def test_settings_require_deepseek_key_when_real_model_is_enabled(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    from support_agent.config import SupportAgentSettings

    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        SupportAgentSettings.from_env()


def test_compose_keeps_agent_server_private():
    compose = Path("docker-compose.yml").read_text()
    assert "agent-server:" in compose
    assert "LANGGRAPH_AGENT_URL: http://agent-server:2024" in compose
    assert '"2024:2024"' not in compose
```

- [ ] **Step 2: Run the tests to verify the expected failure**

Run: `python -m pytest tests/support_agent/test_config.py tests/test_agent_compose.py -q`

Expected: FAIL because the `support_agent` package and `agent-server` Compose service do not exist.

- [ ] **Step 3: Add the minimal isolated server configuration**

Create `agent-server/requirements.txt` with pinned compatible packages:

```text
langgraph>=1.2,<2
langgraph-cli[inmem]>=0.2.6
langchain>=1,<2
langchain-deepseek>=0.1,<1
psycopg[binary,pool]>=3.2,<4
pydantic>=2.10,<3
```

Implement `SupportAgentSettings` with these fields:

```python
@dataclass(frozen=True)
class SupportAgentSettings:
    database_url: str
    deepseek_api_key: str
    deepseek_model: str
    langsmith_tracing: bool
    langsmith_api_key: str | None
    langsmith_project: str

    @classmethod
    def from_env(cls) -> "SupportAgentSettings": ...
```

`from_env()` must default `DEEPSEEK_MODEL` to `deepseek-v4-flash`, require `DATABASE_URL` and `DEEPSEEK_API_KEY`, and require `LANGSMITH_API_KEY` only when `LANGSMITH_TRACING=true`.

Register the graph in `agent-server/langgraph.json`:

```json
{
  "dependencies": ["."],
  "graphs": {
    "customer_support_agent": "./support_agent/graph.py:customer_support_agent"
  },
  "env": ".env"
}
```

Use this Docker command so the Agent Server is only reachable from the Compose network:

```dockerfile
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "2024", "--no-browser", "--no-reload"]
```

Add an `agent-server` Compose service with `expose: ["2024"]`, no `ports`, `DATABASE_URL=postgresql://memguard:memguard@postgres:5432/memguard`, DeepSeek/LangSmith environment pass-through, and a healthcheck against `http://localhost:2024/info`.

- [ ] **Step 4: Re-run settings and Compose tests**

Run: `python -m pytest tests/support_agent/test_config.py tests/test_agent_compose.py -q`

Expected: PASS.

- [ ] **Step 5: Commit the isolated server skeleton**

```bash
git add agent-server docker-compose.yml .env.example tests/support_agent/test_config.py tests/test_agent_compose.py
git commit -m "feat: add LangGraph agent server skeleton"
```

## Task 2: Add tenant-scoped support-business persistence and deterministic seed data

**Files:**

- Create: `agent-server/support_agent/domain.py`
- Create: `agent-server/support_agent/migrations.py`
- Create: `agent-server/support_agent/repository.py`
- Create: `agent-server/support_agent/seed.py`
- Create: `tests/support_agent/test_repository.py`

**Interfaces:**

- Consumes `SupportAgentSettings.database_url`.
- Produces `SupportRepository` with tenant-scoped customer, order, policy, memory, and action operations.
- Produces `seed_baseline_data(repository: SupportRepository, tenant_id: str) -> None`.

- [ ] **Step 1: Write failing repository behavior tests**

```python
def test_get_order_cannot_cross_tenant(repository):
    seed_baseline_data(repository, tenant_id="acme-dev")

    assert repository.get_order("other-tenant", "ORD-4821") is None
    assert repository.get_order("acme-dev", "ORD-4821").order_id == "ORD-4821"


def test_memory_update_creates_a_new_version(repository):
    first = repository.write_memory(
        tenant_id="acme-dev", owner_id="CUS-1042", kind="address",
        value={"city": "Macau"}, source_type="user_statement",
    )
    second = repository.write_memory(
        tenant_id="acme-dev", owner_id="CUS-1042", kind="address",
        value={"city": "Hong Kong"}, source_type="user_statement",
        supersedes_version_id=first.version_id,
    )

    assert first.version_id != second.version_id
    assert repository.get_memory(first.version_id).status == "superseded"
```

- [ ] **Step 2: Run the repository tests to verify the expected failure**

Run: `python -m pytest tests/support_agent/test_repository.py -q`

Expected: FAIL because the repository and schema do not exist.

- [ ] **Step 3: Implement the minimal schema, repository, and seed**

Create separate support tables; do not alter existing `memory_events` or `decision_traces`:

```text
support_customers(tenant_id, customer_id, name, tier, account_status)
support_orders(tenant_id, order_id, customer_id, status, delivered_at, payment_status, shipping_address_json)
support_policies(tenant_id, document_id, version, effective_from, policy_json, status)
support_memories(tenant_id, memory_id, version_id, owner_id, kind, value_json, source_type, source_id, valid_from, valid_until, supersedes_version_id, trust_level, status)
support_actions(tenant_id, action_id, idempotency_key, action_type, order_id, payload_json, status, created_at)
```

Add uniqueness constraints on `(tenant_id, customer_id)`, `(tenant_id, order_id)`, `(tenant_id, document_id, version)`, `(tenant_id, version_id)`, and `(tenant_id, idempotency_key)`.

Implement only parameterized SQL. Every method receives `tenant_id` first:

```python
class SupportRepository:
    def get_customer(self, tenant_id: str, customer_id: str) -> Customer | None: ...
    def get_order(self, tenant_id: str, order_id: str) -> Order | None: ...
    def active_refund_policy(self, tenant_id: str, at: datetime) -> PolicyDocument | None: ...
    def search_memories(self, tenant_id: str, customer_id: str, query: str) -> list[MemoryRecord]: ...
    def write_memory(self, *, tenant_id: str, owner_id: str, kind: str, value: dict[str, Any] | str, source_type: str, source_id: str | None = None, supersedes_version_id: str | None = None) -> MemoryRecord: ...
    def create_action_once(self, *, tenant_id: str, idempotency_key: str, action_type: str, order_id: str, payload: dict[str, Any]) -> SupportAction: ...
```

Seed tenant `acme-dev`, `CUS-1042`, `ORD-4821`, refund-policy v2, expired exception `MEM-EXCEPTION-77`, and the explicitly labelled lossy agent summary from the approved baseline. Make seeding idempotent.

- [ ] **Step 4: Re-run repository tests**

Run: `python -m pytest tests/support_agent/test_repository.py -q`

Expected: PASS.

- [ ] **Step 5: Commit persistence and seed data**

```bash
git add agent-server/support_agent tests/support_agent/test_repository.py
git commit -m "feat: add tenant scoped support data"
```

## Task 3: Implement policy validation and interrupt-gated business tools

**Files:**

- Create: `agent-server/support_agent/policy.py`
- Create: `agent-server/support_agent/tools.py`
- Create: `tests/support_agent/test_policy.py`
- Create: `tests/support_agent/test_tools.py`

**Interfaces:**

- Consumes `SupportRepository` and `SupportState` configuration context.
- Produces pure `evaluate_refund(...) -> RefundEligibility`.
- Produces `build_support_tools(repository) -> dict[str, BaseTool]`.

- [ ] **Step 1: Write the failing eligibility and interruption tests**

```python
def test_expired_exception_requires_manual_review():
    result = evaluate_refund(
        delivered_at=datetime(2026, 7, 5, tzinfo=UTC),
        now=datetime(2026, 8, 2, tzinfo=UTC),
        standard_refund_days=14,
        exception_valid_until=datetime(2026, 7, 20, 23, 59, 59, tzinfo=UTC),
        defective=True,
    )

    assert result.outcome == "manual_review"


def test_refund_tool_requests_approval_before_creating_action(monkeypatch, repository):
    requested = []
    monkeypatch.setattr("support_agent.tools.interrupt", lambda value: requested.append(value) or {"decision": "reject"})
    tool = build_support_tools(repository)["create_refund_request"]

    tool.invoke({"order_id": "ORD-4821", "reason": "defective"}, config=tenant_config())

    assert requested[0]["action"] == "create_refund_request"
    assert repository.actions_for("acme-dev", "ORD-4821") == []
```

- [ ] **Step 2: Run the tests to verify the expected failure**

Run: `python -m pytest tests/support_agent/test_policy.py tests/support_agent/test_tools.py -q`

Expected: FAIL because the policy evaluator and tools do not exist.

- [ ] **Step 3: Implement pure validation and safe tools**

Implement the pure result contract:

```python
@dataclass(frozen=True)
class RefundEligibility:
    outcome: Literal["approve", "reject", "manual_review"]
    reason: str
```

Read tools must fetch only the configured tenant. Each write tool must call `interrupt()` with this serializable request shape before it validates or writes:

```python
{
  "kind": "approval_required",
  "action": "create_refund_request",
  "arguments": {"order_id": "ORD-4821", "reason": "defective"},
  "allowed_decisions": ["approve", "edit", "reject"]
}
```

After `Command(resume=...)`, reject invalid decisions, accept edited arguments only from an explicit allowlist, compute eligibility against fresh repository data, and use a UUID supplied by the runtime as the idempotency key. If the exception is expired, return the manual-review result without creating an automatic refund action.

- [ ] **Step 4: Re-run policy and tool tests**

Run: `python -m pytest tests/support_agent/test_policy.py tests/support_agent/test_tools.py -q`

Expected: PASS.

- [ ] **Step 5: Commit safe business tools**

```bash
git add agent-server/support_agent/policy.py agent-server/support_agent/tools.py tests/support_agent/test_policy.py tests/support_agent/test_tools.py
git commit -m "feat: add approval gated support tools"
```

## Task 4: Build the DeepSeek LangGraph graph and LangSmith tracing configuration

**Files:**

- Create: `agent-server/support_agent/graph.py`
- Create: `tests/support_agent/test_graph.py`
- Modify: `agent-server/support_agent/config.py`
- Modify: `agent-server/langgraph.json`

**Interfaces:**

- Consumes `build_support_tools(repository)` and `SupportAgentSettings`.
- Produces `customer_support_agent`, a compiled graph whose state contains `messages`.
- Produces `build_customer_support_agent(settings, repository, model=None)` for tests.

- [ ] **Step 1: Write the failing graph tests**

```python
def test_graph_has_a_messages_channel_and_registered_name():
    graph = build_customer_support_agent(settings=fake_settings(), repository=fake_repository(), model=fake_model())

    assert graph is not None
    assert Path("agent-server/langgraph.json").read_text().count("customer_support_agent") == 1


def test_read_question_returns_a_tool_backed_answer():
    result = graph.invoke(
        {"messages": [("user", "What is the status of ORD-4821?")]},
        config={"configurable": {"tenant_id": "acme-dev", "actor_id": "demo-user", "thread_id": "thread-1"}},
    )

    assert "delivered" in result["messages"][-1].content.lower()
```

- [ ] **Step 2: Run the graph tests to verify the expected failure**

Run: `python -m pytest tests/support_agent/test_graph.py -q`

Expected: FAIL because `build_customer_support_agent` is not defined.

- [ ] **Step 3: Implement the graph**

Create `ChatDeepSeek` only in the real settings path:

```python
ChatDeepSeek(
    model=settings.deepseek_model,
    api_key=settings.deepseek_api_key,
    api_base="https://api.deepseek.com",
    temperature=0,
    streaming=True,
)
```

Use `create_agent(model, tools, system_prompt=...)` or an explicit `StateGraph` with a `messages` reducer, provided it exposes the same message state and supports `interrupt()` resumes. The system prompt must tell the model to use tools for business facts, never invent order data, and explain when a requested action needs approval.

Configure LangSmith only through environment values in the Agent Server process. Set project name to `memguard-customer-support-baseline`. Do not call LangSmith from browser code.

- [ ] **Step 4: Re-run graph tests**

Run: `python -m pytest tests/support_agent/test_graph.py -q`

Expected: PASS using the injected fake model; no DeepSeek network call occurs in unit tests.

- [ ] **Step 5: Commit graph and tracing setup**

```bash
git add agent-server/support_agent/graph.py agent-server/support_agent/config.py agent-server/langgraph.json tests/support_agent/test_graph.py
git commit -m "feat: add DeepSeek customer support graph"
```

## Task 5: Add the Keycloak-authenticated Agent Server proxy

**Files:**

- Create: `backend/app/agent_proxy.py`
- Modify: `backend/app/main.py`
- Modify: `backend/requirements.txt`
- Create: `tests/test_agent_proxy.py`

**Interfaces:**

- Consumes `TenantPrincipal` from `app.auth` and `LANGGRAPH_AGENT_URL`.
- Produces `proxy_agent_request(request: Request, path: str) -> Response`.
- Exposes `/v1/agent-server/{path:path}` with `GET`, `POST`, `PATCH`, and `DELETE` forwarding.

- [ ] **Step 1: Write failing tenant-injection and streaming tests**

```python
def test_proxy_replaces_client_tenant_and_actor(monkeypatch, authenticated_client):
    captured = {}

    def fake_stream(*args, **kwargs):
        captured["json"] = kwargs["json"]
        return fake_sse_response("event: values\\ndata: {}\\n\\n")

    monkeypatch.setattr("app.agent_proxy.open_agent_stream", fake_stream)
    response = authenticated_client.post(
        "/v1/agent-server/threads/thread-1/runs/stream",
        json={"config": {"configurable": {"tenant_id": "attacker", "actor_id": "attacker"}}},
    )

    assert response.status_code == 200
    assert captured["json"]["config"]["configurable"]["tenant_id"] == "acme-dev"
    assert captured["json"]["config"]["configurable"]["actor_id"] != "attacker"


def test_proxy_forwards_server_sent_events_without_buffering(authenticated_client, monkeypatch):
    monkeypatch.setattr("app.agent_proxy.open_agent_stream", fake_sse_response)
    response = authenticated_client.post("/v1/agent-server/runs/stream", json={"input": {}})
    assert response.headers["content-type"].startswith("text/event-stream")
```

- [ ] **Step 2: Run the proxy tests to verify the expected failure**

Run: `python -m pytest tests/test_agent_proxy.py -q`

Expected: FAIL because the proxy module and routes do not exist.

- [ ] **Step 3: Implement the minimal safe streaming proxy**

Use `httpx.AsyncClient` and `StreamingResponse`. For JSON request bodies, deep-copy the body and merge this exact context:

```python
payload.setdefault("config", {}).setdefault("configurable", {}).update({
    "tenant_id": principal.tenant_id,
    "actor_id": principal.subject,
})
```

Forward `Content-Type`, `Accept`, and `Last-Event-ID`, but never forward browser-controlled LangSmith or DeepSeek credentials. Preserve Agent Server `text/event-stream` response bytes and relevant headers without collecting the whole response in memory. Do not allow an arbitrary outbound host; use only `LANGGRAPH_AGENT_URL` with a default of `http://agent-server:2024`.

- [ ] **Step 4: Re-run proxy tests**

Run: `python -m pytest tests/test_agent_proxy.py -q`

Expected: PASS.

- [ ] **Step 5: Commit authenticated proxy support**

```bash
git add backend/app/agent_proxy.py backend/app/main.py backend/requirements.txt tests/test_agent_proxy.py
git commit -m "feat: proxy authenticated LangGraph requests"
```

## Task 6: Add the adapted Agent Chat UI client foundation

**Files:**

- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Create: `frontend/vitest.config.ts`
- Create: `frontend/test/agent-client.test.ts`
- Create: `frontend/lib/agent-client.ts`
- Create: `frontend/components/agent/AgentProviders.tsx`

**Interfaces:**

- Consumes Keycloak access token returned by `loginRequired()`.
- Produces `agentApiUrl()` and `agentHeaders(accessToken)`.
- Produces `AgentProviders` that wraps adapted `useStream` and thread context with graph ID `customer_support_agent`.

- [ ] **Step 1: Write failing frontend client tests**

```ts
it('sends the Keycloak token only to the local backend agent proxy', () => {
  expect(agentApiUrl()).toBe('http://localhost:3001/api/v1/agent-server')
  expect(agentHeaders('token-123')).toEqual({ Authorization: 'Bearer token-123' })
})

it('does not expose DeepSeek or LangSmith configuration', () => {
  expect(JSON.stringify(publicAgentConfig())).not.toContain('DEEPSEEK')
  expect(JSON.stringify(publicAgentConfig())).not.toContain('LANGSMITH')
})
```

- [ ] **Step 2: Run the test to verify the expected failure**

Run: `cd frontend && npm run test -- agent-client.test.ts`

Expected: FAIL because Vitest, `agent-client.ts`, and the test command do not exist.

- [ ] **Step 3: Add only the upstream dependencies needed for the adapted UI**

Add `@langchain/langgraph-sdk`, `@langchain/core`, `react-markdown`, `remark-gfm`, `lucide-react`, Vitest, jsdom, and Testing Library. Add:

```json
"test": "vitest run"
```

Implement `agentApiUrl()` from `window.location.origin` so both local development and the Docker frontend use the same Next.js rewrite path. Implement `AgentProviders` using the official `useStream` contract:

```tsx
useStream({
  apiUrl: agentApiUrl(),
  assistantId: 'customer_support_agent',
  defaultHeaders: agentHeaders(accessToken),
  fetchStateHistory: true,
  streamMode: ['values', 'tools'],
})
```

Use an `onThreadId` callback to refresh the tenant-scoped thread list. Never add an API-key input or local-storage secret storage.

- [ ] **Step 4: Run frontend client tests and the production build**

Run: `cd frontend && npm run test -- agent-client.test.ts && npm run build`

Expected: PASS.

- [ ] **Step 5: Commit UI client foundation**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vitest.config.ts frontend/test/agent-client.test.ts frontend/lib/agent-client.ts frontend/components/agent/AgentProviders.tsx
git commit -m "feat: add authenticated LangGraph UI client"
```

## Task 7: Implement the `/agent` conversation route and approval UI

**Files:**

- Create: `frontend/app/agent/page.tsx`
- Create: `frontend/components/agent/SupportAgentChat.tsx`
- Create: `frontend/components/agent/ToolActivityCard.tsx`
- Create: `frontend/components/agent/ApprovalCard.tsx`
- Create: `frontend/test/support-agent-chat.test.tsx`
- Modify: `frontend/app/globals.css`

**Interfaces:**

- Consumes `AgentProviders`, `useStream`, and `loginRequired()`.
- Produces `/agent`, an authenticated user route.
- Produces inline `approve`, `edit`, and `reject` resume commands for an interrupted graph.

- [ ] **Step 1: Write failing UI behavior tests**

```tsx
it('shows streamed tool progress before the final answer', async () => {
  render(<SupportAgentChat stream={streamWithRunningTool('get_order')} />)
  expect(screen.getByText('get_order')).toBeVisible()
  expect(screen.getByText('Looking up order')).toBeVisible()
})

it('requires a decision before a pending write action can resume', async () => {
  const submit = vi.fn()
  render(<ApprovalCard interrupt={refundInterrupt} submit={submit} />)

  await userEvent.click(screen.getByRole('button', { name: 'Approve' }))

  expect(submit).toHaveBeenCalledWith({
    command: { resume: { decision: 'approve' } },
  })
})
```

- [ ] **Step 2: Run the UI tests to verify the expected failure**

Run: `cd frontend && npm run test -- support-agent-chat.test.tsx`

Expected: FAIL because the agent route and components do not exist.

- [ ] **Step 3: Implement the smallest usable chat surface**

`page.tsx` must authenticate with the existing `loginRequired()` hook and show a non-secret configuration error if sign-in fails.

Implement this layout without a second dashboard framework:

```text
top bar: MEMGUARD | Support Agent | Evidence Console | account actions
left rail: New chat + current tenant thread list
main panel: messages, tool cards, approval cards, composer
```

`SupportAgentChat` renders `stream.messages`, `stream.toolProgress`, and the latest graph interrupt. The composer submits a `HumanMessage` and disables only while a run is active. `ToolActivityCard` must distinguish starting, running, completed, and error states. `ApprovalCard` must render the tool name and permitted arguments, restrict edits to the action's allowlisted fields, and call the exact resume command shown in the test.

Add a visible connection state and starter prompts for `CUS-1042` and `ORD-4821`. Add a navigation link back to `/` without altering the evidence console.

- [ ] **Step 4: Re-run UI tests and production build**

Run: `cd frontend && npm run test -- support-agent-chat.test.tsx && npm run build`

Expected: PASS.

- [ ] **Step 5: Commit the support-agent UI**

```bash
git add frontend/app/agent frontend/components/agent frontend/test/support-agent-chat.test.tsx frontend/app/globals.css
git commit -m "feat: add customer support agent page"
```

## Task 8: Verify the complete Compose flow, LangSmith integration, and user setup

**Files:**

- Modify: `tests/test_agent_compose.py`
- Create: `tests/test_agent_end_to_end.py`
- Create: `THIRD_PARTY_NOTICES.md`
- Modify: `.env.example`
- Modify: `README.md`

**Interfaces:**

- Consumes the complete Compose stack and server-only credentials.
- Produces a reproducible setup and end-to-end verification path.

- [ ] **Step 1: Write failing end-to-end contract tests**

```python
def test_seeded_control_question_creates_manual_review_not_refund(agent_client):
    result = agent_client.ask(
        thread_id="control-thread",
        message="Can CUS-1042 automatically refund ORD-4821 for a defective item?",
    )

    assert result.final_text
    assert result.pending_action["action"] == "create_support_ticket"
    assert result.refund_actions == []


def test_faulty_exception_proposal_is_revalidated_after_approval(agent_client):
    pending = agent_client.ask_fault_injection(thread_id="fault-thread")
    completed = agent_client.resume(pending, decision="approve")

    assert completed.action_status == "manual_review"
    assert completed.automatic_refund_created is False
```

- [ ] **Step 2: Run the end-to-end test to verify the expected failure**

Run: `python -m pytest tests/test_agent_end_to_end.py -q`

Expected: FAIL until the Compose services, seed command, graph, proxy, and UI protocol are connected.

- [ ] **Step 3: Add a reproducible verification command and setup guidance**

Add the required server-only settings to `.env.example`:

```env
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-v4-flash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=memguard-customer-support-baseline
```

Document the actual operator sequence:

```bash
cp .env.example .env
# fill DEEPSEEK_API_KEY and LANGSMITH_API_KEY; do not commit .env
docker compose up --build -d
docker compose exec agent-server python -m support_agent.seed --tenant acme-dev
docker compose ps
```

Add MIT attribution for the adapted `langchain-ai/agent-chat-ui` components to `THIRD_PARTY_NOTICES.md`. Update the README with `/agent`, required registrations, the local Keycloak test account, and the explicit statement that LangSmith tracing may transmit run data when enabled.

- [ ] **Step 4: Run full verification**

Run: `python -m pytest tests/support_agent tests/test_agent_proxy.py tests/test_agent_compose.py tests/test_agent_end_to_end.py -q`

Run: `cd frontend && npm run test && npm run build`

Run: `docker compose config`

Expected: all tests pass, frontend builds, and Compose configuration validates. With real user-provided credentials, a manual browser check at `http://localhost:3001/agent` shows a streamed DeepSeek reply, tool card, approval interrupt, and a LangSmith trace.

- [ ] **Step 5: Commit end-to-end verification and setup**

```bash
git add tests/test_agent_compose.py tests/test_agent_end_to_end.py .env.example README.md THIRD_PARTY_NOTICES.md
git commit -m "test: verify standalone support agent flow"
```

## Final Verification Checklist

- [ ] `git status --short` shows only intentional changes.
- [ ] Existing evidence-console Python tests still pass.
- [ ] Support-agent unit, proxy, UI, and end-to-end tests pass.
- [ ] `frontend/npm run build` passes.
- [ ] `docker compose config` passes.
- [ ] `/` still opens the evidence console after Keycloak login.
- [ ] `/agent` authenticates through Keycloak and has no API-key input.
- [ ] A missing DeepSeek key produces a safe configuration message.
- [ ] A write action cannot run without interruption and approval.
- [ ] An expired exception cannot create an automatic refund, even after approval.
- [ ] No DeepSeek or LangSmith secret is present in source-controlled frontend code or build output.
