"""Shared Qt application-data location for all dataset consumers."""

import os
from pathlib import Path

from PySide6.QtCore import QStandardPaths


def default_database_path() -> Path:
    override = os.environ.get("SMARTPOWER_DB_PATH")
    if override:
        return Path(override)
    return Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)) / "datasets.sqlite3"
