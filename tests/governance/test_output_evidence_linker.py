from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from memguard.governance import (
    ConflictStatus,
    DataClassification,
    GovernanceContext,
    GovernancePolicy,
    MemoryEvidence,
    MemoryGovernanceEngine,
    PolicyAction,
    RetrievalSignals,
    TrustLevel,
)
from memguard.governance.models import EvidenceGap, OutputCitation, OutputEvidenceRole
from memguard.governance.output import OutputEvidenceLinker


NOW = datetime(2026, 8, 5, tzinfo=timezone.utc)


def governance_run(*, include_second_allowed: bool = False):
    policy = GovernancePolicy(
        policy_id="governance-v1",
        source_scores={"crm": 100},
        writer_scores={"crm-sync": 100},
        max_age_days={"crm": 365},
    )
    context = GovernanceContext("acme", "support-agent", "customer_support", NOW)
    allowed = MemoryEvidence(
        memory_id="crm-104",
        tenant_id="acme",
        content="Renewal date: October",
        source_type="crm",
        writer_id="crm-sync",
        created_at=NOW - timedelta(days=1),
        verified_at=NOW - timedelta(days=1),
        valid_until=NOW + timedelta(days=30),
        conflict_status=ConflictStatus.NONE,
        allowed_purposes=("customer_support",),
        data_classification=DataClassification.INTERNAL,
        retrieval=RetrievalSignals(similarity=0.9, retrieved=True),
    )
    quarantined = MemoryEvidence(
        memory_id="secret-1",
        tenant_id="acme",
        content="Production token: secret-token-value",
        source_type="crm",
        writer_id="crm-sync",
        data_classification=DataClassification.SECRET,
        retrieval=RetrievalSignals(similarity=0.9, retrieved=True),
    )
    blocked = MemoryEvidence(
        memory_id="private-1",
        tenant_id="acme",
        content="Employee phone: 555-0108",
        source_type="crm",
        writer_id="crm-sync",
        data_classification=DataClassification.PRIVATE_EMPLOYEE,
        retrieval=RetrievalSignals(similarity=0.9, retrieved=True),
    )
    memories = [allowed, quarantined, blocked]
    if include_second_allowed:
        memories.append(replace(allowed, memory_id="crm-105"))
    return MemoryGovernanceEngine(policy).evaluate_and_build_prompt(
        "When does Northstar renew?", memories, context
    )


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


@pytest.mark.parametrize(
    ("citation", "reason"),
    [
        (OutputCitation(-1, 5, "North", "crm-104", "Renewal date", "factual_support"), "segment:invalid_offsets"),
        (OutputCitation(0, 5, "South", "crm-104", "Renewal date", "factual_support"), "segment:mismatch"),
        (OutputCitation(0, 5, "North", "missing", "Renewal date", "factual_support"), "memory:unknown"),
        (OutputCitation(0, 5, "North", "secret-1", "secret-token-value", "factual_support"), "policy:memory_not_eligible"),
        (OutputCitation(0, 5, "North", "private-1", "555-0108", "factual_support"), "policy:memory_not_eligible"),
        (OutputCitation(0, 5, "North", "crm-104", "not in memory", "factual_support"), "evidence:quote_not_found"),
        (OutputCitation(0, 5, "North", "crm-104", "Renewal date", "unsupported"), "role:unsupported"),
    ],
)
def test_rejects_citations_that_are_not_safe_evidence_links(citation, reason):
    result = OutputEvidenceLinker().link(governance_run(), "North", (citation,))

    assert result.valid_links == ()
    assert reason in result.invalid_citations[0].reason_codes
    assert not hasattr(result.invalid_citations[0], "evidence_quote")


def test_rejects_memory_that_was_not_included_in_the_prompt():
    run = governance_run()
    run = replace(run, gate=replace(run.gate, included_memory_ids=()))
    citation = OutputCitation(0, 5, "North", "crm-104", "Renewal date", "factual_support")

    result = OutputEvidenceLinker().link(run, "North", (citation,))

    assert result.valid_links == ()
    assert result.invalid_citations[0].reason_codes == ("memory:not_prompt_included",)


def test_offsets_disambiguate_repeated_answer_text():
    answer = "Renew in October. Renew in October."
    second = answer.rindex("Renew")

    result = OutputEvidenceLinker().link(
        governance_run(),
        answer,
        (
            OutputCitation(
                second,
                len(answer),
                answer[second:],
                "crm-104",
                "Renewal date: October",
                "factual_support",
            ),
        ),
    )

    assert result.valid_links[0].start_offset == second
    assert result.evidence_gaps == (EvidenceGap(0, 17, "Renew in October."),)


def test_multiple_memories_can_support_the_same_answer_segment():
    answer = "North"
    result = OutputEvidenceLinker().link(
        governance_run(include_second_allowed=True),
        answer,
        (
            OutputCitation(0, 5, answer, "crm-104", "Renewal date: October", "factual_support"),
            OutputCitation(0, 5, answer, "crm-105", "Renewal date: October", "factual_support"),
        ),
    )

    assert tuple(link.memory_id for link in result.valid_links) == ("crm-104", "crm-105")
    assert result.evidence_gaps == ()


