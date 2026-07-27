"""Contract checks for dashboard OIDC integration."""

import pathlib
import unittest


class FrontendOidcTests(unittest.TestCase):
    def test_dashboard_uses_keycloak_auth_for_api_requests(self):
        project_root = pathlib.Path(__file__).parent.parent
        page = (project_root / "frontend" / "app" / "page.tsx").read_text()
        auth_module = project_root / "frontend" / "lib" / "auth.ts"

        self.assertTrue(auth_module.exists())
        auth_source = auth_module.read_text()
        self.assertIn("keycloak-js", auth_source)
        self.assertIn("login-required", auth_source)
        self.assertIn("Authorization", page)


if __name__ == "__main__":
    unittest.main()
