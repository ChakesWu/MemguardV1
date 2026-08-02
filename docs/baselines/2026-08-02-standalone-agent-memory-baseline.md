# Standalone Customer-Support Agent Baseline

**Status:** Approved design  
**Date:** 2026-08-02  
**Purpose:** Build a genuinely usable customer-support agent before connecting it to any external observability product.

## 1. Outcome

This baseline is a real customer-support application, not a static demo. An authenticated user can open a chat page, ask a question about a customer, order, policy, or previous support case, and receive a streamed answer from DeepSeek.

The agent can use real business tools backed by PostgreSQL. It can read customer records, orders, refund policies, and support history. When it proposes a business-changing action, such as creating a refund request or changing a delivery address, it pauses and waits for an explicit human decision.

The application must work with no MemGuard SDK, collector, dashboard ingestion, or other MemGuard dependency. It is deliberately a clean baseline that can later be observed without changing its business behavior.

## 2. Core User Experience

The existing evidence console remains at `/`. A separate authenticated route, `/agent`, hosts the customer-support application.

An operator can type questions such as:

> Find customer CUS-1042 and tell me whether order ORD-4821 can be refunded.

> What did the previous support agent promise this customer?

> Create a manual-review ticket for the defective headphones.

> Change the delivery address for the customer's unshipped order.

The system streams the agent response, shows each tool invocation and result, preserves conversation history, and presents approval controls for business-changing actions.

## 3. Reference Architecture

```text
Browser
  |
  +--> /              Existing evidence console
  |
  +--> /agent         Customized LangGraph Agent Chat UI
                         |
                         | authenticated requests
                         v
                 MemGuard backend proxy
                 (Keycloak verification,
                  tenant context injection)
                         |
                         v
                 LangGraph Agent Server
                 graph: customer_support_agent
                         |
         +---------------+----------------+
         |               |                |
         v               v                v
      DeepSeek       PostgreSQL       LangSmith
      chat model     business data    tracing, Studio,
      and tools      and memory       and deployment
```

The public browser never receives a DeepSeek or LangSmith secret. The backend proxy is the only browser-facing path to the agent server. It verifies the Keycloak bearer token, injects the authenticated tenant and actor into the graph configuration, and streams the agent-server response back to the browser.

## 4. Open-Source UI Baseline

Use selected components and patterns from LangChain's official MIT-licensed [Agent Chat UI](https://github.com/langchain-ai/agent-chat-ui). Do not build a second custom chat product or embed the complete upstream application as an iframe.

Reuse and adapt:

- LangGraph SDK stream and thread providers.
- Persistent thread list and new-chat control.
- Streaming message rendering and automatic scroll behavior.
- Markdown rendering.
- Tool-call and tool-result cards.
- LangGraph interrupt cards.
- Reconnect, cancellation, and error states.

Customize:

- Mount at `/agent` inside the existing Next.js frontend.
- Keep the existing MemGuard visual system and Keycloak session.
- Add top navigation between **Support Agent** and **Evidence Console**.
- Remove the upstream deployment-configuration form; Docker Compose provides the graph URL and graph ID.
- Show the selected DeepSeek model and agent-server connection status.
- Display example prompts that work against the seeded local business database.
- Keep risky-action approvals inline in the conversation.

Keep the upstream license and attribution in the repository's third-party notices.

## 5. LangGraph Application

The graph is a real LangGraph tool-calling workflow. Its public graph ID is `customer_support_agent`.

```text
START
  |
  v
Load thread history and authenticated context
  |
  v
DeepSeek agent node
  |
  +--> no tool call --------------------------> Final response
  |
  +--> read tool call --> execute tool -------> DeepSeek agent node
  |
  +--> write tool call --> LangGraph interrupt
                                      |
                         approve / edit / reject
                                      |
                    execute or cancel requested tool
                                      |
                                      v
                              DeepSeek final response
                                      |
                                      v
                         Write support-summary memory
                                      |
                                      v
                                     END
```

The graph uses LangGraph's `messages` state channel and a persistent `thread_id`. The browser creates or selects a thread; every new turn reuses that thread ID, so the conversation resumes naturally across page reloads.

```python
class SupportState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    customer_id: str | None
    order_id: str | None
    retrieved_records: list[dict]
    pending_action: dict | None
    completed_actions: list[dict]
```

The graph configuration additionally carries server-injected `tenant_id` and `actor_id`. Browser-supplied values for those fields must be ignored or overwritten by the authenticated backend proxy.

## 6. DeepSeek Model Integration

Use LangChain's provider-specific `ChatDeepSeek` integration with a tool-capable model.

Default local configuration:

