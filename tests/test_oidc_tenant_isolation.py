"""Phase 2 contract tests for OIDC authentication and tenant isolation."""

import os
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch


_db_dir = tempfile.TemporaryDirectory(prefix="memguard-oidc-")
os.environ["MEMGUARD_DB_PATH"] = os.path.join(_db_dir.name, "events.db")
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.auth import TenantAccessError, TenantPrincipal, enforce_tenant  # noqa: E402
from app.main import app  # noqa: E402


class OidcTenantIsolationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_evidence_api_rejects_missing_bearer_token(self):
        response = self.client.get("/v1/events")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Missing bearer token"})

    def test_cors_preflight_is_not_authenticated(self):
        response = self.client.options(
            "/v1/db/stats",
            headers={
                "Origin": "http://localhost:3001",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:3001")

    def test_token_tenant_cannot_be_overridden_by_request_data(self):
        with self.assertRaises(TenantAccessError):
            enforce_tenant("acme-dev", "other-tenant")

    @patch("app.main.authenticate_bearer_token")
    def test_api_rejects_cross_tenant_memory_write(self, authenticate_bearer_token):
        authenticate_bearer_token.return_value = TenantPrincipal(
            subject="demo-user",
            tenant_id="acme-dev",
            claims={"sub": "demo-user", "tenant_id": "acme-dev"},
        )

        response = self.client.post(
            "/v1/memory/write",
            headers={"Authorization": "Bearer test-token"},
            json={
                "tenant_id": "other-tenant",
                "agent_id": "test-agent",
                "content": "This write must be denied.",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {"detail": "Token tenant does not match requested tenant"},
        )


if __name__ == "__main__":
    unittest.main()
