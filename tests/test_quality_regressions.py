from decimal import Decimal, localcontext
from pathlib import Path

import numpy as np
import pytest

from smartpower.analysis.statistics import summarize
from smartpower.data.demo import export_demo, generate_demo
from smartpower.data.validation import DataError
from smartpower.settings.manager import SettingsManager


@pytest.mark.parametrize('values', [[1e16, 1e16 + 2], [220., np.nextafter(220., np.inf)], [1e308, np.nextafter(1e308, np.inf)], [0., 1e-320]])
def test_population_deviation_matches_independent_decimal(values):
    with localcontext() as context:
        context.prec = 400
        exact = [Decimal.from_float(float(x)) for x in values]
        mean = sum(exact) / len(exact)
        deviation = (sum((x - mean) ** 2 for x in exact) / len(exact)).sqrt()
    result = summarize(values, '电压', 'V')
    assert result.population_std == pytest.approx(float(deviation), rel=2e-15, abs=0)
    assert result.mean == pytest.approx(float(mean), rel=2e-16, abs=0)


def test_settings_permission_failure_falls_back_without_writing(tmp_path, monkeypatch):
    manager = SettingsManager(tmp_path / '设置.json', tmp_path)
    def denied(self):
        raise PermissionError('测试：无读取权限')
    monkeypatch.setattr(Path, 'exists', denied)
    loaded = manager.load()
    assert loaded.value == manager.defaults
    assert '无法读取' in loaded.warning and '权限' in loaded.warning


def test_csv_export_refuses_unconfirmed_replacement(tmp_path):
    path = tmp_path / '原文件.csv'
    original = b'original private contents'
    path.write_bytes(original)
    with pytest.raises(DataError, match='已存在'):
        export_demo(generate_demo(3), path)
    assert path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [path]

@pytest.mark.parametrize('u,i,pf', [(1e-200, 1e-200, .9), (1e-300, 1., 1e-100), (np.nextafter(0., 1.), 1., np.nextafter(1., 0.))])
def test_nonzero_power_underflow_is_not_reported_as_zero(u, i, pf):
    from smartpower.analysis.power import analyze_power
    from smartpower.analysis.statistics import AnalysisError
    with pytest.raises(AnalysisError, match='可表示范围'):
        analyze_power([u], [i], [pf])


def test_csv_publication_race_does_not_replace_new_file(tmp_path, monkeypatch):
    import pandas as pd
    target = tmp_path / '并发.csv'
    write = pd.DataFrame.to_csv
    def create_competing_file(frame, *args, **kwargs):
        result = write(frame, *args, **kwargs)
        target.write_bytes(b'created by another process')
        return result
    monkeypatch.setattr(pd.DataFrame, 'to_csv', create_competing_file)
    with pytest.raises(DataError):
        export_demo(generate_demo(3), target)
    assert target.read_bytes() == b'created by another process'
    assert list(tmp_path.iterdir()) == [target]


def test_csv_gui_requires_one_explicit_confirmation(tmp_path, monkeypatch):
    from smartpower.application import create_application
    from smartpower.ui.pages.data_management import DataManagementPage
    from smartpower.storage.repository import DatasetRepository
    from PySide6.QtCore import QEventLoop, QTimer
    app = create_application([])
    page = DataManagementPage(repository=DatasetRepository(tmp_path / 'isolated.sqlite3'))
    target = tmp_path / '已有.csv'
    target.write_bytes(b'original')
    page.dataset = generate_demo(3)
    calls = []
    monkeypatch.setattr(page, '_confirm', lambda *args: calls.append(args) or False)
    page.export_to(target)
    assert len(calls) == 1 and not page.busy
    assert target.read_bytes() == b'original'
    monkeypatch.setattr(page, '_confirm', lambda *args: calls.append(args) or True)
    page.export_to(target)
    loop = QEventLoop()
    page.operation_finished.connect(loop.quit)
    QTimer.singleShot(10000, loop.quit)
    loop.exec()
    assert not page.busy and len(calls) == 2
    assert '数据来源' in target.read_text(encoding='utf-8-sig')
    page.close()
    page.deleteLater()
    app.processEvents()
