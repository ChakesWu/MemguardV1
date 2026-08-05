from __future__ import annotations

from datetime import datetime, timedelta, timezone

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
from memguard.governance.models import OutputCitation, OutputEvidenceRole
from memguard.governance.output import OutputEvidenceLinker


NOW = datetime(2026, 8, 5, tzinfo=timezone.utc)


def governance_run():
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
    return MemoryGovernanceEngine(policy).evaluate_and_build_prompt(
        "When does Northstar renew?", (allowed, quarantined), context
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
