import sqlite3
import tempfile
import unittest
from pathlib import Path

from smartpower.storage.database import initialize_database


class DatabaseTests(unittest.TestCase):
    def test_explicit_initialization_is_idempotent_and_has_no_analysis_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workspace.sqlite3"
            initialize_database(path)
            initialize_database(path)
            connection = sqlite3.connect(path)
            try:
                self.assertEqual(connection.execute("SELECT * FROM app_metadata").fetchall(),
                                 [("schema_version", "1")])
                self.assertEqual(connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall(), [("app_metadata",)])
            finally:
                connection.close()
