from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from memguard.governance import (
    ConflictStatus,
    DataClassification,
    GovernanceContext,
    GovernancePolicy,
    MemoryEvidence,
    PolicyAction,
    PolicyEngine,
    TrustEngine,
)


NOW = datetime(2026, 8, 5, tzinfo=timezone.utc)
CONTEXT = GovernanceContext("acme", "agent-1", "customer_support", NOW)
POLICY = GovernancePolicy(
    policy_id="governance-v1",
    source_scores={"policy": 100, "crm": 90, "agent": 45},
    writer_scores={"owner": 100, "agent-1": 50},
    max_age_days={"policy": 365, "crm": 90, "agent": 30},
)


def evidence(**overrides) -> MemoryEvidence:
    values = {
        "memory_id": "m1",
        "tenant_id": "acme",
        "content": "Verified company information.",
        "source_type": "policy",
        "writer_id": "owner",
        "created_at": NOW - timedelta(days=1),
        "verified_at": NOW - timedelta(days=1),
        "valid_until": NOW + timedelta(days=30),
        "conflict_status": ConflictStatus.NONE,
        "allowed_purposes": ("customer_support",),
        "data_classification": DataClassification.INTERNAL,
    }
    values.update(overrides)
    return MemoryEvidence(**values)


@pytest.mark.parametrize(
    ("item", "expected", "reason"),
    [
        (evidence(), PolicyAction.ALLOW, "trust:high"),
        (
            evidence(source_type="crm", writer_id="agent-1", verified_at=NOW - timedelta(days=60)),
            PolicyAction.WARN,
            "trust:medium",
        ),
        (
            MemoryEvidence(memory_id="unknown", tenant_id="acme", content="Unverified note", source_type="unknown"),
            PolicyAction.REVIEW_REQUIRED,
            "metadata:insufficient",
        ),
        (
            evidence(valid_until=NOW - timedelta(seconds=1)),
            PolicyAction.BLOCK,
            "lifecycle:expired",
        ),
        (
            evidence(data_classification=DataClassification.SECRET),
            PolicyAction.QUARANTINE,
            "classification:secret",
        ),
        (
            evidence(data_classification=DataClassification.RESTRICTED),
            PolicyAction.REVIEW_REQUIRED,
            "classification:restricted",
        ),
    ],
)
def test_policy_actions_are_deterministic(item, expected, reason):
    trust = TrustEngine(POLICY).evaluate(item, CONTEXT)
    decision = PolicyEngine(POLICY).decide(item, CONTEXT, trust)

    assert decision.action is expected
    assert reason in decision.reason_codes
    assert decision.enforced is (expected in {PolicyAction.BLOCK, PolicyAction.QUARANTINE})


def test_private_employee_data_is_blocked_even_with_high_trust():
    item = evidence(data_classification=DataClassification.PRIVATE_EMPLOYEE)
    trust = TrustEngine(POLICY).evaluate(item, CONTEXT)

    assert trust.score > 95
    decision = PolicyEngine(POLICY).decide(item, CONTEXT, trust)
    assert decision.action is PolicyAction.BLOCK
    assert "classification:private_employee" in decision.reason_codes


def test_memory_not_allowed_for_current_purpose_is_blocked():
    item = evidence(allowed_purposes=("sales",))
    trust = TrustEngine(POLICY).evaluate(item, CONTEXT)

    assert trust.factors.policy_fit.score == 0
    decision = PolicyEngine(POLICY).decide(item, CONTEXT, trust)
    assert decision.action is PolicyAction.BLOCK
    assert "policy:purpose_not_allowed" in decision.reason_codes


def test_restricted_data_cannot_bypass_expiration_block():
    item = evidence(
        data_classification=DataClassification.RESTRICTED,
        valid_until=NOW - timedelta(seconds=1),
    )
    trust = TrustEngine(POLICY).evaluate(item, CONTEXT)

    decision = PolicyEngine(POLICY).decide(item, CONTEXT, trust)
    assert decision.action is PolicyAction.BLOCK
    assert "lifecycle:expired" in decision.reason_codes


@pytest.mark.parametrize("tenant_id", [None, "another-tenant"])
def test_missing_or_cross_tenant_evidence_is_blocked(tenant_id):
    item = evidence(tenant_id=tenant_id)
    trust = TrustEngine(POLICY).evaluate(item, CONTEXT)

    decision = PolicyEngine(POLICY).decide(item, CONTEXT, trust)
    assert decision.action is PolicyAction.BLOCK
    assert decision.enforced is True
    assert decision.reason_codes[0].startswith("tenant:")


def test_missing_classification_requires_review_instead_of_default_allow():
    item = evidence(data_classification=DataClassification.UNKNOWN)
    trust = TrustEngine(POLICY).evaluate(item, CONTEXT)

    assert trust.level.value == "high"
    decision = PolicyEngine(POLICY).decide(item, CONTEXT, trust)
    assert decision.action is PolicyAction.REVIEW_REQUIRED
    assert "classification:unknown" in decision.reason_codes
