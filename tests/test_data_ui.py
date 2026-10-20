import time

from PySide6.QtCore import QEventLoop, QTimer, Qt
from PySide6.QtTest import QTest
import pytest

from smartpower.application import create_application
from smartpower.data.demo import export_demo, generate_demo
from smartpower.storage.repository import DatasetRepository, StorageError
from smartpower.ui.pages.data_management import DataManagementPage


@pytest.fixture(scope="session")
def app():
    return create_application([])


@pytest.fixture
def page(app, tmp_path, monkeypatch):
    widget = DataManagementPage(repository=DatasetRepository(tmp_path / "ui.sqlite3"))
    monkeypatch.setattr(widget, "_confirm", lambda *args: True)
    widget.resize(800, 850)
    widget.show()
    yield widget
    wait_idle(widget)
    widget._dirty = False
    widget.close()
    widget.deleteLater()
    app.processEvents()


def wait_idle(page, seconds=20):
    if page.busy:
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        page.operation_finished.connect(loop.quit)
        timer.start(seconds * 1000)
        loop.exec()
        timer.stop()
        page.operation_finished.disconnect(loop.quit)
    assert not page.busy, "后台任务未在时限内完成"


def test_generate_preview_filter_sort_export_save_reload_delete(page, tmp_path):
    QTest.mouseClick(page.demo_button, Qt.MouseButton.LeftButton)
    wait_idle(page)
    QTest.qWait(20)  # Let the table finish its deferred geometry/scrollbar update.
    assert page.model.rowCount() == 1000
    assert page.table.verticalScrollBar().maximum() > 0
    assert page.table.horizontalScrollBar().maximum() > 0
    assert "模拟数据" in page.source_label.text()
    assert "预览未保存" in page.source_label.text()
    assert page.repository.list_datasets() == []
    page.filter_column.setCurrentText("时间")
    page.filter_edit.setText("2026-01-01 00:00:00")
    QTest.mouseClick(page.filter_button, Qt.MouseButton.LeftButton)
    wait_idle(page)
    assert page.model.rowCount() == 1
    assert "总记录数：1000" in page.count_label.text()
    page.clear_filter()
    wait_idle(page)
    page.model.sort(1, Qt.SortOrder.DescendingOrder)
    wait_idle(page)
    first = float(page.model.index(0, 1).data())
    last = float(page.model.index(999, 1).data())
    assert first >= last
    path = tmp_path / "中文导出.csv"
    page.export_to(path)
    wait_idle(page)
    assert path.exists()
    page.name_edit.setText("测试数据集")
    QTest.mouseClick(page.save_button, Qt.MouseButton.LeftButton)
    wait_idle(page)
    assert not page.has_unsaved_data
    page.refresh_history()
    wait_idle(page)
    assert page.history_combo.count() == 1
    identifier = page.history_combo.currentData()
    page.load_selected()
    wait_idle(page)
    assert page.model.rowCount() == 1000
    assert page.name_edit.text() == "测试数据集"
    assert not page.has_unsaved_data
    page.delete_selected()
    wait_idle(page)
    assert page.repository.list_datasets() == []
    assert page.history_combo.findData(identifier) == -1
    assert page.has_unsaved_data
    assert "历史记录已删除" in page.source_label.text()


def test_bad_import_and_database_failure_preserve_preview(page, tmp_path, monkeypatch):
    path = tmp_path / "正常.csv"
    export_demo(generate_demo(), path)
    page.import_path(path)
    wait_idle(page)
    original = page.dataset
    bad = tmp_path / "非法.csv"
    bad.write_text("时间,电压,电流,功率因数\n不是时间,abc,-1,2", encoding="utf-8")
    page.import_path(bad)
    wait_idle(page)
    assert page.dataset is original
    assert "校验失败" in page.message.toPlainText()
    assert page.save_button.isEnabled()
    def fail(*args):
        raise StorageError("数据库操作失败（测试）")
    monkeypatch.setattr(page.repository, "save", fail)
    page.save()
    wait_idle(page)
    assert page.dataset is original
    assert page.has_unsaved_data
    assert "数据库操作失败" in page.message.toPlainText()
    assert page.save_button.isEnabled()


def test_delete_requires_explicit_confirmation(page, monkeypatch):
    identifier = page.repository.save(generate_demo(), "不能误删")
    page.refresh_history()
    wait_idle(page)
    calls = []
    monkeypatch.setattr(page, "_confirm", lambda *args: calls.append(args) or False)
    page.delete_selected()
    assert len(calls) == 1
    assert calls[0][0] == "删除数据集"
    assert not page.busy
    assert page.repository.load(identifier).name == "不能误删"


