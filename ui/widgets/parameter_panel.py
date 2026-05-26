from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QHeaderView, QAbstractItemView, QLabel,
    QTableView,
)
from PySide6.QtCore import Qt, Signal, QTimer, QAbstractTableModel, QModelIndex, QSortFilterProxyModel

from infrastructure.mavlink.param_client import PARAM_TYPES


class _ParamModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._names: list[str] = []
        self._values: list[tuple[float, int]] = []
        self._on_set: callable = None

    def load(self, params: dict[str, tuple[float, int]]) -> None:
        self.beginResetModel()
        self._names = sorted(params.keys())
        self._values = [params[n] for n in self._names]
        self.endResetModel()

    def clear(self) -> None:
        self.beginResetModel()
        self._names.clear()
        self._values.clear()
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._names)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 3

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        if role == Qt.DisplayRole:
            name = self._names[row]
            value, ptype = self._values[row]
            if col == 0:
                return name
            if col == 1:
                if ptype in (0, 1, 2, 3, 4, 5):
                    return str(int(value))
                return f"{value:.4f}"
            if col == 2:
                return PARAM_TYPES.get(ptype, f"T{ptype}")
        if role == Qt.UserRole and col == 1:
            return (self._names[row], self._values[row][0], self._values[row][1])
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid() or index.column() != 1:
            return False
        try:
            new_val = float(value)
        except ValueError:
            return False
        row = index.row()
        name = self._names[row]
        old_val, ptype = self._values[row]
        if old_val == new_val:
            return False
        self._values[row] = (new_val, ptype)
        self.dataChanged.emit(index, index, [Qt.DisplayRole])
        if self._on_set:
            self._on_set(name, new_val, ptype)
        return True

    def flags(self, index):
        flags = super().flags(index)
        if index.column() == 1:
            flags |= Qt.ItemIsEditable
        return flags

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return ["Name", "Value", "Type"][section]
        return None


class _FilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = ""

    def set_filter(self, text: str) -> None:
        self._text = text.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, row, parent):
        if not self._text:
            return True
        name = self.sourceModel()._names[row]
        return self._text in name.lower()


class ParameterPanel(QWidget):
    set_param_requested = Signal(str, float, int)
    refresh_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("parameter_panel")
        self._params: dict[str, tuple[float, int]] = {}
        self._syncing = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QLabel("Parameters")
        header.setObjectName("card_header")
        layout.addWidget(header)

        top_bar = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search parameters...")
        self._search_input.setObjectName("param_search")
        self._search_input.textChanged.connect(self._on_search)
        top_bar.addWidget(self._search_input)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setObjectName("param_refresh_btn")
        self._refresh_btn.clicked.connect(self.refresh_requested.emit)
        top_bar.addWidget(self._refresh_btn)
        layout.addLayout(top_bar)

        self._status_label = QLabel("0 parameters")
        self._status_label.setObjectName("info_label")
        layout.addWidget(self._status_label)

        self._model = _ParamModel()
        self._model._on_set = self._on_model_set
        self._proxy = _FilterProxy()
        self._proxy.setSourceModel(self._model)

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table)

    def set_params(self, params: dict[str, tuple[float, int]]) -> None:
        self._params = params
        self._model.load(params)
        self._update_status()

    def add_param(self, name: str, value: float, ptype: int) -> None:
        self._params[name] = (value, ptype)
        if self._syncing:
            self._status_label.setText(f"Loading… {len(self._params)}")

    def sync_started(self) -> None:
        self._syncing = True
        self._params.clear()
        self._model.clear()
        self._status_label.setText("Loading…")

    def sync_finished(self) -> None:
        self._syncing = False
        self._model.load(self._params)
        self._update_status()

    def _update_status(self) -> None:
        total = len(self._params)
        self._status_label.setText(f"{total} parameters")

    def _on_search(self, text: str) -> None:
        self._proxy.set_filter(text)

    def _on_model_set(self, name: str, value: float, ptype: int) -> None:
        self._params[name] = (value, ptype)
        self.set_param_requested.emit(name, value, ptype)
