"""Exercise main.py and its event loop in a bounded child process."""

import os
from pathlib import Path
import subprocess
import sys
import unittest


class EntrypointTests(unittest.TestCase):
    def test_main_starts_window_and_exits_cleanly(self):
        env = os.environ.copy()
        env.setdefault("QT_QPA_PLATFORM", "offscreen")
        script = """
import runpy
from PySide6.QtCore import QTimer
from smartpower.application import create_application
from smartpower.config import APP_NAME
from smartpower.ui.main_window import MainWindow
app = create_application([])
def inspect_window():
    windows = [w for w in app.topLevelWidgets() if isinstance(w, MainWindow)]
    valid = len(windows) == 1 and windows[0].isVisible() and windows[0].windowTitle() == APP_NAME
    if valid:
        print('ENTRYPOINT_WINDOW_OK', flush=True)
    app.exit(0 if valid else 1)
QTimer.singleShot(200, inspect_window)
runpy.run_path('main.py', run_name='__main__')
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=Path(__file__).resolve().parents[1],
            env=env, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ENTRYPOINT_WINDOW_OK", result.stdout)
