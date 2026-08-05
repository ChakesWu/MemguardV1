# Output Evidence Links Final Fix Report

## Status

PASS. Every Critical, Important, and named Minor finding in `final-findings.md` is addressed in the governance SDK and covered by regression tests. Provider neutrality, English-only behavior, explicit-citation-only linking, and existing pre-generation report payloads are preserved. No backend, frontend, customer-support, or `docs/handovers/` file was changed.

## Files

- `sdk/memguard/governance/engine.py`
- `sdk/memguard/governance/models.py`
- `sdk/memguard/governance/output.py`
- `sdk/memguard/governance/report.py`
- `tests/governance/test_output_evidence_linker.py`
- `tests/governance/test_governance_engine.py`
- `tests/governance/test_evidence_report.py`
- `.superpowers/sdd/2026-08-05-output-evidence-links/final-fix-report.md`

The pre-existing untracked `docs/handovers/2026-08-05-memguard-session-handoff.md` remains untouched and untracked.

## Security design decisions

1. Default report output uses the same capture decision as memory content. A valid quote is emitted as `[hash-only]` in default mode, `[redacted]` for restricted content, and raw only when `capture_allowed_content=True`.
2. `block` and `quarantine` are terminal for content-dependent citation checks. The linker emits `policy:memory_not_eligible` without checking whether the submitted quote occurs in governed content, so present and absent guesses have identical audit results.
3. Invalid citations retain only normalized fields. Offsets are normalized to integers or `-1`; a segment is reconstructed from the final answer only after valid offsets and an exact match; an existing run memory ID is reconstructed from the evaluation or becomes `[unknown]`; a supported role is normalized to its enum value or becomes `None`; the submitted quote is never retained.
4. Every `EvidenceReport` receives an opaque UUID provenance value before output linking. `OutputEvidenceResult` receives that provenance from its run, and report serialization raises `ValueError` on a mismatch before reading link mappings.
5. Duplicate memory IDs are rejected before trust, policy, prompt, or report construction. `GovernanceRun.__post_init__` also enforces the invariant for directly constructed runs.
6. Evidence gaps consume boundary punctuation adjacent to a covered segment while retaining correct absolute offsets. `North, south` with `North` covered now yields gap `EvidenceGap(7, 12, "south")`.
7. `OutputEvidenceResult` now carries summary counts and stable, de-duplicated aggregate reason codes. One memory may still support multiple answer segments, and no citation inference or provider-specific behavior was added.

## Commit

- Subject: `fix: secure output evidence reporting`
- Final hash: reported by `git log -1 --format=%H` after this report is committed. A commit cannot embed its own final object hash because changing this file changes that hash.
- Base before fix: `9ae1974245b40da7e6d8d8b7cb88d285dfba3b3f`

## TDD evidence

### Baseline

Command:

```text
/Users/chakeswu/cursor/MemguardV1/myenv/bin/python -m pytest tests/governance/test_output_evidence_linker.py tests/governance/test_governance_engine.py tests/governance/test_evidence_report.py -q
```

Output:

```text
/Users/chakeswu/cursor/MemguardV1/myenv/lib/python3.9/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
......................                                                   [100%]
22 passed in 0.10s
```

Exit: `0`.

### RED

All new security and missing-contract tests were added before production changes.

Command:

```text
/Users/chakeswu/cursor/MemguardV1/myenv/bin/python -m pytest tests/governance/test_output_evidence_linker.py tests/governance/test_governance_engine.py tests/governance/test_evidence_report.py -q
```

Output:

```text
/Users/chakeswu/cursor/MemguardV1/myenv/lib/python3.9/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
..............FFFF..F....F..F...F                                        [100%]
=================================== FAILURES ===================================
_______ test_blocked_policy_validation_does_not_reveal_quote_membership ________
E       AssertionError: present quote produced ('policy:memory_not_eligible',), absent quote produced ('policy:memory_not_eligible', 'evidence:quote_not_found')
____ test_invalid_audit_fields_are_reconstructed_only_from_validated_values ____
E       AssertionError: assert 'submitted secret segment' is None
____ test_invalid_audit_retains_only_normalized_fields_that_were_validated _____
E       AssertionError: assert 'OutputEvidenceRole.FACTUAL_SUPPORT' == 'factual_support'
________ test_result_contains_summary_counts_and_aggregate_reason_codes ________
E       AttributeError: 'OutputEvidenceResult' object has no attribute 'summary'
_____ test_evidence_gap_excludes_punctuation_adjacent_to_a_covered_segment _____
E       AssertionError: EvidenceGap(start_offset=5, end_offset=12, segment=', south') != EvidenceGap(start_offset=7, end_offset=12, segment='south')
_____ test_engine_rejects_duplicate_memory_ids_before_building_a_run ________
E       Failed: DID NOT RAISE <class 'ValueError'>
______ test_default_hash_only_report_does_not_serialize_raw_output_quote _______
E       AssertionError: assert 'Renewal date: October' == '[hash-only]'
_____ test_report_rejects_output_evidence_from_a_different_governance_run ______
E       Failed: DID NOT RAISE <class 'ValueError'>
=========================== short test summary info ============================
FAILED tests/governance/test_output_evidence_linker.py::test_blocked_policy_validation_does_not_reveal_quote_membership
FAILED tests/governance/test_output_evidence_linker.py::test_invalid_audit_fields_are_reconstructed_only_from_validated_values
FAILED tests/governance/test_output_evidence_linker.py::test_invalid_audit_retains_only_normalized_fields_that_were_validated
FAILED tests/governance/test_output_evidence_linker.py::test_result_contains_summary_counts_and_aggregate_reason_codes
FAILED tests/governance/test_output_evidence_linker.py::test_evidence_gap_excludes_punctuation_adjacent_to_a_covered_segment
FAILED tests/governance/test_governance_engine.py::test_engine_rejects_duplicate_memory_ids_before_building_a_run
FAILED tests/governance/test_evidence_report.py::test_default_hash_only_report_does_not_serialize_raw_output_quote
FAILED tests/governance/test_evidence_report.py::test_report_rejects_output_evidence_from_a_different_governance_run
8 failed, 25 passed in 0.13s
```

