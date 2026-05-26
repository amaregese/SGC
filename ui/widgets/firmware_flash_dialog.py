from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFileDialog, QTextEdit, QProgressBar,
    QMessageBox,
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QTextCursor

from infrastructure.firmware.flasher import FirmwareFlasher, FirmwareInfo


class _FlashWorker(QObject):
    finished = Signal(bool, str)

    def __init__(self, port: str, path: str, flasher: FirmwareFlasher):
        super().__init__()
        self._port = port
        self._path = path
        self._flasher = flasher

    def run(self) -> None:
        self._flasher.flash(self._port, self._path)


class FirmwareFlashDialog(QDialog):
    def __init__(self, serial_port: str, parent=None):
        super().__init__(parent)
        self._serial_port = serial_port
        self._flasher = FirmwareFlasher()
        self._worker_thread: QThread | None = None
        self._firmware_info: FirmwareInfo | None = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Firmware Installer")
        self.setMinimumWidth(560)
        self.setMinimumHeight(480)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        instructions = QLabel(
            "1. Put the FCU into bootloader mode:\n"
            "   \u2022  Hold the BOOT/DFU button while powering on, OR\n"
            "   \u2022  Send reboot-to-bootloader command (automatic if connected)\n"
            "2. Select an .apj firmware file below\n"
            "3. Click 'Flash Firmware'"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #aaa; padding: 6px; border: 1px solid #333; border-radius: 4px;")
        layout.addWidget(instructions)

        file_row = QHBoxLayout()
        file_row.addWidget(QLabel("Firmware file:"))
        self._file_path = QLineEdit()
        self._file_path.setPlaceholderText("Select an .apj firmware file...")
        self._file_path.setObjectName("fw_file_path")
        file_row.addWidget(self._file_path)
        self._browse_btn = QPushButton("Browse")
        self._browse_btn.setObjectName("fw_browse_btn")
        self._browse_btn.clicked.connect(self._on_browse)
        file_row.addWidget(self._browse_btn)
        layout.addLayout(file_row)

        self._info_label = QLabel("Select a firmware file to see details")
        self._info_label.setObjectName("fw_info")
        self._info_label.setWordWrap(True)
        self._info_label.setFixedHeight(60)
        layout.addWidget(self._info_label)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setObjectName("fw_log")
        layout.addWidget(self._log)

        self._progress = QProgressBar()
        self._progress.setObjectName("fw_progress")
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        layout.addWidget(self._progress)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._flash_btn = QPushButton("Flash Firmware")
        self._flash_btn.setObjectName("fw_flash_btn")
        self._flash_btn.setEnabled(False)
        self._flash_btn.clicked.connect(self._on_flash)
        btn_row.addWidget(self._flash_btn)
        self._close_btn = QPushButton("Close")
        self._close_btn.setObjectName("fw_close_btn")
        self._close_btn.clicked.connect(self.close)
        btn_row.addWidget(self._close_btn)
        layout.addLayout(btn_row)

        self._flasher.log_message.connect(self._on_log)
        self._flasher.progress.connect(self._progress.setValue)
        self._flasher.finished.connect(self._on_flash_finished)

    def _on_browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Firmware", "",
            "Firmware files (*.apj *.px4);;All files (*)",
        )
        if not path:
            return
        self._file_path.setText(path)
        try:
            self._firmware_info = FirmwareInfo.from_file(path)
            if not self._firmware_info.is_valid:
                self._info_label.setText("No firmware data found in file")
                self._flash_btn.setEnabled(False)
                return
            info = self._firmware_info
            text = (
                f"Vehicle: {info.vehicle}\n"
                f"Version: {info.version}\n"
                f"Platform: {info.platform}\n"
                f"Size: {info.size_kb:.0f} KB"
            )
            self._info_label.setText(text)
            self._flash_btn.setEnabled(True)
            self._log.clear()
            self._progress.setValue(0)
        except Exception as e:
            self._info_label.setText(f"Error reading file: {e}")
            self._flash_btn.setEnabled(False)

    def _on_flash(self) -> None:
        if not self._firmware_info or not self._serial_port:
            return
        self._flash_btn.setEnabled(False)
        self._browse_btn.setEnabled(False)
        self._close_btn.setEnabled(False)
        self._worker_thread = QThread()
        self._worker = _FlashWorker(
            self._serial_port, self._file_path.text(), self._flasher
        )
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker_thread.finished.connect(self._worker_thread.deleteLater)
        self._worker_thread.start()

    def _on_log(self, msg: str) -> None:
        self._log.append(msg)
        cursor = self._log.textCursor()
        cursor.movePosition(QTextCursor.End)
        self._log.setTextCursor(cursor)

    def _on_flash_finished(self, success: bool, msg: str) -> None:
        self._flash_btn.setEnabled(True)
        self._browse_btn.setEnabled(True)
        self._close_btn.setEnabled(True)
        self._on_log(f"\n{'SUCCESS' if success else 'FAILED'}: {msg}")
        if success:
            QMessageBox.information(self, "Firmware", msg)
        else:
            QMessageBox.critical(self, "Firmware Error", msg)
