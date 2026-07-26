# MemGuard Enterprise Roadmap

## Product goal

MemGuard is a horizontal enterprise platform for answering: “What memory,
retrieved context, and tool data were available when this AI agent produced
this output?” V1 presents evidence-backed lineage, not unvalidated causal
attribution.

FinCompli remains a demonstration and regression workload, not the product
boundary. LangGraph is the first automatic integration; explicit SDK hooks
cover retrieval and tool context.

## Phase 0 — Baseline

- Preserve the existing dirty worktree; never reset or overwrite user work.
- Ignore and untrack generated environments, databases, build artifacts and OS files without deleting local copies.
- Keep `frontend/` as the canonical product UI; archive `dashboard/` as a non-production mock.
- Establish repeatable Python/Node setup, tests, SDK packaging, frontend build and CI checks.

## Phase 1A — Truthful output-first MVP

Timebox: 5–7 solo working days.

- Repair the primary frontend build and the trace type contract.
- Remove mocked data from the production render path.
- Fix audit/session lookup and proper HTTP error responses.
- Use one evidence model containing output, linked memory reads, retrieval/tool context, timestamps, source/type, hash or permitted preview, and resulting writes.
- Ship one output-first view: select an output, inspect available evidence, and inspect resulting memory writes.
- Add a deterministic generic LangGraph demo and API/database-backed tests.

Do not build agent-first navigation, memory-first navigation, AWS, multi-region,
enterprise authentication, Postgres migration or new framework adapters here.

Acceptance: a clean local install runs the demo and displays only persisted,
linked evidence with no hard-coded decision values.

## Solo AI validation gate

Timebox: 2 days after Phase 1A.

- Exercise stale-memory, conflicting-memory, irrelevant-retrieval, missing-retrieval and untrusted-memory scenarios.
- Use adversarial AI review to identify unsupported claims, missing context and unclear debugging actions.
- Fix only P0/P1 truthfulness or usability defects.
- Record the product statement: “MemGuard is a memory-native evidence layer that helps AI teams inspect what memory and retrieved context were available when an agent produced an output.”

This validates technical truthfulness and usability, not market willingness to
switch. Future design-partner outreach is optional and non-blocking.

## Phase 1B — Feedback-driven expansion

Only build when Phase 1A or validation shows the need:

- agent-run-first debugging view;
- memory-first lifecycle view;
- memory version timeline, provenance, trust/policy status and conflict visualization;
- FinCompli Scenario 02 regression coverage.

## Phase 2 — Lean pilot platform

- PostgreSQL, migrations and basic backup/restore;
- Docker Compose deployment;
- basic OIDC, tenant isolation, restricted CORS and hash-only capture;
- bounded SDK queue, batching, retry and explicit flush;
- one LangGraph integration plus explicit generic retrieval/tool hooks.

Acceptance: one authenticated team can deploy and use MemGuard safely in a
controlled environment.

## Phase 3 — Enterprise scale and memory security

Only after a pilot or strong external interest:

- shared SaaS with logical tenant isolation;
- dedicated AWS deployment option;
- RBAC, encryption, redaction, retention, key rotation and access audits;
- immutable evidence, replay/dead-letter handling, monitoring, infrastructure-as-code and disaster recovery;
- source trust, suspicious-memory quarantine, tamper evidence and policy violations.


