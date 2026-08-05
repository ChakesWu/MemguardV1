"""Explainable, deterministic trust evaluation."""

from __future__ import annotations

from dataclasses import fields

from .models import (
    ConflictStatus,
    GovernanceContext,
    GovernancePolicy,
    MemoryEvidence,
    TrustFactor,
    TrustFactors,
    TrustLevel,
    TrustResult,
)


class TrustEngine:
    WEIGHTS = {
        "source": 0.30,
        "writer": 0.20,
        "freshness": 0.15,
        "conflict": 0.20,
        "policy_fit": 0.15,
    }
    CONFLICT_SCORES = {
        ConflictStatus.NONE: 100.0,
        ConflictStatus.LOW: 70.0,
        ConflictStatus.MEDIUM: 40.0,
        ConflictStatus.HIGH: 0.0,
    }

    def __init__(self, policy: GovernancePolicy) -> None:
        self.policy = policy

    def evaluate(self, evidence: MemoryEvidence, context: GovernanceContext) -> TrustResult:
        factors = TrustFactors(
            source=self._source(evidence),
            writer=self._writer(evidence),
            freshness=self._freshness(evidence, context),
            conflict=self._conflict(evidence),
            policy_fit=self._policy_fit(evidence, context),
        )
        factor_values = {item.name: getattr(factors, item.name).score for item in fields(factors)}
        missing = tuple(name for name, score in factor_values.items() if score is None)
        reasons = self._reason_codes(factors)
        if missing:
            return TrustResult(None, TrustLevel.UNKNOWN, factors, reasons, missing)

        score = round(sum(float(factor_values[name]) * weight for name, weight in self.WEIGHTS.items()), 6)
        if score >= self.policy.allow_threshold:
            level = TrustLevel.HIGH
        elif score >= self.policy.warn_threshold:
            level = TrustLevel.MEDIUM
        else:
            level = TrustLevel.LOW
        return TrustResult(score, level, factors, reasons, ())

    def _source(self, evidence: MemoryEvidence) -> TrustFactor:
        if not evidence.source_type or evidence.source_type not in self.policy.source_scores:
            return TrustFactor()
        score = float(self.policy.source_scores[evidence.source_type])
        return TrustFactor(score, f"source type {evidence.source_type!r} has configured authority")

    def _writer(self, evidence: MemoryEvidence) -> TrustFactor:
        if not evidence.writer_id or evidence.writer_id not in self.policy.writer_scores:
            return TrustFactor()
        score = float(self.policy.writer_scores[evidence.writer_id])
        return TrustFactor(score, f"writer {evidence.writer_id!r} has configured authority")

    def _freshness(self, evidence: MemoryEvidence, context: GovernanceContext) -> TrustFactor:
        if evidence.superseded_by_version_id:
            return TrustFactor(0.0, f"superseded by {evidence.superseded_by_version_id}")
        if evidence.valid_until is not None and evidence.valid_until < context.evaluated_at:
            return TrustFactor(0.0, "memory validity period has expired")
        if not evidence.source_type or evidence.source_type not in self.policy.max_age_days:
            return TrustFactor()
        reference = evidence.verified_at or evidence.created_at
        if reference is None:
            return TrustFactor()
        age_days = max(0.0, (context.evaluated_at - reference).total_seconds() / 86400)
        max_age = float(self.policy.max_age_days[evidence.source_type])
        score = max(0.0, 100.0 * (1.0 - age_days / max_age))
        return TrustFactor(score, f"last verified {age_days:.1f} days ago; maximum age is {max_age:.0f} days")

    def _conflict(self, evidence: MemoryEvidence) -> TrustFactor:
        if evidence.conflict_status is ConflictStatus.UNKNOWN:
            return TrustFactor()
        score = self.CONFLICT_SCORES[evidence.conflict_status]
        return TrustFactor(score, f"conflict status is {evidence.conflict_status.value}")

    @staticmethod
    def _policy_fit(evidence: MemoryEvidence, context: GovernanceContext) -> TrustFactor:
        if evidence.allowed_purposes is None:
            return TrustFactor()
        allowed = context.purpose in evidence.allowed_purposes
        return TrustFactor(100.0 if allowed else 0.0, f"purpose {context.purpose!r} is {'allowed' if allowed else 'not allowed'}")

    @staticmethod
    def _reason_codes(factors: TrustFactors) -> tuple[str, ...]:
        reasons = []
        if factors.source.score is not None:
            reasons.append("source:trusted" if factors.source.score >= 80 else "source:limited")
        if factors.writer.score is not None:
            reasons.append("writer:trusted" if factors.writer.score >= 80 else "writer:limited")
        if factors.freshness.score is not None:
            reasons.append("freshness:current" if factors.freshness.score >= 60 else "freshness:stale")
        if factors.conflict.score is not None:
            reasons.append("conflict:none" if factors.conflict.score == 100 else "conflict:detected")
        if factors.policy_fit.score is not None:
            reasons.append("policy:fit" if factors.policy_fit.score == 100 else "policy:not_fit")
        return tuple(reasons)
