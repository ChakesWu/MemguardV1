"""
Report Generation Agent - Generates SAR draft reports.

[OBSERVABILITY] When Qwen is available, generates a professional SAR narrative
synthesizing all prior agent analyses. This is the CROWN JEWEL of observability:
the DecisionTrace shows exactly which historical cases and regulations shaped
the SAR recommendation.
"""

import logging
from typing import Dict, Any, List

from .base import BaseAgent, MemoryOp, MemoryType

logger = logging.getLogger(__name__)

SAR_PROMPT = """You are a senior compliance officer at a Hong Kong bank. Write a Suspicious Activity Report (SAR) draft based on the multi-agent analysis below.

CASE SUMMARY:
- Transaction ID: {transaction_id}
- Customer: {customer_id}
- Amount: {currency} {amount:,.2f}
- Pattern: {transaction_pattern}
- Risk Score: {risk_score:.2f} ({risk_level})

FRAUD DETECTION FINDINGS:
{fraud_findings}

HISTORICAL CASE ANALYSIS:
{case_history}

COMPLIANCE RESEARCH:
{compliance_research}

Write a complete SAR report with these sections:
1. EXECUTIVE SUMMARY (2-3 sentences)
2. TRANSACTION DETAILS
3. RISK ANALYSIS (integrate fraud + historical case findings)
4. REGULATORY BASIS (cite specific regulations)
5. RECOMMENDATION (File SAR / Enhanced Due Diligence / Clear)

Respond with JSON ONLY:
{{
  "executive_summary": "...",
  "sar_draft": "The complete SAR narrative text...",
  "recommendation": "file_sar" | "enhanced_due_diligence" | "clear",
  "reasoning": "Why this recommendation was chosen, citing specific evidence"
}}"""


