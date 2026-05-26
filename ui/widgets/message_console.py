from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel,
)
from PySide6.QtCore import Qt, Signal, QObject, QTimer
from PySide6.QtGui import QColor, QTextCursor


_SEVERITY_COLORS = {
    0: QColor("#ff4444"),   # EMERGENCY
    1: QColor("#ff4444"),   # ALERT
    2: QColor("#ff4444"),   # CRITICAL
    3: QColor("#ff6666"),   # ERROR
    4: QColor("#ffaa00"),   # WARNING
    5: QColor("#cccccc"),   # NOTICE
    6: QColor("#cccccc"),   # INFO
    7: QColor("#888888"),   # DEBUG
}

SEVERITY_NAMES = {
    0: "EMRG", 1: "ALRT", 2: "CRIT", 3: "ERR",
    4: "WARN", 5: "NOTE", 6: "INFO", 7: "DBUG",
}

_MAX_LINES = 1000


class ConsoleBridge(QObject):
    message_received = Signal(str, str, int)

    def process(self, msg) -> None:
        if msg.get_type() == "STATUS_TEXT":
            self.message_received.emit("FCU", msg.text, msg.severity)


class MessageConsole(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("message_console")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QLabel("Messages")
        header.setObjectName("card_header")
        layout.addWidget(header)

        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setObjectName("console_output")
        self._output.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        layout.addWidget(self._output)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("console_clear_btn")
        clear_btn.clicked.connect(self._output.clear)
        btn_row.addWidget(clear_btn)
        layout.addLayout(btn_row)

    def append_message(self, sender: str, text: str, severity: int = 6) -> None:
        color = _SEVERITY_COLORS.get(severity, QColor("#cccccc"))
        sname = SEVERITY_NAMES.get(severity, "INFO")
        line = f"[{sname}] <{sender}> {text}"

        self._output.moveCursor(QTextCursor.End)
        self._output.setTextColor(color)
        self._output.insertPlainText(line + "\n")

        doc = self._output.document()
        if doc.blockCount() > _MAX_LINES:
            cursor = QTextCursor(doc.begin())
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, doc.blockCount() - _MAX_LINES)
            cursor.removeSelectedText()
            cursor.deleteChar()

        sb = self._output.verticalScrollBar()
        sb.setValue(sb.maximum())
