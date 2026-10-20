"""Explicit SQLite initialization, without fabricated electrical records."""

import sqlite3
from pathlib import Path


def initialize_database(path: str | Path) -> None:
    """Create only schema metadata when explicitly requested by a caller.

    No database is created at application startup. Dataset tables and schema
    migrations belong to subsequent data-management releases.
    """
    connection = sqlite3.connect(path)
    try:
        with connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS app_metadata "
                "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            connection.execute(
                "INSERT OR IGNORE INTO app_metadata (key, value) VALUES (?, ?)",
                ("schema_version", "1"),
            )
    finally:
        connection.close()
