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


if __name__ == "__main__":
    unittest.main()
