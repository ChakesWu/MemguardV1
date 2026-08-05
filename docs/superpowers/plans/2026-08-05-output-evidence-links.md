# Output Evidence Links Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic, English-only links from exact answer segments to explicitly cited, prompt-eligible memories, with content-safe audit serialization.

**Architecture:** Keep the existing pre-generation trust, policy, and prompt-gate pipeline intact. Add immutable output-evidence contracts plus a focused `OutputEvidenceLinker` that validates Agent-provided citations against a `GovernanceRun`; expose it through `MemoryGovernanceEngine` and serialize it through the existing evidence report without inventing post-generation links.

**Tech Stack:** Python 3.9+, frozen dataclasses, enums, pytest, existing `memguard.governance` package.

## Global Constraints

- English output only; do not add multilingual tokenization or matching.
- Do not modify the customer-support Agent, backend, frontend, or Playground UI.
- Do not infer citations after generation; only validate explicit citations supplied by an Agent integration.
- A valid link must identify an exact answer segment, an exact evidence quote, and a memory included in the governed prompt.
- Blocked and quarantined memories must never produce valid links or leak content through audit output.
- Keep retrieval, trust, policy, influence, and output evidence as separate concepts.
- Preserve all existing public governance behavior and tests.

---

## File Structure

- Modify `sdk/memguard/governance/models.py`: define immutable output citation, validation, link, gap, and result contracts.
- Create `sdk/memguard/governance/output.py`: validate explicit citations and calculate uncovered answer ranges.
- Modify `sdk/memguard/governance/engine.py`: compose and expose the output linker without changing pre-generation behavior.
- Modify `sdk/memguard/governance/report.py`: serialize valid links, invalid citations, and gaps with existing redaction guarantees.
- Modify `sdk/memguard/governance/__init__.py`: export the new provider-neutral API.
- Modify `sdk/memguard/__init__.py`: expose the Agent-facing citation and result types from the SDK root.
- Create `tests/governance/test_output_evidence_linker.py`: focused validation and evidence-gap tests.
- Modify `tests/governance/test_governance_engine.py`: public API and end-to-end composition tests.
- Modify `tests/governance/test_evidence_report.py`: output-evidence serialization and redaction tests.

### Task 1: Output Evidence Contracts and Valid Link Path

**Files:**
- Modify: `sdk/memguard/governance/models.py`
- Create: `sdk/memguard/governance/output.py`
- Create: `tests/governance/test_output_evidence_linker.py`

**Interfaces:**
- Consumes: `GovernanceRun.by_id(memory_id)`, `PromptGateResult.included_memory_ids`, and existing `EvidenceEvaluation` fields.
- Produces: `OutputEvidenceRole`, `OutputCitation`, `ValidatedEvidenceLink`, `InvalidEvidenceCitation`, `EvidenceGap`, `OutputEvidenceResult`, and `OutputEvidenceLinker.link(run, answer, citations)`.

- [ ] **Step 1: Write a failing valid-link test**

Create a test helper that builds one allowed and one quarantined memory through the real engine, then add:

```python
def test_links_exact_answer_segment_to_prompt_included_memory():
    run = governance_run()
    answer = "Northstar renews in October."
    citation = OutputCitation(
        start_offset=0,
        end_offset=len(answer),
        segment=answer,
        memory_id="crm-104",
        evidence_quote="Renewal date: October",
        role=OutputEvidenceRole.FACTUAL_SUPPORT,
    )

    result = OutputEvidenceLinker().link(run, answer, (citation,))

    assert result.answer == answer
    assert result.invalid_citations == ()
    assert result.evidence_gaps == ()
    link = result.valid_links[0]
    assert link.memory_id == "crm-104"
    assert link.segment == answer
    assert link.link_method == "explicit_citation"
    assert link.validation_status == "valid"
    assert link.prompt_included is True
    assert link.trust.level is TrustLevel.HIGH
    assert link.policy.action is PolicyAction.ALLOW
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```bash
/Users/chakeswu/cursor/MemguardV1/myenv/bin/python -m pytest tests/governance/test_output_evidence_linker.py::test_links_exact_answer_segment_to_prompt_included_memory -q
```

Expected: collection or import failure because the output-evidence contracts and linker do not exist.

- [ ] **Step 3: Add immutable output-evidence contracts**

Add these shapes to `models.py`, using tuples for result collections and `OutputEvidenceRole(str, Enum)` for roles:

```python
class OutputEvidenceRole(str, Enum):
    FACTUAL_SUPPORT = "factual_support"
    CONSTRAINT = "constraint"
    PREFERENCE = "preference"
    BACKGROUND_CONTEXT = "background_context"


