"""Application setup; importing this module does not start the event loop."""

import sys

from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import QLibraryInfo, QTranslator, QTimer
from PySide6.QtWidgets import QApplication

from smartpower.config import APP_NAME, APP_VERSION, ORGANIZATION
from smartpower.resources import resource_path
from smartpower.ui.main_window import MainWindow
from smartpower.ui.theme import LIGHT_THEME


def create_application(argv: list[str] | None = None) -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv if argv is None else argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setWindowIcon(QIcon(str(resource_path("app.ico"))))
    app.setOrganizationName(ORGANIZATION)
    app.setStyle("Fusion")
    app.setFont(QFont("Microsoft YaHei UI", 10))
    app.setStyleSheet(LIGHT_THEME)
    if not hasattr(app, "_chinese_translator"):
        translator = QTranslator(app)
        if translator.load("qtbase_zh_CN", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
            app.installTranslator(translator)
        app._chinese_translator = translator
    return app


def main() -> int:
    arguments = sys.argv[1:]
    if arguments and arguments[0] in ("--release-check", "--release-reopen"):
        if len(arguments) != 2:
            return 2
        from smartpower.release_check import run_release_check
        return run_release_check(arguments[1], reopen=arguments[0] == "--release-reopen")
    app = create_application()
    window = MainWindow()
    # Show inside the active event loop so an immediate native close cannot
    # occur before QApplication can process its quit request.
    QTimer.singleShot(0, window.show)
    return app.exec()
