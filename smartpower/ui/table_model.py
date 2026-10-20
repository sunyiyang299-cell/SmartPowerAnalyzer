"""Read-only lazy cell access; no per-cell widget allocation."""

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal

from smartpower.data.validation import REQUIRED_COLUMNS


class SampleTableModel(QAbstractTableModel):
    sort_requested = Signal(int, bool)
    HEADERS = ("时间", "电压（V）", "电流（A）", "功率因数", "数据来源")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dataset = None
        self.rows = ()
        self._resetting = False

    def set_view(self, dataset, rows):
        self._resetting = True
        self.beginResetModel()
        self.dataset = dataset
        self.rows = rows
        self.endResetModel()
        self._resetting = False

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if (not index.isValid() or self.dataset is None or
                not 0 <= index.row() < len(self.rows) or not 0 <= index.column() < 5):
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == len(REQUIRED_COLUMNS):
                return self.dataset.source
            value = self.dataset.frame.iat[int(self.rows[index.row()]), index.column()]
            return str(value) if index.column() == 0 else format(float(value), ".12g")
        if role == Qt.ItemDataRole.TextAlignmentRole and index.column() in (1, 2, 3):
            return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal and 0 <= section < 5:
                return self.HEADERS[section]
            if orientation == Qt.Orientation.Vertical and 0 <= section < len(self.rows):
                return str(int(self.rows[section]) + 1)
        return None

    def sort(self, column, order=Qt.SortOrder.AscendingOrder):
        if not self._resetting:
            self.sort_requested.emit(column, order == Qt.SortOrder.AscendingOrder)
