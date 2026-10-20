import importlib
import unittest

from smartpower.config import APP_NAME, APP_VERSION


class StructureTests(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(APP_NAME, "智电析电力系统运行数据分析与可视化软件 V1.0")
        self.assertEqual(APP_VERSION, "1.0.0")

    def test_entry_import_does_not_start_application(self):
        module = importlib.import_module("main")
        self.assertTrue(callable(module.main))

    def test_declared_technology_imports(self):
        for name in ("PySide6", "pandas", "numpy", "pyqtgraph", "sqlite3"):
            with self.subTest(name=name):
                self.assertIsNotNone(importlib.import_module(name))
