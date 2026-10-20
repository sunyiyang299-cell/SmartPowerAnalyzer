import time

import numpy as np
import pytest
from PySide6.QtCore import QEventLoop, QTimer, Qt
from PySide6.QtTest import QTest

from smartpower.analysis.service import analyze_saved_dataset
from smartpower.application import create_application
from smartpower.data.demo import generate_demo
from smartpower.storage.repository import DatasetRepository, StorageError
from smartpower.ui.pages.analysis import AnalysisPage


@pytest.fixture(scope="session")
def analysis_app():
    return create_application([])


def wait_idle(page):
    if page.busy:
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        page.operation_finished.connect(loop.quit)
        timer.start(20000)
        loop.exec()
        timer.stop()
        page.operation_finished.disconnect(loop.quit)
    assert not page.busy, "分析任务超时"


@pytest.fixture(params=["voltage", "current", "power"])
def page(request, analysis_app, tmp_path):
    widget = AnalysisPage(request.param, repository=DatasetRepository(tmp_path / "分析.sqlite3"))
    widget.resize(850, 850)
    widget.show()
    yield widget
    wait_idle(widget)
    widget.close()
    widget.deleteLater()
    analysis_app.processEvents()


def choose_saved(page, name="模拟数据", value=220):
    dataset = generate_demo(3)
    dataset.frame["电压"] = float(value)
    dataset.frame["电流"] = 10.0
    dataset.frame["功率因数"] = 0.9
    identifier = page.repository.save(dataset, name)
    page.refresh_datasets()
    wait_idle(page)
    page.dataset_combo.setCurrentIndex(page.dataset_combo.findData(identifier))
    return identifier


def test_no_dataset_selection_is_explicit_and_safe(page):
    QTest.mouseClick(page.analyze_button, Qt.MouseButton.LeftButton)
    assert "请先选择" in page.message.text()
    assert page.summary.rowCount() == 0
    assert page.current_result is None
    assert not page.busy


def test_saved_dataset_analysis_displays_units_source_and_real_results(page, monkeypatch):
    identifier = choose_saved(page)
    load = page.repository.load
    calls = []
    def record_load(identifier):
        calls.append(identifier)
        return load(identifier)
    monkeypatch.setattr(page.repository, "load", record_load)
    QTest.mouseClick(page.analyze_button, Qt.MouseButton.LeftButton)
    assert page.busy
    assert page.current_result is None
    assert not page.analyze_button.isEnabled()
    wait_idle(page)
    assert page.current_result.dataset_id == identifier
    assert page.current_result.count == 3
    assert "模拟数据（非真实设备测量）" in page.metadata.toPlainText()
    assert page.summary.item(0, 1).text() == "3"
    rows = {page.summary.item(r, 0).text():
            (float(page.summary.item(r, 1).text()), page.summary.item(r, 2).text())
            for r in range(page.summary.rowCount())}
    if page.mode == "voltage":
        assert rows["平均电压有效值"] == (220, "V")
    elif page.mode == "current":
        assert rows["电流有效值最大值"] == (10, "A")
    else:
        assert rows["有功功率算术平均值"] == (1980, "W")
        assert rows["视在功率算术平均值"] == (2200, "VA")
        assert rows["无功功率绝对值 |Q|算术平均值"][0] == pytest.approx(958.957767578948)
        assert rows["无功功率绝对值 |Q|算术平均值"][1] == "var"
        assert rows["功率因数算术平均值（采样点）"] == (0.9, "无量纲")
        assert page.series_model.rowCount() == 3
        assert page.series_model.index(0, 0).data().endswith("00:00:00")
        assert float(page.series_model.index(0, 1).data()) == pytest.approx(1980)
        assert not page.series_table.isHidden()
    # A second click re-reads the repository rather than keeping cached values.
    page.start_analysis()
    wait_idle(page)
    assert page.current_result.dataset_id == identifier
    assert page.analyze_button.isEnabled()
    assert calls == [identifier, identifier]


def test_switch_dataset_and_read_failure_clear_old_results(page, monkeypatch):
    first = choose_saved(page, "第一份")
    page.start_analysis()
    wait_idle(page)
    assert page.current_result.dataset_id == first
    second_dataset = generate_demo(2)
    second = page.repository.save(second_dataset, "第二份")
    page.dataset_combo.addItem("第二份", second)
    page.dataset_combo.setCurrentIndex(page.dataset_combo.findData(second))
    assert page.current_result is None
    assert page.summary.rowCount() == 0
    assert page.series_model.rowCount() == 0
    def fail(*args):
        raise StorageError("数据读取失败（测试）")
    monkeypatch.setattr(page.repository, "load", fail)
    page.start_analysis()
    wait_idle(page)
    assert page.current_result is None
    assert page.summary.rowCount() == 0
    assert "读取失败" in page.message.text()
    assert "第一份" not in page.metadata.toPlainText()


