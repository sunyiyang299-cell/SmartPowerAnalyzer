import json
import os
from pathlib import Path
import platform
import time

import numpy as np
import pandas as pd
import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer, Qt, QPoint, QPointF
from PySide6.QtGui import QImage, QWheelEvent, QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QFileDialog, QMessageBox

from smartpower.analysis.service import analyze_dataset
from smartpower.anomaly.detector import detect_anomalies
from smartpower.anomaly.models import Thresholds
from smartpower.application import create_application
from smartpower.data.demo import generate_demo
from smartpower.data.validation import DataError
from smartpower.visualization.export import save_png
from smartpower.visualization.plot_widget import TimePlotWidget


@pytest.fixture(scope="session")
def plot_app():
    return create_application([])


@pytest.fixture(params=["voltage", "current", "power"])
def chart(request, plot_app):
    widget = TimePlotWidget(request.param)
    widget.resize(900, 620)
    widget.show()
    widget.set_result(analyze_dataset(generate_demo(), request.param, 12))
    plot_app.processEvents()
    yield widget
    widget.close()
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    plot_app.processEvents()


def test_full_curves_match_original_values_and_units(chart):
    result = chart.result
    assert result.count == 1000
    assert "模拟数据，非真实设备测量" in chart.heading.text()
    expected = ([result.power.active, result.power.apparent, result.power.reactive_abs] if chart.mode == "power"
                else [result.samples.voltage if chart.mode == "voltage" else result.samples.current])
    assert len(chart.curves) == len(expected)
    for curve, values in zip(chart.curves.values(), expected):
        np.testing.assert_array_equal(curve.xData, result.samples.seconds)
        np.testing.assert_array_equal(curve.yData, values[result.samples.order])
        assert curve.opts["autoDownsample"] and curve.opts["clipToView"]
    axis = chart.plot.getAxis("left").labelText
    assert ("W" in axis and "VA" in axis and "var" in axis) if chart.mode == "power" else ("V" in axis if chart.mode == "voltage" else "A" in axis)
    assert "2026-01-01" in chart.axis.tickStrings([0], 1, 1)[0]
    assert "原始记录索引 0" in chart.describe_point(0)
    assert len(chart.legend.items) == len(expected)


def test_irregular_duplicate_unsorted_multidate_time_mapping(chart):
    dataset = generate_demo(4)
    dataset.frame["时间"] = pd.to_datetime(["2026-02-03 12:03:01", "2026-01-01 00:00:00",
        "2026-01-01 00:00:00", "2026-01-01 00:00:00.000000001"], format="mixed")
    original = dataset.frame.copy(deep=True)
    chart.set_result(analyze_dataset(dataset, chart.mode, 3))
    np.testing.assert_array_equal(chart.result.samples.order, [1, 2, 3, 0])
    assert chart.result.samples.seconds[0] == chart.result.samples.seconds[1] == 0
    assert chart.result.samples.seconds[2] == 1e-9
    assert "原始记录索引 2" in chart.describe_point(1)
    assert "2026-01-01" in chart.axis.tickStrings([0], 1, 1)[0]
    assert "2026-02-03" in chart.axis.tickStrings([chart.result.samples.seconds[-1]], 1, 1)[0]
    pd.testing.assert_frame_equal(dataset.frame, original)


def test_mouse_wheel_pan_and_restore(chart, plot_app):
    box = chart.plot.getViewBox()
    before = box.viewRange()[0][:]
    point = chart.plot.viewport().rect().center()
    wheel = QWheelEvent(QPointF(point), QPointF(chart.plot.mapToGlobal(point)), QPoint(), QPoint(0, 120),
                        Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
                        Qt.ScrollPhase.NoScrollPhase, False)
    plot_app.sendEvent(chart.plot.viewport(), wheel)
    plot_app.processEvents()
    zoomed = box.viewRange()[0][:]
    assert zoomed[1] - zoomed[0] < before[1] - before[0]
    # Explicit viewport events avoid native cursor-position coalescing when the
    # previous parametrized window left the OS pointer at the same destination.
    viewport = chart.plot.viewport()
    for kind, delta, button, buttons in (
        (QEvent.Type.MouseButtonPress, 0, Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton),
        (QEvent.Type.MouseMove, 20, Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton),
        (QEvent.Type.MouseMove, 55, Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton),
        (QEvent.Type.MouseButtonRelease, 55, Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton),
    ):
        local = point + QPoint(delta, 0)
        event = QMouseEvent(kind, QPointF(local), QPointF(viewport.mapToGlobal(local)),
                            button, buttons, Qt.KeyboardModifier.NoModifier)
        plot_app.sendEvent(viewport, event)
    plot_app.processEvents()
    assert box.viewRange()[0] != zoomed
    chart.reset_button.click()
    plot_app.processEvents()
    restored = box.viewRange()[0]
    assert restored[0] <= 0 and restored[1] >= chart.result.samples.seconds[-1]


