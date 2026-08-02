# Customer-Support Agent Design

**Status:** Approved by the user on 2026-08-02.

## Decision

Build the standalone customer-support agent described in [the baseline design](../../baselines/2026-08-02-standalone-agent-memory-baseline.md). It is a usable local application, not a dashboard mock.

## Chosen architecture

- Use the official LangGraph Agent Server protocol and graph ID `customer_support_agent`.
- Reuse and customize selected MIT-licensed components from LangChain's official Agent Chat UI.
- Add the customized chat experience at `/agent`; retain the evidence console at `/`.
- Use DeepSeek through `ChatDeepSeek`, defaulting to `deepseek-v4-flash`.
- Use LangGraph threads and interrupts for conversational persistence and approval-gated actions.
- Store operational business data and versioned memory in PostgreSQL.
- Keep the Agent Server private behind the existing Keycloak-authenticated backend proxy.
- Enable LangSmith for tracing, Studio, evaluation, and future managed deployment.

## Functional behavior

Read tools execute automatically. Refunds, tickets, order cancellation, and address changes pause the graph and show inline Approve, Edit, and Reject controls. The actual write tool revalidates live business data and idempotency before making any change.

The app supports both a correct policy-resolution scenario and a reproducible stale-memory scenario. The stale-memory scenario may lead the model to propose an invalid action, but the business guard must reject it after approval when its underlying exception has expired.

## Credentials required

- `DEEPSEEK_API_KEY`
- `LANGSMITH_API_KEY`

Both are server-side secrets in `.env`; neither may be committed or included in a browser-visible `NEXT_PUBLIC_*` variable.

## Deployment boundary

Docker Compose provides the first usable local environment. LangGraph's local server is used for development and testing; a public deployment will use LangSmith Deployment or an appropriately licensed self-hosted Agent Server only after the local acceptance tests pass.

## Test commitment

Implementation starts with failing tests for tool validation, interrupts, proxy tenant isolation, streaming UI states, and secret non-exposure. The full test and acceptance matrix is in the baseline design.
