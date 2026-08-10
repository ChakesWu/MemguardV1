"""HTTP contract for the enterprise offboarding demo."""

from __future__ import annotations

import os
import pathlib
import sys
import tempfile
from unittest.mock import patch


ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "sdk"))
sys.path.insert(0, str(ROOT / "backend"))
_db_dir = tempfile.TemporaryDirectory(prefix="memguard-handover-api-")
os.environ["MEMGUARD_DB_PATH"] = str(pathlib.Path(_db_dir.name) / "events.db")

from fastapi.testclient import TestClient  # noqa: E402
from app.auth import TenantPrincipal  # noqa: E402
from app.main import app  # noqa: E402


def test_enterprise_handover_demo_exposes_safe_manifest_for_the_signed_in_tenant():
    with patch(
        "app.main.authenticate_bearer_token",
        return_value=TenantPrincipal(subject="demo-user", tenant_id="acme", claims={}),
    ):
        response = TestClient(app).get("/v1/demo/enterprise-handover")

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "acme"
    assert payload["summary"]["transferred"] > 0
    assert payload["summary"]["protected"] > 0
    assert payload["summary"]["redacted_for_review"] > 0
    assert "medical appointment" not in payload["successor_prompt"]
    assert "secret-token-value" not in payload["successor_prompt"]
    assert any(item["outcome"] == "retained_at_source" for item in payload["items"])

    protected = [item for item in payload["items"] if item["outcome"] == "protected"]
    assert {item["content"] for item in protected} >= {
        "Recurring medical-care schedule — exact diagnosis and appointment details protected.",
        "Family caregiving availability — family member and care details protected.",
    }
    assert all("[protected employee memory]" not in item["content"] for item in protected)
