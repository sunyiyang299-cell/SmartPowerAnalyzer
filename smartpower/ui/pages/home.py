"""Home page with working shortcuts, without fabricated metrics."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton

from smartpower.ui.pages.base import BasePage
from smartpower.ui.widgets import card, label


class HomePage(BasePage):
    navigate_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__("首页", "欢迎使用智电析，集中管理电力系统运行数据与分析工作。", parent)
        self.content.addWidget(label("V0.4 可视化与异常检测", "badge"))
        self.content.addWidget(card(
            "从运行数据开始",
            "前往数据管理导入 CSV / Excel 并保存。分析页提供统计指标、逐点功率和时间曲线；异常检测页可启用用户阈值并联动曲线标记。报告生成待后续实现。",
        ))
        self.content.addWidget(card(
            "数据来源清晰可见",
            "文件导入仅表示来源未核验；模拟来源标记将保留到分析结果。功率计算仅适用于单相正弦稳态交流，数据统计不代表设备合格判定。",
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