def test_background_import_keeps_event_loop_responsive(page, tmp_path):
    large = generate_demo(100000)
    path = tmp_path / "十万条模拟数据.csv"
    export_demo(large, path)
    ticks = []
    timer = QTimer(page)
    timer.setInterval(5)
    timer.timeout.connect(lambda: ticks.append(time.monotonic()))
    timer.start()
    page.import_path(path)
    assert page.busy
    assert not page.import_button.isEnabled()
    wait_idle(page, seconds=30)
    timer.stop()
    assert len(ticks) >= 2
    assert page.model.rowCount() == 100000
    assert page.import_button.isEnabled()


def test_unsaved_preview_replacement_can_be_cancelled(page, monkeypatch):
    page.generate()
    wait_idle(page)
    original = page.dataset
    monkeypatch.setattr(page, "_confirm", lambda *args: False)
    page.generate()
    assert not page.busy
    assert page.dataset is original


def test_history_delete_failure_is_visible_and_preserves_list(page, monkeypatch):
    identifier = page.repository.save(generate_demo(), "已有数据")
    page.refresh_history()
    wait_idle(page)
    def fail(*args):
        raise StorageError("数据库删除失败（测试）")
    monkeypatch.setattr(page.repository, "delete", fail)
    page.delete_selected()
    wait_idle(page)
    assert page.history_combo.currentData() == identifier
    assert "删除失败" in page.message.toPlainText()
    assert len(page.repository.load(identifier).frame) == 1000


def test_main_window_close_protects_worker_and_unsaved_preview(app, tmp_path, monkeypatch):
    from smartpower.ui.main_window import MainWindow
    window = MainWindow()
    page = window.pages["data"]
    page.repository = DatasetRepository(tmp_path / "window.sqlite3")
    window.show()
    page._start(lambda: time.sleep(0.1), lambda _: None, "后台任务测试")
    QTest.mouseClick(window.navigation_buttons["voltage"], Qt.MouseButton.LeftButton)
    assert window.stack.currentWidget() is window.pages["voltage"]
    window.close()
    assert window.isVisible()
    wait_idle(page)
    page.generate()
    wait_idle(page)
    monkeypatch.setattr(page, "_confirm", lambda *args: False)
    window.close()
    assert window.isVisible()
    monkeypatch.setattr(page, "_confirm", lambda *args: True)
    window.close()
    assert not window.isVisible()
    window.deleteLater()
    app.processEvents()


def test_file_picker_import_and_export_actions(page, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog
    source = tmp_path / "选择文件.csv"
    export_demo(generate_demo(20), source)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(source), ""))
    QTest.mouseClick(page.import_button, Qt.MouseButton.LeftButton)
    wait_idle(page)
    assert page.model.rowCount() == 20
    target = tmp_path / "导出选择.csv"
    monkeypatch.setattr(QFileDialog, "exec", lambda self: 1)
    monkeypatch.setattr(QFileDialog, "selectedFiles", lambda self: [str(target)])
    QTest.mouseClick(page.export_button, Qt.MouseButton.LeftButton)
    wait_idle(page)
    assert target.exists()


def test_confirmation_dialog_defaults_to_chinese_cancel(page):
    from PySide6.QtWidgets import QApplication, QMessageBox
    observed = []
    def cancel():
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, QMessageBox)
        observed.append(dialog.defaultButton().text())
        dialog.defaultButton().click()
    QTimer.singleShot(10, cancel)
    accepted = DataManagementPage._confirm(page, "删除数据集", "确认测试", "确认删除")
    assert not accepted
    assert observed == ["取消"]


def test_long_database_path_does_not_expand_minimum_page_width(app, tmp_path, monkeypatch):
    from smartpower.ui.main_window import MainWindow
    monkeypatch.setenv("SMARTPOWER_DB_PATH", str(tmp_path / ("long_ascii_directory_" * 10) / "data.sqlite3"))
    window = MainWindow()
    window.resize(900, 620)
    window.navigate("data")
    window.show()
    app.processEvents()
    page = window.pages["data"]
    try:
        assert page.widget().minimumSizeHint().width() <= page.viewport().width()
    finally:
        window.close()
        window.deleteLater()
        app.processEvents()
