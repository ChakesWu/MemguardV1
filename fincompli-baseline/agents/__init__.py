"""
Agents Module

Contains all compliance analysis agents.
"""

from .base import BaseAgent
from .fraud_detection import FraudDetectionAgent
from .case_history import CaseHistoryAgent
from .compliance_research import ComplianceResearchAgent
from .report_generation import ReportGenerationAgent
from .supervisor import SupervisorAgent

__all__ = [
    "BaseAgent",
    "FraudDetectionAgent",
    "CaseHistoryAgent",
    "ComplianceResearchAgent",
    "ReportGenerationAgent",
    "SupervisorAgent",
]
