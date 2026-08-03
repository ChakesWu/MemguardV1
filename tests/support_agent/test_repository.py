import pathlib
import sys

import pytest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "agent-server"))


@pytest.fixture()
def repository(tmp_path):
    from support_agent.repository import SupportRepository

    repo = SupportRepository(f"sqlite:///{tmp_path / 'support.db'}")
    repo.migrate()
    return repo


def test_get_order_cannot_cross_tenant(repository):
    from support_agent.seed import seed_baseline_data

    seed_baseline_data(repository, tenant_id="acme-dev")

    assert repository.get_order("other-tenant", "ORD-4821") is None
    order = repository.get_order("acme-dev", "ORD-4821")
    assert order is not None
    assert order.order_id == "ORD-4821"
    assert order.status == "delivered"


def test_memory_update_creates_new_version_and_supersedes_old_version(repository):
    first = repository.write_memory(
        tenant_id="acme-dev",
        owner_id="CUS-1042",
        kind="shipping_address",
        value={"city": "Macau"},
        source_type="user_statement",
    )
    second = repository.write_memory(
        tenant_id="acme-dev",
        owner_id="CUS-1042",
        kind="shipping_address",
        value={"city": "Hong Kong"},
        source_type="user_statement",
        supersedes_version_id=first.version_id,
    )

    assert first.version_id != second.version_id
    assert repository.get_memory("acme-dev", first.version_id).status == "superseded"
    assert repository.get_memory("acme-dev", second.version_id).value == {"city": "Hong Kong"}


def test_create_action_once_returns_same_action_for_duplicate_idempotency_key(repository):
    first = repository.create_action_once(
        tenant_id="acme-dev",
        idempotency_key="approve-refund-run-1",
        action_type="create_refund_request",
        order_id="ORD-4821",
        payload={"reason": "defective"},
        status="manual_review",
    )
    second = repository.create_action_once(
        tenant_id="acme-dev",
        idempotency_key="approve-refund-run-1",
        action_type="create_refund_request",
        order_id="ORD-4821",
        payload={"reason": "defective"},
        status="manual_review",
    )

    assert first.action_id == second.action_id
    assert len(repository.actions_for("acme-dev", "ORD-4821")) == 1


def test_postgres_customer_upsert_uses_conflict_syntax(monkeypatch):
    from unittest.mock import MagicMock

    from support_agent.domain import Customer
    from support_agent.repository import SupportRepository

    connection = MagicMock()
    monkeypatch.setattr("psycopg.connect", lambda *args, **kwargs: connection)
    repository = SupportRepository("postgresql://memguard:memguard@postgres:5432/memguard")

    repository.upsert_customer(Customer("acme-dev", "CUS-1042", "Alex Chen", "VIP", "active"))

    statement = connection.execute.call_args.args[0]
    assert "ON CONFLICT (tenant_id, customer_id) DO UPDATE" in statement
