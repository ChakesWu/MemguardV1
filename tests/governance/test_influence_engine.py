from __future__ import annotations

from memguard.governance import InfluenceEngine, MemoryEvidence, RetrievalSignals


def test_influence_separates_availability_from_output_support():
    evidence = MemoryEvidence(
        memory_id="m1",
        tenant_id="acme",
        content="Acme requires SAML SSO.",
        source_type="crm",
        retrieval=RetrievalSignals(similarity=0.8, retrieved=True, included_in_prompt=True, cited=True),
    )

    result = InfluenceEngine().evaluate(evidence, output_text="Acme requires SAML SSO before renewal.")

    assert result.retrieved is True
    assert result.included_in_prompt is True
    assert result.cited is True
    assert result.output_supported is True
    assert 0 < result.score <= 1
    assert "evidence:available_to_model" in result.reason_codes
    assert "evidence:output_support" in result.reason_codes


def test_retrieved_but_blocked_memory_has_no_prompt_influence():
    evidence = MemoryEvidence(
        memory_id="m2",
        tenant_id="acme",
        content="Secret token value",
        source_type="note",
        retrieval=RetrievalSignals(similarity=0.95, retrieved=True, included_in_prompt=False, cited=False),
    )

    result = InfluenceEngine().evaluate(evidence, output_text="General answer")

    assert result.score == 0.15
    assert result.included_in_prompt is False
    assert result.output_supported is False
