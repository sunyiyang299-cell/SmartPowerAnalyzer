"""Shared light theme; retain native title bar and window controls."""

LIGHT_THEME = """
QWidget { color: #24334b; font-size: 14px; }
QMainWindow, QWidget#workspace { background: #f4f7fb; }
QFrame#sidebar { background: #ffffff; border-right: 1px solid #e2e8f0; }
QLabel { background: transparent; }
QLabel#brand { font-size: 26px; font-weight: 700; color: #2262cf; }
QLabel#muted { color: #66768d; }
QLabel#pageTitle { font-size: 28px; font-weight: 700; }
QLabel#sectionTitle { font-size: 18px; font-weight: 600; }
QLabel#badge { color: #2262cf; background: #eaf1ff; border-radius: 6px; padding: 6px 10px; }
QFrame#card { background: white; border: 1px solid #e2e8f0; border-radius: 12px; }
QPushButton { background: #ffffff; border: 1px solid #d7e0ee; border-radius: 7px; padding: 10px 16px; }
QPushButton:hover { background: #edf3ff; border-color: #8eafe6; }
QPushButton:pressed { background: #dce9ff; }
QPushButton:focus { border: 2px solid #2262cf; }
QPushButton#navButton { text-align: left; border: 0; padding: 12px 16px; color: #506078; }
QPushButton#navButton:checked { background: #eaf1ff; color: #1d58ba; font-weight: 600; }
QPushButton#navButton:focus { border: 2px solid #2262cf; }
QStatusBar { background: white; color: #66768d; border-top: 1px solid #e2e8f0; }
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
"""
