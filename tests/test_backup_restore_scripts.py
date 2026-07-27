"""Contract checks for pilot PostgreSQL backup and restore commands."""

import pathlib
import unittest


class BackupRestoreScriptTests(unittest.TestCase):
    def test_backup_and_restore_scripts_use_postgres_custom_dumps(self):
        root = pathlib.Path(__file__).parent.parent
        backup = root / "scripts" / "backup-postgres.sh"
        restore = root / "scripts" / "restore-postgres.sh"

        self.assertTrue(backup.exists())
        self.assertTrue(restore.exists())
        self.assertIn("pg_dump", backup.read_text())
        self.assertIn("--format=custom", backup.read_text())
        self.assertIn("pg_restore", restore.read_text())
        self.assertIn("--clean", restore.read_text())


if __name__ == "__main__":
    unittest.main()
