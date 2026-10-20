# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import PySide6
import os
import sys
import runpy
from PyInstaller.utils.hooks import collect_submodules

# Ignore unrelated developer tool DLL directories (Poppler/libheif/etc.).
# They can expose an incompatible ICU/UCRT under the same Windows DLL names.
os.environ['PATH'] = os.pathsep.join([str(Path(sys.executable).parent),
    str(Path(os.environ['WINDIR'])/'System32'), os.environ['WINDIR']])
root = Path(SPECPATH).parent
notice_dir = root / 'build' / 'notices'
runpy.run_path(str(root / 'tools/collect_licenses.py'))['collect'](notice_dir)
assets = root / 'smartpower/assets'
a = Analysis([str(root/'main.py')], pathex=[str(root)],
    binaries=[], datas=[(str(assets),'smartpower/assets'), (str(notice_dir),'notices'),
    (str(root/'packaging/DISTRIBUTION_NOTICE.md'),'.')],
    hiddenimports=collect_submodules('reportlab.pdfbase'), hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['pytest','pypdf','matplotlib','scipy','IPython','tkinter','pandas.tests','numpy.tests',
              'PySide6.QtWebEngineCore','PySide6.QtWebEngineWidgets','PySide6.QtQml','PySide6.QtQuick','PySide6.QtDesigner','PySide6.QtTest'],
    noarchive=False, optimize=0)
# No third-party font binary is distributed. User TrueType files stay external.
a.datas = [entry for entry in a.datas if not entry[0].lower().endswith(('.ttf','.ttc','.otf','.pfb'))]
# No unused QML/VirtualKeyboard/PDF plugins: the app uses Widgets/ReportLab.
def unnecessary(name):
    lower = name.lower().replace('\\','/')
    leaf = lower.rsplit('/',1)[-1]
    return ('/qml/' in lower or '/platforminputcontexts/' in lower
            or leaf.startswith(('qt6qml','qt6quick','qt6virtualkeyboard','qt6pdf'))
            or leaf == 'qpdf.dll')
a.binaries = [entry for entry in a.binaries if not unnecessary(entry[0])]
a.datas = [entry for entry in a.datas if not unnecessary(entry[0])]
allowed_roots = [Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve(), Path(os.environ['WINDIR']).resolve()]
for destination, source, kind in a.binaries:
    if not any(Path(source).resolve().is_relative_to(base) for base in allowed_roots):
        raise RuntimeError('Unexpected native dependency outside Python/Windows: ' + destination)
# Qt 6.10 requires its shipped VC runtime. Python 3.13.0 ships an older
# vcruntime which the bootloader otherwise loads first from _internal.
# Preserve the wheel's unmodified, redistributable DLLs at that search root.
qt_root = Path(PySide6.__file__).resolve().parent
for name in ['vcruntime140.dll', 'vcruntime140_1.dll', 'msvcp140.dll', 'msvcp140_1.dll', 'msvcp140_2.dll']:
    source = qt_root / name
    if source.is_file():
        a.binaries = [entry for entry in a.binaries if entry[0].lower() != name]
        a.binaries.append((name, str(source), 'BINARY'))
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='SmartPowerAnalyzer', debug=False,
    bootloader_ignore_signals=False, strip=False, upx=False, console=bool(os.environ.get("SPA_CONSOLE")),
    icon=str(assets/'app.ico'), version=str(root/'packaging/version_info.txt'),
    manifest=str(root/'packaging/app.manifest'), uac_admin=False, uac_uiaccess=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='SmartPowerAnalyzer')
