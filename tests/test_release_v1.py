"""V1.0 resource, bounded-PDF and real source-entry regression checks."""
from dataclasses import replace
import json
from pathlib import Path
import re
import subprocess
import sys

import pytest
from PIL import Image
from pypdf import PdfReader

from smartpower.config import APP_NAME, APP_VERSION
from smartpower.data.demo import generate_demo
from smartpower.anomaly.models import Thresholds
from smartpower.reporting.pdf_exporter import DeferredEventTable, export_pdf
from smartpower.reporting.service import build_report_snapshot
from smartpower.storage.repository import DatasetRepository
from smartpower.resources import resource_path


def test_formal_version_identity_and_owned_icon_resources():
    assert APP_VERSION == '1.0.0'
    assert APP_NAME == '智电析电力系统运行数据分析与可视化软件 V1.0'
    with Image.open(resource_path('app.ico')) as icon:
        assert {(16,16),(32,32),(48,48),(256,256)} <= icon.ico.sizes()
    assert '<svg' in resource_path('app.svg').read_text(encoding='utf-8-sig')


def test_resource_lookup_is_independent_of_cwd_and_cannot_escape(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert resource_path('app.ico').is_file()
    with pytest.raises(ValueError):resource_path('../config.py')


def test_event_table_is_lazy_and_materializes_only_bounded_batch():
    from types import SimpleNamespace
    event = SimpleNamespace(row_index=1,timestamp='2026-01-01',kind='电压偏高',value=240,threshold=230,unit='V')
    calls=[]
    class Table:
        def wrapOn(self, *args): return (495,100)
    def make(rows,widths):calls.append(rows); return Table()
    table=DeferredEventTable((event,)*100000,256,512,make)
    assert not calls and table._table is None
    table.canv=None
    table.wrap(495,700)
    assert len(calls)==1 and len(calls[0])==257
    table.wrap(495,700)
    assert len(calls)==1


def test_pdf_crosses_batches_without_losing_events_or_glyph_checks(tmp_path):
    repo=DatasetRepository(tmp_path/'isolated.sqlite3')
    identifier=repo.save(generate_demo(600),'分块报告模拟数据')
    snapshot=build_report_snapshot(repo,identifier,thresholds=Thresholds(1,2,.1))
    assert len(snapshot.detection.events)==1200
    path=tmp_path/'full.pdf'
    export_pdf(snapshot,path)
    reader=PdfReader(path)
    text='\n'.join(page.extract_text() for page in reader.pages)
    actual=re.findall(r'(\d+)\n(\d{4}-\d{2}-\d{2} [\d:.]+)\n(电压偏高|电流偏高)\n([\d.e+\-]+)\n([\d.e+\-]+)\n([VA])\n',text)
    expected=[(str(e.row_index),str(e.timestamp).replace('T',' '),e.kind,f'{e.value:.12g}',f'{e.threshold:.12g}',e.unit) for e in snapshot.detection.events]
    assert actual==expected
    from smartpower.data.validation import DataError
    last=replace(snapshot.detection.events[-1],kind='缺字😀')
    changed=replace(snapshot,detection=replace(snapshot.detection,events=snapshot.detection.events[:-1]+(last,)))
    with pytest.raises(DataError,match='缺少'):
        export_pdf(changed,tmp_path/'unsupported.pdf')
    assert not (tmp_path/'unsupported.pdf').exists()


def test_source_release_entry_full_business_and_reopen(tmp_path):
    root=Path(__file__).resolve().parents[1]
    directory=tmp_path/'隔离验证'
    for flag,result_name in [('--release-check','result.json'),('--release-reopen','reopen-result.json')]:
        result=subprocess.run([sys.executable,'main.py',flag,str(directory)],cwd=root,capture_output=True,timeout=120)
        assert result.returncode==0, result.stderr.decode('utf-8',errors='replace')
        evidence=json.loads((directory/result_name).read_text(encoding='utf-8'))
        assert evidence['status']=='PASS' and evidence['records']==1000
        assert not evidence['frozen'] and evidence['version']=='1.0.0'
    assert len(list((directory/'screenshots').glob('*.png')))==8


def test_release_verifier_never_overwrites_existing_user_directory(tmp_path):
    directory=tmp_path/'private'
    directory.mkdir()
    original=directory/'important.txt'; original.write_bytes(b'preserve this file')
    root=Path(__file__).resolve().parents[1]
    result=subprocess.run([sys.executable,'main.py','--release-check',str(directory)],cwd=root,capture_output=True,timeout=30)
    assert result.returncode!=0
    assert original.read_bytes()==b'preserve this file'
    assert list(directory.iterdir())==[original]


def test_main_window_is_shown_only_after_event_loop_is_ready():
    root=Path(__file__).resolve().parents[1]
    script='''
from PySide6.QtCore import QThread
from smartpower import application
original=application.MainWindow.show
observed=[]
def show(window):
    observed.append(QThread.currentThread().loopLevel())
    assert observed[-1] > 0, 'window shown before event loop is ready'
    original(window)
    window.close()
application.MainWindow.show=show
assert application.main()==0
assert observed
'''
    result=subprocess.run([sys.executable,'-c',script],cwd=root,capture_output=True,timeout=30)
    assert result.returncode==0,result.stderr.decode('utf-8',errors='replace')
