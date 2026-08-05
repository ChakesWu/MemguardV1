"""Explicit links from generated answer segments to governed memory evidence."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Tuple

from .models import (
    EvidenceGap,
    InvalidEvidenceCitation,
    OutputCitation,
    OutputEvidenceResult,
    OutputEvidenceRole,
    ValidatedEvidenceLink,
)

if TYPE_CHECKING:
    from .engine import GovernanceRun


class OutputEvidenceLinker:
    def link(
        self,
        run: "GovernanceRun",
        answer: str,
        citations: Iterable[OutputCitation],
    ) -> OutputEvidenceResult:
        valid = []
        invalid = []
        for citation in citations:
            reasons = self._reason_codes(run, answer, citation)
            if reasons:
                invalid.append(self._invalid(citation, reasons))
                continue
            evaluation = run.by_id(citation.memory_id)
            valid.append(
                ValidatedEvidenceLink(
                    start_offset=citation.start_offset,
                    end_offset=citation.end_offset,
                    segment=citation.segment,
                    memory_id=citation.memory_id,
                    evidence_quote=citation.evidence_quote,
                    role=OutputEvidenceRole(citation.role),
                    retrieval=evaluation.evidence.retrieval,
                    trust=evaluation.trust,
                    policy=evaluation.policy,
                    influence=evaluation.influence,
                )
            )
        links = tuple(valid)
        return OutputEvidenceResult(answer, links, tuple(invalid), self._gaps(answer, links))

    def _reason_codes(
        self,
        run: "GovernanceRun",
        answer: str,
        citation: OutputCitation,
    ) -> Tuple[str, ...]:
        return ()

    def _invalid(
        self,
        citation: OutputCitation,
        reason_codes: Tuple[str, ...],
    ) -> InvalidEvidenceCitation:
        return InvalidEvidenceCitation(
            start_offset=citation.start_offset,
            end_offset=citation.end_offset,
            segment=citation.segment,
            memory_id=citation.memory_id,
            role=str(citation.role),
            reason_codes=reason_codes,
        )

    def _gaps(
        self,
        answer: str,
        links: Tuple[ValidatedEvidenceLink, ...],
    ) -> Tuple[EvidenceGap, ...]:
        return ()
