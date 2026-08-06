"""Maps support records to governed MemGuard output-evidence reports."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from memguard.governance import (
    ConflictStatus,
    DataClassification,
    GovernanceContext,
    GovernancePolicy,
    MemoryEvidence,
    MemoryGovernanceEngine,
    OutputCitation,
    RetrievalSignals,
)

from .output_evidence import ExplicitCitation
from .output_evidence import extract_explicit_citations
from .repository import SupportRepository


_POLICY = GovernancePolicy(
    policy_id="customer-support-governance-v1",
    source_scores={"support_order": 100},
    allow_threshold=80,
    warn_threshold=60,
    review_threshold=40,
)


def _order_evidence(repository: SupportRepository, tenant_id: str, memory_id: str) -> MemoryEvidence | None:
    order_id = memory_id.removeprefix("order:")
    if order_id == memory_id:
        return None
    order = repository.get_order(tenant_id, order_id)
    if order is None:
        return None
    delivered_at = order.delivered_at.date().isoformat() if order.delivered_at else "unknown"
    content = f"Order {order.order_id}: status {order.status}; payment {order.payment_status}; delivered {delivered_at}."
    return MemoryEvidence(
        memory_id=memory_id,
        tenant_id=tenant_id,
        content=content,
        source_type="support_order",
        source_id=order.order_id,
        created_at=order.delivered_at,
        verified_at=datetime.now(timezone.utc),
        conflict_status=ConflictStatus.NONE,
        data_classification=DataClassification.INTERNAL,
        allowed_purposes=("customer_support",),
        retrieval=RetrievalSignals(retrieved=True, included_in_prompt=True),
    )


def _evidence_for_ids(
    repository: SupportRepository, tenant_id: str, memory_ids: Iterable[str]
) -> tuple[MemoryEvidence, ...]:
    evidence = []
    for memory_id in memory_ids:
        item = _order_evidence(repository, tenant_id, memory_id)
        if item is not None:
            evidence.append(item)
    return tuple(evidence)


def _find_unique_segment(answer: str, segment: str) -> tuple[int, int] | None:
    start = answer.find(segment)
    if start < 0 or answer.find(segment, start + 1) >= 0:
        return None
    return start, start + len(segment)


def _infer_support_order_citations(
    repository: SupportRepository,
    tenant_id: str,
    answer: str,
    prompt_memory_ids: set[str],
) -> tuple[ExplicitCitation, ...]:
    citations = []
    occupied: list[tuple[int, int]] = []
    for memory_id in sorted(prompt_memory_ids):
        order_id = memory_id.removeprefix("order:")
        if order_id == memory_id:
            continue
        order = repository.get_order(tenant_id, order_id)
        if order is None:
            continue
        delivered_date = order.delivered_at.date().isoformat() if order.delivered_at else None
        for segment in (order.order_id, order.status, order.payment_status, delivered_date):
            if not segment:
                continue
            offsets = _find_unique_segment(answer, segment)
            if offsets is None:
                continue
            start, end = offsets
            if any(start < used_end and end > used_start for used_start, used_end in occupied):
                continue
            citations.append(ExplicitCitation(start, end, segment, memory_id, segment, "factual_support"))
            occupied.append((start, end))
    return tuple(citations)


def build_output_evidence_report(
    *,
    repository: SupportRepository,
    tenant_id: str,
    answer: str,
    citations: Iterable[ExplicitCitation],
    prompt_memory_ids: set[str],
) -> dict:
    """Return a content-safe report for only records actually seen by the model."""
    now = datetime.now(timezone.utc)
    engine = MemoryGovernanceEngine(_POLICY)
    run = engine.evaluate_and_build_prompt(
        answer,
        _evidence_for_ids(repository, tenant_id, prompt_memory_ids),
        GovernanceContext(tenant_id, "customer_support_agent", "customer_support", now),
        output_text=answer,
    )
    result = engine.link_output_evidence(
        run,
        answer=answer,
        citations=tuple(
            OutputCitation(
                citation.start_offset,
                citation.end_offset,
                citation.segment,
                citation.memory_id,
                citation.evidence_quote,
                citation.role,
            )
            for citation in citations
        ),
    )
    return run.report.to_dict(output_evidence=result)


def govern_output_content(
    *,
    repository: SupportRepository,
    tenant_id: str,
    content: str,
    prompt_memory_ids: set[str],
) -> tuple[str, dict | None]:
    """Strip private citations and return governed links for explicit or deterministic support facts."""
    answer, citations = extract_explicit_citations(content)
    if not citations:
        citations = _infer_support_order_citations(repository, tenant_id, answer, prompt_memory_ids)
    if not citations:
        return answer, None
    return answer, build_output_evidence_report(
        repository=repository,
        tenant_id=tenant_id,
        answer=answer,
        citations=citations,
        prompt_memory_ids=prompt_memory_ids,
    )