def test_one_memory_can_support_multiple_answer_segments():
    answer = "North renews in October. North is covered."
    first_end = answer.index(".") + 1
    second_start = answer.index("North", first_end)

    result = OutputEvidenceLinker().link(
        governance_run(),
        answer,
        (
            OutputCitation(0, first_end, answer[:first_end], "crm-104", "Renewal date: October", "factual_support"),
            OutputCitation(second_start, len(answer), answer[second_start:], "crm-104", "Renewal date: October", "background_context"),
        ),
    )

    assert tuple(link.memory_id for link in result.valid_links) == ("crm-104", "crm-104")
    assert result.evidence_gaps == ()


@pytest.mark.parametrize(
    "citation",
    [
        OutputCitation(5, 0, "North", "crm-104", "Renewal date", "factual_support"),
        OutputCitation(0, 6, "North", "crm-104", "Renewal date", "factual_support"),
    ],
)
def test_rejects_reversed_and_beyond_answer_offsets(citation):
    result = OutputEvidenceLinker().link(governance_run(), "North", (citation,))

    assert result.valid_links == ()
    assert result.invalid_citations[0].reason_codes == ("segment:invalid_offsets",)


@pytest.mark.parametrize(
    ("memory_id", "known_quote"),
    [
        ("secret-1", "secret-token-value"),
        ("private-1", "555-0108"),
    ],
)
def test_blocked_policy_validation_does_not_reveal_quote_membership(memory_id, known_quote):
    present = OutputCitation(0, 5, "North", memory_id, known_quote, "factual_support")
    absent = replace(present, evidence_quote="wrong guess")

    present_result = OutputEvidenceLinker().link(governance_run(), "North", (present,))
    absent_result = OutputEvidenceLinker().link(governance_run(), "North", (absent,))

    assert present_result.invalid_citations == absent_result.invalid_citations
    assert present_result.invalid_citations[0].reason_codes == ("policy:memory_not_eligible",)


def test_invalid_audit_fields_are_reconstructed_only_from_validated_values():
    submitted_values = (
        "submitted secret segment",
        "submitted-secret-memory-id",
        "submitted-secret-role",
    )
    citation = OutputCitation(
        0,
        5,
        submitted_values[0],
        submitted_values[1],
        "submitted secret quote",
        submitted_values[2],
    )

    result = OutputEvidenceLinker().link(governance_run(), "North", (citation,))
    invalid = result.invalid_citations[0]

    assert invalid.start_offset == 0
    assert invalid.end_offset == 5
    assert invalid.segment is None
    assert invalid.memory_id == "[unknown]"
    assert invalid.role is None
    assert all(value not in repr(result) for value in submitted_values)
    assert "submitted secret quote" not in repr(result)


def test_invalid_audit_retains_only_normalized_fields_that_were_validated():
    result = OutputEvidenceLinker().link(
        governance_run(),
        "North",
        (OutputCitation(0, 5, "North", "crm-104", "wrong quote", OutputEvidenceRole.FACTUAL_SUPPORT),),
    )

    invalid = result.invalid_citations[0]
    assert invalid.segment == "North"
    assert invalid.memory_id == "crm-104"
    assert invalid.role == "factual_support"


def test_result_contains_summary_counts_and_aggregate_reason_codes():
    result = OutputEvidenceLinker().link(
        governance_run(),
        "North south",
        (
            OutputCitation(0, 5, "North", "crm-104", "Renewal date", "factual_support"),
            OutputCitation(6, 11, "south", "missing", "guess", "unsupported"),
        ),
    )

    assert result.summary == {
        "valid_links": 1,
        "invalid_citations": 1,
        "evidence_gaps": 1,
    }
    assert result.reason_codes == ("memory:unknown", "role:unsupported")


def test_uncited_answer_has_one_evidence_gap_and_no_link():
    result = OutputEvidenceLinker().link(governance_run(), "Unsupported answer.", ())

    assert result.valid_links == ()
    assert result.evidence_gaps == (EvidenceGap(0, 19, "Unsupported answer."),)


def test_partial_citation_leaves_the_remaining_words_as_an_evidence_gap():
    answer = "North needs renewal details."
    result = OutputEvidenceLinker().link(
        governance_run(),
        (answer),
        (OutputCitation(0, 5, "North", "crm-104", "Renewal date: October", "factual_support"),),
    )

    assert result.evidence_gaps == (EvidenceGap(6, 28, "needs renewal details."),)


def test_evidence_gap_excludes_punctuation_adjacent_to_a_covered_segment():
    answer = "North, south"
    result = OutputEvidenceLinker().link(
        governance_run(),
        answer,
        (OutputCitation(0, 5, "North", "crm-104", "Renewal date", "factual_support"),),
    )

    assert result.evidence_gaps == (EvidenceGap(7, 12, "south"),)
