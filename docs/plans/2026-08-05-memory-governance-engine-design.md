# Memory Governance Engine Design

## Goal

Build MemGuard as an independent governance layer that can inspect memory evidence, calculate explainable trust, enforce policy before prompt construction, and emit an auditable report. The existing customer-support agent remains an unchanged baseline and is used only through an external adapter and tests.

## Runtime boundary

```text
memory provider -> evidence adapter -> governance engine -> prompt gate -> agent
                                           |
                                           +-> evidence report
```

The prompt gate is mandatory. Memories receiving `block` or `quarantine` never enter the model prompt. `allow` and `warn` may enter. `review_required` may enter in the first milestone but must be visibly marked for review. All decisions remain present in the evidence report, including blocked records, while sensitive content is represented by a hash or permitted preview.

## Core contracts

`MemoryEvidence` is provider-neutral and carries identity, content/hash, source, writer, timestamps, version lineage, conflicts, retrieval signals, prompt inclusion, and policy context. Missing governance metadata remains missing; the engine must not silently substitute a positive score.

`GovernanceContext` describes the actor, tenant, agent, purpose, risk level, requested action, and evaluation time.

`InfluenceResult` explains whether evidence was retrieved, offered to the model, cited or supported by output, and its bounded influence score. Retrieval relevance is evidence of availability, not proof of model causality.

`TrustResult` contains optional factor scores for source, writer, freshness, conflict, and policy fit. When required metadata is insufficient, its level is `unknown`, numeric score is absent, and the default policy action is `review_required`.

`PolicyDecision` contains an action, reason codes, human-readable explanation, and enforcement flag. Initial actions are `allow`, `warn`, `review_required`, `block`, and `quarantine`. Offboarding lifecycle actions such as `transfer`, `delete`, and `do_not_transfer` are policy outcomes built on the same contract, not hard-coded into the trust calculator.

`EvidenceReport` joins the input evidence, factor breakdown, influence result, policy decision, enforcement result, and content-safe audit representation.

## Trust calculation

When all required factors are known:

```text
trust_score =
  source_score * 0.30
+ writer_score * 0.20
+ freshness_score * 0.15
+ conflict_score * 0.20
+ policy_fit_score * 0.15
```

Scores use a 0–100 scale and include reason codes. Thresholds are policy configuration, not embedded in provider adapters. Critical policy violations can override a high numeric score and force `block` or `quarantine`.

## WideMem integration

WideMem remains a separable Apache-2.0 dependency or adapter. Its similarity, importance, recency, retrieval confidence, and conflict signals may populate evidence fields. Its retrieval `final_score` must never be relabeled as MemGuard trust: WideMem itself documents that retrieval strength is not answer correctness.

## Baseline integration

The customer-support baseline code is not edited. A test-side adapter maps its existing `MemoryRecord` fields into `MemoryEvidence`. Tests construct the prompt through MemGuard's gate and verify that blocked or quarantined records are absent, allowed records remain, and the report contains both groups.

The employee-offboarding scenario is the first acceptance fixture. It demonstrates that transferable company knowledge survives while private, secret, stale, conflicting, or policy-incompatible memory is blocked, quarantined, archived, or queued for review with explicit evidence.

## Safety properties

- Deterministic policy has final authority; an LLM cannot independently allow restricted memory.
- Unknown metadata never becomes an invented trust score.
- Trust, retrieval relevance, and influence are separate concepts.
- Enforcement happens before prompt construction.
- Reports redact restricted content while retaining identifiers, hashes, reasons, and lineage.
- Every result is tenant-scoped and reproducible for a fixed evaluation time and policy version.

## First milestone acceptance

- Pure unit tests cover factor weighting, unknown metadata, critical overrides, and every initial action.
- Prompt-gate tests prove `block` and `quarantine` content is absent.
- WideMem adapter tests prove retrieval score remains distinct from trust.
- Customer baseline objects can be evaluated without changes to baseline modules.
- Offboarding acceptance tests produce a content-safe report with allowed, blocked, quarantined, and review-required evidence.
