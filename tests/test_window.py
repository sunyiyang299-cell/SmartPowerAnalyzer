"""Offscreen by default; set QT_QPA_PLATFORM=windows for native smoke tests."""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLabel

from smartpower.application import create_application
from smartpower.config import APP_NAME
from smartpower.ui.main_window import MainWindow
from smartpower.ui.pages.registry import PAGE_SPECS


class WindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_application([])

    def setUp(self):
        self.window = MainWindow()
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def test_initial_page_and_all_expected_modules(self):
        self.assertEqual(self.window.windowTitle(), APP_NAME)
        self.assertEqual([spec.title for spec in PAGE_SPECS], [
            "首页", "数据管理", "电压分析", "电流分析", "功率分析", "异常检测", "分析报告", "系统设置",
        ])
        self.assertEqual(self.window.stack.count(), 8)
        self.assertEqual(self.window.stack.currentWidget(), self.window.pages["home"])
        self.assertTrue(self.window.navigation_buttons["home"].isChecked())

    def test_every_navigation_button_and_exclusive_state(self):
        for spec in (*PAGE_SPECS, *reversed(PAGE_SPECS)):
            with self.subTest(page=spec.key):
                QTest.mouseClick(self.window.navigation_buttons[spec.key], Qt.MouseButton.LeftButton)
                self.app.processEvents()
                self.assertIs(self.window.stack.currentWidget(), self.window.pages[spec.key])
                self.assertEqual(self.window.pages[spec.key].title_label.text(), spec.title)
                self.assertIn(spec.title, self.window.statusBar().currentMessage())
                self.assertEqual(sum(b.isChecked() for b in self.window.navigation_buttons.values()), 1)
                self.assertTrue(self.window.navigation_buttons[spec.key].isChecked())

    def test_home_shortcuts_and_keyboard_navigation(self):
        home = self.window.pages["home"]
        QTest.mouseClick(home.data_button, Qt.MouseButton.LeftButton)
        self.assertIs(self.window.stack.currentWidget(), self.window.pages["data"])
        self.window.navigate("home")
        QTest.mouseClick(home.settings_button, Qt.MouseButton.LeftButton)
        self.assertIs(self.window.stack.currentWidget(), self.window.pages["settings"])
        button = self.window.navigation_buttons["voltage"]
        button.setFocus()
        QTest.keyClick(button, Qt.Key.Key_Space)
        self.assertIs(self.window.stack.currentWidget(), self.window.pages["voltage"])

    def test_programmatic_navigation_sync_and_invalid_route(self):
        self.window.stack.setCurrentIndex(4)
        self.assertTrue(self.window.navigation_buttons["power"].isChecked())
        with self.assertRaises(KeyError):
            self.window.navigate("missing")
        self.assertEqual(self.window.stack.currentIndex(), 4)

    def test_feature_pages_explicitly_describe_unimplemented_state(self):
        from smartpower.ui.pages.data_management import DataManagementPage
        self.assertIsInstance(self.window.pages["data"], DataManagementPage)
        self.assertTrue(self.window.pages["data"].import_button.isEnabled())
        from smartpower.ui.pages.analysis import AnalysisPage
        for key in ("voltage", "current", "power"):
            with self.subTest(page=key):
                page = self.window.pages[key]
                self.assertIsInstance(page, AnalysisPage)
                self.assertTrue(page.analyze_button.isEnabled())
                self.assertIsNone(page.current_result)
                self.assertEqual(page.summary.rowCount(), 0)
        from smartpower.ui.pages.anomaly import AnomalyPage
        anomaly = self.window.pages["anomalies"]
        self.assertIsInstance(anomaly, AnomalyPage)
        self.assertFalse(anomaly.enabled_check.isChecked())
        self.assertEqual(anomaly.event_model.rowCount(), 0)
        self.assertTrue(anomaly.analyze_button.isEnabled())
        from smartpower.ui.pages.reports import ReportsPage
        reports = self.window.pages["reports"]
        self.assertIsInstance(reports, ReportsPage)
        self.assertIsNone(reports.current_snapshot)
        self.assertFalse(reports.detection_enabled.isChecked())
        self.assertTrue(reports.pdf_button.isEnabled())
        self.assertTrue(reports.excel_button.isEnabled())

    def test_resize_and_native_window_state_support(self):
        flags = self.window.windowFlags()
        self.assertTrue(flags & Qt.WindowType.WindowMinimizeButtonHint)
        self.assertTrue(flags & Qt.WindowType.WindowMaximizeButtonHint)
        self.window.resize(1000, 700)
        self.app.processEvents()
        self.assertEqual(self.window.size().width(), 1000)
        self.assertEqual(self.window.size().height(), 700)
        self.window.showMaximized()
        QTest.qWait(100)
        self.assertTrue(self.window.isMaximized())
        self.window.showMinimized()
        QTest.qWait(100)
        self.assertTrue(self.window.isMinimized())
        self.window.showNormal()
        QTest.qWait(100)
        self.assertFalse(self.window.isMaximized())
        self.assertFalse(self.window.isMinimized())

    def test_pages_fit_minimum_window_with_scrollable_content(self):
        self.window.resize(900, 620)
        self.app.processEvents()
        for spec in PAGE_SPECS:
            self.window.navigate(spec.key)
            self.app.processEvents()
            page = self.window.pages[spec.key]
            self.assertLessEqual(page.widget().minimumSizeHint().width(), page.viewport().width(), spec.key)
