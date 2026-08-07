# MemGuard customer-support demo handoff

## Repository, worktree, and branch

- Repository: `https://github.com/ChakesWu/MemguardV1`
- Demo worktree: `/Users/chakeswu/cursor/MemguardV1/.worktrees/customer-support-memguard-evidence`
- Branch: `codex/customer-support-memguard-evidence`
- Latest feature commit: `bf7e5f5` (`fix: persist streamed evidence and retry providers`)

Do all demo work from this worktree. The original baseline remains separate and should not be used for this demo.

## What this demo is

The demo layers **MemGuard governed memory evidence** onto the customer-support agent. It is not a generic tracing UI: it explains, for each customer-facing answer, which trusted records and policies supported the answer and why that information was permitted in the prompt.

Main routes after starting Docker Compose:

- `http://localhost:3001/agent` — customer-support conversation with evidence chips, hover cards, and full-evidence side panel.
- `http://localhost:3001/` — Evidence Console showing persisted memory events and decision traces from governed outputs.

## MemGuard core used by the demo

The core path is:

1. `agent-server/support_agent/output_evidence_report.py` builds a governed output-evidence report from the actual support order metadata and policy result.
2. `backend/app/agent_proxy.py` adds the governed context to the agent request, reads the final `memguard_output_evidence` report from the LangGraph stream, and persists canonical memory-read events plus a decision trace.
3. `frontend/components/agent/OutputEvidence.ts` renders per-output evidence chips and the hover summary.
4. `frontend/components/agent/EvidenceDetailPanel.ts` opens the full same-page evidence side panel.
5. `backend/app/main.py` exposes the persisted records to the Evidence Console.

The support order record is the memory source. Its source type, source ID, writer, update/verification timestamps, and conflict state are stored in `agent-server/support_agent/domain.py`, migrations, repository, and seed data. The displayed trust score is computed from that metadata and policy result; it is not a static 100% UI value.

## Implemented behavior

- Each relevant final agent output gets one or more evidence chips such as `support order`.
- Hovering a chip shows its role in the output, trust score/band, policy decision, source, and whether it was included in the prompt.
- **Open full evidence** opens a persistent same-page side panel, so it remains usable after the pointer leaves the chip.
- The side panel exposes why the selected memory was used: source provenance, writer, freshness, conflict status, policy decision, and prompt inclusion.
- The agent persists governed memory-read events and decision traces, which populate the Evidence Console after a successful chat response.
- Actual transient DeepSeek stream failures (`RemoteProtocolError`, connection/read timeouts) are retried automatically up to three attempts before reporting an error.
- Refund flows retain their existing guardrail: an out-of-window defective-item request becomes a manual-review request; the agent does not promise a refund.

## Running and testing

From this worktree, start the stack with the API key available to the same shell that launches Docker:

```bash
export DEEPSEEK_API_KEY='...'
docker compose -p customer-support-memguard-evidence up -d --build
```

Then:

1. Open `/agent` and submit: `I need a refund for ORD-4821 because the item is defective.`
2. Wait for the final support-agent response. Hover the `support order` evidence chip, then select **Open full evidence**.
3. Open `/` to inspect the memory-read events and decision trace emitted for that response.

If the agent server reports `DEEPSEEK_API_KEY is required`, the key was exported in a different terminal process. Export it again in the terminal that runs the Docker command.