@dataclass(frozen=True)
class OutputCitation:
    start_offset: int
    end_offset: int
    segment: str
    memory_id: str
    evidence_quote: str
    role: OutputEvidenceRole | str


@dataclass(frozen=True)
class ValidatedEvidenceLink:
    start_offset: int
    end_offset: int
    segment: str
    memory_id: str
    evidence_quote: str
    role: OutputEvidenceRole
    retrieval: RetrievalSignals
    trust: TrustResult
    policy: PolicyDecision
    influence: InfluenceResult
    prompt_included: bool = True
    link_method: str = "explicit_citation"
    validation_status: str = "valid"


@dataclass(frozen=True)
class InvalidEvidenceCitation:
    start_offset: int
    end_offset: int
    segment: str
    memory_id: str
    role: str
    reason_codes: Tuple[str, ...]
    validation_status: str = "invalid"


@dataclass(frozen=True)
class EvidenceGap:
    start_offset: int
    end_offset: int
    segment: str


@dataclass(frozen=True)
class OutputEvidenceResult:
    answer: str
    valid_links: Tuple[ValidatedEvidenceLink, ...]
    invalid_citations: Tuple[InvalidEvidenceCitation, ...]
    evidence_gaps: Tuple[EvidenceGap, ...]
```

`InvalidEvidenceCitation` intentionally has no `evidence_quote` field so an invalid reference cannot retain secret input.

- [ ] **Step 4: Implement the minimal valid-link path**

Create `output.py` with a focused class. Use `TYPE_CHECKING` for `GovernanceRun` to avoid an engine import cycle:

```python
class OutputEvidenceLinker:
    def link(
        self,
        run: "GovernanceRun",
        answer: str,
        citations: Iterable[OutputCitation],
    ) -> OutputEvidenceResult:
        valid = []
        invalid = []
        for citation in citations:
            reasons = self._reason_codes(run, answer, citation)
            if reasons:
                invalid.append(self._invalid(citation, reasons))
                continue
            evaluation = run.by_id(citation.memory_id)
            valid.append(ValidatedEvidenceLink(
                start_offset=citation.start_offset,
                end_offset=citation.end_offset,
                segment=citation.segment,
                memory_id=citation.memory_id,
                evidence_quote=citation.evidence_quote,
                role=OutputEvidenceRole(citation.role),
                retrieval=evaluation.evidence.retrieval,
                trust=evaluation.trust,
                policy=evaluation.policy,
                influence=evaluation.influence,
            ))
        links = tuple(valid)
        return OutputEvidenceResult(answer, links, tuple(invalid), self._gaps(answer, links))
