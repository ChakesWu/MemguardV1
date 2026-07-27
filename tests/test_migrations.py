"""Contract tests for MemGuard's versioned database migrations."""

import pathlib
import sys
import tempfile
import unittest


sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "backend"))


class MigrationTests(unittest.TestCase):
    def test_initial_schema_migration_is_recorded_and_idempotent(self):
        from app.database import DatabaseConfig
        from app.migrations import apply_migrations

        with tempfile.TemporaryDirectory(prefix="memguard-migrations-") as directory:
            database = DatabaseConfig(url=f"sqlite:///{directory}/memguard.db", driver="sqlite")

            apply_migrations(database)
            apply_migrations(database)

            with database.connect() as connection:
                versions = connection.execute(
                    "SELECT version FROM schema_migrations ORDER BY version"
                ).fetchall()
                events_table = connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'memory_events'"
                ).fetchone()

        self.assertEqual([row["version"] for row in versions], [1])
        self.assertIsNotNone(events_table)


if __name__ == "__main__":
    unittest.main()
