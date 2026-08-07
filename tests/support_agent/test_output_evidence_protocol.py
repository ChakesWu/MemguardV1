import pathlib
import sys


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "agent-server"))
sys.path.insert(0, str(PROJECT_ROOT / "sdk"))


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


def test_builds_a_governed_report_only_for_a_memory_seen_by_the_model(tmp_path) -> None:
    from support_agent.output_evidence import ExplicitCitation
    from support_agent.output_evidence_report import build_output_evidence_report
    from support_agent.repository import SupportRepository
    from support_agent.seed import seed_baseline_data

    repository = SupportRepository(f"sqlite:///{tmp_path / 'support.db'}")
    repository.migrate()
    seed_baseline_data(repository)
    answer = "ORD-4821 is delivered."
    report = build_output_evidence_report(
        repository=repository,
        tenant_id="acme-dev",
        answer=answer,
        citations=(ExplicitCitation(0, 8, "ORD-4821", "order:ORD-4821", "ORD-4821", "factual_support"),),
        prompt_memory_ids={"order:ORD-4821"},
    )

    assert report["output_evidence"]["summary"]["valid_links"] == 1
    assert report["output_evidence"]["valid_links"][0]["memory_id"] == "order:ORD-4821"
    assert report["output_evidence"]["valid_links"][0]["evidence_quote"] == "[hash-only]"


def test_does_not_report_a_citation_for_memory_not_seen_by_the_model(tmp_path) -> None:
    from support_agent.output_evidence import ExplicitCitation
    from support_agent.output_evidence_report import build_output_evidence_report
    from support_agent.repository import SupportRepository
    from support_agent.seed import seed_baseline_data

    repository = SupportRepository(f"sqlite:///{tmp_path / 'support.db'}")
    repository.migrate()
    seed_baseline_data(repository)
    report = build_output_evidence_report(
        repository=repository,
        tenant_id="acme-dev",
        answer="ORD-4821 is delivered.",
        citations=(ExplicitCitation(0, 8, "ORD-4821", "order:ORD-4821", "ORD-4821", "factual_support"),),
        prompt_memory_ids=set(),
    )

    assert report["output_evidence"]["summary"]["valid_links"] == 0


def test_governs_private_protocol_content_before_it_reaches_the_ui(tmp_path) -> None:
    from support_agent.output_evidence_report import govern_output_content
    from support_agent.repository import SupportRepository
    from support_agent.seed import seed_baseline_data

    repository = SupportRepository(f"sqlite:///{tmp_path / 'support.db'}")
    repository.migrate()
    seed_baseline_data(repository)
    answer, report = govern_output_content(
        repository=repository,
        tenant_id="acme-dev",
        content=(
            "ORD-4821 is delivered.\n"
            '<memguard-evidence>{"citations":[{"segment":"ORD-4821","memory_id":"order:ORD-4821",'
            '"evidence_quote":"ORD-4821","role":"factual_support"}]}</memguard-evidence>'
        ),
        prompt_memory_ids={"order:ORD-4821"},
    )

    assert answer == "ORD-4821 is delivered."
    assert report["output_evidence"]["summary"]["valid_links"] == 1


def test_governs_visible_support_order_fields_without_private_protocol(tmp_path) -> None:
    from support_agent.output_evidence_report import govern_output_content
    from support_agent.repository import SupportRepository
    from support_agent.seed import seed_baseline_data

    repository = SupportRepository(f"sqlite:///{tmp_path / 'support.db'}")
    repository.migrate()
    seed_baseline_data(repository)
    answer, report = govern_output_content(
        repository=repository,
        tenant_id="acme-dev",
        content="ORD-4821 was delivered and payment is paid.",
        prompt_memory_ids={"order:ORD-4821"},
    )

    assert answer == "ORD-4821 was delivered and payment is paid."
    assert report["output_evidence"]["summary"]["valid_links"] >= 3
    assert {link["segment"] for link in report["output_evidence"]["valid_links"]} >= {"ORD-4821", "delivered", "paid"}


def test_support_order_evidence_has_a_complete_high_trust_assessment(tmp_path) -> None:
    from support_agent.output_evidence_report import govern_output_content
    from support_agent.repository import SupportRepository
    from support_agent.seed import seed_baseline_data

    repository = SupportRepository(f"sqlite:///{tmp_path / 'support.db'}")
    repository.migrate()
    seed_baseline_data(repository)

    _, report = govern_output_content(
        repository=repository,
        tenant_id="acme-dev",
        content="ORD-4821 was delivered.",
        prompt_memory_ids={"order:ORD-4821"},
    )

    link = report["output_evidence"]["valid_links"][0]
    assert link["trust"]["score"] is not None
    assert 80 < link["trust"]["score"] < 100
    assert link["trust"]["level"] == "high"
    assert link["policy"]["action"] == "allow"
    assert link["trust"]["factors"]["writer"]["score"] == 88
    assert link["trust"]["factors"]["freshness"]["score"] < 100