```env
DEEPSEEK_API_KEY=replace-with-your-secret
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

`deepseek-v4-flash` is the default for fast conversational use. `deepseek-v4-pro` may be selected for higher-quality evaluations. Do not use legacy `deepseek-chat` or `deepseek-reasoner` names in new configuration.

The model is configured for streaming and tool calling. It never directly accesses PostgreSQL or performs writes: it can only request typed tool calls, and application code validates every call.

## 7. Business Data and Tools

PostgreSQL is the source of truth. The first local installation uses persistent data that the operator can modify, not hard-coded response text.

### Read tools

Read tools execute automatically:

```text
find_customer(customer_reference)
get_customer_profile(customer_id)
list_customer_orders(customer_id)
get_order(order_id, customer_id)
get_active_refund_policy(at)
search_support_history(customer_id, query)
get_refund_status(order_id)
```

### Write tools

Write tools always require a LangGraph interrupt and explicit operator approval:

```text
create_refund_request(order_id, resolution, reason)
create_support_ticket(customer_id, order_id, reason)
update_shipping_address(order_id, address)
cancel_order(order_id, reason)
```

The UI gives the operator three choices:

- **Approve**: execute the exact proposed tool call.
- **Edit**: modify permitted arguments, then execute the edited call.
- **Reject**: cancel the request and return the feedback to the agent.

Approval is not a bypass. Every write tool revalidates the tenant, order state, policy version, current time, customer exception, and idempotency key at execution time.

## 8. Memory and Data Lifecycle

The baseline has real, updateable memory. Memory is not a fixed prompt or a static vector-store example.

### Memory categories

| Category | Example | Authority |
|---|---|---|
| Thread state | Current conversation messages | Thread scoped |
| Operational record | Order delivery date | High |
| Versioned policy | Refund policy v2 | High |
| Support history | Previous exception record | Medium |
| User statement | Address correction | Candidate until confirmed |
| Agent summary | Conversation summary | Low to medium |

### Versioned memory model

```text
memory_id
version_id
tenant_id
owner_id
kind
value
source_type
source_id
created_at
verified_at
valid_from
valid_until
supersedes_version_id
trust_level
status
```

Allowed statuses are `candidate`, `active`, `superseded`, `expired`, `quarantined`, and `rejected`.

Updates never overwrite an existing record. A user correction, policy import, tool observation, or agent summary creates a new version. An agent-generated summary stays labelled as such; it cannot silently acquire the authority of an order record or policy document.

### LangGraph persistence

- **Threads/checkpoints:** short-term conversational state and paused approval requests.
- **PostgreSQL business data:** customer, order, policy, support, refund, ticket, and durable memory records.
- **LangGraph store:** optional graph-level long-term data only when it does not duplicate the business source of truth.

## 9. Canonical Local Data

Seed a local PostgreSQL tenant with a realistic support case.

### Customer and order

```json
{
  "customer_id": "CUS-1042",
  "name": "Alex Chen",
  "tier": "VIP",
  "order_id": "ORD-4821",
  "product": "Noise-cancelling headphones",
  "delivered_at": "2026-07-05T10:00:00Z",
  "order_status": "delivered",
  "payment_status": "paid"
}
```

### Policy and exception

```json
{
  "policy_document": "refund-policy",
  "policy_version": "v2",
  "effective_from": "2026-07-01T00:00:00Z",
  "standard_refund_days": 14,
  "defective_item_action": "manual_review_after_window"
}
```

```json
{
  "memory_id": "MEM-EXCEPTION-77",
  "kind": "refund_exception",
  "refund_window_days": 30,
  "scope": "one_future_order",
  "source_type": "support_agent_note",
  "source_id": "TICKET-8842",
  "valid_until": "2026-07-20T23:59:59Z",
  "status": "expired"
}
```

The seed also includes an intentionally lossy generated summary:

> Customer has a 30-day refund exception.

It demonstrates a genuine memory-compression risk because it omits the original record's expiry and scope.

## 10. Control and Fault Scenarios

### Control scenario

Complete policy and exception metadata are available. The order is outside both the 14-day policy window and expired exception.

Expected result:

```json
{
  "outcome": "manual_review",
  "tool": "create_support_ticket"
}
```

No automatic refund is created.

### Fault-injection scenario

Retrieval returns the original exception and a generated summary, but context selection keeps only the concise summary. The model sees a 30-day exception without its expiration or scope and proposes an automatic refund.

Expected intermediate result:

```json
{
  "proposed_tool": "create_refund_request",
  "reason": "The customer has a 30-day exception."
}
```

The action pauses for human approval. Even if approved, the write tool revalidates the expired exception and rejects automatic approval, returning a manual-review outcome. This gives the application realistic defense-in-depth while keeping the faulty memory context reproducible.

## 11. Authentication and Tenant Isolation

Keycloak remains the user-facing identity provider.

1. The `/agent` page calls the existing `loginRequired()` flow.
2. The browser sends its Keycloak bearer token only to the existing backend.
3. The backend verifies the token and derives `tenant_id` and `actor_id`.
4. The backend proxy writes those values into the LangGraph run configuration.
5. Every business tool filters PostgreSQL queries by the injected tenant.
6. The LangGraph Agent Server is private to the Docker network and has no public port.

The frontend must never call the agent server directly in the first version.

## 12. LangSmith Use

LangSmith is enabled for agent development, tracing, evaluation, Studio, and future managed deployment.

Required environment variables:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=replace-with-your-secret
LANGSMITH_PROJECT=memguard-customer-support-baseline
```

