"""Probe minimum-size page reachability in a separate Qt DPI-scaled process."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize('scale', ['1', '1.25', '1.5'])
def test_scaled_minimum_window_navigation_in_child(tmp_path, scale):
    script = '''
import json, sys
from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest
from smartpower.application import create_application
from smartpower.ui.main_window import MainWindow
app=create_application([])
w=MainWindow(); w.resize(900,620); w.show(); QTest.qWait(150)
assert w.size().width()==900 and w.size().height()==620
base_scale = 1.0
if app.platformName() == 'windows':
    import ctypes
    from ctypes import wintypes
    get_dpi = ctypes.windll.user32.GetDpiForWindow
    get_dpi.argtypes = [wintypes.HWND]
    get_dpi.restype = wintypes.UINT
    base_scale = get_dpi(int(w.winId())) / 96
assert abs(w.devicePixelRatioF() - base_scale*float(sys.argv[1])) < .02, (w.devicePixelRatioF(), base_scale, sys.argv[1])
for key,page in w.pages.items():
    w.navigate(key); QTest.qWait(20)
    assert w.stack.currentWidget() is page and page.isVisible()
    assert page.title_label.text()
    assert page.viewport().width() > 500
    # Content can be reached by scrolling, rather than clipped outside a fixed container.
    page.verticalScrollBar().setValue(page.verticalScrollBar().maximum())
    app.processEvents()
    assert page.verticalScrollBar().value()==page.verticalScrollBar().maximum()
w.navigate('reports'); assert w.grab().save(sys.argv[2])
w.close(); app.processEvents()
print(json.dumps({'scale':w.devicePixelRatioF(),'pages':8,'size':[900,620]}))
'''
    env = os.environ.copy()
    env['QT_SCALE_FACTOR'] = scale
    # Preserve requested platform: native run uses windows, CI uses offscreen.
    env.setdefault('QT_QPA_PLATFORM', 'offscreen')
    result = subprocess.run([sys.executable, '-c', script, scale, str(tmp_path / '布局.png')],
                            cwd=Path(__file__).resolve().parents[1], env=env,
                            capture_output=True, text=True, encoding='utf-8', timeout=45)
    assert result.returncode == 0, result.stdout + result.stderr
    measured = json.loads(result.stdout)
    assert measured['pages'] == 8
    import struct
    png = (tmp_path / '布局.png').read_bytes()
    assert png[:8] == b'\x89PNG\r\n\x1a\n'
    width, height = struct.unpack('>II', png[16:24])
    assert abs(width - 900*measured['scale']) <= 1
    assert abs(height - 620*measured['scale']) <= 1
