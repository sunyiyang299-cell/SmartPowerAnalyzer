"""Home page with working shortcuts, without fabricated metrics."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton

from smartpower.ui.pages.base import BasePage
from smartpower.ui.widgets import card, label


class HomePage(BasePage):
    navigate_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__("首页", "欢迎使用智电析，集中管理电力系统运行数据与分析工作。", parent)
        self.content.addWidget(label("V0.2 数据管理", "badge"))
        self.content.addWidget(card(
            "从运行数据开始",
            "前往数据管理导入 CSV / Excel，校验并预览数据后手动保存；也可生成明确标记的模拟数据进行演示。计算、图表和报告将在后续实现。",
        ))
        self.content.addWidget(card(
            "数据来源清晰可见",
            "文件导入仅表示来源未核验；演示数据明确标为模拟。请在数据管理查看预览和历史记录，当前不生成电气分析结论。",
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
