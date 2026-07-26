import os
import pathlib
import sys
import unittest
from unittest.mock import patch


sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "backend"))


class DatabaseConfigTests(unittest.TestCase):
    def test_defaults_to_sqlite_for_local_development(self):
        with patch.dict(os.environ, {}, clear=True):
            from app.database import DatabaseConfig

            config = DatabaseConfig.from_env()

        self.assertEqual(config.driver, "sqlite")
        self.assertTrue(config.url.startswith("sqlite:///"))

    def test_uses_postgres_database_url_when_configured(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://memguard:secret@db:5432/memguard"}, clear=True):
            from app.database import DatabaseConfig

            config = DatabaseConfig.from_env()

        self.assertEqual(config.driver, "postgres")
        self.assertEqual(config.url, "postgresql://memguard:secret@db:5432/memguard")


if __name__ == "__main__":
    unittest.main()