class ReportGenerationAgent(BaseAgent):
    """Report Generation Agent — template-based + Qwen-enhanced SAR drafting."""

    def __init__(self, memory_layer=None, interceptor=None, llm_client=None):
        super().__init__(memory_layer=memory_layer, interceptor=interceptor, llm_client=llm_client)

    @property
    def agent_id(self) -> str:
        return "report_generation"

    def analyze(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SAR draft report."""
        logger.info(f"[{self.agent_id}] Generating SAR draft...")

        input_event_ids: List[str] = []
        output_event_ids: List[str] = []

        # ── Collect "memory reads" from prior agent outputs ──
        # (These are working-state reads — the agent is reading prior analyses)
        if self.interceptor:
            for key, label in [
                ("fraud_analysis", "state:fraud_analysis"),
                ("case_history_analysis", "state:case_history"),
                ("compliance_research", "state:compliance_research"),
            ]:
                if state.get(key):
                    try:
                        eid = self.interceptor.record(
                            operation=MemoryOp.READ,
                            memory_key=label,
                            memory_type=MemoryType.WORKING,
                            agent_id=self.agent_id,
                            tags=[self.agent_id, "input", key],
                        )
                        input_event_ids.append(eid)
                    except Exception:
                        pass

        # ── Get report format preference ──
        report_format = "detailed"
        if self.memory and self.memory.user_prefs:
            report_format = self.memory.user_prefs.get_report_format(
                "compliance_officer_001"
            )

        # ── Generate SAR (Qwen or template) ──
        prompt = ""
        if self.llm:
            prompt = self._build_sar_prompt(state)
            try:
                from llm_client import parse_json_response

                response = self.llm.chat(
                    [{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=4096,
                )
                qwen_result = parse_json_response(response.content)
                executive_summary = qwen_result.get(
                    "executive_summary",
                    self._generate_executive_summary(state),
                )
                sar_draft = qwen_result.get(
                    "sar_draft", response.content
                )
                recommendation = qwen_result.get(
                    "recommendation",
                    self._recommendation_from_score(state.get("risk_score", 0)),
                )
                reasoning = qwen_result.get(
                    "reasoning", response.content[:500]
                )
                logger.info(
                    "[%s] Qwen SAR: %d chars, recommendation=%s",
                    self.agent_id, len(sar_draft), recommendation,
                )
            except Exception as e:
                logger.warning(
                    "[%s] Qwen failed, using template: %s", self.agent_id, e
                )
                executive_summary = self._generate_executive_summary(state)
                sar_draft = self._assemble_sar_draft(
                    executive_summary,
                    self._generate_transaction_details(state),
                    self._generate_risk_analysis(state),
                    self._generate_regulatory_basis(state),
                    self._generate_recommendation(state),
                    report_format,
                )
                recommendation = self._recommendation_from_score(
                    state.get("risk_score", 0)
                )
                reasoning = f"Generated {report_format} SAR draft based on multi-agent analysis"
        else:
            # Pure template (no LLM)
            executive_summary = self._generate_executive_summary(state)
            sar_draft = self._assemble_sar_draft(
                executive_summary,
                self._generate_transaction_details(state),
                self._generate_risk_analysis(state),
                self._generate_regulatory_basis(state),
                self._generate_recommendation(state),
                report_format,
            )
            recommendation = self._recommendation_from_score(
                state.get("risk_score", 0)
            )
            reasoning = f"Generated {report_format} SAR draft based on multi-agent analysis"
            prompt = f"[template] format={report_format}"

        # ── Build output ──
        from datetime import datetime, timezone

        analysis_result = {
            "sar_draft": sar_draft,
            "executive_summary": executive_summary,
            "report_format": report_format,
            "recommendation": recommendation,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "reasoning": reasoning,
            "llm_used": self.llm is not None,
            "supporting_evidence": self._collect_supporting_evidence(state),
        }

        state["final_report"] = analysis_result

        # ── Record output event ──
        output_event_id = self._record_output_event(
            memory_key="state:final_report",
            after_value={
                "sar_length": len(sar_draft),
                "recommendation": recommendation,
                "reasoning": reasoning[:200],
            },
            tags=[self.agent_id, "output", "sar_report"],
        )
        if output_event_id:
            output_event_ids.append(output_event_id)

        # ── DecisionTrace — the crown jewel ──
        influence = self._compute_influence(state)
        self._emit_decision_trace(
            input_event_ids=input_event_ids,
            output_event_ids=output_event_ids,
            prompt_text=prompt,
            output_text=sar_draft[:500],
            influence_score=influence,
            analysis_type="sar_generation",
            recommendation=recommendation,
            sar_length=len(sar_draft),
        )

        self._add_message(
            state,
            f"SAR draft report generated ({report_format} format). "
            f"Recommendation: {recommendation}. "
            f"Ready for {'human review' if state.get('requires_human_review') else 'submission'}.",
        )

        logger.info(f"[{self.agent_id}] Report generation complete.")
        return state

    def _build_sar_prompt(self, state: Dict[str, Any]) -> str:
        """Build the SAR generation prompt from all prior analyses."""
        fraud = state.get("fraud_analysis", {})
        case = state.get("case_history_analysis", {})
        compliance = state.get("compliance_research", {})

        fraud_findings = "No fraud analysis available."
        if fraud:
            fraud_findings = (
                f"Fraud Score: {fraud.get('fraud_score', 0):.2f}\n"
                f"Indicators: {', '.join(fraud.get('risk_indicators', [])[:5]) or 'none'}\n"
                f"Similar Cases: {fraud.get('similar_cases_count', 0)}\n"
                f"Analysis: {fraud.get('reasoning', '')[:300]}"
            )

        case_history = "No historical case analysis available."
        if case:
            case_history = (
                f"Similar Cases: {case.get('similar_cases_count', 0)}\n"
                f"Lessons: {', '.join(case.get('lessons_learned', [])[:3]) or 'none'}\n"
                f"Risk Pattern Match: {case.get('risk_pattern_match', 'none')}"
            )

        compliance_research = "No compliance research available."
        if compliance:
            compliance_research = (
                f"Regulations: {compliance.get('citation_text', 'none cited')}\n"
                f"Requirements: {', '.join(compliance.get('compliance_requirements', [])[:5]) or 'none'}\n"
                f"Analysis: {compliance.get('reasoning', '')[:300]}"
            )

        return SAR_PROMPT.format(
            transaction_id=state["transaction_id"],
            customer_id=state["customer_id"],
            amount=state["amount"],
            currency=state.get("currency", "HKD"),
            transaction_pattern=state["transaction_pattern"],
            risk_score=state.get("risk_score", 0.0),
            risk_level=state.get("risk_level", "unknown"),
            fraud_findings=fraud_findings,
            case_history=case_history,
            compliance_research=compliance_research,
        )

    def _compute_influence(self, state: Dict[str, Any]) -> float:
        """Compute how much prior analyses shaped the SAR."""
        score = 0.0
        if state.get("fraud_analysis"):
            score += 0.3
        if state.get("case_history_analysis"):
            score += 0.2
        if state.get("compliance_research"):
            score += 0.3
        if state.get("memory_traces"):
            score += 0.1 * min(len(state["memory_traces"]), 5) / 5
        return round(min(score, 1.0), 2)

    @staticmethod
    def _recommendation_from_score(risk_score: float) -> str:
        if risk_score >= 0.85:
            return "file_sar"
        elif risk_score >= 0.50:
            return "enhanced_due_diligence"
        else:
            return "clear"

    # ── Template methods (fallback / no-LLM) ──

    def _generate_executive_summary(self, state: Dict[str, Any]) -> str:
        risk_score = state.get("risk_score", 0.0)
        risk_level = state.get("risk_level", "unknown")
        return (
            f"Transaction {state['transaction_id']} by customer "
            f"{state['customer_id']} for {state.get('currency', 'HKD')} "
            f"{state['amount']:,.2f}. Risk Score: {risk_score:.2f} "
            f"({risk_level.upper()} RISK). This SAR documents a "
            f"transaction exhibiting characteristics consistent with "
            f"potential money laundering activity."
        )

    def _generate_transaction_details(self, state: Dict[str, Any]) -> str:
        details = (
            f"PATTERN: {state['transaction_pattern']}\n"
            f"AMOUNT: {state.get('currency', 'HKD')} {state['amount']:,.2f}\n"
            f"CUSTOMER: {state['customer_id']}"
        )
        if state.get("from_account"):
            details += f"\nFROM: {state['from_account']}"
        if state.get("to_account"):
            details += f"\nTO: {state['to_account']}"
        if state.get("to_country"):
            details += f"\nDESTINATION: {state['to_country']}"
        return details

    def _generate_risk_analysis(self, state: Dict[str, Any]) -> str:
        analysis = ""
        fraud = state.get("fraud_analysis", {})
        if fraud:
            analysis += (
                f"Fraud Detection: score={fraud.get('fraud_score', 0):.2f}, "
                f"{len(fraud.get('risk_indicators', []))} indicators. "
                f"{fraud.get('reasoning', '')}\n"
            )
        case = state.get("case_history_analysis", {})
        if case:
            analysis += (
                f"Historical Cases: {case.get('similar_cases_count', 0)} similar, "
                f"{len(case.get('lessons_learned', []))} lessons."
            )
        return analysis or "No risk analysis available."

    def _generate_regulatory_basis(self, state: Dict[str, Any]) -> str:
        compliance = state.get("compliance_research", {})
        if compliance:
            return (
                f"Regulations: {compliance.get('citation_text', 'None cited')}\n"
                + "\n".join(
                    f"  • {r}" for r in compliance.get("compliance_requirements", [])
                )
            )
        return "Regulatory research not completed."

    def _generate_recommendation(self, state: Dict[str, Any]) -> str:
        risk_score = state.get("risk_score", 0.0)
        if risk_score >= 0.85:
            return (
                "RECOMMENDATION: FILE SAR. High-risk transaction requiring "
                "immediate filing. Human review required."
            )
        elif risk_score >= 0.50:
            return (
                "RECOMMENDATION: ENHANCED DUE DILIGENCE. Monitor and document. "
                "Consider SAR if additional suspicious activity detected."
            )
        else:
            return (
                "RECOMMENDATION: CLEAR. Transaction within normal parameters. "
                "Continue routine monitoring."
            )

    def _assemble_sar_draft(
        self, exec_summary, txn_details, risk_analysis, regulatory_basis, recommendation, report_format
    ):
        """Assemble complete SAR draft from sections."""
        from datetime import datetime, timezone

        return (
            f"{'='*70}\n"
            f"SUSPICIOUS ACTIVITY REPORT (DRAFT)\n"
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"Format: {report_format.upper()}\n"
            f"{'='*70}\n\n"
            f"EXECUTIVE SUMMARY\n{exec_summary}\n\n"
            f"{'='*70}\n"
            f"TRANSACTION DETAILS\n{txn_details}\n\n"
            f"{'='*70}\n"
            f"RISK ANALYSIS\n{risk_analysis}\n\n"
            f"{'='*70}\n"
            f"REGULATORY BASIS\n{regulatory_basis}\n\n"
            f"{'='*70}\n"
            f"{recommendation}\n\n"
            f"{'='*70}\n"
            f"END OF REPORT\n"
        )

    def _collect_supporting_evidence(self, state: Dict[str, Any]) -> list:
        evidence = []
        if state.get("memory_traces"):
            evidence.append({
                "type": "memory_analysis",
                "description": f"{len(state['memory_traces'])} memory queries performed",
            })
        if state.get("fraud_analysis", {}).get("similar_cases"):
            evidence.append({
                "type": "historical_cases",
                "description": f"{len(state['fraud_analysis']['similar_cases'])} similar SAR cases",
            })
        if state.get("compliance_research", {}).get("applicable_regulations"):
            evidence.append({
                "type": "regulations",
                "description": f"{len(state['compliance_research']['applicable_regulations'])} regulations cited",
            })
        return evidence
