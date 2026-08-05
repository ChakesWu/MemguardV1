# Memory Governance Engine Implementation Plan

**Goal:** Deliver a provider-neutral MemGuard governance SDK that calculates explainable trust, applies deterministic policy, blocks unsafe memories before prompt construction, and emits content-safe evidence reports without modifying the customer-support baseline.

**Architecture:** Add a `memguard.governance` package made of immutable contracts and pure engines. `MemoryGovernanceEngine` composes influence, trust, policy, gate, and report behavior. Provider adapters only map retrieval signals into the common evidence contract; they never decide trust.

**Tech stack:** Python 3.9+, dataclasses/enums, hashlib, pytest, existing MemGuard SDK packaging.

---

## Task 1: Governance contracts and trust calculation

**Files:**
- Create: `sdk/memguard/governance/models.py`
- Create: `sdk/memguard/governance/trust.py`
- Test: `tests/governance/test_trust_engine.py`

Write failing tests for the approved five-factor weighted score, deterministic levels, bounded inputs, factor explanations, and `unknown` when required metadata is absent. Implement the smallest immutable models and calculator needed to pass them.

## Task 2: Deterministic policy and critical overrides

**Files:**
- Create: `sdk/memguard/governance/policy.py`
- Test: `tests/governance/test_policy_engine.py`

Write failing tests for `allow`, `warn`, `review_required`, `block`, and `quarantine`. Prove critical flags such as secret material, private employee data, invalid purpose, and explicit quarantine override numeric trust. Implement configurable thresholds and reason codes.

## Task 3: Evidence-backed influence

**Files:**
- Create: `sdk/memguard/governance/influence.py`
- Test: `tests/governance/test_influence_engine.py`

Write failing tests that distinguish retrieved, prompt-included, cited, and output-supported evidence. Implement a bounded evidence score without claiming model-causal attribution.

## Task 4: Prompt enforcement and evidence reporting

**Files:**
- Create: `sdk/memguard/governance/gate.py`
- Create: `sdk/memguard/governance/report.py`
- Test: `tests/governance/test_prompt_gate.py`
- Test: `tests/governance/test_evidence_report.py`

Write failing tests proving blocked and quarantined contents never appear in the prompt, while decisions remain in a redacted report with IDs, hashes, factor breakdowns, reasons, and policy version. Implement the gate and serializer.

## Task 5: Composed public engine

**Files:**
- Create: `sdk/memguard/governance/engine.py`
- Create: `sdk/memguard/governance/__init__.py`
- Modify: `sdk/memguard/__init__.py`
- Modify: `sdk/pyproject.toml`
- Test: `tests/governance/test_governance_engine.py`

Write a failing end-to-end unit test for evaluating a batch and constructing a safe prompt. Compose the four engines, expose the public API, and include the new package in SDK builds.

## Task 6: WideMem signal adapter

**Files:**
- Create: `sdk/memguard/governance/adapters/__init__.py`
- Create: `sdk/memguard/governance/adapters/widemem.py`
- Test: `tests/governance/test_widemem_adapter.py`

Use structural input rather than importing or copying WideMem internals. Test that similarity, importance, recency, retrieval confidence, and conflict hints map into evidence signals while WideMem `final_score` stays labeled retrieval score and never populates trust.

## Task 7: Independent offboarding acceptance fixture

**Files:**
- Modify: `examples/offboarding_memory_demo.py`
- Modify: `tests/test_offboarding_memory_demo.py`

Refactor the existing isolated prototype to call the public Governance Engine. Add acceptance assertions for actual prompt exclusion and content-safe reports. Do not import or modify customer-support baseline modules.

## Verification

Run focused governance tests first, then the existing SDK and relevant regression suite. Verify the customer-support worktree has no tracked changes caused by this implementation. Commit only intended files and push `codex/offboarding-memory-demo`.
