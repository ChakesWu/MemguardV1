import pathlib
import unittest


class PilotComposeTests(unittest.TestCase):
    def test_compose_defines_frontend_backend_and_postgres(self):
        compose_path = pathlib.Path(__file__).parent.parent / "docker-compose.yml"
        self.assertTrue(compose_path.exists())
        compose = compose_path.read_text()

        self.assertIn("frontend:", compose)
        self.assertIn("backend:", compose)
        self.assertIn("postgres:", compose)
        self.assertIn("postgresql://memguard:memguard@postgres:5432/memguard", compose)

    def test_compose_imports_reproducible_keycloak_realm(self):
        project_root = pathlib.Path(__file__).parent.parent
        compose = (project_root / "docker-compose.yml").read_text()
        realm_export = project_root / "keycloak" / "realm-export.json"

        self.assertIn("keycloak:", compose)
        self.assertIn("realm-export.json", compose)
        self.assertTrue(realm_export.exists())
        self.assertIn('"realm": "memguard"', realm_export.read_text())


if __name__ == "__main__":
    unittest.main()
