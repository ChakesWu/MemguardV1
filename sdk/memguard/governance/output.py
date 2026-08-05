"""Explicit links from generated answer segments to governed memory evidence."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Tuple

from .models import (
    EvidenceGap,
    InvalidEvidenceCitation,
    OutputCitation,
    OutputEvidenceResult,
    OutputEvidenceRole,
    PolicyAction,
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
        reasons = []
        offsets_valid = 0 <= citation.start_offset < citation.end_offset <= len(answer)
        if not offsets_valid:
            reasons.append("segment:invalid_offsets")
        elif answer[citation.start_offset : citation.end_offset] != citation.segment:
            reasons.append("segment:mismatch")

        try:
            evaluation = run.by_id(citation.memory_id)
        except StopIteration:
            reasons.append("memory:unknown")
            evaluation = None

        if evaluation is not None:
            if evaluation.policy.action in {PolicyAction.BLOCK, PolicyAction.QUARANTINE}:
                reasons.append("policy:memory_not_eligible")
            elif citation.memory_id not in run.gate.included_memory_ids or not evaluation.influence.included_in_prompt:
                reasons.append("memory:not_prompt_included")
            if (
                not citation.evidence_quote
                or not evaluation.evidence.content
                or citation.evidence_quote not in evaluation.evidence.content
            ):
                reasons.append("evidence:quote_not_found")

        try:
            OutputEvidenceRole(citation.role)
        except ValueError:
            reasons.append("role:unsupported")
        return tuple(reasons)

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

    @staticmethod
    def _gaps(
        answer: str,
        links: Tuple[ValidatedEvidenceLink, ...],
    ) -> Tuple[EvidenceGap, ...]:
        merged = []
        for start, end in sorted((link.start_offset, link.end_offset) for link in links):
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))

        gaps = []
        cursor = 0
        for start, end in (*merged, (len(answer), len(answer))):
            raw_start, raw_end = cursor, start
            while raw_start < raw_end and answer[raw_start].isspace():
                raw_start += 1
            while raw_end > raw_start and answer[raw_end - 1].isspace():
                raw_end -= 1
            segment = answer[raw_start:raw_end]
            if any(character.isalnum() for character in segment):
                gaps.append(EvidenceGap(raw_start, raw_end, segment))
            cursor = max(cursor, end)
        return tuple(gaps)
