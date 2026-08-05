from __future__ import annotations

from datetime import datetime, timezone

from memguard.governance import (
    EvidenceEvaluation,
    InfluenceResult,
    MemoryEvidence,
    PolicyAction,
    PolicyDecision,
    PromptGate,
    TrustFactors,
    TrustLevel,
    TrustResult,
)


def evaluation(memory_id: str, content: str, action: PolicyAction) -> EvidenceEvaluation:
    memory = MemoryEvidence(memory_id=memory_id, tenant_id="acme", content=content, source_type="test")
    trust = TrustResult(None, TrustLevel.UNKNOWN, TrustFactors(), (), ())
    decision = PolicyDecision(action, action in {PolicyAction.BLOCK, PolicyAction.QUARANTINE}, (f"test:{action.value}",), "test")
    influence = InfluenceResult(memory_id, 0.0, True, False, False, False, ())
    return EvidenceEvaluation(memory, trust, decision, influence)


def test_blocked_and_quarantined_memory_never_enters_prompt():
    evaluations = (
        evaluation("allow", "Allowed company policy", PolicyAction.ALLOW),
        evaluation("warn", "Warning-tagged context", PolicyAction.WARN),
        evaluation("review", "Review-tagged context", PolicyAction.REVIEW_REQUIRED),
        evaluation("block", "PRIVATE PHONE 555-0108", PolicyAction.BLOCK),
        evaluation("quarantine", "SECRET TOKEN abc123", PolicyAction.QUARANTINE),
    )

    result = PromptGate().build("Answer the customer", evaluations)

    assert "Allowed company policy" in result.prompt
    assert "Warning-tagged context" in result.prompt
    assert "Review-tagged context" in result.prompt
    assert "PRIVATE PHONE 555-0108" not in result.prompt
    assert "SECRET TOKEN abc123" not in result.prompt
    assert result.included_memory_ids == ("allow", "warn", "review")
    assert result.blocked_memory_ids == ("block", "quarantine")