```

Implement `_reason_codes`, `_invalid`, and `_gaps` only far enough for the valid-path test; Task 2 fills every invalid branch and gap edge case.

- [ ] **Step 5: Run the focused test and verify it passes**

Run the command from Step 2. Expected: `1 passed`.

- [ ] **Step 6: Run existing governance tests for regression safety**

Run:

```bash
/Users/chakeswu/cursor/MemguardV1/myenv/bin/python -m pytest tests/governance -q
```

Expected: all governance tests pass.

- [ ] **Step 7: Commit Task 1**

```bash
git add sdk/memguard/governance/models.py sdk/memguard/governance/output.py tests/governance/test_output_evidence_linker.py
git commit -m "feat: add explicit output evidence links"
```

### Task 2: Invalid Citation Validation and Evidence Gaps

**Files:**
- Modify: `sdk/memguard/governance/output.py`
- Modify: `tests/governance/test_output_evidence_linker.py`

**Interfaces:**
- Consumes: Task 1 contracts and `OutputEvidenceLinker.link(...)`.
- Produces: stable validation reason codes and coalesced `EvidenceGap` ranges.

- [ ] **Step 1: Add failing validation tests**

Add parameterized cases that each assert the invalid citation is excluded from `valid_links`:

```python
@pytest.mark.parametrize(
    ("citation", "reason"),
    [
        (OutputCitation(-1, 4, "North", "crm-104", "Renewal date", "factual_support"), "segment:invalid_offsets"),
        (OutputCitation(0, 5, "South", "crm-104", "Renewal date", "factual_support"), "segment:mismatch"),
        (OutputCitation(0, 5, "North", "missing", "Renewal date", "factual_support"), "memory:unknown"),
        (OutputCitation(0, 5, "North", "secret", "token", "factual_support"), "policy:memory_not_eligible"),
        (OutputCitation(0, 5, "North", "crm-104", "not in memory", "factual_support"), "evidence:quote_not_found"),
        (OutputCitation(0, 5, "North", "crm-104", "Renewal date", "unsupported"), "role:unsupported"),
    ],
)
def test_rejects_invalid_citations(citation, reason):
    result = OutputEvidenceLinker().link(governance_run(), "North", (citation,))
    assert result.valid_links == ()
    assert reason in result.invalid_citations[0].reason_codes
    assert not hasattr(result.invalid_citations[0], "evidence_quote")
```

Add a separate fixture where a non-blocking evaluation is removed from `gate.included_memory_ids` to assert `memory:not_prompt_included`.

- [ ] **Step 2: Add failing multiplicity and gap tests**

Cover multiple memories for one segment, one memory for repeated segments, no citations, and partial coverage:

```python
def test_offsets_disambiguate_repeated_answer_text():
    answer = "Renew in October. Renew in October."
    second = answer.rindex("Renew")
    result = OutputEvidenceLinker().link(
        governance_run(),
        answer,
        (OutputCitation(second, len(answer), answer[second:], "crm-104", "Renewal date: October", "factual_support"),),
    )
    assert result.valid_links[0].start_offset == second
    assert result.evidence_gaps[0].segment == "Renew in October."


def test_uncited_answer_has_one_evidence_gap_and_no_link():
    result = OutputEvidenceLinker().link(governance_run(), "Unsupported answer.", ())
    assert result.valid_links == ()
    assert result.evidence_gaps == (EvidenceGap(0, 19, "Unsupported answer."),)
```

For multiple-memory support, submit two valid citations with identical offsets and different included memory IDs and assert both remain valid while the answer has no gap.

- [ ] **Step 3: Run the new test module and verify failures**

Run:

```bash
/Users/chakeswu/cursor/MemguardV1/myenv/bin/python -m pytest tests/governance/test_output_evidence_linker.py -q
```

Expected: the new invalid-branch and gap tests fail against Task 1's minimal implementation.

- [ ] **Step 4: Implement complete validation reason collection**

Implement validation in an order that never dereferences an unknown memory:

```python
def _reason_codes(self, run, answer, citation):
    reasons = []
    offsets_valid = 0 <= citation.start_offset < citation.end_offset <= len(answer)
    if not offsets_valid:
        reasons.append("segment:invalid_offsets")
    elif answer[citation.start_offset:citation.end_offset] != citation.segment:
        reasons.append("segment:mismatch")

    try:
        evaluation = run.by_id(citation.memory_id)
    except StopIteration:
        reasons.append("memory:unknown")
        evaluation = None

    if evaluation is not None:
        if evaluation.policy.action in {PolicyAction.BLOCK, PolicyAction.QUARANTINE}:
            reasons.append("policy:memory_not_eligible")
        elif citation.memory_id not in run.gate.included_memory_ids or not evaluation.influence.included_in_prompt:
            reasons.append("memory:not_prompt_included")
        if not citation.evidence_quote or not evaluation.evidence.content or citation.evidence_quote not in evaluation.evidence.content:
            reasons.append("evidence:quote_not_found")

    try:
        OutputEvidenceRole(citation.role)
    except ValueError:
        reasons.append("role:unsupported")
    return tuple(reasons)
