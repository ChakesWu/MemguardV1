"""Small migration runner for support-agent business records."""

from __future__ import annotations

from datetime import datetime, timezone


SUPPORT_SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS support_schema_migrations (
        version INTEGER PRIMARY KEY,
        applied_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS support_customers (
        tenant_id TEXT NOT NULL,
        customer_id TEXT NOT NULL,
        name TEXT NOT NULL,
        tier TEXT NOT NULL,
        account_status TEXT NOT NULL,
        PRIMARY KEY (tenant_id, customer_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS support_orders (
        tenant_id TEXT NOT NULL,
        order_id TEXT NOT NULL,
        customer_id TEXT NOT NULL,
        product TEXT NOT NULL,
        status TEXT NOT NULL,
        delivered_at TEXT,
        payment_status TEXT NOT NULL,
        shipping_address_json TEXT NOT NULL DEFAULT '{}',
        PRIMARY KEY (tenant_id, order_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS support_policies (
        tenant_id TEXT NOT NULL,
        document_id TEXT NOT NULL,
        version TEXT NOT NULL,
        effective_from TEXT NOT NULL,
        policy_json TEXT NOT NULL,
        status TEXT NOT NULL,
        PRIMARY KEY (tenant_id, document_id, version)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS support_memories (
        tenant_id TEXT NOT NULL,
        memory_id TEXT NOT NULL,
        version_id TEXT NOT NULL,
        owner_id TEXT NOT NULL,
        kind TEXT NOT NULL,
        value_json TEXT NOT NULL,
        source_type TEXT NOT NULL,
        source_id TEXT,
        valid_from TEXT,
        valid_until TEXT,
        supersedes_version_id TEXT,
        trust_level TEXT NOT NULL,
        status TEXT NOT NULL,
        PRIMARY KEY (tenant_id, version_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS support_actions (
        tenant_id TEXT NOT NULL,
        action_id TEXT NOT NULL,
        idempotency_key TEXT NOT NULL,
        action_type TEXT NOT NULL,
        order_id TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (tenant_id, action_id),
        UNIQUE (tenant_id, idempotency_key)
    )
    """,
)


def apply_support_migrations(connection) -> None:
    for statement in SUPPORT_SCHEMA:
        connection.execute(statement)
    connection.execute(
        "INSERT OR IGNORE INTO support_schema_migrations(version, applied_at) VALUES (?, ?)",
        (1, datetime.now(timezone.utc).isoformat()),
    )
    connection.commit()
