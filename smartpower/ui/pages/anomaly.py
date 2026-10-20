"""Threshold detection page reusing saved-dataset selection and task lifecycle."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QLineEdit, QPushButton, QTableView

from smartpower.anomaly.models import DISCLAIMER, KINDS, Thresholds
from smartpower.anomaly.service import detect_saved_dataset
from smartpower.data.validation import DataError
from smartpower.ui.anomaly_model import AnomalyTableModel
from smartpower.ui.pages.analysis import AnalysisPage
from smartpower.ui.widgets import label


class AnomalyPage(AnalysisPage):
    detection_changed = Signal(object)

    def __init__(self, parent=None, repository=None):
        super().__init__("voltage", parent, repository, with_chart=False)
        self.title_label.setText("异常检测")
        self.content.itemAt(1).widget().setText("选择已保存数据集，填写并明确启用用户阈值后开始检测；结果可关联电压、电流曲线。")
        self.analyze_button.setText("开始检测")
        self.summary.hide()
        self.enabled_check = QCheckBox("我已确认阈值，仅按当前配置启用检测")
        self.content.insertWidget(2, self.enabled_check)
        form = QFormLayout()
        self.voltage_lower = QLineEdit()
        self.voltage_upper = QLineEdit()
        self.current_upper = QLineEdit()
        self.threshold_inputs = (self.voltage_lower, self.voltage_upper, self.current_upper)
        for title, edit in zip(("电压下限（V）", "电压上限（V）", "电流上限（A）"), self.threshold_inputs):
            edit.setPlaceholderText("请输入有限非负数值")
            form.addRow(title, edit)
        self.content.insertLayout(3, form)
        self.preset_button = QPushButton("填入演示阈值（非标准：210 V / 230 V / 20 A）")
        self.content.insertWidget(4, self.preset_button)
        self.content.insertWidget(5, label("电压 < 下限或 > 上限、电流 > 上限才计异常；等于阈值不计。演示阈值不是国家标准或设备合格判据。", "muted"))
        self.counts = label("尚无当前阈值的检测结果。", "sectionTitle")
        self.content.addWidget(self.counts)
        self.type_filter = QComboBox()
        self.type_filter.addItems(["全部异常", *KINDS])
        self.content.addWidget(self.type_filter)
        self.event_model = AnomalyTableModel(self)
        self.event_table = QTableView()
        self.event_table.setModel(self.event_model)
        self.event_table.setMinimumHeight(300)
        for col, width in enumerate((140, 220, 120, 80, 120, 120, 60, 100, 230)):
            self.event_table.setColumnWidth(col, width)
        self.content.addWidget(self.event_table)
        self.content.addWidget(label(DISCLAIMER, "muted"))
        self.preset_button.clicked.connect(self.apply_demo_preset)
        for edit in self.threshold_inputs:
            edit.textChanged.connect(self._threshold_changed)
        self.enabled_check.toggled.connect(self._threshold_changed)
        self.type_filter.currentTextChanged.connect(self._filter_events)

    def apply_demo_preset(self):
        for edit, value in zip(self.threshold_inputs, ("210", "230", "20")):
            edit.setText(value)
        self.notify("已填入演示阈值，尚需明确勾选启用并点击“开始检测”；这不是设备合格判据。")

    def _clear_results(self):
        super()._clear_results()
        if hasattr(self, "event_model"):
            self.event_model.set_result(None)
            self.counts.setText("尚无当前阈值的检测结果。")
        self.detection_changed.emit(None)

    def _threshold_changed(self, *_):
        self._revision += 1
        self._clear_results()
        self.notify("阈值或启用状态已变化，旧检测及曲线标记已清除；请重新开始检测。")

    def start_analysis(self):
        if self.busy:
            return
        self._revision += 1
        self._clear_results()
        identifier = self.dataset_combo.currentData()
        if identifier is None:
            self.notify("请先选择已保存的数据集，再开始检测。")
            return
        if not self.enabled_check.isChecked():
            self.notify("请填写阈值并明确勾选启用阈值检测。")
            return
        try:
            try:
                values = [float(edit.text()) for edit in self.threshold_inputs]
            except (ValueError, OverflowError) as exc:
                raise DataError("阈值必须为有限非负数值，请检查输入。") from exc
            thresholds = Thresholds(*values)
        except DataError as exc:
            self.notify(str(exc))
            return
        self._start(lambda: detect_saved_dataset(self.repository, identifier, thresholds),
                    self._display_result, "正在后台读取完整数据并检测…")

    def _display_result(self, result):
        self.current_result = result
        self.event_model.set_result(result, self.type_filter.currentText())
        counts = result.type_counts
        self.counts.setText(f"异常事件 {len(result.events)} 次 · 涉及唯一采样点 {result.unique_sample_count} 条\n"
                            + " · ".join(f"{kind} {counts[kind]} 次" for kind in KINDS))
        self.metadata.setPlainText(f"数据集：{result.dataset_name}\n完整采样：{result.count} 条 · 来源：{result.source}")
        self.notify("检测完成；异常标记已关联相同数据快照的电压/电流曲线。" if result.events
                    else "未检测到符合当前阈值条件的异常记录。")
        self.detection_changed.emit(result)

    def _filter_events(self, kind):
        self.event_model.set_result(self.current_result, kind)
