"""Single source of truth for navigation order and page construction."""

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import QWidget

from smartpower.ui.pages.analysis import AnalysisPage
from smartpower.ui.pages.anomaly import AnomalyPage
from smartpower.ui.pages.data_management import DataManagementPage
from smartpower.ui.pages.home import HomePage
from smartpower.ui.pages.settings import SettingsPage
from smartpower.ui.pages.reports import ReportsPage


@dataclass(frozen=True)
class PageSpec:
    key: str
    title: str
    factory: Callable[[], QWidget]


PAGE_SPECS = (
    PageSpec("home", "首页", HomePage),
    PageSpec("data", "数据管理", DataManagementPage),
    PageSpec("voltage", "电压分析", lambda: AnalysisPage("voltage")),
    PageSpec("current", "电流分析", lambda: AnalysisPage("current")),
    PageSpec("power", "功率分析", lambda: AnalysisPage("power")),
    PageSpec("anomalies", "异常检测", AnomalyPage),
    PageSpec("reports", "分析报告", ReportsPage),
    PageSpec("settings", "系统设置", SettingsPage),
)
