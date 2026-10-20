"""Home page with working shortcuts, without fabricated metrics."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton

from smartpower.ui.pages.base import BasePage
from smartpower.ui.widgets import card, label


class HomePage(BasePage):
    navigate_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__("首页", "欢迎使用智电析，集中管理电力系统运行数据与分析工作。", parent)
        self.content.addWidget(label("V0.1 基础框架", "badge"))
        self.content.addWidget(card(
            "从运行数据开始",
            "当前版本已提供八个模块的导航与页面框架。数据导入、计算、图表和报告功能将在后续版本实现。",
        ))
        self.content.addWidget(card(
            "尚无运行数据",
            "当前未连接数据源，不显示统计指标、示例曲线或模拟分析结论。",
        ))
        shortcuts = QHBoxLayout()
        self.data_button = QPushButton("前往数据管理 →")
        self.settings_button = QPushButton("查看系统设置 →")
        self.data_button.clicked.connect(lambda: self.navigate_requested.emit("data"))
        self.settings_button.clicked.connect(lambda: self.navigate_requested.emit("settings"))
        shortcuts.addWidget(self.data_button)
        shortcuts.addWidget(self.settings_button)
        shortcuts.addStretch()
        self.content.addLayout(shortcuts)
        self.content.addStretch()
