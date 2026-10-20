"""One bounded background task; widgets are only touched by the owner thread."""

from PySide6.QtCore import QThread


class TaskThread(QThread):
    def __init__(self, operation, parent=None):
        super().__init__(parent)
        self.operation = operation
        self.result = None
        self.error = None

    def run(self):
        try:
            self.result = self.operation()
        except Exception as exc:
            self.error = str(exc) or "操作失败，发生未知错误。"
