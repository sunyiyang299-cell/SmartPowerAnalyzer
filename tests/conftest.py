"""Deterministic offscreen defaults; temporary data stays in pytest tmp_path."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
