"""Lazy display of calculated power sequences, without per-row widgets."""

import numpy as np
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class PowerSeriesModel(QAbstractTableModel):
    HEADERS = ("时间", "有功功率 P（W）", "视在功率 S（VA）", "无功功率绝对值 |Q|（var）")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.result = None

    def set_result(self, result):
        self.beginResetModel()
        self.result = result
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() or self.result is None else self.result.count

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else 4

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if (not index.isValid() or self.result is None or
                not 0 <= index.row() < self.result.count or not 0 <= index.column() < 4):
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return np.datetime_as_string(self.result.times[index.row()], unit="ns").replace("T", " ").rstrip("0").rstrip(".")
            series = (self.result.power.active, self.result.power.apparent, self.result.power.reactive_abs)
            return format(float(series[index.column() - 1][index.row()]), ".12g")
        if role == Qt.ItemDataRole.TextAlignmentRole and index.column() > 0:
            return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal and 0 <= section < 4:
                return self.HEADERS[section]
            if orientation == Qt.Orientation.Vertical:
                return str(section + 1)
        return None