def test_empty_history_and_empty_dataset_error(page, monkeypatch):
    page.refresh_datasets()
    wait_idle(page)
    assert "尚无已保存" in page.message.text()
    choose_saved(page)
    empty = generate_demo(1)
    empty.frame = empty.frame.iloc[:0]
    monkeypatch.setattr(page.repository, "load", lambda _: empty)
    page.start_analysis()
    wait_idle(page)
    assert "没有数据" in page.message.text()
    assert page.current_result is None
    assert page.summary.rowCount() == 0


def test_failure_during_reanalysis_clears_same_dataset_old_results(page, monkeypatch):
    choose_saved(page)
    page.start_analysis()
    wait_idle(page)
    assert page.current_result is not None
    invalid = generate_demo(3)
    invalid.frame["电压"] = np.nan
    monkeypatch.setattr(page.repository, "load", lambda _: invalid)
    page.start_analysis()
    assert page.summary.rowCount() == 0
    wait_idle(page)
    assert page.current_result is None
    assert page.series_model.rowCount() == 0
    assert "失败" in page.message.text()


def test_selection_changed_while_worker_runs_discards_stale_result(page, monkeypatch):
    first = choose_saved(page)
    page.dataset_combo.addItem("另一份", first + 100)
    def delayed(repository, identifier, mode):
        time.sleep(0.08)
        return analyze_saved_dataset(repository, identifier, mode)
    monkeypatch.setattr("smartpower.ui.pages.analysis.analyze_saved_dataset", delayed)
    page.start_analysis()
    page.dataset_combo.setCurrentIndex(1)  # Programmatic race despite disabled user controls.
    wait_idle(page)
    assert page.current_result is None
    assert page.summary.rowCount() == 0
    assert "已丢弃" in page.message.text()


def test_analysis_keeps_event_loop_alive_and_window_close_is_guarded(analysis_app, tmp_path, monkeypatch):
    from smartpower.ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    page = window.pages["power"]
    page.repository = DatasetRepository(tmp_path / "window.sqlite3")
    choose_saved(page)
    def delayed(repository, identifier, mode):
        time.sleep(0.1)
        return analyze_saved_dataset(repository, identifier, mode)
    monkeypatch.setattr("smartpower.ui.pages.analysis.analyze_saved_dataset", delayed)
    ticks = []
    timer = QTimer(window)
    timer.setInterval(5)
    timer.timeout.connect(lambda: ticks.append(1))
    timer.start()
    page.start_analysis()
    window.navigate("home")
    window.close()
    assert window.isVisible()
    assert window.stack.currentWidget() is page
    wait_idle(page)
    timer.stop()
    assert len(ticks) >= 2
    assert page.current_result is not None
    window.close()
    assert not window.isVisible()
    window.deleteLater()
    analysis_app.processEvents()


def test_switch_to_another_dataset_updates_values_name_and_source(page):
    choose_saved(page, "第一份模拟数据")
    page.start_analysis()
    wait_idle(page)
    second = generate_demo(2)
    second.simulated = False
    second.frame["电压"] = 110.0
    second.frame["电流"] = 2.0
    second.frame["功率因数"] = 1.0
    identifier = page.repository.save(second, "第二份文件（未核验）")
    page.dataset_combo.addItem("第二份文件", identifier)
    page.dataset_combo.setCurrentIndex(page.dataset_combo.findData(identifier))
    assert page.summary.rowCount() == 0
    page.start_analysis()
    wait_idle(page)
    result = page.current_result
    assert result.dataset_id == identifier
    assert result.dataset_name == "第二份文件（未核验）"
    assert result.count == 2
    assert not result.simulated
    assert "来源未核验" in page.metadata.toPlainText()
    assert "第一份" not in page.metadata.toPlainText()
    if page.mode == "voltage":
        assert result.voltage.mean == pytest.approx(110)
    elif page.mode == "current":
        assert result.current.maximum == 2
    else:
        np.testing.assert_allclose(result.power.active, [220, 220])
        np.testing.assert_allclose(result.power.reactive_abs, [0, 0])


def test_dataset_deleted_after_selection_cannot_keep_old_result(page):
    identifier = choose_saved(page)
    page.start_analysis()
    wait_idle(page)
    page.repository.delete(identifier)
    page.start_analysis()
    wait_idle(page)
    assert "不存在" in page.message.text()
    assert page.current_result is None
    assert page.summary.rowCount() == 0


def test_large_saved_power_analysis_keeps_event_loop_responsive(analysis_app, tmp_path):
    repository = DatasetRepository(tmp_path / "十万条.sqlite3")
    identifier = repository.save(generate_demo(100000), "十万条模拟数据")
    page = AnalysisPage("power", repository=repository)
    page.show()
    page.refresh_datasets()
    wait_idle(page)
    page.dataset_combo.setCurrentIndex(page.dataset_combo.findData(identifier))
    ticks = []
    timer = QTimer(page)
    timer.setInterval(5)
    timer.timeout.connect(lambda: ticks.append(1))
    timer.start()
    page.start_analysis()
    wait_idle(page)
    timer.stop()
    try:
        assert page.current_result.count == 100000
        assert page.series_model.rowCount() == 100000
        assert len(ticks) >= 2
        assert page.current_result.simulated
    finally:
        page.close()
        page.deleteLater()
        analysis_app.processEvents()
