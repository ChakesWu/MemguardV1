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
        self.assertIn("Array.isArray(tracesData)", page)
        self.assertIn("database_driver", page)

    def test_dashboard_keeps_an_api_backed_output_selected(self):
        project_root = pathlib.Path(__file__).parent.parent
        page = (project_root / "frontend" / "app" / "page.tsx").read_text()
        navigator_path = (
            project_root / "frontend" / "components" / "OutputNavigator.tsx"
        )

        self.assertTrue(navigator_path.exists())
        navigator = navigator_path.read_text()

        self.assertIn("selectedTraceId", page)
        self.assertIn("setSelectedTraceId", page)
        self.assertIn("<OutputNavigator", page)
        self.assertIn("trace.trace_id === selectedTraceId", navigator)
        self.assertIn("onSelect(trace.trace_id)", navigator)


if __name__ == "__main__":
    unittest.main()
