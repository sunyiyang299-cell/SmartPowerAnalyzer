"""Desktop shell with native window chrome and synchronized navigation."""

from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QHBoxLayout, QMainWindow,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from smartpower.config import APP_NAME, APP_VERSION
from smartpower.ui.pages.home import HomePage
from smartpower.ui.pages.registry import PAGE_SPECS
from smartpower.ui.widgets import label


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 800)
        self.setMinimumSize(900, 620)
        workspace = QWidget()
        workspace.setObjectName("workspace")
        layout = QHBoxLayout(workspace)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(218)
        navigation = QVBoxLayout(sidebar)
        navigation.setContentsMargins(18, 28, 18, 20)
        navigation.setSpacing(8)
        navigation.addWidget(label("智电析", "brand"))
        navigation.addWidget(label("电力系统运行数据分析", "muted"))
        navigation.addSpacing(24)
        self.navigation_group = QButtonGroup(self)
        self.navigation_group.setExclusive(True)
        self.navigation_buttons: dict[str, QPushButton] = {}
        self.pages: dict[str, QWidget] = {}
        self.stack = QStackedWidget()
        self.stack.setObjectName("pageStack")
        for index, spec in enumerate(PAGE_SPECS):
            button = QPushButton(spec.title)
            button.setObjectName("navButton")
            button.setAccessibleName(spec.title)
            button.setCheckable(True)
            self.navigation_group.addButton(button, index)
            self.navigation_buttons[spec.key] = button
            navigation.addWidget(button)
            page = spec.factory()
            page.setObjectName(f"page_{spec.key}")
            self.pages[spec.key] = page
            self.stack.addWidget(page)
            if isinstance(page, HomePage):
                page.navigate_requested.connect(self.navigate)
        navigation.addStretch()
        navigation.addWidget(label(f"V{APP_VERSION} · 数据管理", "muted"))
        layout.addWidget(sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(workspace)
        self.navigation_group.idClicked.connect(self.stack.setCurrentIndex)
        self.stack.currentChanged.connect(self._sync_navigation)
        self._sync_navigation(0)

    def navigate(self, key: str) -> None:
        """Route by stable key; invalid routes must not silently select a page."""
        if key not in self.pages:
            raise KeyError(f"Unknown page: {key}")
        self.stack.setCurrentWidget(self.pages[key])

    def _sync_navigation(self, index: int) -> None:
        self.navigation_group.button(index).setChecked(True)
        self.statusBar().showMessage(f"当前页面：{PAGE_SPECS[index].title}  |  V{APP_VERSION}")

    def closeEvent(self, event):
        page = self.pages["data"]
        if page.busy:
            page.notify("后台任务尚未完成，请等待结束后再关闭窗口。")
            self.navigate("data")
            event.ignore()
        elif not page.confirm_discard():
            event.ignore()
        else:
            super().closeEvent(event)
