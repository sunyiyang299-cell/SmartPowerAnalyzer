"""Honest empty states for modules scheduled after V0.1."""

from smartpower.ui.pages.base import BasePage
from smartpower.ui.widgets import card, label


class FeaturePage(BasePage):
    def __init__(self, title: str, description: str, planned: str, parent=None):
        super().__init__(title, description, parent)
        self.content.addWidget(label("待开发 · V0.1 仅提供页面框架", "badge"))
        self.content.addWidget(card("后续功能规划", planned))
        self.content.addWidget(card(
            "当前状态",
            "此模块尚未实现。当前未导入运行数据，也未执行电气计算或生成分析结果。"
            "后续版本将基于用户导入的真实数据开展分析。",
        ))
        self.content.addStretch()
