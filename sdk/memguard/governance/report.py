"""Content-safe, machine-readable governance evidence reports."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable, Mapping, Tuple
from uuid import uuid4

from .models import DataClassification, EvidenceEvaluation, OutputEvidenceResult, PolicyAction, TrustFactor


@dataclass(frozen=True)
class EvidenceReport:
    policy_id: str
    tenant_id: str
    generated_at: datetime
    items: Tuple[Mapping[str, Any], ...]
    provenance_id: str = field(default_factory=lambda: uuid4().hex)

    def to_dict(self, output_evidence: OutputEvidenceResult | None = None) -> dict:
        counts = Counter(str(item["policy"]["action"]) for item in self.items)
        payload = {
            "policy_id": self.policy_id,
            "tenant_id": self.tenant_id,
            "generated_at": self.generated_at.isoformat(),
            "summary": dict(counts),
            "items": deepcopy(list(self.items)),
        }
        if output_evidence is not None:
            if output_evidence.provenance_id != self.provenance_id:
                raise ValueError("output evidence belongs to a different governance run")
            payload["output_evidence"] = self._output_evidence(output_evidence)
        return payload

    def _output_evidence(self, result: OutputEvidenceResult) -> dict:
        memory_items = {item["memory_id"]: item for item in self.items}
        valid_links = []
        for link in result.valid_links:
            memory_item = memory_items[link.memory_id]
            if memory_item["content"] == "[redacted]":
                quote = "[redacted]"
            elif memory_item["content"] == "[hash-only]":
                quote = "[hash-only]"
            else:
                quote = link.evidence_quote
            valid_links.append(
                {
                    "start_offset": link.start_offset,
                    "end_offset": link.end_offset,
                    "segment": link.segment,
                    "memory_id": link.memory_id,
                    "evidence_quote": quote,
                    "role": link.role.value,
                    "retrieval": {
                        "similarity": link.retrieval.similarity,
                        "importance": link.retrieval.importance,
                        "recency": link.retrieval.recency,
                        "retrieval_score": link.retrieval.retrieval_score,
                        "confidence_level": link.retrieval.confidence_level,
                        "retrieved": link.retrieval.retrieved,
                        "included_in_prompt": link.retrieval.included_in_prompt,
                        "cited": link.retrieval.cited,
                    },
                    "trust": self._trust(link.trust),
                    "policy": self._policy(link.policy),
                    "influence": {
                        "score": link.influence.score,
                        "retrieved": link.influence.retrieved,
                        "included_in_prompt": link.influence.included_in_prompt,
                        "cited": link.influence.cited,
                        "output_supported": link.influence.output_supported,
                        "reason_codes": list(link.influence.reason_codes),
                    },
                    "prompt_included": link.prompt_included,
                    "link_method": link.link_method,
                    "validation_status": link.validation_status,
                }
            )
        invalid_citations = [
            {
                "start_offset": citation.start_offset,
                "end_offset": citation.end_offset,
                "segment": citation.segment,
                "memory_id": citation.memory_id,
                "role": citation.role,
                "reason_codes": list(citation.reason_codes),
                "validation_status": citation.validation_status,
            }
            for citation in result.invalid_citations
        ]
        evidence_gaps = [
            {"start_offset": gap.start_offset, "end_offset": gap.end_offset, "segment": gap.segment}
            for gap in result.evidence_gaps
        ]
        return {
            "summary": dict(result.summary),
            "reason_codes": list(result.reason_codes),
            "valid_links": valid_links,
            "invalid_citations": invalid_citations,
            "evidence_gaps": evidence_gaps,
        }

    @staticmethod
    def _trust(trust) -> dict:
        factors = trust.factors
        return {
            "score": trust.score,
            "level": trust.level.value,
            "missing_factors": list(trust.missing_factors),
            "reason_codes": list(trust.reason_codes),
            "factors": {
                "source": EvidenceReportBuilder._factor(factors.source),
                "writer": EvidenceReportBuilder._factor(factors.writer),
                "freshness": EvidenceReportBuilder._factor(factors.freshness),
                "conflict": EvidenceReportBuilder._factor(factors.conflict),
                "policy_fit": EvidenceReportBuilder._factor(factors.policy_fit),
            },
        }

    @staticmethod
    def _policy(policy) -> dict:
        return {
            "action": policy.action.value,
            "enforced": policy.enforced,
            "reason_codes": list(policy.reason_codes),
            "explanation": policy.explanation,
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
        *,
        provenance_id: str | None = None,
    ) -> EvidenceReport:
        sanitized = tuple(self._item(item) for item in evaluations)
        return EvidenceReport(
            policy_id,
            tenant_id,
            generated_at,
            sanitized,
            provenance_id or uuid4().hex,
        )
