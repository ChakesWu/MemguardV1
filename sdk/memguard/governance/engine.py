"""Composition root for trust, policy, influence, prompt gating, and reporting."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, Tuple

from .gate import PromptGate
from .influence import InfluenceEngine
from .models import (
    EvidenceEvaluation,
    GovernanceContext,
    GovernancePolicy,
    MemoryEvidence,
    OutputCitation,
    OutputEvidenceResult,
    PolicyAction,
    PromptGateResult,
)
from .output import OutputEvidenceLinker
from .policy import PolicyEngine
from .report import EvidenceReport, EvidenceReportBuilder
from .trust import TrustEngine


@dataclass(frozen=True)
class GovernanceRun:
    evaluations: Tuple[EvidenceEvaluation, ...]
    gate: PromptGateResult
    report: EvidenceReport

    def __post_init__(self) -> None:
        memory_ids = [item.evidence.memory_id for item in self.evaluations]
        if len(memory_ids) != len(set(memory_ids)):
            raise ValueError("duplicate memory_id values are not allowed in a governance run")

    def by_id(self, memory_id: str) -> EvidenceEvaluation:
        return next(item for item in self.evaluations if item.evidence.memory_id == memory_id)


class MemoryGovernanceEngine:
    def __init__(self, policy: GovernancePolicy, *, capture_allowed_content: bool = False) -> None:
        self.policy = policy
        self.trust_engine = TrustEngine(policy)
        self.policy_engine = PolicyEngine(policy)
        self.influence_engine = InfluenceEngine()
        self.prompt_gate = PromptGate()
        self.report_builder = EvidenceReportBuilder(capture_allowed_content)
        self.output_evidence_linker = OutputEvidenceLinker()

    def evaluate_and_build_prompt(
        self,
        user_input: str,
        memories: Iterable[MemoryEvidence],
        context: GovernanceContext,
        *,
        output_text: str | None = None,
    ) -> GovernanceRun:
        memories = tuple(memories)
        memory_ids = [memory.memory_id for memory in memories]
        if len(memory_ids) != len(set(memory_ids)):
            raise ValueError("duplicate memory_id values are not allowed in a governance run")

        evaluations = []
        for original in memories:
            trust = self.trust_engine.evaluate(original, context)
            decision = self.policy_engine.decide(original, context, trust)
            included = decision.action not in {PolicyAction.BLOCK, PolicyAction.QUARANTINE} and original.content is not None
            governed = replace(original, retrieval=replace(original.retrieval, included_in_prompt=included))
            influence = self.influence_engine.evaluate(governed, output_text)
            evaluations.append(EvidenceEvaluation(governed, trust, decision, influence))

        items = tuple(evaluations)
        gate = self.prompt_gate.build(user_input, items)
        report = self.report_builder.build(self.policy.policy_id, context.tenant_id, context.evaluated_at, items)
        return GovernanceRun(items, gate, report)

    def link_output_evidence(
        self,
        run: GovernanceRun,
        *,
        answer: str,
        citations: Iterable[OutputCitation],
    ) -> OutputEvidenceResult:
        return self.output_evidence_linker.link(run, answer, citations)
