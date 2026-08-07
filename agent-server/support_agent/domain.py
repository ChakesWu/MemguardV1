"""Typed domain records for the standalone customer-support agent."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Customer:
    tenant_id: str
    customer_id: str
    name: str
    tier: str
    account_status: str


@dataclass(frozen=True)
class Order:
    tenant_id: str
    order_id: str
    customer_id: str
    product: str
    status: str
    delivered_at: datetime | None
    payment_status: str
    shipping_address: dict[str, Any]
    source_type: str = "unknown"
    source_id: str | None = None
    writer_id: str | None = None
    source_updated_at: datetime | None = None
    verified_at: datetime | None = None
    conflict_status: str = "unknown"


@dataclass(frozen=True)
class PolicyDocument:
    tenant_id: str
    document_id: str
    version: str
    effective_from: datetime
    policy: dict[str, Any]
    status: str


@dataclass(frozen=True)
class MemoryRecord:
    tenant_id: str
    memory_id: str
    version_id: str
    owner_id: str
    kind: str
    value: dict[str, Any] | str
    source_type: str
    source_id: str | None
    valid_from: datetime | None
    valid_until: datetime | None
    supersedes_version_id: str | None
    trust_level: str
    status: str


@dataclass(frozen=True)
class SupportAction:
    tenant_id: str
    action_id: str
    idempotency_key: str
    action_type: str
    order_id: str
    payload: dict[str, Any]
    status: str
    created_at: datetime
