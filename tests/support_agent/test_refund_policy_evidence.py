import pathlib
import sys


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "agent-server"))


def test_refund_policy_is_linked_as_a_constraint_when_it_requires_manual_review(tmp_path) -> None:
    from support_agent.output_evidence_report import govern_output_content
    from support_agent.repository import SupportRepository
    from support_agent.seed import seed_baseline_data

    repository = SupportRepository(f"sqlite:///{tmp_path / 'support.db'}")
    repository.migrate()
    seed_baseline_data(repository)

    answer, report = govern_output_content(
        repository=repository,
        tenant_id="acme-dev",
        content="Your defective-item claim is outside the refund window and requires manual review.",
        prompt_memory_ids={"order:ORD-4821", "policy:refund-policy:v2"},
    )

    assert answer.endswith("requires manual review.")
    assert report is not None
    policy_link = next(
        link
        for link in report["output_evidence"]["valid_links"]
        if link["memory_id"] == "policy:refund-policy:v2"
    )
    assert policy_link["role"] == "constraint"
    assert policy_link["segment"] == "requires manual review"


def test_refund_policy_constraint_is_added_when_answer_already_cites_the_order(tmp_path) -> None:
    """A factual order citation must not suppress the policy constraint link."""
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
            "Order ORD-4821 was delivered. Your defective-item claim requires manual review."
            '<memguard-evidence>{"citations":[{"segment":"ORD-4821","memory_id":"order:ORD-4821",'
            '"evidence_quote":"ORD-4821","role":"factual_support"}]}</memguard-evidence>'
        ),
        prompt_memory_ids={"order:ORD-4821", "policy:refund-policy:v2"},
    )

    assert answer.endswith("requires manual review.")
    assert report is not None
    links = report["output_evidence"]["valid_links"]
    assert {link["memory_id"] for link in links} == {"order:ORD-4821", "policy:refund-policy:v2"}
    assert next(link for link in links if link["memory_id"] == "policy:refund-policy:v2")["role"] == "constraint"


def test_refund_policy_links_manual_review_required_wording(tmp_path) -> None:
    from support_agent.output_evidence_report import govern_output_content
    from support_agent.repository import SupportRepository
    from support_agent.seed import seed_baseline_data

    repository = SupportRepository(f"sqlite:///{tmp_path / 'support.db'}")
    repository.migrate()
    seed_baseline_data(repository)

    _, report = govern_output_content(
        repository=repository,
        tenant_id="acme-dev",
        content="Refund request status: Manual review required — not yet approved.",
        prompt_memory_ids={"policy:refund-policy:v2"},
    )

    assert report is not None
    policy_link = report["output_evidence"]["valid_links"][0]
    assert policy_link["memory_id"] == "policy:refund-policy:v2"
    assert policy_link["role"] == "constraint"
    assert policy_link["segment"] == "Manual review required"
