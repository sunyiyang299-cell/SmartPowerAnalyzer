"""Lazy event table with cheap filtered row indices, without QTableWidget cells."""

from PySide6.QtCore import QAbstractTableModel, Qt


class AnomalyTableModel(QAbstractTableModel):
    HEADERS = ("原始索引（从0起）", "时间", "异常类型", "参数", "采样数值", "用户阈值", "单位", "数据集标识", "数据来源")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.result = None
        self.indices = []

    def set_result(self, result, kind="全部异常"):
        self.beginResetModel()
        self.result = result
        self.indices = ([j for j, e in enumerate(result.events) if kind == "全部异常" or e.kind == kind]
                        if result else [])
        self.endResetModel()

    def rowCount(self, parent=None):
        return 0 if parent and parent.isValid() else len(self.indices)

    def columnCount(self, parent=None):
        return 0 if parent and parent.isValid() else len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section] if orientation == Qt.Orientation.Horizontal else section + 1

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole or self.result is None:
            return None
        e = self.result.events[self.indices[index.row()]]
        return (str(e.row_index), str(e.timestamp).replace("T", " "), e.kind, e.parameter,
                format(e.value, ".12g"), format(e.threshold, ".12g"), e.unit, str(e.dataset_id), e.source)[index.column()]
