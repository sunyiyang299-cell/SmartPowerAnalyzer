import time

import numpy as np
import pytest
from PySide6.QtCore import QEventLoop, QTimer

from smartpower.application import create_application
from smartpower.data.demo import generate_demo
from smartpower.storage.repository import DatasetRepository
from smartpower.ui.pages.anomaly import AnomalyPage


def wait_idle(page):
    if page.busy:
        loop = QEventLoop()
        timeout = QTimer()
        timeout.setSingleShot(True)
        timeout.timeout.connect(loop.quit)
        page.operation_finished.connect(loop.quit)
        timeout.start(20000)
        loop.exec()
        timeout.stop()
        page.operation_finished.disconnect(loop.quit)
    assert not page.busy


@pytest.fixture
def anomaly_page(tmp_path):
    app = create_application([])
    page = AnomalyPage(repository=DatasetRepository(tmp_path / "异常.sqlite3"))
    page.resize(850, 850)
    page.show()
    yield page
    wait_idle(page)
    page.close()
    page.deleteLater()
    app.processEvents()


def prepare(page, u=(205., 220., 235.), i=(21., 10., 30.)):
    dataset = generate_demo(3)
    dataset.frame["电压"] = u
    dataset.frame["电流"] = i
    identifier = page.repository.save(dataset, "阈值演示（模拟）")
    page.refresh_datasets()
    wait_idle(page)
    page.dataset_combo.setCurrentIndex(page.dataset_combo.findData(identifier))
    page.apply_demo_preset()
    page.enabled_check.setChecked(True)
    return identifier


def test_no_selection_and_explicit_enable(anomaly_page):
    page = anomaly_page
    page.analyze_button.click()
    assert "请先选择" in page.message.text() and not page.busy
    prepare(page)
    page.enabled_check.setChecked(False)
    page.analyze_button.click()
    assert "勾选启用" in page.message.text() and page.current_result is None


def test_detection_counts_filter_and_rerun(anomaly_page):
    page = anomaly_page
    identifier = prepare(page)
    page.analyze_button.click()
    assert page.busy and page.current_result is None
    wait_idle(page)
    assert page.current_result.dataset_id == identifier
    assert len(page.current_result.events) == 4
    assert page.current_result.unique_sample_count == 2
    assert "模拟数据" in page.metadata.toPlainText()
    assert "异常事件 4 次" in page.counts.text() and "唯一采样点 2 条" in page.counts.text()
    page.type_filter.setCurrentText("电流偏高")
    assert page.event_model.rowCount() == 2
    assert page.event_model.index(0, 2).data() == "电流偏高"
    page.start_analysis()
    wait_idle(page)
    assert page.event_model.rowCount() == 2 and page.current_result.count == 3


@pytest.mark.parametrize("value", ["", "NaN", "Infinity", "-1", "不是数字", "230", "240"])
def test_invalid_threshold_clear_previous_result(anomaly_page, value):
    page = anomaly_page
    prepare(page)
    page.start_analysis()
    wait_idle(page)
    assert page.current_result
    page.voltage_lower.setText(value)
    assert page.current_result is None and page.event_model.rowCount() == 0
    page.start_analysis()
    assert not page.busy and page.current_result is None
    assert any(s in page.message.text() for s in ("数值", "小于"))


def test_no_anomaly_message(anomaly_page):
    prepare(anomaly_page, (210., 220., 230.), (10., 20., 0.))
    anomaly_page.start_analysis()
    wait_idle(anomaly_page)
    assert anomaly_page.message.text() == "未检测到符合当前阈值条件的异常记录。"
    assert anomaly_page.event_model.rowCount() == 0


@pytest.mark.parametrize("failure", ["deleted", "empty", "nan"])
def test_detection_failure_does_not_crash_or_keep_old(anomaly_page, monkeypatch, failure):
    page = anomaly_page
    identifier = prepare(page)
    page.start_analysis()
    wait_idle(page)
    if failure == "deleted":
        page.repository.delete(identifier)
    else:
        invalid = generate_demo(3)
        if failure == "empty":
            invalid.frame = invalid.frame.iloc[:0]
        else:
            invalid.frame["电压"] = np.nan
        monkeypatch.setattr(page.repository, "load", lambda _: invalid)
    page.start_analysis()
    wait_idle(page)
    assert page.current_result is None and page.event_model.rowCount() == 0
    assert "失败" in page.message.text() and page.analyze_button.isEnabled()


def test_changed_threshold_during_worker_discards_stale_result(anomaly_page, monkeypatch):
    from smartpower.anomaly.service import detect_saved_dataset
    page = anomaly_page
    prepare(page)
    def slow(*args):
        time.sleep(0.08)
        return detect_saved_dataset(*args)
    monkeypatch.setattr("smartpower.ui.pages.anomaly.detect_saved_dataset", slow)
    page.start_analysis()
    page.current_upper.setText("25")
    wait_idle(page)
    assert page.current_result is None and "已丢弃" in page.message.text()


def test_main_window_detection_chart_link_and_invalidation(tmp_path):
    from smartpower.ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    anomaly = window.pages["anomalies"]
    repository = DatasetRepository(tmp_path / "联动.sqlite3")
    anomaly.repository = repository
    identifier = prepare(anomaly)
    voltage = window.pages["voltage"]
    voltage.repository = repository
    voltage.refresh_datasets()
    wait_idle(voltage)
    voltage.dataset_combo.setCurrentIndex(voltage.dataset_combo.findData(identifier))
    voltage.start_analysis()
    wait_idle(voltage)
    anomaly.start_analysis()
    wait_idle(anomaly)
    assert voltage.chart.detection is anomaly.current_result and voltage.chart.markers
    anomaly.voltage_upper.setText("240")
    assert voltage.chart.detection is None and not voltage.chart.markers
    anomaly.start_analysis()
    wait_idle(anomaly)
    assert voltage.chart.detection.thresholds.voltage_upper == 240
    voltage.dataset_combo.setCurrentIndex(-1)
    assert voltage.chart.result is None and not voltage.chart.markers
    anomaly.dataset_combo.setCurrentIndex(-1)
    assert voltage._detection_snapshot is None
    window.close()
    window.deleteLater()
    create_application([]).processEvents()