For the first local version, the LangGraph Agent Server runs through `langgraph dev` and sends graph traces to the selected LangSmith project. The business database remains local in Docker Compose.

For a public staging or production deployment, use LangSmith Deployment or an appropriately licensed self-hosted Agent Server. Before deploying, move the business database to a managed PostgreSQL instance accessible from the deployment, configure secrets in the deployment environment, and verify tenant boundaries.

LangSmith is an explicit data-sharing dependency. Do not enable it with real customer data until the organization has reviewed the data-retention and privacy implications.

## 13. Docker Compose Services

The local stack contains:

```text
keycloak       User authentication
postgres       Business data and durable memory records
backend        Existing authenticated API and Agent Server proxy
agent-server   LangGraph application and DeepSeek integration
frontend       Existing Next.js dashboard with / and /agent
```

`agent-server` exposes port 2024 only inside the Compose network. The frontend exposes port 3001, Keycloak exposes port 8180, and the backend exposes port 8000 as today.

## 14. Configuration and Registration Checklist

Before first use, the operator must:

1. Create a DeepSeek account and API key.
2. Create a LangSmith account/workspace and API key.
3. Copy `.env.example` to `.env`.
4. Set `DEEPSEEK_API_KEY` and `LANGSMITH_API_KEY` in `.env`.
5. Leave `.env` untracked by Git.
6. Start Docker Compose.
7. Sign in through Keycloak.
8. Open `http://localhost:3001/agent`.

No API key is entered in the dashboard UI and no secret is added to a frontend `NEXT_PUBLIC_*` variable.

## 15. Error Handling

| Condition | Required behavior |
|---|---|
| DeepSeek key missing | Explain that server-side model configuration is required. |
| DeepSeek 401 or quota error | Show an actionable authentication or billing error without exposing the key. |
| DeepSeek timeout | Preserve the thread and offer Retry. |
| PostgreSQL unavailable | Do not fabricate customer or order data; show a temporary service error. |
| Customer or order absent | Ask for a valid identifier. |
| Stream interrupted | Reconnect to the existing thread and recover saved state. |
| Approval dismissed | Keep the request paused; never execute it automatically. |
| Duplicate approval | Use idempotency keys so a refund cannot be created twice. |
| Policy changes after proposal | Revalidate at execution and reject or redirect to manual review. |

## 16. Test Plan

### Backend and graph

- Unit-test every tool's tenant filtering and business validation.
- Test policy version selection by decision time.
- Test versioned memory writes instead of destructive overwrites.
- Test that read tools execute without interruption.
- Test that every write tool creates an interrupt.
- Test approve, edit, reject, reconnect, and duplicate-approval paths.
- Test that an expired exception blocks automatic refund after approval.
- Test that missing database records produce an explicit agent response.

### Frontend

- Test `/agent` requires Keycloak authentication.
- Test new-thread creation and existing-thread selection.
- Test streamed message rendering.
- Test read tool cards and pending-approval cards.
- Test approve, edit, and reject controls.
- Test a missing model-configuration message.
- Test that no DeepSeek or LangSmith key appears in browser output or built assets.

### End to end

- Start from a clean Docker Compose environment.
- Seed the canonical customer-support data.
- Ask the control question and verify manual-review behavior.
- Run the fault-injection question and verify that the agent proposes an action but the execution guard blocks invalid automatic approval.
- Verify a LangSmith trace appears when tracing is enabled.
- Verify one user cannot read or act on another tenant's data.

## 17. Acceptance Criteria

The baseline is complete when:

1. An authenticated user can have a multi-turn chat at `/agent`.
2. DeepSeek produces streamed, non-hard-coded replies.
3. The graph uses real LangGraph threads, tool calls, and interrupts.
4. Customer, order, policy, and support data comes from PostgreSQL.
5. Operators can modify the local business data and get different agent answers.
6. A business-changing action cannot execute without explicit approval.
7. Business validation can still reject an approved action when current data makes it invalid.
8. Thread history survives a browser reload.
9. Long-term memory updates are versioned and source-labelled.
10. LangSmith receives traces only when explicitly configured.
11. The application has no dependency on MemGuard telemetry or dashboard ingestion.
12. The user can run the local stack by configuring DeepSeek and LangSmith credentials, then starting Docker Compose.

## 18. Future Integration Boundary

Future observability integrations may observe, but must not alter, these ordinary application boundaries:

```text
retrieval -> context selection -> model call -> tool proposal
-> approval interrupt -> tool execution -> response -> memory write
```

The standalone baseline remains the authority for business behavior. Any later product integration is optional and must be removable without breaking chat, persistence, tools, approvals, or data integrity.
