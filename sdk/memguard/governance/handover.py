"""Ownership-aware, policy-enforced transfer of agent memory during employee offboarding."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping, Tuple

from .engine import MemoryGovernanceEngine
from .models import EvidenceEvaluation, GovernanceContext, GovernancePolicy, MemoryEvidence, PolicyAction


class MemoryOwner(str, Enum):
    """Who may control a memory after an employee leaves."""

    COMPANY_SYSTEM = "company_system"
    COMPANY = "company"
    TEAM = "team"
    EMPLOYEE = "employee"


class TransferPolicy(str, Enum):
    """The declared lifecycle rule for a memory record."""

    SOURCE_OF_TRUTH = "source_of_truth"
    TRANSFER_IF_ALLOWED = "transfer_if_allowed"
    PROTECT = "protect"
    REDACT_AND_REVIEW = "redact_and_review"


class HandoverOutcome(str, Enum):
    RETAINED_AT_SOURCE = "retained_at_source"
    TRANSFERRED = "transferred"
    PROTECTED = "protected"
    REDACTED_FOR_REVIEW = "redacted_for_review"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class HandoverMemory:
    """A governed record plus the ownership terms needed for transfer."""

    evidence: MemoryEvidence
    owner: MemoryOwner
    transfer_policy: TransferPolicy
    business_owner: str
    source_label: str
    redacted_content: str | None = None


@dataclass(frozen=True)
class HandoverItem:
    memory: HandoverMemory
    evaluation: EvidenceEvaluation
    outcome: HandoverOutcome
    reason: str

    @property
    def redacted_content(self) -> str | None:
        return self.memory.redacted_content


@dataclass(frozen=True)
class HandoverReport:
    """An auditable manifest for a successor agent's memory boundary."""

    items: Tuple[HandoverItem, ...]
    successor_prompt: str

    def by_id(self, memory_id: str) -> HandoverItem:
        return next(item for item in self.items if item.memory.evidence.memory_id == memory_id)

    @property
    def source_of_truth_ids(self) -> Tuple[str, ...]:
        return tuple(
            item.memory.evidence.memory_id
            for item in self.items
            if item.outcome is HandoverOutcome.RETAINED_AT_SOURCE
        )

    @property
    def successor_memory_ids(self) -> Tuple[str, ...]:
        return tuple(
            item.memory.evidence.memory_id
            for item in self.items
            if item.outcome is HandoverOutcome.TRANSFERRED
        )

    def summary(self) -> Mapping[str, int]:
        return {
            "source_of_truth": len(self.source_of_truth_ids),
            "transferred": sum(item.outcome is HandoverOutcome.TRANSFERRED for item in self.items),
            "protected": sum(item.outcome is HandoverOutcome.PROTECTED for item in self.items),
            "redacted_for_review": sum(item.outcome is HandoverOutcome.REDACTED_FOR_REVIEW for item in self.items),
            "archived": sum(item.outcome is HandoverOutcome.ARCHIVED for item in self.items),
        }

    def to_dict(self) -> dict:
        return {
            "summary": dict(self.summary()),
            "source_of_truth_ids": list(self.source_of_truth_ids),
            "successor_memory_ids": list(self.successor_memory_ids),
            "successor_prompt": self.successor_prompt,
            "items": [
                {
                    "memory_id": item.memory.evidence.memory_id,
                    "content": self._display_content(item),
                    "redacted_content": item.redacted_content,
                    "owner": item.memory.owner.value,
                    "transfer_policy": item.memory.transfer_policy.value,
                    "business_owner": item.memory.business_owner,
                    "source_label": item.memory.source_label,
                    "source_id": item.memory.evidence.source_id,
                    "classification": item.memory.evidence.data_classification.value,
                    "outcome": item.outcome.value,
                    "reason": item.reason,
                    "trust": {
                        "score": item.evaluation.trust.score,
                        "level": item.evaluation.trust.level.value,
                        "reason_codes": list(item.evaluation.trust.reason_codes),
                    },
                    "policy": {
                        "action": item.evaluation.policy.action.value,
                        "reason_codes": list(item.evaluation.policy.reason_codes),
                        "explanation": item.evaluation.policy.explanation,
                    },
                    "eligible_for_successor": item.outcome is HandoverOutcome.TRANSFERRED,
                }
                for item in self.items
            ],
        }

    @staticmethod
    def _display_content(item: HandoverItem) -> str:
        if item.outcome is HandoverOutcome.PROTECTED:
            return item.redacted_content or "[protected employee memory]"
        if item.outcome is HandoverOutcome.REDACTED_FOR_REVIEW:
            return item.redacted_content or "[redacted pending review]"
        return item.memory.evidence.content or "[content unavailable]"


class HandoverEngine:
    """Apply MemGuard governance before company memory enters a successor agent."""

    def __init__(self, policy: GovernancePolicy) -> None:
        self.governance = MemoryGovernanceEngine(policy)

    def prepare(
        self,
        memories: Iterable[HandoverMemory],
        context: GovernanceContext,
    ) -> HandoverReport:
        records = tuple(memories)
        run = self.governance.evaluate_and_build_prompt(
            "Prepare a governed employee-agent handover.",
            (record.evidence for record in records),
            context,
        )
        evaluations = {evaluation.evidence.memory_id: evaluation for evaluation in run.evaluations}
        items = tuple(
            self._item(record, evaluations[record.evidence.memory_id])
            for record in records
        )
        return HandoverReport(items=items, successor_prompt=self._successor_prompt(items))

    @staticmethod
    def _item(memory: HandoverMemory, evaluation: EvidenceEvaluation) -> HandoverItem:
        reasons = set(evaluation.policy.reason_codes)
        if memory.transfer_policy is TransferPolicy.SOURCE_OF_TRUTH:
            return HandoverItem(memory, evaluation, HandoverOutcome.RETAINED_AT_SOURCE, "Company source of truth remains read-only; it is not copied into an employee handover.")
        if memory.transfer_policy is TransferPolicy.PROTECT or memory.owner is MemoryOwner.EMPLOYEE:
            return HandoverItem(memory, evaluation, HandoverOutcome.PROTECTED, "Employee-owned memory is protected and never enters the successor agent.")
        if memory.transfer_policy is TransferPolicy.REDACT_AND_REVIEW:
            return HandoverItem(memory, evaluation, HandoverOutcome.REDACTED_FOR_REVIEW, "Mixed memory is redacted before human review; the original is not transferred.")
        if any(reason.startswith("lifecycle:") for reason in reasons):
            return HandoverItem(memory, evaluation, HandoverOutcome.ARCHIVED, "Memory has expired or been superseded and is excluded from the successor agent.")
        if evaluation.policy.action in {PolicyAction.QUARANTINE, PolicyAction.REVIEW_REQUIRED, PolicyAction.BLOCK}:
            return HandoverItem(memory, evaluation, HandoverOutcome.REDACTED_FOR_REVIEW, "Governance policy requires review before this company memory can be shared.")
        return HandoverItem(memory, evaluation, HandoverOutcome.TRANSFERRED, "Verified company knowledge is approved for the successor agent.")

    @staticmethod
    def _successor_prompt(items: Iterable[HandoverItem]) -> str:
        allowed = []
        for item in items:
            if item.outcome not in {HandoverOutcome.TRANSFERRED, HandoverOutcome.RETAINED_AT_SOURCE}:
                continue
            content = item.memory.evidence.content
            if content:
                allowed.append(f"- [memory_id={item.memory.evidence.memory_id}] {content}")
        return "Governed successor context:\n" + ("\n".join(allowed) or "(no approved memory)")