Exit: `1`, with every failure caused by a missing required behavior.

### GREEN

Command:

```text
/Users/chakeswu/cursor/MemguardV1/myenv/bin/python -m pytest tests/governance/test_output_evidence_linker.py tests/governance/test_governance_engine.py tests/governance/test_evidence_report.py -q
```

Output after the final security cases (both block and quarantine oracle resistance plus report-level invalid-field sanitization) were included:

```text
/Users/chakeswu/cursor/MemguardV1/myenv/lib/python3.9/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
...................................                                      [100%]
35 passed in 0.10s
```

Exit: `0`.

### Governance regression

Command:

```text
/Users/chakeswu/cursor/MemguardV1/myenv/bin/python -m pytest tests/governance -q
```

Output:

```text
/Users/chakeswu/cursor/MemguardV1/myenv/lib/python3.9/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
.......................................................                  [100%]
55 passed in 0.13s
```

Exit: `0`.

## Full relevant regression output

Command from the approved implementation plan:

```text
/Users/chakeswu/cursor/MemguardV1/myenv/bin/python -m pytest tests/governance tests/test_offboarding_memory_demo.py tests/test_memory_tracing.py tests/test_phase1a_contract.py tests/test_sdk_backend_integration.py tests/test_solo_validation_gate.py -q
```

Output:

```text
/Users/chakeswu/cursor/MemguardV1/myenv/lib/python3.9/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
........................................................................ [ 87%]
..........                                                               [100%]
=============================== warnings summary ===============================
<frozen importlib._bootstrap>:228
  <frozen importlib._bootstrap>:228: DeprecationWarning: builtin type SwigPyPacked has no __module__ attribute

<frozen importlib._bootstrap>:228
  <frozen importlib._bootstrap>:228: DeprecationWarning: builtin type SwigPyObject has no __module__ attribute

<frozen importlib._bootstrap>:228
  <frozen importlib._bootstrap>:228: DeprecationWarning: builtin type swigvarlink has no __module__ attribute

tests/test_sdk_backend_integration.py::test_basic_integration
  /Users/chakeswu/cursor/MemguardV1/myenv/lib/python3.9/site-packages/_pytest/python.py:161: PytestReturnNotNoneWarning: Test functions should return None, but tests/test_sdk_backend_integration.py::test_basic_integration returned <class 'bool'>.
  Did you mean to use `assert` instead of `return`?
  See https://docs.pytest.org/en/stable/how-to/assert.html#return-not-none for more information.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
82 passed, 4 warnings in 2.50s
```

Exit: `0`.

## Package verification

First isolated build attempt was blocked by sandbox DNS while trying to install `wheel`; no code/test failure occurred. The required retry with dependency-download approval succeeded.

Command:

```text
cd sdk
/Users/chakeswu/cursor/MemguardV1/myenv/bin/python -m build
```

Outcome: exit `0`; `Successfully built memguard-0.1.0.tar.gz and memguard-0.1.0-py3-none-any.whl`.

Command:

```text
/Users/chakeswu/cursor/MemguardV1/myenv/bin/python -c "import glob, zipfile; wheel=sorted(glob.glob('dist/memguard-*.whl'))[-1]; names=zipfile.ZipFile(wheel).namelist(); assert 'memguard/governance/output.py' in names; print(wheel)"
```

Output:

```text
dist/memguard-0.1.0-py3-none-any.whl
```

Exit: `0`.

## Git diff check and scope audit

Command:

```text
git diff --check
```

Output: no output. Exit: `0`.

Command:

```text
rg -n "final_score.*trust|trust.*final_score|post.?generation.*citation" sdk/memguard/governance tests/governance
```

Output: no matches. Exit: `1` (expected for no matches).

Changed implementation/test paths from `git diff --name-only` before adding this report:

```text
sdk/memguard/governance/engine.py
sdk/memguard/governance/models.py
sdk/memguard/governance/output.py
sdk/memguard/governance/report.py
tests/governance/test_evidence_report.py
tests/governance/test_governance_engine.py
tests/governance/test_output_evidence_linker.py
```

`git status --short --branch` showed only those seven tracked modifications plus the preserved pre-existing `?? docs/handovers/` entry. Build artifacts remained ignored.

## Concerns

- The suite emits a pre-existing urllib3 LibreSSL warning, three SWIG deprecation warnings, and one `PytestReturnNotNoneWarning` in `tests/test_sdk_backend_integration.py`; none is caused by this change.
- The first isolated package build could not resolve PyPI inside the sandbox. The approved retry succeeded and the wheel-content assertion passed.
- No unresolved implementation or security concern remains within the approved scope.