```

- [ ] **Step 5: Implement coalesced evidence gaps**

Sort and merge valid link ranges, then emit uncovered trimmed slices only when they contain an alphanumeric character. This prevents whitespace and standalone punctuation from becoming fake gaps while preserving their absolute offsets:

```python
@staticmethod
def _gaps(answer, links):
    merged = []
    for start, end in sorted((link.start_offset, link.end_offset) for link in links):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    gaps = []
    cursor = 0
    for start, end in (*merged, (len(answer), len(answer))):
        raw_start, raw_end = cursor, start
        while raw_start < raw_end and answer[raw_start].isspace():
            raw_start += 1
        while raw_end > raw_start and answer[raw_end - 1].isspace():
            raw_end -= 1
        segment = answer[raw_start:raw_end]
        if any(character.isalnum() for character in segment):
            gaps.append(EvidenceGap(raw_start, raw_end, segment))
        cursor = max(cursor, end)
    return tuple(gaps)
```

- [ ] **Step 6: Run focused and governance suites**

Run:

```bash
/Users/chakeswu/cursor/MemguardV1/myenv/bin/python -m pytest tests/governance/test_output_evidence_linker.py tests/governance -q
```

Expected: all tests pass with no duplicate collection failures or regressions.

- [ ] **Step 7: Commit Task 2**

```bash
git add sdk/memguard/governance/output.py tests/governance/test_output_evidence_linker.py
git commit -m "feat: validate output evidence citations"
```

### Task 3: Engine API, Public Exports, and Content-Safe Reports

**Files:**
- Modify: `sdk/memguard/governance/engine.py`
- Modify: `sdk/memguard/governance/report.py`
- Modify: `sdk/memguard/governance/__init__.py`
- Modify: `sdk/memguard/__init__.py`
- Modify: `tests/governance/test_governance_engine.py`
- Modify: `tests/governance/test_evidence_report.py`

**Interfaces:**
- Consumes: `OutputEvidenceLinker.link(...)` and all Task 1 result contracts.
- Produces: `MemoryGovernanceEngine.link_output_evidence(...)`, root-package imports for Agent integrations, and `EvidenceReport.to_dict(output_evidence=...)`.

- [ ] **Step 1: Add a failing engine composition test**

```python
def test_engine_links_explicit_output_evidence():
    engine = MemoryGovernanceEngine(POLICY)
    run = engine.evaluate_and_build_prompt(
        "When does Northstar renew?",
        (item("crm-104", "Renewal date: October"),),
        CONTEXT,
    )
    answer = "Northstar renews in October."

    result = engine.link_output_evidence(
        run,
        answer=answer,
        citations=(OutputCitation(0, len(answer), answer, "crm-104", "Renewal date: October", "factual_support"),),
    )

    assert result.valid_links[0].memory_id == "crm-104"
    assert result.evidence_gaps == ()
```

Also assert `OutputCitation` and `OutputEvidenceResult` can be imported from both `memguard.governance` and `memguard`.

- [ ] **Step 2: Add failing report serialization tests**

Create a valid result for an allowed memory and assert:

```python
payload = run.report.to_dict(output_evidence=result)
assert payload["output_evidence"]["summary"] == {
    "valid_links": 1,
    "invalid_citations": 0,
    "evidence_gaps": 0,
}
assert payload["output_evidence"]["valid_links"][0]["evidence_quote"] == "Renewal date: October"
assert payload["output_evidence"]["valid_links"][0]["trust"]["level"] == "high"
```

Create a review-required restricted memory that enters the prompt, build a valid link to it, and assert the serialized `evidence_quote` is `[redacted]`. Submit an invalid citation containing a secret-looking quote and assert the raw quote is absent from `repr(result)` and the serialized report.

- [ ] **Step 3: Run focused tests and verify failures**

Run:

```bash
/Users/chakeswu/cursor/MemguardV1/myenv/bin/python -m pytest tests/governance/test_governance_engine.py tests/governance/test_evidence_report.py -q
```

Expected: failures because the engine method, public exports, and optional report output do not exist.

- [ ] **Step 4: Compose the linker in the engine**

Initialize `self.output_evidence_linker = OutputEvidenceLinker()` and add:

```python
def link_output_evidence(
    self,
    run: GovernanceRun,
    *,
    answer: str,
    citations: Iterable[OutputCitation],
) -> OutputEvidenceResult:
    return self.output_evidence_linker.link(run, answer, citations)
