from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QInputDialog, QLineEdit,
)
from PySide6.QtCore import Qt, Signal

from domain.models.mission import Waypoint, COMMAND_NAMES, FRAME_NAMES


_HEADERS = ["Seq", "Command", "Lat", "Lon", "Alt", "Frame", "Params"]


class MissionPanel(QWidget):
    set_param_requested = Signal(str, float, int)
    download_requested = Signal()
    upload_requested = Signal(object)
    clear_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("mission_panel")
        self._waypoints: list[Waypoint] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QLabel("Mission")
        header.setObjectName("card_header")
        layout.addWidget(header)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)

        self._download_btn = QPushButton("Download")
        self._download_btn.setObjectName("mission_btn")
        self._download_btn.clicked.connect(self._on_download)
        btn_row.addWidget(self._download_btn)

        self._upload_btn = QPushButton("Upload")
        self._upload_btn.setObjectName("mission_btn")
        self._upload_btn.clicked.connect(self._on_upload)
        btn_row.addWidget(self._upload_btn)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setObjectName("mission_btn")
        self._clear_btn.clicked.connect(self._on_clear)
        btn_row.addWidget(self._clear_btn)

        self._add_btn = QPushButton("Add")
        self._add_btn.setObjectName("mission_btn")
        self._add_btn.clicked.connect(self._on_add)
        btn_row.addWidget(self._add_btn)

        self._del_btn = QPushButton("Delete")
        self._del_btn.setObjectName("mission_btn")
        self._del_btn.clicked.connect(self._on_delete)
        btn_row.addWidget(self._del_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._status_label = QLabel("No mission loaded")
        self._status_label.setObjectName("info_label")
        layout.addWidget(self._status_label)

        self._table = QTableWidget()
        self._table.setColumnCount(len(_HEADERS))
        self._table.setHorizontalHeaderLabels(_HEADERS)
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table)

    def set_waypoints(self, waypoints: list[Waypoint]) -> None:
        self._waypoints = list(waypoints)
        self._rebuild_table()
        self._status_label.setText(f"{len(waypoints)} waypoints")

    def set_status(self, text: str) -> None:
        self._status_label.setText(text)

    def _rebuild_table(self):
        self._table.setRowCount(len(self._waypoints))
        for row, wp in enumerate(self._waypoints):
            self._table.setItem(row, 0, QTableWidgetItem(str(wp.seq)))
            self._table.setItem(row, 1, QTableWidgetItem(wp.command_name))
            self._table.setItem(row, 2, QTableWidgetItem(f"{wp.lat:.6f}"))
            self._table.setItem(row, 3, QTableWidgetItem(f"{wp.lon:.6f}"))
            self._table.setItem(row, 4, QTableWidgetItem(f"{wp.alt:.1f}"))
            self._table.setItem(row, 5, QTableWidgetItem(wp.frame_name))
            params = f"p1={wp.param1}" if any([wp.param1, wp.param2, wp.param3, wp.param4]) else ""
            self._table.setItem(row, 6, QTableWidgetItem(params))

    def _on_download(self):
        self.download_requested.emit()

    def _on_upload(self):
        if not self._waypoints:
            return
        reply = QMessageBox.question(
            self, "Upload Mission",
            f"Upload {len(self._waypoints)} waypoints to FCU?\n"
            "This will overwrite the current mission.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.upload_requested.emit(self._waypoints)

    def _on_clear(self):
        if not self._waypoints:
            return
        reply = QMessageBox.question(
            self, "Clear Mission",
            "Clear all waypoints from FCU?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.clear_requested.emit()

    def _on_add(self):
        wp = Waypoint(seq=len(self._waypoints))
        self._waypoints.append(wp)
        self._rebuild_table()
        self._status_label.setText(f"{len(self._waypoints)} waypoints")

    def _on_delete(self):
        row = self._table.currentRow()
        if row < 0 or row >= len(self._waypoints):
            return
        del self._waypoints[row]
        for i, wp in enumerate(self._waypoints):
            wp.seq = i
        self._rebuild_table()
        self._status_label.setText(f"{len(self._waypoints)} waypoints")