def test_calendar_dates_outside_nanosecond_epoch_do_not_wrap(chart):
    dataset = generate_demo(2)
    dataset.frame["时间"] = pd.to_datetime(["3000-01-01", "3000-01-02"], format="mixed")
    chart.set_result(analyze_dataset(dataset, chart.mode, 2))
    assert chart.result.samples.seconds[1] == 86400
    assert "3000-01-01" in chart.axis.tickStrings([0], 1, 1)[0]


def test_power_individual_visibility(chart):
    if chart.mode == "power":
        assert len(chart.curve_checks) == 3
        for name, check in chart.curve_checks.items():
            check.setChecked(False)
            assert not chart.curves[name].isVisible()
            check.setChecked(True)
            assert chart.curves[name].isVisible()
    else:
        assert not chart.curve_checks


def test_downsampling_changes_only_rendering(chart, plot_app):
    dataset = generate_demo()
    before = dataset.frame.copy(deep=True)
    detection = detect_anomalies(dataset, Thresholds(210, 230, 20), 12)
    chart.set_detection(detection)
    result = chart.result
    for curve in chart.curves.values():
        original_y = curve.yData.copy()
        curve.setDownsampling(ds=20, auto=False, method="peak")
        chart.reset_view()
        plot_app.processEvents()
        np.testing.assert_array_equal(curve.yData, original_y)
        assert len(curve.getData()[0]) < len(curve.xData)
    assert chart.result is result
    assert detect_anomalies(dataset, detection.thresholds, 12).events == detection.events
    pd.testing.assert_frame_equal(dataset.frame, before)


def test_markers_match_original_indices_thresholds_and_snapshot(plot_app):
    dataset = generate_demo(4)
    dataset.frame["电压"] = [235., 205., 230., 220.]
    dataset.frame["电流"] = [21., 20., 30., 10.]
    dataset.frame["时间"] = pd.to_datetime(["2026-01-04", "2026-01-01", "2026-01-01", "2026-01-02"])
    detection = detect_anomalies(dataset, Thresholds(210, 230, 20), 1)
    for mode, expected in (("voltage", {0, 1}), ("current", {0, 2})):
        dataset.frame.loc[0, "电压"] = 235.
        widget = TimePlotWidget(mode)
        widget.resize(900, 620)
        widget.show()
        widget.set_result(analyze_dataset(dataset, mode, 1))
        plot_app.processEvents()
        widget.set_detection(detection)
        shown = [point for marker in widget.markers.values() for point in marker.points()]
        assert {p.data().row_index for p in shown} == expected
        for point in shown:
            event = point.data()
            assert point.pos().y() == event.value
            assert "阈值" in widget.event_text(event)
            widget._marker_clicked(None, [point], None)
            assert str(event.row_index) in widget.readout.text()
        widget.show_anomalies.setChecked(False)
        assert all(not m.isVisible() for m in widget.markers.values())
        widget.show_anomalies.setChecked(True)
        widget.set_result(analyze_dataset(dataset, mode, 2))
        assert not widget.markers and widget.detection is None
        widget.set_detection(detection)
        assert widget.detection is None  # Wrong dataset ID.
        dataset.frame.loc[0, "电压"] = 240
        widget.set_result(analyze_dataset(dataset, mode, 1))
        widget.set_detection(detection)
        assert widget.detection is None  # Same ID but stale saved contents.
        widget.clear()
        assert not widget.curves and widget.result is None and not widget.export_button.isEnabled()
        widget.close()
        widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_png_export_all_modes_chinese_path_provenance(chart, tmp_path):
    path = tmp_path / f"中文路径_{chart.mode}.png"
    before = chart.result
    save_png(chart.capture_image(), path)
    image = QImage(str(path))
    assert not image.isNull() and image.width() >= 800 and image.height() >= 500
    assert image.text("Source") == "模拟数据，非真实设备测量"
    assert image.text("Dataset") == chart.result.dataset_name
    assert chart.result is before
    # Source text and dataset are rendered within the captured widget, not just metadata.
    assert chart.heading.isVisible() and chart.heading.geometry().intersects(chart.rect())


