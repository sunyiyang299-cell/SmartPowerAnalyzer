"""Single source of truth for navigation order and page construction."""

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import QWidget

from smartpower.ui.pages.features import FeaturePage
from smartpower.ui.pages.data_management import DataManagementPage
from smartpower.ui.pages.home import HomePage
from smartpower.ui.pages.settings import SettingsPage


@dataclass(frozen=True)
class PageSpec:
    key: str
    title: str
    factory: Callable[[], QWidget]


PAGE_SPECS = (
    PageSpec("home", "首页", HomePage),
    PageSpec("data", "数据管理", DataManagementPage),
    PageSpec("voltage", "电压分析", lambda: FeaturePage(
        "电压分析", "查看与分析电压运行特征。",
        "计划支持电压趋势、统计与限值检查；分析前需明确单位、采样时间及限值来源。")),
    PageSpec("current", "电流分析", lambda: FeaturePage(
        "电流分析", "查看与分析电流运行特征。",
        "计划支持电流趋势、负载变化与三相数据对比，具体计算将在后续实现。")),
    PageSpec("power", "功率分析", lambda: FeaturePage(
        "功率分析", "查看有功、无功及相关功率运行特征。",
        "计划支持功率趋势及相关指标；需先明确输入字段、单位和计算约定。")),
    PageSpec("anomalies", "异常检测", lambda: FeaturePage(
        "异常检测", "基于明确规则识别运行数据中的可疑记录。",
        "计划支持缺失值、越限及突变检查，并展示规则与证据。当前未执行检测。")),
    PageSpec("reports", "分析报告", lambda: FeaturePage(
        "分析报告", "整理真实分析过程与结果，形成可追溯的报告。",
        "计划支持汇总数据来源、分析参数、图表和结论。当前未实现报告生成或导出。")),
    PageSpec("settings", "系统设置", SettingsPage),
)
