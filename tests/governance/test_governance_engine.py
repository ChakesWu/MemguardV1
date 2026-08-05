from __future__ import annotations

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
)
from memguard.governance.models import OutputCitation, OutputEvidenceResult


def test_engine_is_exposed_from_the_sdk_public_api():
    import memguard
    import memguard.governance

    assert memguard.MemoryGovernanceEngine is MemoryGovernanceEngine
    assert memguard.OutputCitation is OutputCitation
    assert memguard.OutputEvidenceResult is OutputEvidenceResult
    assert memguard.governance.OutputCitation is OutputCitation
    assert memguard.governance.OutputEvidenceResult is OutputEvidenceResult


NOW = datetime(2026, 8, 5, tzinfo=timezone.utc)
POLICY = GovernancePolicy(
    policy_id="governance-v1",
    source_scores={"signed_policy": 100, "employee_note": 80},
    writer_scores={"policy-owner": 100, "alex": 90},
    max_age_days={"signed_policy": 365, "employee_note": 90},
)
CONTEXT = GovernanceContext("acme", "support-agent", "customer_support", NOW)


def item(memory_id: str, content: str, **overrides) -> MemoryEvidence:
    values = {
        "memory_id": memory_id,
        "tenant_id": "acme",
        "content": content,
        "source_type": "signed_policy",
        "writer_id": "policy-owner",
        "created_at": NOW - timedelta(days=1),
        "verified_at": NOW - timedelta(days=1),
        "valid_until": NOW + timedelta(days=30),
        "conflict_status": ConflictStatus.NONE,
        "allowed_purposes": ("customer_support",),
        "data_classification": DataClassification.INTERNAL,
        "retrieval": RetrievalSignals(similarity=0.9, retrieved=True),
    }
    values.update(overrides)
    return MemoryEvidence(**values)


def test_engine_enforces_policy_before_constructing_prompt():
    memories = (
        item("policy", "Refunds use the active fourteen-day policy."),
        item("secret", "Production token: secret-token-value", data_classification=DataClassification.SECRET),
        item("private", "Alex private phone is 555-0108", data_classification=DataClassification.PRIVATE_EMPLOYEE),
    )

    run = MemoryGovernanceEngine(POLICY).evaluate_and_build_prompt("Can this order be refunded?", memories, CONTEXT)

    assert run.gate.included_memory_ids == ("policy",)
    assert run.gate.blocked_memory_ids == ("secret", "private")
    assert "fourteen-day policy" in run.gate.prompt
    assert "secret-token-value" not in run.gate.prompt
    assert "555-0108" not in run.gate.prompt
    assert run.by_id("secret").policy.action is PolicyAction.QUARANTINE
    assert run.by_id("private").policy.action is PolicyAction.BLOCK
    assert run.by_id("policy").influence.included_in_prompt is True
    assert run.by_id("secret").influence.included_in_prompt is False


def test_engine_blocks_cross_tenant_evidence_before_prompt():
    cross_tenant = item("foreign", "Another tenant's customer details", tenant_id="other")

    run = MemoryGovernanceEngine(POLICY).evaluate_and_build_prompt("Help customer", (cross_tenant,), CONTEXT)

    assert run.gate.included_memory_ids == ()
    assert run.gate.blocked_memory_ids == ("foreign",)
    assert "Another tenant" not in run.gate.prompt
    assert run.by_id("foreign").policy.reason_codes == ("tenant:mismatch",)


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


def test_engine_rejects_duplicate_memory_ids_before_building_a_run():
    duplicate_memories = (
        item("duplicate", "First memory value"),
        item("duplicate", "Second memory value"),
    )

    with pytest.raises(ValueError, match="duplicate memory_id"):
        MemoryGovernanceEngine(POLICY).evaluate_and_build_prompt(
            "Use governed memory",
            duplicate_memories,
            CONTEXT,
        )
