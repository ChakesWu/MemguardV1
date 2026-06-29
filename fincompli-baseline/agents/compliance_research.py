"""
Compliance Research Agent - Queries applicable regulations
"""

import logging
from typing import Dict, Any
from .base import BaseAgent

logger = logging.getLogger(__name__)


class ComplianceResearchAgent(BaseAgent):
    """Compliance Research Agent"""

    @property
    def agent_id(self) -> str:
        return "compliance_research"

    def analyze(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Query applicable regulations"""
        logger.info(f"[{self.agent_id}] Researching regulations...")

        compliance_question = self._build_compliance_question(state)

        regulations = []
        if self.memory and self.memory.semantic:
            regulations = self.memory.semantic.query_regulations(
                compliance_question=compliance_question,
                n_results=5
            )
            self._log_memory_access(
                state=state,
                memory_type="semantic",
                query=compliance_question,
                results=regulations,
                similarity_scores=[r.get("similarity_score") for r in regulations]
            )

        requirements = self._extract_requirements(regulations, state)
        citation_text = self._generate_citations(regulations)

        analysis_result = {
            "applicable_regulations": [
                {
                    "regulation_id": reg.get("regulation_id"),
                    "authority": reg.get("metadata", {}).get("authority"),
                    "similarity_score": reg.get("similarity_score")
                }
                for reg in regulations
            ],
            "compliance_requirements": requirements,
            "citation_text": citation_text,
            "reasoning": self._generate_reasoning(regulations, requirements)
        }

        state["compliance_research"] = analysis_result
        self._add_message(state, f"Compliance research complete. {len(regulations)} regulations, {len(requirements)} requirements.")
        return state

    def _build_compliance_question(self, state: Dict[str, Any]) -> str:
        risk_factors = state.get("risk_factors", [])
        if any("structuring" in f.lower() for f in risk_factors):
            return "What are regulatory requirements for reporting structuring transactions?"
        elif state.get("risk_score", 0) > 0.85:
            return "What are mandatory reporting obligations for high-risk suspicious transactions?"
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

    def _generate_reasoning(self, regulations: list, requirements: list) -> str:
        if not regulations:
            return "No applicable regulations identified."
        return f"Identified {len(regulations)} applicable regulations. Extracted {len(requirements)} requirements."
