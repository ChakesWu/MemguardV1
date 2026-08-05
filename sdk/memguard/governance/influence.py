"""Evidence-backed influence indicators without model-causality claims."""

from __future__ import annotations

import re

from .models import InfluenceResult, MemoryEvidence


class InfluenceEngine:
    def evaluate(self, evidence: MemoryEvidence, output_text: str | None = None) -> InfluenceResult:
        signals = evidence.retrieval
        output_supported = self._supports_output(evidence.content, output_text)
        score = 0.0
        reasons = []
        if signals.retrieved:
            score += 0.15
            reasons.append("evidence:retrieved")
        if signals.included_in_prompt:
            score += 0.35
            reasons.append("evidence:available_to_model")
        if signals.cited:
            score += 0.20
            reasons.append("evidence:cited")
        if output_supported:
            score += 0.30
            reasons.append("evidence:output_support")
        return InfluenceResult(
            evidence.memory_id,
            round(min(1.0, score), 3),
            signals.retrieved,
            signals.included_in_prompt,
            signals.cited,
            output_supported,
            tuple(reasons),
        )

    @staticmethod
    def _supports_output(content: str | None, output_text: str | None) -> bool:
        if not content or not output_text:
            return False
        content_tokens = set(re.findall(r"[a-z0-9]+", content.lower()))
        output_tokens = set(re.findall(r"[a-z0-9]+", output_text.lower()))
        meaningful = {token for token in content_tokens if len(token) > 2}
        return bool(meaningful) and len(meaningful & output_tokens) / len(meaningful) >= 0.5