def test_png_no_overwrite_and_write_failure_preserve_original(chart, tmp_path, monkeypatch):
    path = tmp_path / "原图.png"
    path.write_bytes(b"original")
    with pytest.raises(DataError, match="确认覆盖"):
        save_png(chart.capture_image(), path)
    assert path.read_bytes() == b"original"
    def fail(*args):
        raise OSError("测试模拟磁盘写入失败")
    monkeypatch.setattr("smartpower.visualization.export.os.replace", fail)
    with pytest.raises(DataError, match="原文件保留"):
        save_png(chart.capture_image(), path, overwrite=True)
    assert path.read_bytes() == b"original"
    assert list(tmp_path.iterdir()) == [path]
    with pytest.raises(DataError):
        save_png(chart.capture_image(), tmp_path / "不存在" / "图.png")


def test_export_dialog_overwrite_cancel_and_dataset_switch(chart, tmp_path, monkeypatch):
    path = tmp_path / "覆盖.png"
    path.write_bytes(b"original")
    messages = []
    chart.message.connect(messages.append)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **kw: (str(path), ""))
    calls = []
    def deny(*args):
        calls.append(args)
        return QMessageBox.StandardButton.No
    monkeypatch.setattr(QMessageBox, "question", deny)
    chart.export_png()
    assert len(calls) == 1 and path.read_bytes() == b"original"
    monkeypatch.setattr(QMessageBox, "question", lambda *a: QMessageBox.StandardButton.Yes)
    chart.export_png()
    assert not QImage(str(path)).isNull()
    before = path.read_bytes()
    def switch(*args, **kwargs):
        chart.clear()
        return str(path), ""
    monkeypatch.setattr(QFileDialog, "getSaveFileName", switch)
    chart.export_png()
    assert "已取消" in messages[-1]
    assert path.read_bytes() == before


def test_export_error_is_reported_without_losing_chart(chart, tmp_path, monkeypatch):
    messages = []
    chart.message.connect(messages.append)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **kw: (str(tmp_path / "缺少目录" / "曲线.png"), ""))
    result = chart.result
    chart.export_png()
    assert "导出失败" in messages[-1]
    assert chart.result is result and chart.curves


def test_100k_full_detection_bounded_markers_and_event_loop(plot_app):
    from smartpower.ui.pages.analysis import AnalysisPage
    from smartpower.ui.tasks import TaskThread
    dataset = generate_demo(100000)
    widget = TimePlotWidget("voltage")
    widget.resize(900, 620)
    widget.show()
    ticks = []
    timer = QTimer()
    timer.setInterval(5)
    timer.timeout.connect(lambda: ticks.append(time.perf_counter()))
    timer.start()
    started = time.perf_counter()
    worker = TaskThread(lambda: (analyze_dataset(dataset, "voltage", 1),
                                 detect_anomalies(dataset, Thresholds(0, 1, 0.1), 1)))
    loop = QEventLoop()
    worker.finished.connect(loop.quit)
    worker.start()
    loop.exec()
    assert worker.error is None
    result, detection = worker.result
    painted = time.perf_counter()
    widget.set_result(result)
    widget.set_detection(detection)
    widget.grab()
    plot_app.processEvents()
    bind_ms = (time.perf_counter() - painted) * 1000
    for _ in range(3):
        widget.plot.getViewBox().scaleBy((0.8, 0.8))
        widget.plot.getViewBox().translateBy(x=2)
        plot_app.processEvents()
    QTest.qWait(30)
    timer.stop()
    assert len(ticks) >= 2
    assert result.count == 100000 and len(detection.events) == 200000
    assert detection.unique_sample_count == 100000
    assert len(widget.markers) == 1
    assert len(next(iter(widget.markers.values())).points()) <= widget.MAX_MARKERS
    assert len(next(iter(widget.curves.values())).yData) == 100000
    measurements = {"python": platform.python_version(), "platform": platform.platform(),
                    "qt_backend": plot_app.platformName(), "samples": 100000, "events": len(detection.events),
                    "total_seconds": round(time.perf_counter() - started, 4), "bind_render_ms": round(bind_ms, 2),
                    "timer_ticks": len(ticks), "max_timer_gap_ms": round(max(np.diff(ticks)) * 1000, 2)}
    print("V04_PERFORMANCE=" + json.dumps(measurements))
    assert bind_ms < 5000, "绑定及首次绘制超过5秒，需要检查绘图性能"
    widget.close()
    widget.deleteLater()
    worker.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
