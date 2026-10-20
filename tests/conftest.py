"""Deterministic offscreen defaults; temporary data stays in pytest tmp_path."""

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(autouse=True)
def isolated_user_settings(tmp_path, monkeypatch):
    """Never read or overwrite the developer's persisted personal preferences."""
    monkeypatch.setenv("SMARTPOWER_SETTINGS_PATH", str(tmp_path / "user-settings.json"))
