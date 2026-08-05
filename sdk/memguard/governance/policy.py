"""Deterministic policy decisions and hard safety overrides."""

from __future__ import annotations

from .models import (
    DataClassification,
    GovernanceContext,
    GovernancePolicy,
    MemoryEvidence,
    PolicyAction,
    PolicyDecision,
    TrustLevel,
    TrustResult,
)


class PolicyEngine:
    def __init__(self, policy: GovernancePolicy) -> None:
        self.policy = policy

    def decide(self, evidence: MemoryEvidence, context: GovernanceContext, trust: TrustResult) -> PolicyDecision:
        if evidence.data_classification is DataClassification.SECRET:
            return self._decision(PolicyAction.QUARANTINE, "classification:secret", "Secret material is isolated from agent context.")
        if evidence.data_classification is DataClassification.PRIVATE_EMPLOYEE:
            return self._decision(PolicyAction.BLOCK, "classification:private_employee", "Private employee data is not permitted in this agent context.")
        if evidence.tenant_id is None:
            return self._decision(PolicyAction.BLOCK, "tenant:missing", "Evidence without a tenant identity cannot enter an agent prompt.")
        if evidence.tenant_id != context.tenant_id:
            return self._decision(PolicyAction.BLOCK, "tenant:mismatch", "Cross-tenant evidence cannot enter an agent prompt.")
        if evidence.superseded_by_version_id:
            return self._decision(PolicyAction.BLOCK, "lifecycle:superseded", "A newer memory version supersedes this record.")
        if evidence.valid_until is not None and evidence.valid_until < context.evaluated_at:
            return self._decision(PolicyAction.BLOCK, "lifecycle:expired", "The memory is outside its validity period.")
        if trust.factors.policy_fit.score == 0:
            return self._decision(PolicyAction.BLOCK, "policy:purpose_not_allowed", "The memory is not allowed for the current purpose.")
        if evidence.data_classification is DataClassification.RESTRICTED:
            return self._decision(PolicyAction.REVIEW_REQUIRED, "classification:restricted", "Restricted data requires human approval before normal use.")
        if trust.level is TrustLevel.UNKNOWN:
            return self._decision(PolicyAction.REVIEW_REQUIRED, "metadata:insufficient", "Required governance metadata is missing.")
        if evidence.data_classification is DataClassification.UNKNOWN:
            return self._decision(PolicyAction.REVIEW_REQUIRED, "classification:unknown", "Data classification is required before normal use.")
        if trust.score is not None and trust.score >= self.policy.allow_threshold:
            return self._decision(PolicyAction.ALLOW, "trust:high", "Trust evidence meets the allow threshold.")
        if trust.score is not None and trust.score >= self.policy.warn_threshold:
            return self._decision(PolicyAction.WARN, "trust:medium", "Memory may be used with a visible trust warning.")
        if trust.score is not None and trust.score >= self.policy.review_threshold:
            return self._decision(PolicyAction.REVIEW_REQUIRED, "trust:low", "Memory requires human review.")
        return self._decision(PolicyAction.BLOCK, "trust:below_minimum", "Trust evidence is below the minimum permitted threshold.")

    @staticmethod
    def _decision(action: PolicyAction, reason: str, explanation: str) -> PolicyDecision:
        return PolicyDecision(
            action=action,
            enforced=action in {PolicyAction.BLOCK, PolicyAction.QUARANTINE},
            reason_codes=(reason,),
            explanation=explanation,
        )
