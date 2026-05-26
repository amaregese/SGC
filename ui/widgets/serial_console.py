from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QLineEdit, QPushButton, QLabel,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QColor, QTextCursor


class SerialConsolePanel(QWidget):
    send_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(4, 4, 4, 4)
        vbox.setSpacing(4)

        self._title = QLabel("Serial Console")
        self._title.setStyleSheet("font-size:13px;font-weight:bold;color:#eee;")
        vbox.addWidget(self._title)

        self._output = QPlainTextEdit()
        self._output.setObjectName("console_output")
        self._output.setReadOnly(True)
        self._output.setFont(QFont("Menlo", 10))
        self._output.setMaximumBlockCount(2000)
        vbox.addWidget(self._output, 1)

        row = QHBoxLayout()
        row.setSpacing(4)
        self._input = QLineEdit()
        self._input.setObjectName("console_input")
        self._input.setPlaceholderText("Enter command...")
        self._input.setFont(QFont("Menlo", 10))
        self._input.returnPressed.connect(self._on_send)
        row.addWidget(self._input, 1)
        self._send_btn = QPushButton("Send")
        self._send_btn.setObjectName("console_send_btn")
        self._send_btn.clicked.connect(self._on_send)
        row.addWidget(self._send_btn)
        vbox.addLayout(row)

    def _on_send(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        self.append_output(f">>> {text}\n", "#4fc3f7")
        self.send_requested.emit(text + "\n")
        self._input.clear()

    def append_output(self, text: str, color: str = "#ccc") -> None:
        self._output.moveCursor(QTextCursor.End)
        self._output.insertHtml(
            f'<span style="color:{color};white-space:pre-wrap;">'
            f'{_escape(text)}</span>'
        )
        scroll = self._output.verticalScrollBar()
        scroll.setValue(scroll.maximum())

    def append_received(self, raw: bytes) -> None:
        try:
            text = raw.decode("utf-8", errors="replace")
        except Exception:
            text = repr(raw)
        self.append_output(text, "#e0e0e0")

    def clear(self) -> None:
        self._output.clear()


def _escape(text: str) -> str:
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            )
