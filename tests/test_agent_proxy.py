import pathlib
import sys


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.auth import TenantPrincipal
from app.agent_proxy import inject_trusted_agent_context


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
