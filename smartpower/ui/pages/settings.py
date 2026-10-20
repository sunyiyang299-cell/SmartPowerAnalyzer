"""Read-only software information; do not present unimplemented controls."""

import platform
import sqlite3

from PySide6.QtCore import qVersion

from smartpower.config import APP_NAME, APP_VERSION
from smartpower.ui.pages.base import BasePage
from smartpower.ui.widgets import card


class SettingsPage(BasePage):
    def __init__(self, parent=None):
        super().__init__("系统设置", "查看软件版本与当前运行环境。", parent)
        self.content.addWidget(card("软件信息", f"{APP_NAME}\n框架版本：V{APP_VERSION}"))
        self.content.addWidget(card(
            "运行环境",
            f"Python {platform.python_version()} · Qt {qVersion()} · SQLite {sqlite3.sqlite_version}\n"
            "界面主题：浅色。当前版本不提供可修改设置。",
        ))
        self.content.addWidget(card(
            "后续扩展",
            "数据路径、分析参数及报告选项将在对应功能实现后加入。当前启动不会创建数据库或写入分析数据。",
        ))
        self.content.addStretch()
