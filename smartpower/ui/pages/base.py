"""Scrollable page shell shared by all modules."""

from PySide6.QtWidgets import QScrollArea, QVBoxLayout, QWidget

from smartpower.ui.widgets import label


class BasePage(QScrollArea):
    def __init__(self, title: str, description: str, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        body = QWidget()
        self.content = QVBoxLayout(body)
        self.content.setContentsMargins(36, 32, 36, 32)
        self.content.setSpacing(20)
        self.title_label = label(title, "pageTitle")
        self.content.addWidget(self.title_label)
        self.content.addWidget(label(description, "muted"))
        self.setWidget(body)
