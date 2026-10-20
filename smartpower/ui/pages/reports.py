"""Report centre: options captured before background snapshot and export."""

from pathlib import Path

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLineEdit,
                              QMessageBox, QPlainTextEdit, QProgressBar, QPushButton)

from smartpower.anomaly.models import DISCLAIMER, Thresholds
from smartpower.data.validation import DataError
from smartpower.reporting.excel_exporter import export_excel
from smartpower.reporting.models import validate_title
from smartpower.reporting.pdf_exporter import export_pdf
from smartpower.reporting.service import build_report_snapshot
from smartpower.storage.repository import DatasetRepository
from smartpower.ui.pages.base import BasePage
from smartpower.ui.paths import default_database_path, default_settings_manager
from smartpower.ui.tasks import TaskThread
from smartpower.ui.widgets import label


class ReportsPage(BasePage):
    operation_finished = Signal()

    def __init__(self, parent=None, repository=None, manager=None):
        super().__init__("分析报告", "从本次读取的数据快照离线生成 PDF / Excel，完整统计和异常明细不随图表抽稀改变。", parent)
        self.content.setContentsMargins(24, 20, 24, 20)
        self.manager = manager or default_settings_manager()
        self.repository = repository or DatasetRepository(default_database_path())
        self.current_snapshot = None
        self._thread = None
        self._revision = 0
        self._rows = {}
        row = QHBoxLayout()
        self.dataset_combo = QComboBox()
        self.dataset_combo.setMinimumContentsLength(8)
        self.dataset_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.dataset_combo.setPlaceholderText("请选择已保存数据集")
        self.refresh_button = QPushButton("刷新数据集")
        row.addWidget(self.dataset_combo, 1)
        row.addWidget(self.refresh_button)
        self.content.addLayout(row)
        self.metadata = QPlainTextEdit()
        self.metadata.setReadOnly(True)
        self.metadata.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        self.metadata.setFixedHeight(85)
        self.content.addWidget(self.metadata)
        form = QFormLayout()
        self.report_title = QLineEdit()
        form.addRow("报告标题", self.report_title)
        self.detection_enabled = QCheckBox("在本次报告中执行用户阈值检测")
        form.addRow(self.detection_enabled)
        self.voltage_lower, self.voltage_upper, self.current_upper = (QLineEdit() for _ in range(3))
        self.threshold_inputs = (self.voltage_lower, self.voltage_upper, self.current_upper)
        for text, edit in zip(("电压下限（V）", "电压上限（V）", "电流上限（A）"), self.threshold_inputs):
            edit.setPlaceholderText("启用检测时必填有限非负数值")
            form.addRow(text, edit)
        self.content.addLayout(form)
        self.content.addWidget(label("不勾选时明确标注“本次未执行异常检测”，不会写成零异常。用户阈值不是国家标准限值，等于阈值不计异常。", "muted"))
        row = QHBoxLayout()
        self.pdf_button, self.excel_button = QPushButton("生成 PDF 报告"), QPushButton("生成 Excel 报告")
        row.addWidget(self.pdf_button)
        row.addWidget(self.excel_button)
        row.addStretch()
        self.content.addLayout(row)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        self.content.addWidget(self.progress)
        self.message = label("请先刷新并选择已保存数据集。", "muted")
        self.content.addWidget(self.message)
        self.content.addWidget(label("任务开始后固定数据集、标题、阈值和字体配置；后台生成期间可继续使用导航。配置发生变化时仍按启动时快照导出，并明确提示文件对应的数据集。", "muted"))
        self.content.addWidget(label(DISCLAIMER, "muted"))
        self.preference_note = label("", "muted")
        self.content.addWidget(self.preference_note)
        self.refresh_button.clicked.connect(self.refresh_datasets)
        self.dataset_combo.currentIndexChanged.connect(self._changed)
        self.report_title.textChanged.connect(self._changed)
        self.detection_enabled.toggled.connect(self._changed)
        for edit in self.threshold_inputs:
            edit.textChanged.connect(self._changed)
        self.pdf_button.clicked.connect(lambda: self.start_export("pdf"))
        self.excel_button.clicked.connect(lambda: self.start_export("xlsx"))
        loaded = self.manager.load()
        self.apply_preferences(loaded.value)
        self._changed()
        if loaded.warning:
            self.notify(loaded.warning)

    @property
    def busy(self):
        return self._thread is not None

    def notify(self, text):
        self.message.setText(text)

    def apply_preferences(self, settings):
        self._revision += 1
        self.current_snapshot = None
        if not self.busy:
            self.report_title.setText(settings.report_title)
        self.preference_note.setText(f"默认报告目录：{settings.report_directory}\nPDF 字体：{'用户配置 TrueType 字体' if settings.font_path else '标准 STSong-Light 引用；阅读器需支持中文，亦可在设置中配置嵌入字体'}")

    def _changed(self, *_):
        self._revision += 1
        self.current_snapshot = None
        row = self._rows.get(self.dataset_combo.currentData())
        if row:
            source = "模拟数据，非真实设备测量" if row["simulated"] else "导入文件（来源未核验）"
            self.metadata.setPlainText(f"数据集：{row['name']}\n来源：{source}\n已保存记录：{row['row_count']} 条（导出时重新读取并校验）")
        else:
            self.metadata.setPlainText("尚未选择数据集，没有当前数据集的报告结果。")
        if not self.busy:
            self.notify("配置或数据集已变化，请选择格式生成报告。")

    def _start(self, operation, task_kind):
        self._task_kind = task_kind
        self._task_revision = self._revision
        self._thread = TaskThread(operation, self)
        self._thread.finished.connect(self._finish)
        self.progress.show()
        self._set_enabled(False)
        self._thread.start()

    def _set_enabled(self, enabled):
        for widget in (self.dataset_combo, self.refresh_button, self.pdf_button, self.excel_button,
                       self.report_title, self.detection_enabled, *self.threshold_inputs):
            widget.setEnabled(enabled)

    def _finish(self):
        thread = self._thread
        self._thread = None
        self.progress.hide()
        self._set_enabled(True)
        try:
            if thread.error:
                self.current_snapshot = None
                self.notify("报告生成或读取失败：" + thread.error)
            elif self._task_kind == "list":
                with QSignalBlocker(self.dataset_combo):
                    self.dataset_combo.clear()
                    self._rows = {row["id"]: row for row in thread.result}
                    for row in thread.result:
                        self.dataset_combo.addItem(f"{row['name']} · {'模拟数据' if row['simulated'] else '来源未核验'}", row["id"])
                    self.dataset_combo.setCurrentIndex(-1)
                self._changed()
                self.notify(f"已读取 {len(self._rows)} 个数据集，请选择。" if self._rows else "尚无已保存数据集，请先在数据管理中保存。")
            else:
                snapshot, path = thread.result
                changed = self._revision != self._task_revision
                self.current_snapshot = None if changed else snapshot
                suffix = "当前选择或配置已变化，该文件仍对应启动时的快照。" if changed else "报告对应本次读取并校验的数据快照。"
                self.notify(f"报告已保存：{path}\n数据集：{snapshot.analysis.dataset_name} · {snapshot.source_label}\n{suffix}")
        except Exception as exc:
            self.current_snapshot = None
            self.notify(f"报告结果处理失败：{exc}")
        finally:
            thread.deleteLater()
            self.operation_finished.emit()

    def refresh_datasets(self):
        if self.busy:
            return
        self.current_snapshot = None
        self._revision += 1
        self.notify("正在后台读取已保存数据集…")
        self._start(self.repository.list_datasets, "list")

    def start_export(self, kind):
        if self.busy:
            return
        self.current_snapshot = None
        identifier = self.dataset_combo.currentData()
        if identifier is None:
            self.notify("请先选择已保存的数据集，再生成报告。")
            return
        try:
            title = validate_title(self.report_title.text())
            thresholds = None
            if self.detection_enabled.isChecked():
                try:
                    thresholds = Thresholds(*(float(edit.text()) for edit in self.threshold_inputs))
                except (ValueError, OverflowError) as exc:
                    raise DataError(f"异常检测阈值无效：{exc}。请填写有效阈值或取消检测。") from exc
            loaded = self.manager.load()
            if loaded.warning:
                raise DataError(loaded.warning + "请先在系统设置确认并保存有效的目录、标题与字体配置，再生成报告。")
            settings = loaded.value
            revision = self._revision
            path, _ = QFileDialog.getSaveFileName(self, "保存 PDF 报告" if kind == "pdf" else "保存 Excel 报告",
                str(Path(settings.report_directory) / f"分析报告.{kind}"),
                "PDF 报告 (*.pdf)" if kind == "pdf" else "Excel 报告 (*.xlsx)", options=QFileDialog.Option.DontConfirmOverwrite)
            if not path:
                return
            if not Path(path).suffix:
                path += f".{kind}"
            if Path(path).suffix.lower() != f".{kind}":
                raise DataError(f"文件必须使用 .{kind} 扩展名。")
            overwrite = Path(path).exists()
            if overwrite and QMessageBox.question(self, "确认覆盖", "报告已存在，是否覆盖？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                return
            if revision != self._revision:
                self.notify("选择或配置已变化，本次导出已取消，请重新生成。")
                return
            repository = self.repository
            def generate():
                snapshot = build_report_snapshot(repository, identifier, title=title, thresholds=thresholds)
                if kind == "pdf":
                    export_pdf(snapshot, path, overwrite=overwrite, font_path=settings.font_path)
                else:
                    export_excel(snapshot, path, overwrite=overwrite)
                return snapshot, str(Path(path).resolve())
            self.notify((loaded.warning + "\n" if loaded.warning else "") + "正在后台读取完整快照并生成报告…")
            self._start(generate, kind)
        except Exception as exc:
            self.notify(f"无法生成报告：{exc}")
