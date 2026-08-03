import pathlib
import sys


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.auth import TenantPrincipal
import pytest

from app.agent_proxy import (
    create_tenant_thread_id,
    inject_trusted_agent_context,
    is_allowed_thread_path,
)


def test_agent_proxy_overwrites_browser_supplied_identity() -> None:
    principal = TenantPrincipal(
        subject="keycloak-user-123",
        tenant_id="acme-dev",
        claims={"sub": "keycloak-user-123", "tenant_id": "acme-dev"},
    )
    payload = {
        "input": {"messages": [{"role": "user", "content": "Refund ORD-4821"}]},
        "config": {"configurable": {"tenant_id": "other-tenant", "actor_id": "attacker", "ui_mode": "chat"}},
        "context": {"tenant_id": "other-tenant", "actor_id": "attacker"},
    }

    secured = inject_trusted_agent_context(payload, principal)

    assert secured["config"]["configurable"]["tenant_id"] == "acme-dev"
    assert secured["config"]["configurable"]["actor_id"] == "keycloak-user-123"
    assert secured["config"]["configurable"]["ui_mode"] == "chat"
    assert secured["context"] == {"tenant_id": "acme-dev", "actor_id": "keycloak-user-123"}


def test_agent_proxy_does_not_mutate_original_browser_payload() -> None:
    principal = TenantPrincipal(subject="user-1", tenant_id="acme-dev", claims={})
    payload = {"config": {"configurable": {"tenant_id": "other-tenant"}}}

    inject_trusted_agent_context(payload, principal)

    assert payload["config"]["configurable"]["tenant_id"] == "other-tenant"


def test_agent_proxy_generates_thread_ids_owned_by_the_token_tenant() -> None:
    acme = TenantPrincipal(subject="user-1", tenant_id="acme-dev", claims={})
    other = TenantPrincipal(subject="user-2", tenant_id="other-tenant", claims={})
    thread_id = create_tenant_thread_id(acme)

    assert is_allowed_thread_path(f"threads/{thread_id}/history", acme)
    assert not is_allowed_thread_path(f"threads/{thread_id}/history", other)


@pytest.mark.parametrize("path", ["threads/search", "threads/count", "threads/prune"])
def test_agent_proxy_blocks_global_thread_enumeration(path: str) -> None:
    principal = TenantPrincipal(subject="user-1", tenant_id="acme-dev", claims={})

    assert not is_allowed_thread_path(path, principal)


def test_agent_proxy_rejects_dot_segments_that_could_normalize_to_global_routes() -> None:
    principal = TenantPrincipal(subject="user-1", tenant_id="acme-dev", claims={})
    thread_id = create_tenant_thread_id(principal)

    assert not is_allowed_thread_path(f"threads/{thread_id}/../search", principal)
