import pathlib
import sys


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "agent-server"))


def test_extracts_explicit_citations_and_removes_protocol_block_from_answer() -> None:
    from support_agent.output_evidence import extract_explicit_citations

    answer, citations = extract_explicit_citations(
        "ORD-4821 is delivered.\n"
        '<memguard-evidence>{"citations":[{"segment":"ORD-4821","memory_id":"order:ORD-4821",'
        '"evidence_quote":"ORD-4821","role":"factual_support"}]}</memguard-evidence>'
    )

    assert answer == "ORD-4821 is delivered."
    assert len(citations) == 1
    assert citations[0].memory_id == "order:ORD-4821"
    assert citations[0].start_offset == 0
    assert citations[0].end_offset == 8


def test_rejects_protocol_block_when_a_cited_segment_is_not_in_the_visible_answer() -> None:
    from support_agent.output_evidence import extract_explicit_citations

    answer, citations = extract_explicit_citations(
        "ORD-4821 is delivered.\n"
        '<memguard-evidence>{"citations":[{"segment":"wrong segment","memory_id":"order:ORD-4821",'
        '"evidence_quote":"ORD-4821","role":"factual_support"}]}</memguard-evidence>'
    )

    assert answer == "ORD-4821 is delivered."
    assert citations == ()
