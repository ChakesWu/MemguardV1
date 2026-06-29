"""TASK 5 Agent verification test suite"""
from datetime import datetime, timezone
from agents import (
    FraudDetectionAgent, CaseHistoryAgent,
    ComplianceResearchAgent, ReportGenerationAgent
)

def build_state():
    return {
        'transaction_id': 'TXN-TEST-001', 'customer_id': 'C-00412',
        'amount': 490000, 'currency': 'HKD',
        'transaction_pattern': 'structuring multiple transactions below HKD 500K threshold across jurisdictions in short time window',
        'messages': [], 'fraud_analysis': None, 'case_history_analysis': None,
        'compliance_research': None, 'final_report': None,
        'risk_score': 0.0, 'risk_level': 'unknown', 'risk_factors': [],
        'memory_traces': [], 'current_stage': 'fraud_detection',
        'requires_human_review': False, 'final_decision': None,
        'thread_id': 'test-001', 'start_time': datetime.now(timezone.utc).isoformat(),
    }

passed = 0
failed = 0

# Test 1: Fraud Detection Agent
print("=" * 70)
print("  TEST 1: FraudDetectionAgent")
print("=" * 70)
fraud = FraudDetectionAgent()
result = fraud.analyze(build_state())
fa = result['fraud_analysis']
assert fa is not None, "fraud_analysis should not be None"
assert fa['fraud_score'] > 0, f"Expected fraud_score > 0, got {fa['fraud_score']}"
assert len(fa['risk_indicators']) >= 3, f"Expected >=3 indicators, got {len(fa['risk_indicators'])}"
assert len(result['messages']) >= 1, "Should have added a message"
for ind in fa['risk_indicators']:
    print(f"  ✓ Indicator: {ind}")
print(f"  Fraud score: {fa['fraud_score']}")
print(f"  Reasoning: {fa['reasoning'][:80]}...")
print(f"✅ FraudDetectionAgent PASSED\n")
passed += 1

# Test 2: Case History Agent (without ChromaDB)
print("=" * 70)
print("  TEST 2: CaseHistoryAgent")
print("=" * 70)
result['current_stage'] = 'case_history'
case = CaseHistoryAgent()
result2 = case.analyze(result)
ch = result2['case_history_analysis']
assert ch is not None, "case_history_analysis should not be None"
assert isinstance(ch['similar_cases_count'], int), "similar_cases_count should be int"
assert len(ch['lessons_learned']) >= 1, "Should have at least 1 lesson"
print(f"  Similar cases: {ch['similar_cases_count']} (expected 0 without ChromaDB)")
for lesson in ch['lessons_learned']:
    print(f"  ✓ Lesson: {lesson}")
print(f"✅ CaseHistoryAgent PASSED\n")
passed += 1

# Test 3: Compliance Research Agent (without ChromaDB)
print("=" * 70)
print("  TEST 3: ComplianceResearchAgent")
print("=" * 70)
result2['current_stage'] = 'compliance_research'
compliance = ComplianceResearchAgent()
result3 = compliance.analyze(result2)
cr = result3['compliance_research']
assert cr is not None, "compliance_research should not be None"
assert 'applicable_regulations' in cr, "Should have applicable_regulations"
assert 'compliance_requirements' in cr, "Should have compliance_requirements"
assert 'citation_text' in cr, "Should have citation_text"
print(f"  Regulations found: {len(cr['applicable_regulations'])} (expected 0 without ChromaDB)")
for req in cr['compliance_requirements']:
    print(f"  ✓ Requirement: {req}")
print(f"✅ ComplianceResearchAgent PASSED\n")
passed += 1

# Test 4: Report Generation Agent (no ChromaDB needed)
print("=" * 70)
print("  TEST 4: ReportGenerationAgent")
print("=" * 70)
result3['current_stage'] = 'report_generation'
report = ReportGenerationAgent()
result4 = report.analyze(result3)
fr = result4['final_report']
assert fr is not None, "final_report should not be None"
assert 'sar_draft' in fr, "Should have sar_draft"
assert 'executive_summary' in fr, "Should have executive_summary"
assert 'supporting_evidence' in fr, "Should have supporting_evidence"
assert len(fr['sar_draft']) > 100, f"SAR draft too short: {len(fr['sar_draft'])} chars"
assert "SUSPICIOUS ACTIVITY REPORT" in fr['sar_draft'], "SAR draft should have title"
assert "TXN-TEST-001" in fr['sar_draft'], "SAR draft should include transaction ID"
assert "C-00412" in fr['sar_draft'], "SAR draft should include customer ID"
print(f"  SAR draft length: {len(fr['sar_draft'])} chars")
print(f"  Report format: {fr['report_format']}")
print(f"  Evidence items: {len(fr['supporting_evidence'])}")
for ev in fr['supporting_evidence']:
    print(f"  ✓ Evidence: {ev['description']}")

# Print SAR draft preview
print(f"\n  --- SAR Draft Preview (first 300 chars) ---")
print(f"  {fr['sar_draft'][:300]}...")
print(f"\n✅ ReportGenerationAgent PASSED\n")
passed += 1

# Test 5: Full pipeline integration
print("=" * 70)
print("  TEST 5: Full Agent Pipeline")
print("=" * 70)
state = build_state()
state = fraud.analyze(state)
state = case.analyze(state)
state = compliance.analyze(state)
state = report.analyze(state)

assert state['fraud_analysis'] is not None, "fraud_analysis missing"
assert state['case_history_analysis'] is not None, "case_history_analysis missing"
assert state['compliance_research'] is not None, "compliance_research missing"
assert state['final_report'] is not None, "final_report missing"
assert len(state['messages']) >= 4, f"Should have >=4 messages, got {len(state['messages'])}"

print(f"  Pipeline stages completed:")
print(f"    1. fraud_analysis: ✅")
print(f"    2. case_history_analysis: ✅")
print(f"    3. compliance_research: ✅")
print(f"    4. final_report: ✅")
print(f"  Total messages: {len(state['messages'])}")
print(f"  Final risk_score: {state['risk_score']}")
print(f"✅ Full Pipeline PASSED\n")
passed += 1

# Summary
print("=" * 70)
print(f"  RESULTS: {passed}/{passed} tests passed, {failed} failed")
print("=" * 70)
