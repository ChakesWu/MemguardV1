import pathlib
import sys
from uuid import UUID


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.auth import TenantPrincipal
import pytest

from app.agent_proxy import (
    create_tenant_thread_id,
    governed_output_records,
    inject_trusted_agent_context,
    is_allowed_thread_path,
)


def test_governed_output_records_preserve_the_human_evidence_story() -> None:
    report = {
        "items": [
            {
                "memory_id": "order:ORD-4821",
                "content": "Order ORD-4821 is for noise-cancelling headphones; delivered July 5, 2026; payment paid.",
                "content_hash": "order-hash",
                "source": {"type": "support_order_db", "id": "ORD-4821", "writer_id": "support-order-sync"},
                "trust": {
                    "score": 94.67,
                    "level": "high",
                    "factors": {
                        "source": {"score": 92, "reason": "authoritative order database"},
                        "writer": {"score": 88, "reason": "verified sync service"},
                        "freshness": {"score": 93, "reason": "verified one day ago"},
                        "conflict": {"score": 100, "reason": "no conflicting order record"},
                    },
                },
                "policy": {"action": "allow", "reason_codes": ["trust:high"], "explanation": "Meets the allow threshold."},
                "influence": {"score": 0.8, "included_in_prompt": True},
            },
            {
                "memory_id": "MEM-EXCEPTION-77",
                "content": "[redacted]",
                "content_hash": "expired-hash",
                "source": {"type": "support_agent_note", "id": "TICKET-8842", "writer_id": None},
                "trust": {"score": 55, "level": "low", "factors": {}},
                "policy": {"action": "block", "reason_codes": ["lifecycle:expired"], "explanation": "The exception expired."},
                "influence": {"score": 0, "included_in_prompt": False},
            },
        ],
        "output_evidence": {
            "valid_links": [
                {
                    "memory_id": "order:ORD-4821",
                    "segment": "Your order was delivered and paid.",
                    "evidence_quote": "delivered July 5, 2026; payment paid",
                    "role": "factual_support",
                    "prompt_included": True,
                    "validation_status": "valid",
                    "trust": {"score": 94.67, "level": "high"},
                    "policy": {"action": "allow"},
                    "influence": {"score": 0.8},
                }
            ]
        },
    }

    events, trace = governed_output_records(
        tenant_id="acme-dev",
        agent_id="customer_support_agent",
        session_id="thread-1",
        user_input="Can I get a refund?",
        answer="Your order was delivered and paid.",
        report=report,
    )

    assert events[0].content.startswith("Order ORD-4821 is for noise-cancelling headphones")
    assert events[0].content_hash == "order-hash"
    assert events[0].metadata["evidence_quote"] == "delivered July 5, 2026; payment paid"
    assert events[0].metadata["output_segment"] == "Your order was delivered and paid."
    assert events[0].metadata["trust_factors"]["conflict"]["score"] == 100
    considered = trace.metadata["considered_memories"]
    assert next(item for item in considered if item["memory_id"] == "order:ORD-4821")["usage"] == "used"
    assert next(item for item in considered if item["memory_id"] == "MEM-EXCEPTION-77")["usage"] == "rejected"


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

    assert "config" not in secured
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

    UUID(thread_id)
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
