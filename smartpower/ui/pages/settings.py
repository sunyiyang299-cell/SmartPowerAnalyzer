"""Explicit user preferences; no dataset path changes."""

import platform
import sqlite3

from PySide6.QtCore import Signal, qVersion
from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton

from smartpower.config import APP_NAME, APP_VERSION
from smartpower.settings.models import AppSettings, PAGE_KEYS
from smartpower.ui.pages.base import BasePage
from smartpower.ui.paths import default_settings_manager
from smartpower.ui.widgets import card, label


class SettingsPage(BasePage):
    settings_saved = Signal(object)

    def __init__(self, parent=None, manager=None):
        super().__init__("系统设置", "设置报告和图表默认目录、标题及启动页面；数据存储路径规则保持不变。", parent)
        self.manager = manager or default_settings_manager()
        self.content.setContentsMargins(24, 20, 24, 20)
        self.content.addWidget(card("软件信息", f"{APP_NAME}\n开发版本：V{APP_VERSION}\nPython {platform.python_version()} · Qt {qVersion()} · SQLite {sqlite3.sqlite_version}"))
        form = QFormLayout()
        self.report_directory, self.chart_directory, self.report_title, self.font_path = (QLineEdit() for _ in range(4))
        self.startup_page = QComboBox()
        for title, key in zip(("首页", "数据管理", "电压分析", "电流分析", "功率分析", "异常检测", "分析报告", "系统设置"), PAGE_KEYS):
            self.startup_page.addItem(title, key)
        for text, edit in (("默认报告目录", self.report_directory), ("默认图表目录", self.chart_directory)):
            row = QHBoxLayout()
            button = QPushButton("浏览…")
            button.clicked.connect(lambda checked=False, field=edit: self.choose_directory(field))
            row.addWidget(edit, 1)
            row.addWidget(button)
            form.addRow(text, row)
        form.addRow("默认报告标题", self.report_title)
        form.addRow("启动页面（重启生效）", self.startup_page)
        font_row = QHBoxLayout()
        font_button = QPushButton("选择字体…")
        font_button.clicked.connect(self.choose_font)
        font_row.addWidget(self.font_path, 1)
        font_row.addWidget(font_button)
        self.font_path.setPlaceholderText("留空：标准 PDF 中文字体 STSong-Light 引用")
        form.addRow("PDF 中文字体", font_row)
        self.content.addLayout(form)
        self.content.addWidget(label("标准引用不分发字体文件，阅读器需支持中文/亚洲字体包。离线跨机阅读建议选择有合法嵌入许可、包含所需中文的 TrueType 字体；文件仅在本机使用，不上传。", "muted"))
        buttons = QHBoxLayout()
        self.save_button, self.restore_button = QPushButton("保存设置"), QPushButton("恢复默认设置")
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.restore_button)
        buttons.addStretch()
        self.content.addLayout(buttons)
        self.message = label("", "muted")
        self.content.addWidget(self.message)
        self.config_location = QPlainTextEdit()
        self.config_location.setReadOnly(True)
        self.config_location.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        self.config_location.setFixedHeight(105)
        self.config_location.setPlainText(f"设置文件：{self.manager.path}\n仅在保存或确认恢复时创建专用设置目录；不创建不存在的报告/图表目录，不修改数据库。")
        self.content.addWidget(self.config_location)
        self.save_button.clicked.connect(self.save_settings)
        self.restore_button.clicked.connect(self.restore_defaults)
        self.reload()

    def fill(self, settings):
        for edit, value in ((self.report_directory, settings.report_directory), (self.chart_directory, settings.chart_directory),
                            (self.report_title, settings.report_title), (self.font_path, settings.font_path)):
            edit.setText(value)
        self.startup_page.setCurrentIndex(self.startup_page.findData(settings.startup_page))

    def reload(self):
        loaded = self.manager.load()
        self.fill(loaded.value)
        self.message.setText(loaded.warning or "设置已读取；更改后点击保存。")

    def choose_directory(self, edit):
        path = QFileDialog.getExistingDirectory(self, "选择已有目录", edit.text())
        if path:
            edit.setText(path)

    def choose_font(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择具有合法嵌入许可的中文 TrueType 字体", self.font_path.text(), "TrueType 字体 (*.ttf *.ttc)")
        if path:
            self.font_path.setText(path)

    def save_settings(self):
        try:
            settings = AppSettings(self.report_directory.text(), self.chart_directory.text(), self.report_title.text(),
                                   self.startup_page.currentData(), self.font_path.text())
            self.manager.save(settings)
            self.settings_saved.emit(settings)
            self.message.setText("设置已保存；默认导出路径立即使用，启动页面在重启后生效。")
        except Exception as exc:
            self.message.setText(f"设置保存失败：{exc}")

    def restore_defaults(self):
        if QMessageBox.question(self, "恢复默认设置", "确认恢复并保存默认设置？不会修改或删除数据集。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        try:
            self.manager.save(self.manager.defaults)
            self.fill(self.manager.defaults)
            self.settings_saved.emit(self.manager.defaults)
            self.message.setText("默认设置已恢复并保存。")
        except Exception as exc:
            self.message.setText(f"恢复默认设置失败：{exc}")
