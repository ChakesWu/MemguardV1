"""
Compliance Research Agent - Queries applicable regulations.

[OBSERVABILITY] When Qwen is available, synthesizes retrieved regulations
into a structured compliance analysis. Every semantic memory read and
the resulting compliance findings are traced via MemGuard.
"""

import logging
from typing import Dict, Any, List

from .base import BaseAgent

logger = logging.getLogger(__name__)

COMPLIANCE_PROMPT = """You are a financial regulatory compliance expert. Analyze which regulations apply to this transaction.

Transaction:
- ID: {transaction_id}
- Amount: {currency} {amount:,.2f}
- Pattern: {transaction_pattern}
- Risk Score: {risk_score:.2f} ({risk_level})
- Risk Factors: {risk_factors}

Applicable Regulations (retrieved from regulatory database):
{regulation_texts}

Respond with a JSON object ONLY:
{{
  "applicable_regulations": [{{"regulation_id": "...", "relevance": "why this applies"}}],
  "compliance_requirements": ["requirement 1", "requirement 2", ...],
  "risk_level": "critical" | "high" | "medium" | "low",
  "citation_text": "Formatted legal citations",
  "reasoning": "Synthesis explaining which regulations are most relevant and why"
}}"""


class ComplianceResearchAgent(BaseAgent):
    """Compliance Research Agent — ChromaDB retrieval + Qwen synthesis."""

    def __init__(self, memory_layer=None, interceptor=None, llm_client=None):
        super().__init__(memory_layer=memory_layer, interceptor=interceptor, llm_client=llm_client)

    @property
    def agent_id(self) -> str:
        return "compliance_research"

    def analyze(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Query applicable regulations and synthesize findings."""
        logger.info(f"[{self.agent_id}] Researching regulations...")

        compliance_question = self._build_compliance_question(state)
        input_event_ids: List[str] = []
        output_event_ids: List[str] = []

        # ── Step 1: Query semantic memory (regulations) ──
        regulations = []
        if self.memory and self.memory.semantic:
            regulations = self.memory.semantic.query_regulations(
                compliance_question=compliance_question,
                n_results=5,
            )
            input_event_ids = self._log_memory_access(
                state=state,
                memory_type="semantic",
                query=compliance_question,
                results=regulations,
                similarity_scores=[r.get("similarity_score") for r in regulations],
            )

        # ── Step 2: Synthesize (Qwen or heuristic) ──
        prompt = ""
        if self.llm and regulations:
            prompt = self._build_compliance_prompt(state, regulations)
            try:
                from llm_client import parse_json_response

                response = self.llm.chat(
                    [{"role": "user", "content": prompt}],
                    temperature=0.1,
                )
                qwen_result = parse_json_response(response.content)
                applicable = qwen_result.get("applicable_regulations", [])
                requirements = qwen_result.get("compliance_requirements", [])
                citation_text = qwen_result.get("citation_text", "")
                reasoning = qwen_result.get(
                    "reasoning", response.content[:500]
                )
                logger.info(
                    "[%s] Qwen synthesis: %d regulations, %d requirements",
                    self.agent_id, len(applicable), len(requirements),
                )
            except Exception as e:
                logger.warning(
                    "[%s] Qwen failed, using heuristic: %s", self.agent_id, e
                )
                applicable = [
                    {
                        "regulation_id": reg.get("regulation_id"),
                        "authority": reg.get("metadata", {}).get("authority"),
                        "similarity_score": reg.get("similarity_score"),
                    }
                    for reg in regulations
                ]
                requirements = self._extract_requirements(regulations, state)
                citation_text = self._generate_citations(regulations)
                reasoning = self._generate_reasoning(regulations, requirements)
        else:
            # Heuristic (no LLM or no regulations)
            applicable = [
                {
                    "regulation_id": reg.get("regulation_id"),
                    "authority": reg.get("metadata", {}).get("authority"),
                    "similarity_score": reg.get("similarity_score"),
                }
                for reg in regulations
            ]
            requirements = self._extract_requirements(regulations, state)
            citation_text = self._generate_citations(regulations)
            reasoning = self._generate_reasoning(regulations, requirements)
            prompt = f"[heuristic] question={compliance_question}"

        # ── Step 3: Build output ──
        analysis_result = {
            "applicable_regulations": applicable,
            "compliance_requirements": requirements,
            "citation_text": citation_text,
            "reasoning": reasoning,
            "llm_used": self.llm is not None and bool(regulations),
        }

        state["compliance_research"] = analysis_result

        # ── Step 4: Record output event ──
        output_event_id = self._record_output_event(
            memory_key="state:compliance_research",
            after_value={
                "regulation_count": len(regulations),
                "requirement_count": len(requirements),
                "reasoning": reasoning[:200],
            },
            tags=[self.agent_id, "output", "compliance_research"],
        )
        if output_event_id:
            output_event_ids.append(output_event_id)

        # ── Step 5: DecisionTrace ──
        self._emit_decision_trace(
            input_event_ids=input_event_ids,
            output_event_ids=output_event_ids,
            prompt_text=prompt,
            output_text=reasoning,
            influence_score=0.8 if regulations else 0.2,
            analysis_type="compliance_research",
        )

        self._add_message(
            state,
            f"Compliance research complete. {len(regulations)} regulations, "
            f"{len(requirements)} requirements.",
        )

        return state

    def _build_compliance_prompt(self, state: Dict[str, Any], regulations: list) -> str:
        """Build Qwen prompt with transaction context and regulation texts."""
        regulation_texts = "No regulations retrieved."
        if regulations:
            lines = []
            for i, reg in enumerate(regulations, 1):
                rid = reg.get("regulation_id", f"REG-{i}")
                text = reg.get("text", reg.get("content", ""))[:300]
                authority = reg.get("metadata", {}).get("authority", "")
                lines.append(f"{i}. {rid} ({authority}): {text}")
            regulation_texts = "\n\n".join(lines)

        return COMPLIANCE_PROMPT.format(
            transaction_id=state["transaction_id"],
            amount=state["amount"],
            currency=state.get("currency", "HKD"),
            transaction_pattern=state["transaction_pattern"],
            risk_score=state.get("risk_score", 0.0),
            risk_level=state.get("risk_level", "unknown"),
            risk_factors=", ".join(state.get("risk_factors", [])[:5]) or "none",
            regulation_texts=regulation_texts,
        )

    # ── Heuristic methods ──

    def _build_compliance_question(self, state: Dict[str, Any]) -> str:
        risk_factors = state.get("risk_factors", [])
        if any("structuring" in f.lower() for f in risk_factors):
            return (
                "What are regulatory requirements for reporting structuring transactions?"
            )
        elif state.get("risk_score", 0) > 0.85:
            return (
                "What are mandatory reporting obligations for high-risk "
                "suspicious transactions?"
            )
        else:
            return "What are general AML and STR reporting requirements?"

    def _extract_requirements(self, regulations: list, state: Dict[str, Any]) -> list:
        requirements = []
        if not regulations:
            return ["Consult compliance manual"]

        for reg in regulations[:3]:
            authority = reg.get("metadata", {}).get("authority", "")
            if "HKMA" in authority or "MAS" in authority:
                requirements.append("File STR/SAR with FIU as soon as practicable")

        if state.get("risk_score", 0) > 0.85:
            requirements.append("Escalate to senior management")

        return list(set(requirements))

    def _generate_citations(self, regulations: list) -> str:
        if not regulations:
            return "No specific regulations cited."
        citations = []
        for reg in regulations[:3]:
            reg_id = reg.get("regulation_id", "")
            authority = reg.get("metadata", {}).get("authority", "")
            citations.append(f"{reg_id} ({authority})")
        return "; ".join(citations)

    def _generate_reasoning(
        self, regulations: list, requirements: list
    ) -> str:
        if not regulations:
            return "No applicable regulations identified."
        return (
            f"Identified {len(regulations)} applicable regulations. "
            f"Extracted {len(requirements)} requirements."
        )
