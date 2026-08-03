"""Tenant-scoped support-business persistence."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4

from .domain import Customer, MemoryRecord, Order, PolicyDocument, SupportAction
from .migrations import apply_support_migrations


def _timestamp(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


class SupportRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.driver = "postgres" if database_url.startswith(("postgres://", "postgresql://")) else "sqlite"
        if self.driver == "sqlite" and not database_url.startswith("sqlite:///"):
            raise ValueError("SQLite URLs must use sqlite:///.")

    @contextmanager
    def _connection(self) -> Iterator[Any]:
        if self.driver == "sqlite":
            path = Path(self.database_url.removeprefix("sqlite:///"))
            path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(path)
            connection.row_factory = sqlite3.Row
        else:
            import psycopg
            from psycopg.rows import dict_row

            connection = psycopg.connect(self.database_url, row_factory=dict_row)
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _execute(self, connection: Any, statement: str, params: tuple[Any, ...] = ()):
        if self.driver == "postgres":
            statement = statement.replace("?", "%s").replace("INSERT OR IGNORE", "INSERT")
            if "INSERT INTO support_schema_migrations" in statement:
                statement = statement.replace("VALUES (%s, %s)", "VALUES (%s, %s) ON CONFLICT (version) DO NOTHING")
        return connection.execute(statement, params)

    def migrate(self) -> None:
        with self._connection() as connection:
            if self.driver == "postgres":
                for statement in SUPPORT_SCHEMA_POSTGRES:
                    connection.execute(statement)
                connection.execute(
                    "INSERT INTO support_schema_migrations(version, applied_at) VALUES (%s, %s) ON CONFLICT (version) DO NOTHING",
                    (1, datetime.now().astimezone().isoformat()),
                )
            else:
                apply_support_migrations(connection)

    def get_customer(self, tenant_id: str, customer_id: str) -> Customer | None:
        with self._connection() as connection:
            row = self._execute(connection, "SELECT * FROM support_customers WHERE tenant_id = ? AND customer_id = ?", (tenant_id, customer_id)).fetchone()
        return Customer(**dict(row)) if row else None

    def get_order(self, tenant_id: str, order_id: str) -> Order | None:
        with self._connection() as connection:
            row = self._execute(connection, "SELECT * FROM support_orders WHERE tenant_id = ? AND order_id = ?", (tenant_id, order_id)).fetchone()
        if not row:
            return None
        data = dict(row)
        return Order(
            tenant_id=data["tenant_id"], order_id=data["order_id"], customer_id=data["customer_id"],
            product=data["product"], status=data["status"], delivered_at=_timestamp(data["delivered_at"]),
            payment_status=data["payment_status"], shipping_address=json.loads(data["shipping_address_json"]),
        )

    def upsert_customer(self, customer: Customer) -> None:
        with self._connection() as connection:
            statement = "INSERT OR REPLACE INTO support_customers (tenant_id, customer_id, name, tier, account_status) VALUES (?, ?, ?, ?, ?)"
            if self.driver == "postgres":
                statement = "INSERT INTO support_customers (tenant_id, customer_id, name, tier, account_status) VALUES (?, ?, ?, ?, ?) ON CONFLICT (tenant_id, customer_id) DO UPDATE SET name = EXCLUDED.name, tier = EXCLUDED.tier, account_status = EXCLUDED.account_status"
            self._execute(connection, statement, (customer.tenant_id, customer.customer_id, customer.name, customer.tier, customer.account_status))

    def upsert_order(self, order: Order) -> None:
        with self._connection() as connection:
            statement = "INSERT OR REPLACE INTO support_orders (tenant_id, order_id, customer_id, product, status, delivered_at, payment_status, shipping_address_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            if self.driver == "postgres":
                statement = "INSERT INTO support_orders (tenant_id, order_id, customer_id, product, status, delivered_at, payment_status, shipping_address_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (tenant_id, order_id) DO UPDATE SET customer_id = EXCLUDED.customer_id, product = EXCLUDED.product, status = EXCLUDED.status, delivered_at = EXCLUDED.delivered_at, payment_status = EXCLUDED.payment_status, shipping_address_json = EXCLUDED.shipping_address_json"
            self._execute(connection, statement, (order.tenant_id, order.order_id, order.customer_id, order.product, order.status, order.delivered_at.isoformat() if order.delivered_at else None, order.payment_status, json.dumps(order.shipping_address)))

    def upsert_policy(self, policy: PolicyDocument) -> None:
        with self._connection() as connection:
            statement = "INSERT OR REPLACE INTO support_policies (tenant_id, document_id, version, effective_from, policy_json, status) VALUES (?, ?, ?, ?, ?, ?)"
            if self.driver == "postgres":
                statement = "INSERT INTO support_policies (tenant_id, document_id, version, effective_from, policy_json, status) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT (tenant_id, document_id, version) DO UPDATE SET effective_from = EXCLUDED.effective_from, policy_json = EXCLUDED.policy_json, status = EXCLUDED.status"
            self._execute(connection, statement, (policy.tenant_id, policy.document_id, policy.version, policy.effective_from.isoformat(), json.dumps(policy.policy), policy.status))

    def get_memory(self, tenant_id: str, version_id: str) -> MemoryRecord | None:
        with self._connection() as connection:
            row = self._execute(connection, "SELECT * FROM support_memories WHERE tenant_id = ? AND version_id = ?", (tenant_id, version_id)).fetchone()
        return self._memory_from_row(row) if row else None

    def write_memory(self, *, tenant_id: str, owner_id: str, kind: str, value: dict[str, Any] | str, source_type: str, source_id: str | None = None, supersedes_version_id: str | None = None) -> MemoryRecord:
        memory_id = str(uuid4())
        if supersedes_version_id:
            old = self.get_memory(tenant_id, supersedes_version_id)
            if old is None:
                raise ValueError("Cannot supersede an unknown memory version")
            memory_id = old.memory_id
            with self._connection() as connection:
                self._execute(connection, "UPDATE support_memories SET status = ? WHERE tenant_id = ? AND version_id = ?", ("superseded", tenant_id, supersedes_version_id))
        record = MemoryRecord(tenant_id=tenant_id, memory_id=memory_id, version_id=str(uuid4()), owner_id=owner_id, kind=kind, value=value, source_type=source_type, source_id=source_id, valid_from=None, valid_until=None, supersedes_version_id=supersedes_version_id, trust_level="medium", status="active")
        self.insert_memory(record)
        return record

    def insert_memory(self, record: MemoryRecord) -> None:
        with self._connection() as connection:
            self._execute(connection, "INSERT INTO support_memories (tenant_id, memory_id, version_id, owner_id, kind, value_json, source_type, source_id, valid_from, valid_until, supersedes_version_id, trust_level, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (record.tenant_id, record.memory_id, record.version_id, record.owner_id, record.kind, json.dumps(record.value), record.source_type, record.source_id, record.valid_from.isoformat() if record.valid_from else None, record.valid_until.isoformat() if record.valid_until else None, record.supersedes_version_id, record.trust_level, record.status))

    def create_action_once(self, *, tenant_id: str, idempotency_key: str, action_type: str, order_id: str, payload: dict[str, Any], status: str) -> SupportAction:
        action_id = str(uuid4())
        created_at = datetime.now().astimezone()
        with self._connection() as connection:
            if self.driver == "sqlite":
                self._execute(connection, "INSERT OR IGNORE INTO support_actions (tenant_id, action_id, idempotency_key, action_type, order_id, payload_json, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (tenant_id, action_id, idempotency_key, action_type, order_id, json.dumps(payload), status, created_at.isoformat()))
            else:
                self._execute(connection, "INSERT INTO support_actions (tenant_id, action_id, idempotency_key, action_type, order_id, payload_json, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (tenant_id, idempotency_key) DO NOTHING", (tenant_id, action_id, idempotency_key, action_type, order_id, json.dumps(payload), status, created_at.isoformat()))
            row = self._execute(connection, "SELECT * FROM support_actions WHERE tenant_id = ? AND idempotency_key = ?", (tenant_id, idempotency_key)).fetchone()
        return self._action_from_row(row)

    def actions_for(self, tenant_id: str, order_id: str) -> list[SupportAction]:
        with self._connection() as connection:
            rows = self._execute(connection, "SELECT * FROM support_actions WHERE tenant_id = ? AND order_id = ? ORDER BY created_at", (tenant_id, order_id)).fetchall()
        return [self._action_from_row(row) for row in rows]

    @staticmethod
    def _memory_from_row(row: Any) -> MemoryRecord:
        data = dict(row)
        return MemoryRecord(tenant_id=data["tenant_id"], memory_id=data["memory_id"], version_id=data["version_id"], owner_id=data["owner_id"], kind=data["kind"], value=json.loads(data["value_json"]), source_type=data["source_type"], source_id=data["source_id"], valid_from=_timestamp(data["valid_from"]), valid_until=_timestamp(data["valid_until"]), supersedes_version_id=data["supersedes_version_id"], trust_level=data["trust_level"], status=data["status"])

    @staticmethod
    def _action_from_row(row: Any) -> SupportAction:
        data = dict(row)
        return SupportAction(tenant_id=data["tenant_id"], action_id=data["action_id"], idempotency_key=data["idempotency_key"], action_type=data["action_type"], order_id=data["order_id"], payload=json.loads(data["payload_json"]), status=data["status"], created_at=_timestamp(data["created_at"]))


SUPPORT_SCHEMA_POSTGRES = (
    "CREATE TABLE IF NOT EXISTS support_schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS support_customers (tenant_id TEXT NOT NULL, customer_id TEXT NOT NULL, name TEXT NOT NULL, tier TEXT NOT NULL, account_status TEXT NOT NULL, PRIMARY KEY (tenant_id, customer_id))",
    "CREATE TABLE IF NOT EXISTS support_orders (tenant_id TEXT NOT NULL, order_id TEXT NOT NULL, customer_id TEXT NOT NULL, product TEXT NOT NULL, status TEXT NOT NULL, delivered_at TEXT, payment_status TEXT NOT NULL, shipping_address_json TEXT NOT NULL DEFAULT '{}', PRIMARY KEY (tenant_id, order_id))",
    "CREATE TABLE IF NOT EXISTS support_policies (tenant_id TEXT NOT NULL, document_id TEXT NOT NULL, version TEXT NOT NULL, effective_from TEXT NOT NULL, policy_json TEXT NOT NULL, status TEXT NOT NULL, PRIMARY KEY (tenant_id, document_id, version))",
    "CREATE TABLE IF NOT EXISTS support_memories (tenant_id TEXT NOT NULL, memory_id TEXT NOT NULL, version_id TEXT NOT NULL, owner_id TEXT NOT NULL, kind TEXT NOT NULL, value_json TEXT NOT NULL, source_type TEXT NOT NULL, source_id TEXT, valid_from TEXT, valid_until TEXT, supersedes_version_id TEXT, trust_level TEXT NOT NULL, status TEXT NOT NULL, PRIMARY KEY (tenant_id, version_id))",
    "CREATE TABLE IF NOT EXISTS support_actions (tenant_id TEXT NOT NULL, action_id TEXT NOT NULL, idempotency_key TEXT NOT NULL, action_type TEXT NOT NULL, order_id TEXT NOT NULL, payload_json TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY (tenant_id, action_id), UNIQUE (tenant_id, idempotency_key))",
)
