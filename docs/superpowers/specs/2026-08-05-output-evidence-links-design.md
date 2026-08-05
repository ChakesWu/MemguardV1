# Output Evidence Links Design

## Goal

Add provider-neutral, English-only output evidence links to the MemGuard governance core. A valid link records that an agent explicitly associated an exact answer segment with one or more governed memories during generation. MemGuard validates the recorded association and exposes it for audit and later UI rendering.

The feature explains evidence lineage. It does not claim access to hidden model reasoning or prove model-internal causality.

## Scope

- Preserve the existing trust, policy, prompt-gate, and evidence-report behavior.
- Add explicit answer-segment-to-memory links after prompt governance.
- Validate links deterministically without post-generation citation guessing.
- Attach retrieval, trust, policy, and prompt-inclusion evidence to each valid link.
- Keep invalid citations and evidence gaps auditable but non-renderable.
- Support English output only in this milestone.

The visualization, Playground API, customer-support Agent integration, and multilingual matching are outside this milestone.

## Runtime flow

```text
memories
  -> trust and policy evaluation
  -> prompt gate
  -> governed prompt with eligible memory IDs
  -> agent returns answer plus explicit citations
  -> output evidence linker validates citations
  -> valid evidence links plus invalid-citation audit records
```

The governance engine remains provider-neutral and does not call an LLM. An Agent integration is responsible for requesting and parsing structured citations from its model provider.

## Public API

The existing pre-generation call remains compatible:

```python
governance_run = engine.evaluate_and_build_prompt(
    user_input,
    memories,
    governance_context,
)
```

The engine gains a post-generation call:

```python
output_evidence = engine.link_output_evidence(
    governance_run,
    answer=answer,
    citations=citations,
)
```

No automatic text-matching fallback creates citations when the Agent did not record one.

## Contracts

### `OutputCitation`

An Agent-provided citation contains:

- `start_offset`: inclusive character offset in the final answer;
- `end_offset`: exclusive character offset in the final answer;
- `segment`: the exact answer substring at those offsets;
- `memory_id`: the cited memory;
- `evidence_quote`: an exact substring of the cited memory content;
- `role`: one of `factual_support`, `constraint`, `preference`, or `background_context`.

Multiple citations may target the same answer segment, and one memory may support multiple segments.

### `ValidatedEvidenceLink`

A valid link contains the citation fields plus:

- `link_method = explicit_citation`;
- the memory's retrieval evidence;
- trust score, level, factor breakdown, and reason codes;
- policy action, explanation, and reason codes;
- prompt-inclusion state;
- `validation_status = valid`.

Only valid links are eligible for later inline-index rendering.

### `InvalidEvidenceCitation`

An invalid citation retains content-safe identifiers, offsets, role, validation status, and reason codes. It must not retain a restricted or ineligible raw memory value or evidence quote.

### `OutputEvidenceResult`

The result contains:

- the final answer;
- valid links;
- invalid citations;
- evidence gaps;
- summary counts and reason codes.

## Deterministic validation

The linker validates every citation independently and returns all applicable reason codes:

1. Offsets are non-negative, ordered, and within the answer.
2. `answer[start_offset:end_offset]` exactly equals `segment`.
3. `memory_id` exists in the supplied `GovernanceRun`.
4. The memory is present in `gate.included_memory_ids` and has `included_in_prompt = true`.
5. The memory's policy action is not `block` or `quarantine`.
6. `evidence_quote` is a non-empty exact substring of the governed memory content.
7. `role` is a supported enum value.

Validation proves that the recorded segment, evidence quote, and governed memory are internally consistent. It does not claim semantic entailment or hidden causality.

## Failure handling

Stable reason codes include:

- `segment:invalid_offsets`
- `segment:mismatch`
- `memory:unknown`
- `memory:not_prompt_included`
- `policy:memory_not_eligible`
- `evidence:quote_not_found`
- `role:unsupported`

Invalid citations never appear in `valid_links`. They remain in the content-safe audit result. An answer without citations remains available but produces no links. Evidence gaps are the coalesced, non-whitespace character ranges not covered by any valid link; punctuation adjacent to covered text stays with that covered segment. Gaps must not receive invented UI indices.

If a citation references blocked or quarantined evidence, the invalid audit record contains only permitted identifiers, hashes, policy metadata, and reason codes. Raw governed content and the submitted evidence quote are redacted.

## Explanation model

MemGuard keeps four concepts separate:

- Retrieval explains why a memory was selected as a candidate.
- Trust explains whether its source, writer, freshness, conflict state, and policy fit are reliable enough for the current context.
- Policy explains whether it was allowed to enter the prompt.
- Output evidence identifies the exact answer segment and source quote explicitly linked during generation.

Retrieval score is never represented as trust. A high trust score cannot override a blocking policy action.

## Evidence report integration

The existing report gains an output-evidence section without changing its current memory evaluation items. The section includes valid links, invalid citations, evidence gaps, and counts. Existing report redaction rules apply to all new fields.

The report builder receives the output-evidence result explicitly. Pre-generation reports remain supported when no output evidence exists.

## Testing

Unit tests cover:

- one memory supporting one segment;
- multiple memories supporting one segment;
- one memory supporting multiple segments;
- repeated answer text disambiguated by offsets;
- invalid, reversed, and out-of-range offsets;
- segment mismatch;
- unknown memory ID;
- memory not included in the prompt;
- blocked and quarantined memory references;
- evidence quote absent from memory content;
- unsupported roles;
- uncited answer spans producing evidence gaps;
- invalid citations excluded from renderable links;
- restricted fields redacted in invalid-citation reports;
- existing governance APIs and tests remaining compatible.

Integration tests run a deterministic English answer with structured citations through trust evaluation, policy enforcement, prompt construction, link validation, and report serialization. They prove that every renderable link refers to an included memory and that no blocked or quarantined memory can produce a renderable link.

## Acceptance criteria

- Existing governance behavior and tests remain unchanged.
- Each valid link identifies one exact answer segment, one governed memory, and one exact evidence quote.
- Every valid link is backed by a memory included in the governed prompt.
- Invalid or missing citations never create renderable links.
- Blocked and quarantined memory content remains excluded and redacted.
- Trust, retrieval, policy, and output evidence remain separate in both contracts and reports.
- The implementation makes no hidden-causality claim and performs no post-generation citation inference.