```

Do not alter `evaluate_and_build_prompt` or the prompt gate.

- [ ] **Step 5: Add content-safe optional output serialization**

Change `EvidenceReport.to_dict` to accept `output_evidence: OutputEvidenceResult | None = None`. Preserve the exact existing payload when it is omitted. When present, add an `output_evidence` object with summary counts, valid links, invalid citations, and gaps.

Serialize valid links using existing factor and policy shapes. Determine redaction from the report's memory item for that memory ID:

```python
memory_items = {item["memory_id"]: item for item in self.items}
memory_item = memory_items[link.memory_id]
quote = "[redacted]" if memory_item["content"] == "[redacted]" else link.evidence_quote
```

Serialize invalid citations from their content-safe fields only. Never serialize the original `OutputCitation` or its unvalidated quote.

- [ ] **Step 6: Export the public API**

Export `OutputCitation`, `OutputEvidenceResult`, `OutputEvidenceRole`, and `ValidatedEvidenceLink` from `memguard.governance`. Export `OutputCitation`, `OutputEvidenceResult`, and `OutputEvidenceRole` from the root `memguard` package for Agent integrations. Keep validation implementation details available only from `memguard.governance` unless tests require them directly.

- [ ] **Step 7: Run focused tests and verify they pass**

Run the command from Step 3. Expected: all focused tests pass.

- [ ] **Step 8: Run the complete relevant regression suite**

Run:

```bash
/Users/chakeswu/cursor/MemguardV1/myenv/bin/python -m pytest tests/governance tests/test_offboarding_memory_demo.py tests/test_memory_tracing.py tests/test_phase1a_contract.py tests/test_sdk_backend_integration.py tests/test_solo_validation_gate.py -q
```

Expected: all tests pass; only previously observed environment/deprecation warnings may remain.

- [ ] **Step 9: Verify package contents**

Build the SDK wheel and inspect that `memguard/governance/output.py` is included:

```bash
cd sdk
/Users/chakeswu/cursor/MemguardV1/myenv/bin/python -m build
/Users/chakeswu/cursor/MemguardV1/myenv/bin/python -c "import glob, zipfile; wheel=sorted(glob.glob('dist/memguard-*.whl'))[-1]; names=zipfile.ZipFile(wheel).namelist(); assert 'memguard/governance/output.py' in names; print(wheel)"
```

Expected: wheel build succeeds and the assertion passes.

- [ ] **Step 10: Commit Task 3**

```bash
git add sdk/memguard/governance/engine.py sdk/memguard/governance/report.py sdk/memguard/governance/__init__.py sdk/memguard/__init__.py tests/governance/test_governance_engine.py tests/governance/test_evidence_report.py
git commit -m "feat: expose auditable output evidence"
```

### Task 4: Final Contract Audit

**Files:**
- Modify only if verification exposes a defect in the files already listed.

**Interfaces:**
- Consumes: the completed public API and serialized evidence contract.
- Produces: fresh evidence that the approved acceptance criteria are met.

- [ ] **Step 1: Run static repository checks**

```bash
git diff --check
rg -n "final_score.*trust|trust.*final_score|post.?generation.*citation" sdk/memguard/governance tests/governance
```

Expected: no whitespace errors, no retrieval-score-as-trust mapping, and no automatic post-generation citation inference.

- [ ] **Step 2: Run the complete relevant regression suite again**

```bash
/Users/chakeswu/cursor/MemguardV1/myenv/bin/python -m pytest tests/governance tests/test_offboarding_memory_demo.py tests/test_memory_tracing.py tests/test_phase1a_contract.py tests/test_sdk_backend_integration.py tests/test_solo_validation_gate.py -q
```

Expected: all tests pass.

- [ ] **Step 3: Inspect the final diff and status**

```bash
git diff --stat HEAD~3..HEAD
git status --short --branch
```

Expected: only the planned core, tests, and approved specification/plan files changed; the pre-existing untracked `docs/handovers/` remains untouched.
