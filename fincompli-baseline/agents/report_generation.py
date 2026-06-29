"""
Report Generation Agent - Generates SAR draft reports
"""

import logging
from typing import Dict, Any
from datetime import datetime, timezone
from .base import BaseAgent

logger = logging.getLogger(__name__)


class ReportGenerationAgent(BaseAgent):
    """Report Generation Agent - Creates SAR draft"""

    @property
    def agent_id(self) -> str:
        return "report_generation"

    def analyze(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SAR draft report"""
        logger.info(f"[{self.agent_id}] Generating SAR draft...")

        # Get user preferences for report format
        report_format = "detailed"
        if self.memory and self.memory.user_prefs:
            report_format = self.memory.user_prefs.get_report_format("compliance_officer_001")

        # Generate report sections
        executive_summary = self._generate_executive_summary(state)
        transaction_details = self._generate_transaction_details(state)
        risk_analysis = self._generate_risk_analysis(state)
        regulatory_basis = self._generate_regulatory_basis(state)
        recommendation = self._generate_recommendation(state)

        # Assemble full SAR draft
        sar_draft = self._assemble_sar_draft(
            executive_summary,
            transaction_details,
            risk_analysis,
            regulatory_basis,
            recommendation,
            report_format
        )

        # Collect supporting evidence
        supporting_evidence = self._collect_supporting_evidence(state)

        # Build analysis result
        analysis_result = {
            "sar_draft": sar_draft,
            "executive_summary": executive_summary,
            "supporting_evidence": supporting_evidence,
            "report_format": report_format,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "reasoning": f"Generated {report_format} SAR draft based on multi-agent analysis"
        }

        state["final_report"] = analysis_result

        self._add_message(
            state,
            f"SAR draft report generated ({report_format} format). "
            f"Ready for {'human review' if state.get('requires_human_review') else 'submission'}."
        )

        logger.info(f"[{self.agent_id}] Report generation complete.")
        return state

    def _generate_executive_summary(self, state: Dict[str, Any]) -> str:
        """Generate executive summary"""
        txn_id = state["transaction_id"]
        customer_id = state["customer_id"]
        amount = state["amount"]
        currency = state["currency"]
        risk_score = state.get("risk_score", 0.0)
        risk_level = state.get("risk_level", "unknown")

        summary = f"""EXECUTIVE SUMMARY

Transaction ID: {txn_id}
Customer ID: {customer_id}
Amount: {currency} {amount:,.2f}
Risk Score: {risk_score:.2f} ({risk_level.upper()} RISK)

This suspicious activity report documents a transaction exhibiting characteristics 
consistent with potential money laundering activity. The transaction has been flagged 
for {risk_level} risk based on multi-factor analysis including fraud detection, 
historical case comparison, and regulatory compliance review."""

        return summary

    def _generate_transaction_details(self, state: Dict[str, Any]) -> str:
        """Generate transaction details section"""
        details = f"""TRANSACTION DETAILS

Pattern Description:
{state['transaction_pattern']}

Transaction Amount: {state['currency']} {state['amount']:,.2f}
Customer: {state['customer_id']}
"""
        
        if state.get("from_account"):
            details += f"From Account: {state['from_account']}\n"
        if state.get("to_account"):
            details += f"To Account: {state['to_account']}\n"
        if state.get("to_country"):
            details += f"Destination Country: {state['to_country']}\n"

        return details

    def _generate_risk_analysis(self, state: Dict[str, Any]) -> str:
        """Generate risk analysis section"""
        analysis = "RISK ANALYSIS\n\n"

        # Fraud analysis
        if state.get("fraud_analysis"):
            fraud = state["fraud_analysis"]
            analysis += f"Fraud Detection:\n"
            analysis += f"- Fraud Score: {fraud.get('fraud_score', 0):.2f}\n"
            for indicator in fraud.get("risk_indicators", [])[:5]:
                analysis += f"  • {indicator}\n"
            analysis += f"- Similar Historical Cases: {fraud.get('similar_cases_count', 0)}\n"
            analysis += f"- Reasoning: {fraud.get('reasoning', 'N/A')}\n\n"

        # Case history
        if state.get("case_history_analysis"):
            case = state["case_history_analysis"]
            analysis += f"Historical Case Analysis:\n"
            analysis += f"- Similar Cases Found: {case.get('similar_cases_count', 0)}\n"
            for lesson in case.get("lessons_learned", [])[:3]:
                analysis += f"  • {lesson}\n"
            analysis += "\n"

        return analysis

    def _generate_regulatory_basis(self, state: Dict[str, Any]) -> str:
        """Generate regulatory basis section"""
        basis = "REGULATORY BASIS\n\n"

        if state.get("compliance_research"):
            compliance = state["compliance_research"]
            basis += f"Applicable Regulations:\n{compliance.get('citation_text', 'None cited')}\n\n"
            
            basis += "Compliance Requirements:\n"
            for req in compliance.get("compliance_requirements", [])[:5]:
                basis += f"  • {req}\n"
        else:
            basis += "Regulatory research not completed.\n"

        return basis

    def _generate_recommendation(self, state: Dict[str, Any]) -> str:
        """Generate recommendation section"""
        rec = "RECOMMENDATION\n\n"

        risk_score = state.get("risk_score", 0.0)

        if risk_score >= 0.85:
            rec += "RECOMMENDATION: FILE SUSPICIOUS ACTIVITY REPORT\n"
            rec += "This transaction exhibits high-risk characteristics requiring immediate SAR filing.\n"
            rec += "Human review and senior management approval recommended before submission.\n"
        elif risk_score >= 0.50:
            rec += "RECOMMENDATION: ENHANCED DUE DILIGENCE\n"
            rec += "This transaction warrants enhanced monitoring and documentation.\n"
            rec += "Consider filing SAR if additional suspicious activity is detected.\n"
        else:
            rec += "RECOMMENDATION: CLEAR FOR PROCESSING\n"
            rec += "Transaction appears within normal risk parameters.\n"
            rec += "Continue routine monitoring.\n"

        # Add recommended actions from case history
        if state.get("case_history_analysis"):
            actions = state["case_history_analysis"].get("recommended_actions", [])
            if actions:
                rec += "\nRecommended Actions:\n"
                for action in actions[:5]:
                    rec += f"  • {action}\n"

        return rec

    def _assemble_sar_draft(self, exec_summary, txn_details, risk_analysis, 
                            regulatory_basis, recommendation, report_format):
        """Assemble complete SAR draft"""
        sar = f"""{'='*70}
SUSPICIOUS ACTIVITY REPORT (DRAFT)
Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
Format: {report_format.upper()}
{'='*70}

{exec_summary}

{'='*70}
{txn_details}

{'='*70}
{risk_analysis}

{'='*70}
{regulatory_basis}

{'='*70}
{recommendation}

{'='*70}
END OF REPORT
"""
        return sar

    def _collect_supporting_evidence(self, state: Dict[str, Any]) -> list:
        """Collect supporting evidence references"""
        evidence = []

        # Memory traces as evidence
        if state.get("memory_traces"):
            evidence.append({
                "type": "memory_analysis",
                "description": f"{len(state['memory_traces'])} memory queries performed",
                "details": "See memory_traces for full audit trail"
            })

        # Similar cases
        if state.get("fraud_analysis", {}).get("similar_cases"):
            cases = state["fraud_analysis"]["similar_cases"]
            evidence.append({
                "type": "historical_cases",
                "description": f"{len(cases)} similar historical SAR cases identified",
                "case_ids": [c["sar_id"] for c in cases]
            })

        # Regulations
        if state.get("compliance_research", {}).get("applicable_regulations"):
            regs = state["compliance_research"]["applicable_regulations"]
            evidence.append({
                "type": "regulations",
                "description": f"{len(regs)} applicable regulations cited",
                "regulation_ids": [r["regulation_id"] for r in regs]
            })

        return evidence
