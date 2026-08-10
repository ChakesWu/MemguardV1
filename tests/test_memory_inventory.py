"""Contract for the human-readable governed memory inventory."""

from __future__ import annotations

import os
import pathlib
import sys
import tempfile


ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "sdk"))
sys.path.insert(0, str(ROOT / "backend"))

from app.services import MemoryGateway  # noqa: E402


def test_inventory_exposes_real_content_and_non_synthetic_governance_factors() -> None:
    with tempfile.TemporaryDirectory(prefix="memguard-inventory-") as directory:
        os.environ["MEMGUARD_DB_PATH"] = str(pathlib.Path(directory) / "events.db")
        gateway = MemoryGateway()
        with gateway.database.connect() as conn:
            conn.execute("""CREATE TABLE support_orders (
                tenant_id TEXT, order_id TEXT, customer_id TEXT, product TEXT, status TEXT,
                delivered_at TEXT, payment_status TEXT, shipping_address_json TEXT,
                source_type TEXT, source_id TEXT, writer_id TEXT, source_updated_at TEXT,
                verified_at TEXT, conflict_status TEXT
            )""")
            conn.execute("""CREATE TABLE support_policies (
                tenant_id TEXT, document_id TEXT, version TEXT, effective_from TEXT,
                policy_json TEXT, status TEXT
            )""")
            conn.execute("""CREATE TABLE support_memories (
                tenant_id TEXT, memory_id TEXT, version_id TEXT, owner_id TEXT, kind TEXT,
                value_json TEXT, source_type TEXT, source_id TEXT, valid_from TEXT,
                valid_until TEXT, supersedes_version_id TEXT, trust_level TEXT, status TEXT
            )""")
            conn.execute(
                "INSERT INTO support_orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    "acme", "ORD-4821", "CUS-1042", "Noise-cancelling headphones", "delivered",
                    "2026-07-05T10:00:00+00:00", "paid", "{}", "support_order_db", "ORD-4821",
                    "support-order-sync", "2026-08-07T00:00:00+00:00", "2026-08-08T00:00:00+00:00", "none",
                ),
            )
            conn.commit()

        items = gateway.governed_memory_inventory("acme")

    order = next(item for item in items if item["memory_id"] == "order:ORD-4821")
    assert order["display_name"] == "Noise-cancelling headphones order"
    assert "Delivered July 5, 2026" in order["summary"]
    assert order["trust_score"] is not None
    assert order["trust_factors"]["source"]["reason"]
    assert order["trust_factors"]["conflict"]["score"] == 100
