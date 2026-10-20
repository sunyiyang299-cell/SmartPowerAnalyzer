"""Data-management UI orchestration. All expensive work runs in TaskThread."""

import os
from pathlib import Path

from PySide6.QtCore import QStandardPaths, Qt, Signal
from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QFileDialog, QHBoxLayout, QLineEdit,
    QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QTableView,
)

from smartpower.data.demo import export_demo, generate_demo
from smartpower.data.importer import import_file
from smartpower.data.query import query_rows
from smartpower.data.validation import REQUIRED_COLUMNS
from smartpower.storage.repository import DatasetRepository
from smartpower.ui.pages.base import BasePage
from smartpower.ui.table_model import SampleTableModel
from smartpower.ui.tasks import TaskThread
from smartpower.ui.widgets import label


def default_database_path() -> Path:
    override = os.environ.get("SMARTPOWER_DB_PATH")
    if override:
        return Path(override)
    return Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)) / "datasets.sqlite3"


class DataManagementPage(BasePage):
    operation_finished = Signal()

    def __init__(self, parent=None, repository=None):
        super().__init__("数据管理", "导入并校验单相交流有效值数据，预览确认后保存到本地数据库。", parent)
        self.content.setContentsMargins(24, 20, 24, 20)
        self.content.setSpacing(10)
        self.repository = repository or DatasetRepository(default_database_path())
        self.dataset = None
        self._dirty = False
        self._dataset_id = None
        self._thread = None
        self._callback = None
        self._sort_column = 0
        self._ascending = True
        self.import_button = QPushButton("导入 CSV / Excel")
        self.demo_button = QPushButton("生成 1000 条模拟数据")
        row = QHBoxLayout()
        row.addWidget(self.import_button)
        row.addWidget(self.demo_button)
        row.addStretch()
        self.content.addLayout(row)
        self.content.addWidget(label("必需字段：时间、电压、电流、功率因数。单位：V、A；有效值非负，功率因数 0～1。", "muted"))

        self.name_edit = QLineEdit()
        self.name_edit.setMaxLength(200)
        self.name_edit.setPlaceholderText("数据集名称（保存前可修改）")
        self.save_button = QPushButton("保存数据集")
        self.export_button = QPushButton("导出模拟 CSV")
        row = QHBoxLayout()
        for widget in (self.name_edit, self.save_button, self.export_button):
            row.addWidget(widget)
        self.content.addLayout(row)

        self.history_combo = QComboBox()
        self.history_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.history_combo.setMinimumContentsLength(8)
        self.history_combo.setPlaceholderText("请选择历史数据集")
        self.refresh_button = QPushButton("刷新历史")
        self.load_button = QPushButton("读取")
        self.delete_button = QPushButton("删除")
        row = QHBoxLayout()
        row.addWidget(self.history_combo, 1)
        for widget in (self.refresh_button, self.load_button, self.delete_button):
            row.addWidget(widget)
        self.content.addLayout(row)

        self.filter_column = QComboBox()
        self.filter_column.addItems(["全部字段", *REQUIRED_COLUMNS])
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("输入包含文本，点击筛选")
        self.filter_button = QPushButton("筛选")
        self.clear_button = QPushButton("清除")
        row = QHBoxLayout()
        for widget in (self.filter_column, self.filter_edit, self.filter_button, self.clear_button):
            row.addWidget(widget)
        self.content.addLayout(row)
        self.source_label = label("尚无预览数据。导入和生成后均需手动保存。", "badge")
        self.count_label = label("总记录数：0 · 当前显示：0", "muted")
        self.content.addWidget(self.source_label)
        self.content.addWidget(self.count_label)
        self.model = SampleTableModel(self)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setMinimumHeight(260)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setStretchLastSection(False)
        for index, width in enumerate((210, 130, 130, 130, 240)):
            self.table.setColumnWidth(index, width)
        self.table.horizontalHeader().setSortIndicator(0, Qt.SortOrder.AscendingOrder)
        self.content.addWidget(self.table, 1)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.content.addWidget(self.progress)
        self.message = QPlainTextEdit()
        self.message.setReadOnly(True)
        self.message.setMaximumHeight(110)
        self.message.setVisible(False)
        self.content.insertWidget(2, self.message)
        self.database_info = QPlainTextEdit()
        self.database_info.setReadOnly(True)
        self.database_info.setAccessibleName("本地数据库路径")
        self.database_info.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        self.database_info.setFixedHeight(60)
        self.database_info.setPlainText(
            f"本地数据库：{self.repository.path}\n点击“刷新历史”读取历史；导入不会自动保存。")
        self.content.addWidget(self.database_info)
        self._controls = (self.import_button, self.demo_button, self.save_button, self.export_button,
                          self.refresh_button, self.load_button, self.delete_button, self.history_combo,
                          self.name_edit, self.filter_column, self.filter_edit, self.filter_button, self.clear_button)
        self.import_button.clicked.connect(self._choose_file)
        self.demo_button.clicked.connect(self.generate)
        self.save_button.clicked.connect(self.save)
        self.export_button.clicked.connect(self._choose_export)
        self.refresh_button.clicked.connect(self.refresh_history)
        self.load_button.clicked.connect(self.load_selected)
        self.delete_button.clicked.connect(self.delete_selected)
        self.filter_button.clicked.connect(self.apply_filter)
        self.filter_edit.returnPressed.connect(self.apply_filter)
        self.clear_button.clicked.connect(self.clear_filter)
        self.model.sort_requested.connect(self._sort)
        self.history_combo.currentIndexChanged.connect(self._update_controls)
        self._update_controls()

    @property
    def busy(self):
        return self._thread is not None

    @property
    def has_unsaved_data(self):
        return self._dirty

    def notify(self, text):
        self.message.setPlainText(text)
        self.message.setFixedHeight(110 if text.count("\n") > 1 else 50)
        self.message.setVisible(bool(text))

    def _update_controls(self, *_):
        for widget in self._controls:
            widget.setEnabled(not self.busy)
        available = self.dataset is not None and not self.busy
        self.save_button.setEnabled(available and self._dirty)
        self.export_button.setEnabled(available and self.dataset.simulated)
        for widget in (self.filter_button, self.clear_button):
            widget.setEnabled(available)
        selected = self.history_combo.currentData() is not None and not self.busy
        self.load_button.setEnabled(selected)
        self.delete_button.setEnabled(selected)
        self.table.horizontalHeader().setEnabled(not self.busy)

    def _start(self, operation, callback, message):
        if self.busy:
            return
        self.notify(message)
        self._callback = callback
        self._thread = TaskThread(operation, self)
        self._thread.finished.connect(self._finish)
        self.progress.setVisible(True)
        self._update_controls()
        self._thread.start()

    def _finish(self):
        thread, callback = self._thread, self._callback
        self._thread = None
        self._callback = None
        self.progress.setVisible(False)
        try:
            if thread.error:
                self.notify(thread.error + "\n当前预览及已有数据集保持不变。")
                self.ensureWidgetVisible(self.message)
            else:
                callback(thread.result)
        except Exception as exc:
            self.notify(f"更新界面失败：{exc}，请刷新历史核实保存状态。")
        finally:
            thread.deleteLater()
            self._update_controls()
            self.operation_finished.emit()

    def _confirm(self, title, text, action="确认"):
        dialog = QMessageBox(self)
        dialog.setWindowTitle(title)
        dialog.setTextFormat(Qt.TextFormat.PlainText)
        dialog.setText(text)
        accept = dialog.addButton(action, QMessageBox.ButtonRole.AcceptRole)
        cancel = dialog.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        dialog.setDefaultButton(cancel)
        dialog.exec()
        return dialog.clickedButton() is accept

    def confirm_discard(self):
        return not self._dirty or self._confirm("尚有未保存的预览", "当前预览尚未保存，继续将放弃此预览。", "放弃预览")

    def _choose_file(self):
        if self.busy:
            return
        path, _ = QFileDialog.getOpenFileName(self, "选择运行数据文件", "", "运行数据 (*.csv *.xlsx)")
        if path:
            self.import_path(path)

    def import_path(self, path):
        if self.busy or not self.confirm_discard():
            return
        self._start(lambda: self._prepare(import_file(path)), self._show_preview, "正在后台读取并校验文件…")

    @staticmethod
    def _prepare(dataset):
        return dataset, query_rows(dataset)

    def generate(self):
        if self.busy or not self.confirm_discard():
            return
        self._start(lambda: self._prepare(generate_demo()), self._show_preview, "正在生成模拟数据，非真实设备测量…")

    def _show_preview(self, result, saved=False):
        self.dataset, rows = result
        self._dirty = not saved
        self._dataset_id = None
        self.name_edit.setText(self.dataset.name)
        self.filter_edit.clear()
        self.filter_column.setCurrentIndex(0)
        self._sort_column, self._ascending = 0, True
        header = self.table.horizontalHeader()
        header.blockSignals(True)
        header.setSortIndicator(0, Qt.SortOrder.AscendingOrder)
        header.blockSignals(False)
        self.model.set_view(self.dataset, rows)
        self.source_label.setText(self.dataset.source + (" · 已保存历史数据" if saved else " · 预览未保存"))
        self._update_count()
        self.notify(self.dataset.warning or "校验通过。请查看预览；保存将存储全部记录，不受筛选影响。")

    def _update_count(self):
        self.count_label.setText(f"总记录数：{len(self.dataset.frame)} · 当前显示：{self.model.rowCount()}")

    def save(self):
        if self.busy or self.dataset is None or not self._dirty:
            return
        name = self.name_edit.text().strip()
        if not name:
            self.notify("数据集名称不能为空。")
            return
        dataset = self.dataset
        def operation():
            identifier = self.repository.save(dataset, name)
            return identifier
        def saved(identifier):
            self._dirty = False
            self._dataset_id = identifier
            self.source_label.setText(dataset.source + " · 已保存")
            self.notify(f"数据集已保存，编号：{identifier}。点击“刷新历史”查看。")
        self._start(operation, saved, "正在保存全部采样记录…")

    def refresh_history(self):
        self._start(self.repository.list_datasets, self._set_history, "正在读取历史数据集…")

    def _set_history(self, rows):
        self.history_combo.clear()
        for item in rows:
            source = "模拟数据" if item["simulated"] else "导入文件"
            self.history_combo.addItem(
                f"{item['name']} · {item['row_count']} 条 · {item['imported_at']} · {source}", item["id"])
        if rows:
            self.history_combo.setCurrentIndex(0)
        self.notify(f"已读取 {len(rows)} 个历史数据集。")

    def load_selected(self):
        identifier = self.history_combo.currentData()
        if self.busy or identifier is None or not self.confirm_discard():
            return
        def loaded(result):
            self._show_preview(result, saved=True)
            self._dataset_id = identifier
        self._start(lambda: self._prepare(self.repository.load(identifier)), loaded, "正在后台读取历史采样记录…")

    def delete_selected(self):
        identifier = self.history_combo.currentData()
        if self.busy or identifier is None:
            return
        if not self._confirm("删除数据集", f"确定删除以下数据集及全部采样记录？\n{self.history_combo.currentText()}\n删除后无法恢复。", "确认删除"):
            return
        def deleted(_):
            self.history_combo.removeItem(self.history_combo.findData(identifier))
            if self._dataset_id == identifier:
                self._dataset_id = None
                self._dirty = True
                self.source_label.setText(self.dataset.source + " · 历史记录已删除，当前预览未保存")
            self.notify("指定数据集已删除。当前表格为内存预览，未受影响。")
        self._start(lambda: self.repository.delete(identifier), deleted, "正在删除指定数据集…")

    def _choose_export(self):
        if self.busy or self.dataset is None or not self.dataset.simulated:
            return
        dialog = QFileDialog(self, "导出模拟数据（非真实设备测量）")
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dialog.setNameFilter("CSV 文件 (*.csv)")
        dialog.setDefaultSuffix("csv")
        dialog.selectFile("模拟数据.csv")
        if dialog.exec():
            self.export_to(dialog.selectedFiles()[0])

    def export_to(self, path):
        if self.busy or self.dataset is None:
            return
        dataset = self.dataset
        self._start(lambda: export_demo(dataset, path),
                    lambda _: self.notify("模拟数据 CSV 已导出，文件内含模拟来源标记。"), "正在导出全部模拟数据…")

    def _sort(self, column, ascending):
        if self.busy:
            return
        self._sort_column, self._ascending = column, ascending
        self.apply_filter()

    def clear_filter(self):
        self.filter_edit.clear()
        self.apply_filter()

    def apply_filter(self):
        if self.busy or self.dataset is None:
            return
        dataset = self.dataset
        text, column = self.filter_edit.text(), self.filter_column.currentText()
        order, ascending = self._sort_column, self._ascending
        def show(rows):
            self.model.set_view(dataset, rows)
            self._update_count()
            self.notify("筛选与排序已完成，原始数据未修改。")
        self._start(lambda: query_rows(dataset, text, column, order, ascending), show, "正在后台筛选与排序…")
