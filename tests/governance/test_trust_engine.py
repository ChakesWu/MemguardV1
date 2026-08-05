from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from memguard.governance import (
    ConflictStatus,
    GovernanceContext,
    GovernancePolicy,
    MemoryEvidence,
    TrustEngine,
    TrustLevel,
)


NOW = datetime(2026, 8, 5, tzinfo=timezone.utc)


def policy() -> GovernancePolicy:
    return GovernancePolicy(
        policy_id="memory-governance-v1",
        source_scores={"signed_policy": 100.0, "crm": 90.0, "agent_summary": 45.0},
        writer_scores={"policy-owner": 100.0, "support-agent": 50.0},
        max_age_days={"signed_policy": 300, "crm": 90, "agent_summary": 30},
    )


def trusted_evidence(**overrides) -> MemoryEvidence:
    values = {
        "memory_id": "memory-1",
        "tenant_id": "acme",
        "content": "The active refund window is fourteen days.",
        "source_type": "signed_policy",
        "source_id": "refund-policy-v2",
        "writer_id": "policy-owner",
        "created_at": NOW - timedelta(days=10),
        "verified_at": NOW - timedelta(days=5),
        "valid_until": NOW + timedelta(days=90),
        "conflict_status": ConflictStatus.NONE,
        "allowed_purposes": ("customer_support",),
    }
    values.update(overrides)
    return MemoryEvidence(**values)


def test_weighted_trust_score_has_explainable_factor_breakdown():
    result = TrustEngine(policy()).evaluate(
        trusted_evidence(),
        GovernanceContext(tenant_id="acme", agent_id="support", purpose="customer_support", evaluated_at=NOW),
    )

    assert result.score == pytest.approx(99.75)
    assert result.level is TrustLevel.HIGH
    assert result.factors.source.score == 100.0
    assert result.factors.writer.score == 100.0
    assert result.factors.freshness.score == pytest.approx(98.333333, rel=1e-5)
    assert result.factors.conflict.score == 100.0
    assert result.factors.policy_fit.score == 100.0
    assert "source:trusted" in result.reason_codes


def test_missing_required_metadata_is_unknown_not_an_invented_score():
    evidence = MemoryEvidence(
        memory_id="memory-unknown",
        tenant_id="acme",
        content="Customer prefers phone support.",
        source_type="unknown_source",
        created_at=NOW,
    )

    result = TrustEngine(policy()).evaluate(
        evidence,
        GovernanceContext(tenant_id="acme", agent_id="support", purpose="customer_support", evaluated_at=NOW),
    )

    assert result.score is None
    assert result.level is TrustLevel.UNKNOWN
    assert set(result.missing_factors) == {"source", "writer", "freshness", "conflict", "policy_fit"}


def test_factor_scores_are_always_bounded():
    with pytest.raises(ValueError, match="between 0 and 100"):
        GovernancePolicy(policy_id="bad", source_scores={"crm": 101.0})
