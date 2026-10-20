"""Reusable time plots. Rendering reduction never changes full sample arrays."""

from pathlib import Path

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QFileDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget,
)

from smartpower.visualization.export import save_png
from smartpower.visualization.time_axis import SampleTimeAxis


class TimePlotWidget(QWidget):
    message = Signal(str)
    MAX_MARKERS = 1500  # Per type and visible range; all events remain in detail table.

    def __init__(self, mode, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.result = self.detection = None
        self.curves = {}
        self.markers = {}
        self._marker_arrays = {}
        self._revision = 0
        self.setMinimumWidth(0)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.heading = QLabel("尚无当前数据集的曲线")
        self.heading.setTextFormat(Qt.TextFormat.PlainText)
        self.heading.setWordWrap(True)
        layout.addWidget(self.heading)
        row = QHBoxLayout()
        self.reset_button = QPushButton("恢复完整视图")
        self.export_button = QPushButton("导出 PNG")
        self.show_anomalies = QCheckBox("显示异常标记")
        self.show_anomalies.setChecked(True)
        self.show_anomalies.setVisible(mode != "power")
        row.addWidget(self.reset_button)
        row.addWidget(self.export_button)
        row.addWidget(self.show_anomalies)
        row.addStretch()
        layout.addLayout(row)
        self.visibility_row = QHBoxLayout()
        layout.addLayout(self.visibility_row)
        self.curve_checks = {}
        self.axis = SampleTimeAxis()
        self.plot = pg.PlotWidget(axisItems={"bottom": self.axis}, background="white")
        self.plot.setMinimumSize(0, 300)
        self.plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.plot.showGrid(x=True, y=True, alpha=0.15)
        self.plot.setMenuEnabled(False)  # No untranslated library context menus.
        self.plot.hideButtons()
        self.plot.setMouseEnabled(x=True, y=True)
        self.plot.getViewBox().setMouseMode(pg.ViewBox.PanMode)
        self.plot.setLabel("left", {"voltage": "电压有效值（V）", "current": "电流有效值（A）",
                                    "power": "功率数值（P: W；S: VA；|Q|: var）"}[mode])
        self.plot.getAxis("left").enableAutoSIPrefix(False)
        self.legend = self.plot.addLegend(offset=(8, 8), labelTextColor="#25334a")
        layout.addWidget(self.plot, 1)
        self.readout = QLabel("滚轮缩放，左键拖动平移；悬停曲线查看完整精度采样值。")
        self.readout.setWordWrap(True)
        self.readout.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.readout)
        self.marker_note = QLabel("未启用阈值检测；请到“异常检测”设置阈值并开始检测。")
        self.marker_note.setWordWrap(True)
        layout.addWidget(self.marker_note)
        self.reset_button.clicked.connect(self.reset_view)
        self.export_button.clicked.connect(self.export_png)
        self.show_anomalies.toggled.connect(self._refresh_markers)
        self.plot.getViewBox().sigXRangeChanged.connect(self._refresh_markers)
        self._mouse_proxy = pg.SignalProxy(self.plot.scene().sigMouseMoved, rateLimit=20, slot=self._mouse_moved)
        self.export_button.setEnabled(False)

    def clear(self):
        self._revision += 1
        self.result = None
        self.clear_detection()
        self.plot.clear()
        self.curves.clear()
        self.legend.clear()
        for check in self.curve_checks.values():
            self.visibility_row.removeWidget(check)
            check.deleteLater()
        self.curve_checks.clear()
        self.axis.origin = None
        self.heading.setText("尚无当前数据集的曲线")
        self.readout.setText("请先选择数据集并开始分析。")
        self.export_button.setEnabled(False)

    def set_result(self, result):
        self.clear()
        self.result = result
        sample = result.samples
        self.axis.origin = sample.origin
        source = "模拟数据，非真实设备测量" if result.simulated else result.source
        title = {"voltage": "电压有效值时间曲线", "current": "电流有效值时间曲线", "power": "单相功率时间曲线"}[self.mode]
        self.heading.setText(f"{title} · {result.dataset_name}\n{result.count} 条采样 · {source}")
        if self.mode == "power":
            series = [("P（W）", result.power.active, "#2563eb"),
                      ("S（VA）", result.power.apparent, "#16805d"),
                      ("|Q|（var，绝对值）", result.power.reactive_abs, "#9b44b5")]
        else:
            values = sample.voltage if self.mode == "voltage" else sample.current
            series = [("电压有效值（V）" if self.mode == "voltage" else "电流有效值（A）", values, "#2563eb")]
        for name, values, color in series:
            # Attach first: in 0.14 enabling clipToView during scene insertion can
            # resolve a temporary PlotWidget rather than the final ViewBox.
            curve = self.plot.plot(name=name, pen=pg.mkPen(color, width=1), antialias=False)
            curve.setData(sample.seconds, values[sample.order])
            curve.setDownsampling(auto=True, method="peak")
            curve.setClipToView(True)
            self.curves[name] = curve
            if self.mode == "power":
                check = QCheckBox(name)
                check.setChecked(True)
                check.toggled.connect(curve.setVisible)
                self.visibility_row.addWidget(check)
                self.curve_checks[name] = check
        self.readout.setText("滚轮缩放，左键平移；按时间稳定排序显示，重复时间全部保留。悬停查看原始行。")
        self.export_button.setEnabled(True)
        if self.mode == "power":
            self.marker_note.setText("单相正弦稳态模型；共享数值轴，各曲线单位分别为 W、VA、var；|Q| 为绝对值。")
        self.reset_view()

    def reset_view(self):
        if self.result is not None:
            # autoRange can otherwise use clipped display data after a zoom.
            sample = self.result.samples
            self.plot.setXRange(float(sample.seconds[0]), float(sample.seconds[-1]), padding=0.03)
            values = [curve.yData for curve in self.curves.values() if curve.isVisible()]
            if values:
                self.plot.setYRange(float(min(np.min(v) for v in values)),
                                    float(max(np.max(v) for v in values)), padding=0.08)

    def describe_point(self, sorted_index):
        result = self.result
        row = int(result.samples.order[sorted_index])
        time = np.datetime_as_string(result.times[row], unit="ns").replace("T", " ")
        if self.mode == "power":
            text = (f"P={result.power.active[row]:.12g} W；S={result.power.apparent[row]:.12g} VA；"
                    f"|Q|={result.power.reactive_abs[row]:.12g} var")
        else:
            value = result.samples.voltage[row] if self.mode == "voltage" else result.samples.current[row]
            text = f"{value:.12g} {'V' if self.mode == 'voltage' else 'A'}"
        return f"原始记录索引 {row}（第 {row + 1} 行） · {time} · {text}"

    def _mouse_moved(self, args):
        if self.result is None or not self.plot.sceneBoundingRect().contains(args[0]):
            return
        point = self.plot.getViewBox().mapSceneToView(args[0])
        xs = self.result.samples.seconds
        right = min(int(np.searchsorted(xs, point.x())), len(xs) - 1)
        index = min((max(0, right - 1), right), key=lambda j: abs(xs[j] - point.x()))
        # Repeated timestamps: choose nearest y among all original rows at that time.
        left, right = np.searchsorted(xs, xs[index], side="left"), np.searchsorted(xs, xs[index], side="right")
        if right - left > 1:
            values = next(iter(self.curves.values())).yData
            index = int(left + np.argmin(np.abs(values[left:right] - point.y())))
        self.readout.setText(self.describe_point(index))

    def clear_detection(self):
        self.detection = None
        self._marker_arrays.clear()
        for marker in self.markers.values():
            self.plot.removeItem(marker)
            self.legend.removeItem(marker)
        self.markers.clear()
        self.marker_note.setText("单相正弦稳态模型；共享数值轴，单位分别为 W、VA、var；|Q| 为绝对值。" if self.mode == "power"
                                 else "无匹配的阈值检测结果；请到“异常检测”设置并启用检测。")

    def set_detection(self, detection):
        self.clear_detection()
        result = self.result
        if (result is None or detection is None or self.mode == "power"
                or detection.dataset_id != result.dataset_id
                or detection.fingerprint != result.samples.fingerprint
                or detection.dataset_name != result.dataset_name
                or detection.source != result.source):
            return
        self.detection = detection
        row_x = np.empty(result.count)
        row_x[result.samples.order] = result.samples.seconds
        for kind, color, symbol in (("电压偏低", "#e69300", "t"), ("电压偏高", "#d83245", "t1"),
                                    ("电流偏高", "#d83245", "x")):
            relevant = [event for event in detection.events if event.kind == kind
                        and event.parameter == ("电压" if self.mode == "voltage" else "电流")]
            if not relevant:
                continue
            relevant.sort(key=lambda event: row_x[event.row_index])
            self._marker_arrays[kind] = (np.array([row_x[e.row_index] for e in relevant]), relevant)
            marker = pg.ScatterPlotItem(size=9, pen=pg.mkPen(color), brush=pg.mkBrush(color), symbol=symbol,
                                        hoverable=True, tip=lambda x, y, data: self.event_text(data))
            marker.sigClicked.connect(self._marker_clicked)
            self.plot.addItem(marker)
            self.legend.addItem(marker, kind)
            self.markers[kind] = marker
        self._refresh_markers()

    @staticmethod
    def event_text(event):
        return (f"{event.timestamp} · 原始索引 {event.row_index} · {event.kind}\n"
                f"采样值 {event.value:.12g} {event.unit} · 阈值 {event.threshold:.12g} {event.unit}")

    def _marker_clicked(self, item, points, event):
        if points:
            self.readout.setText(self.event_text(points[0].data()))

    def _refresh_markers(self, *_):
        if self.detection is None:
            return
        low, high = self.plot.viewRange()[0]
        displayed = 0
        for kind, (xs, events) in self._marker_arrays.items():
            start, stop = np.searchsorted(xs, [low, high])
            stop = min(len(xs), stop + 1)
            indices = np.arange(start, stop)
            if len(indices) > self.MAX_MARKERS:
                indices = indices[np.linspace(0, len(indices) - 1, self.MAX_MARKERS, dtype=int)]
            chosen = [events[j] for j in indices]
            self.markers[kind].setData(x=xs[indices], y=[e.value for e in chosen], data=chosen)
            self.markers[kind].setVisible(self.show_anomalies.isChecked())
            displayed += len(chosen)
        t = self.detection.thresholds
        self.marker_note.setText(f"当前阈值：电压 {t.voltage_lower:g}～{t.voltage_upper:g} V；电流上限 {t.current_upper:g} A。"
                                 f"视区代表标记 {displayed} 个，每类最多 {self.MAX_MARKERS} 个；完整事件请看异常明细。")

    def capture_image(self):
        if self.result is None:
            raise ValueError("尚无当前数据集的图表，请先分析。")
        image = self.grab().toImage()
        # PNG keyword names must be Latin-1; Qt writes Unicode values as iTXt.
        image.setText("Dataset", self.result.dataset_name)
        image.setText("Source", "模拟数据，非真实设备测量" if self.result.simulated else self.result.source)
        return image

    def export_png(self):
        if self.result is None:
            self.message.emit("请先分析当前数据集，再导出图表。")
            return
        revision = self._revision
        path, _ = QFileDialog.getSaveFileName(self, "导出当前图表 PNG", "曲线.png", "PNG 图像 (*.png)",
                                             options=QFileDialog.Option.DontConfirmOverwrite)
        if not path:
            return
        if Path(path).suffix == "":
            path += ".png"
        overwrite = Path(path).exists()
        if overwrite and QMessageBox.question(self, "确认覆盖", "文件已存在，是否覆盖？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        if revision != self._revision or self.result is None:
            self.message.emit("数据集已变化，本次导出已取消，请重新分析后导出。")
            return
        try:
            image = self.capture_image()  # GUI-thread snapshot, no event processing until write ends.
            save_png(image, path, overwrite=overwrite)
            self.message.emit(f"PNG 已导出：{path}")
        except Exception as exc:
            self.message.emit(f"图表导出失败：{exc}")
