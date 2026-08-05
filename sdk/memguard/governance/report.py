"""Content-safe, machine-readable governance evidence reports."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Mapping, Tuple

from .models import DataClassification, EvidenceEvaluation, PolicyAction, TrustFactor


@dataclass(frozen=True)
class EvidenceReport:
    policy_id: str
    tenant_id: str
    generated_at: datetime
    items: Tuple[Mapping[str, Any], ...]

    def to_dict(self) -> dict:
        counts = Counter(str(item["policy"]["action"]) for item in self.items)
        return {
            "policy_id": self.policy_id,
            "tenant_id": self.tenant_id,
            "generated_at": self.generated_at.isoformat(),
            "summary": dict(counts),
            "items": deepcopy(list(self.items)),
        }


class EvidenceReportBuilder:
    def __init__(self, capture_allowed_content: bool = False) -> None:
        self.capture_allowed_content = capture_allowed_content

    def _item(self, item: EvidenceEvaluation) -> dict:
        evidence = item.evidence
        restricted = (
            item.policy.action in {PolicyAction.BLOCK, PolicyAction.QUARANTINE}
            or evidence.data_classification in {
                DataClassification.RESTRICTED,
                DataClassification.PRIVATE_EMPLOYEE,
                DataClassification.SECRET,
            }
        )
        if restricted:
            content = "[redacted]"
        elif self.capture_allowed_content:
            content = evidence.content
        else:
            content = "[hash-only]"
        factors = item.trust.factors
        return {
            "memory_id": evidence.memory_id,
            "version_id": evidence.version_id,
            "content": content,
            "content_hash": evidence.content_hash,
            "source": {"type": evidence.source_type, "id": evidence.source_id, "writer_id": evidence.writer_id},
            "trust": {
                "score": item.trust.score,
                "level": item.trust.level.value,
                "missing_factors": list(item.trust.missing_factors),
                "reason_codes": list(item.trust.reason_codes),
                "factors": {
                    "source": self._factor(factors.source),
                    "writer": self._factor(factors.writer),
                    "freshness": self._factor(factors.freshness),
                    "conflict": self._factor(factors.conflict),
                    "policy_fit": self._factor(factors.policy_fit),
                },
            },
            "policy": {
                "action": item.policy.action.value,
                "enforced": item.policy.enforced,
                "reason_codes": list(item.policy.reason_codes),
                "explanation": item.policy.explanation,
            },
            "influence": {
                "score": item.influence.score,
                "retrieved": item.influence.retrieved,
                "included_in_prompt": item.influence.included_in_prompt,
                "cited": item.influence.cited,
                "output_supported": item.influence.output_supported,
                "reason_codes": list(item.influence.reason_codes),
            },
        }

    @staticmethod
    def _factor(factor: TrustFactor) -> dict:
        return {"score": factor.score, "reason": factor.reason}

    def build(
        self,
        policy_id: str,
        tenant_id: str,
        generated_at: datetime,
        evaluations: Iterable[EvidenceEvaluation],
    ) -> EvidenceReport:
        sanitized = tuple(self._item(item) for item in evaluations)
        return EvidenceReport(policy_id, tenant_id, generated_at, sanitized)
