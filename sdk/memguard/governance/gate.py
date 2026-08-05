"""Prompt boundary enforcement for governance decisions."""

from __future__ import annotations

from typing import Iterable

from .models import EvidenceEvaluation, PolicyAction, PromptGateResult


class PromptGate:
    BLOCKING_ACTIONS = {PolicyAction.BLOCK, PolicyAction.QUARANTINE}

    def build(self, user_input: str, evaluations: Iterable[EvidenceEvaluation]) -> PromptGateResult:
        included = []
        blocked = []
        context_lines = []
        for evaluation in evaluations:
            evidence = evaluation.evidence
            if evaluation.policy.action in self.BLOCKING_ACTIONS or evidence.content is None:
                blocked.append(evidence.memory_id)
                continue
            included.append(evidence.memory_id)
            marker = evaluation.policy.action.value.upper()
            context_lines.append(f"- [{marker}] [memory_id={evidence.memory_id}] {evidence.content}")

        context = "\n".join(context_lines) if context_lines else "(no governed memory available)"
        prompt = f"Governed memory evidence:\n{context}\n\nUser request:\n{user_input}"
        return PromptGateResult(prompt, tuple(included), tuple(blocked))
