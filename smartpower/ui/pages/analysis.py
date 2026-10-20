"""Saved-dataset analysis with background I/O and explicit result provenance."""

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QHeaderView, QHBoxLayout, QPlainTextEdit,
    QProgressBar, QPushButton, QTableView, QTableWidget, QTableWidgetItem,
)

from smartpower.analysis.power import POWER_LIMITATION, POWER_MODEL
from smartpower.analysis.service import analyze_saved_dataset
from smartpower.storage.repository import DatasetRepository
from smartpower.ui.pages.base import BasePage
from smartpower.ui.paths import default_database_path
from smartpower.ui.power_series_model import PowerSeriesModel
from smartpower.ui.tasks import TaskThread
from smartpower.ui.widgets import label
from smartpower.visualization.plot_widget import TimePlotWidget


class AnalysisPage(BasePage):
    operation_finished = Signal()

    def __init__(self, mode: str, parent=None, repository=None, with_chart=True):
        titles = {"voltage": "电压分析", "current": "电流分析", "power": "功率分析"}
        super().__init__(titles[mode], "选择 V0.2 已保存的数据集，点击“开始分析”读取并计算；可手动重新分析。", parent)
        self.content.setContentsMargins(24, 20, 24, 20)
        self.content.setSpacing(12)
        self.mode = mode
        self.repository = repository or DatasetRepository(default_database_path())
        self.current_result = None
        self._thread = None
        self._callback = None
        self._revision = 0
        self._task_revision = 0
        self._detection_snapshot = None
        self.chart = TimePlotWidget(mode) if with_chart else None
        self.dataset_combo = QComboBox()
        self.dataset_combo.setPlaceholderText("请选择已保存的数据集")
        self.dataset_combo.setMinimumContentsLength(10)
        self.dataset_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.refresh_button = QPushButton("刷新数据集")
        self.analyze_button = QPushButton("开始分析")
        row = QHBoxLayout()
        row.addWidget(self.dataset_combo, 1)
        row.addWidget(self.refresh_button)
        row.addWidget(self.analyze_button)
        self.content.addLayout(row)
        self.metadata = QPlainTextEdit()
        self.metadata.setReadOnly(True)
        self.metadata.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        self.metadata.setFixedHeight(66)
        self.metadata.setPlainText("尚无分析结果。先刷新数据集列表，再选择并开始分析。")
        self.content.addWidget(self.metadata)
        self.message = label("请先在数据管理中保存数据集，然后点击“刷新数据集”。", "muted")
        self.content.addWidget(self.message)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        self.content.addWidget(self.progress)
        if self.chart is not None:
            self.content.addWidget(self.chart)
            self.chart.message.connect(self.notify)
        self.summary = QTableWidget(0, 3)
        self.summary.setHorizontalHeaderLabels(["统计指标", "计算结果", "单位"])
        self.summary.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.summary.verticalHeader().hide()
        self.summary.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.summary.setColumnWidth(1, 160)
        self.summary.setColumnWidth(2, 80)
        self.summary.setMinimumHeight(240)
        self.content.addWidget(self.summary)
        self.series_title = label("逐采样点功率计算结果", "sectionTitle")
        self.series_title.hide()
        self.content.addWidget(self.series_title)
        self.series_model = PowerSeriesModel(self)
        self.series_table = QTableView()
        self.series_table.setModel(self.series_model)
        self.series_table.setMinimumHeight(220)
        for column, width in enumerate((200, 180, 180, 250)):
            self.series_table.setColumnWidth(column, width)
        self.series_table.hide()
        self.content.addWidget(self.series_table)
        if mode == "power":
            note = POWER_MODEL + "\n" + POWER_LIMITATION + "\n功率因数平均值为采样点算术平均值，不是整个时间段的综合功率因数。"
        elif mode == "current":
            note = "全部电流为有效值，单位 A；最大值是采样有效值最大值，不是交流瞬时峰值。总体标准差使用 ddof=0。"
        else:
            note = "全部电压为有效值，单位 V；总体标准差使用 ddof=0。所有采样点等权统计，不作时间加权。"
        if not with_chart:
            pass
        elif mode == "power":
            self.content.insertWidget(2, label(note, "muted"))
        else:
            self.content.addWidget(label(note, "muted"))
        self.refresh_button.clicked.connect(self.refresh_datasets)
        self.analyze_button.clicked.connect(self.start_analysis)
        self.dataset_combo.currentIndexChanged.connect(self._selection_changed)

    @property
    def busy(self):
        return self._thread is not None

    def notify(self, text):
        self.message.setText(text)

    def _clear_results(self):
        self.current_result = None
        if self.chart is not None:
            self.chart.clear()
        self.summary.setRowCount(0)
        self.series_model.set_result(None)
        self.series_title.hide()
        self.series_table.hide()
        self.metadata.setPlainText("尚无当前数据集的分析结果。")

    def _selection_changed(self, *_):
        self._revision += 1
        self._clear_results()
        self.notify("请选择数据集。" if self.dataset_combo.currentData() is None else "已选择数据集，请点击“开始分析”；旧结果已清除。")

    def _start(self, operation, callback, message):
        if self.busy:
            return
        self._task_revision = self._revision
        self._callback = callback
        self._thread = TaskThread(operation, self)
        self._thread.finished.connect(self._finish)
        for widget in (self.dataset_combo, self.refresh_button, self.analyze_button):
            widget.setEnabled(False)
        self.progress.show()
        self.notify(message)
        self._thread.start()

    def _finish(self):
        thread, callback = self._thread, self._callback
        self._thread = self._callback = None
        self.progress.hide()
        try:
            if self._task_revision != self._revision:
                self._clear_results()
                self.notify("数据集选择已变化，本次结果已丢弃，请重新分析。")
            elif thread.error:
                self._clear_results()
                self.notify("分析或读取失败：" + thread.error)
            else:
                callback(thread.result)
        except Exception as exc:
            self._clear_results()
            self.notify(f"结果展示失败：{exc}。请重新分析。")
        finally:
            for widget in (self.dataset_combo, self.refresh_button, self.analyze_button):
                widget.setEnabled(True)
            thread.deleteLater()
            self.operation_finished.emit()

    def refresh_datasets(self):
        if self.busy:
            return
        self._revision += 1
        self._clear_results()
        self._start(self.repository.list_datasets, self._fill_datasets, "正在后台读取已保存的数据集…")

    def _fill_datasets(self, rows):
        with QSignalBlocker(self.dataset_combo):
            self.dataset_combo.clear()
            for row in rows:
                source = "模拟数据" if row["simulated"] else "导入文件（来源未核验）"
                self.dataset_combo.addItem(f"{row['name']} · {source}", row["id"])
            self.dataset_combo.setCurrentIndex(-1)
        self.notify(f"已读取 {len(rows)} 个数据集，请选择后开始分析。" if rows else "尚无已保存数据集，请先在数据管理中保存。")

    def start_analysis(self):
        if self.busy:
            return
        self._revision += 1
        self._clear_results()
        identifier = self.dataset_combo.currentData()
        if identifier is None:
            self.notify("请先选择已保存的数据集，再点击“开始分析”。")
            return
        self._start(lambda: analyze_saved_dataset(self.repository, identifier, self.mode),
                    self._display_result, "正在后台读取数据并计算，旧结果已清除…")

    def _display_result(self, result):
        rows = [("采样记录数量", result.count, "条")]
        if self.mode in ("voltage", "current"):
            stats = result.voltage if self.mode == "voltage" else result.current
            name = "电压有效值" if self.mode == "voltage" else "电流有效值"
            rows.extend([(f"平均{name}", stats.mean, stats.unit),
                         (f"{name}最大值", stats.maximum, stats.unit),
                         (f"{name}最小值", stats.minimum, stats.unit),
                         ("总体标准差（ddof=0）", stats.population_std, stats.unit)])
        else:
            power = result.power
            for stats in (power.active_statistics, power.apparent_statistics, power.reactive_abs_statistics):
                rows.extend([(stats.quantity + "算术平均值", stats.mean, stats.unit),
                             (stats.quantity + "最大值", stats.maximum, stats.unit),
                             (stats.quantity + "最小值", stats.minimum, stats.unit)])
            pf = power.power_factor_statistics
            rows.extend([("功率因数算术平均值（采样点）", pf.mean, pf.unit),
                         ("功率因数最大值", pf.maximum, pf.unit),
                         ("功率因数最小值", pf.minimum, pf.unit),
                         ("功率因数总体标准差", pf.population_std, pf.unit)])
            self.series_model.set_result(result)
            self.series_title.show()
            self.series_table.show()
        self.summary.setRowCount(len(rows))
        for row, (name, value, unit) in enumerate(rows):
            for column, text in enumerate((name, format(value, ".12g"), unit)):
                self.summary.setItem(row, column, QTableWidgetItem(text))
        self.current_result = result
        if self.chart is not None:
            self.chart.set_result(result)
            self.chart.set_detection(self._detection_snapshot)
        self.metadata.setPlainText(f"数据集：{result.dataset_name}\n采样记录：{result.count} 条 · 来源：{result.source}")
        self.notify("分析完成。结果基于当前已保存数据集；可再次点击“开始分析”重新读取和计算。")

    def receive_detection(self, detection):
        self._detection_snapshot = detection
        if self.chart is not None:
            self.chart.set_detection(detection)
