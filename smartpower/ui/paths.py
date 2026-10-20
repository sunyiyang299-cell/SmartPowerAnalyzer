"""Shared Qt application-data location for all dataset consumers."""

import os
from pathlib import Path

from PySide6.QtCore import QStandardPaths


def default_database_path() -> Path:
    override = os.environ.get("SMARTPOWER_DB_PATH")
    if override:
        return Path(override)
    return Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)) / "datasets.sqlite3"


def default_settings_manager():
    from smartpower.settings.manager import SettingsManager
    override = os.environ.get("SMARTPOWER_SETTINGS_PATH")
    path = Path(override) if override else Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)) / "settings.json"
    directory = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation))
    if not directory.is_dir():
        directory = Path.home()
    return SettingsManager(path, directory)
