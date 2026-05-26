from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox,
)
from PySide6.QtCore import Signal


CONFIRMATION: dict[str, str] = {
    "Reboot": "Reboot the flight controller?",
    "Reboot to Bootloader": "Reboot to bootloader for firmware update?",
    "Calibrate Gyro": "Start gyro calibration? Keep vehicle level and still.",
    "Calibrate Accel": "Start accelerometer calibration? Follow on-screen prompts.",
    "Calibrate Compass": "Start compass calibration? Rotate vehicle as instructed.",
    "Calibrate Radio": "Start radio calibration? Move all sticks to endpoints.",
}


class ActionsPanel(QWidget):
    action_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(6, 6, 6, 6)
        vbox.setSpacing(8)

        vbox.addWidget(QLabel("Actions"))
        vbox.addWidget(QLabel(""))  # spacer

        vbox.addWidget(_ActionGroupLabel("Reboot"))
        reboot_row = QHBoxLayout()
        reboot_row.setSpacing(4)
        self._reboot_btn = QPushButton("Reboot FCU")
        self._reboot_btn.setObjectName("action_btn_warn")
        self._reboot_btn.clicked.connect(lambda: self._confirm_then_emit("Reboot"))
        reboot_row.addWidget(self._reboot_btn)
        self._bootloader_btn = QPushButton("Bootloader")
        self._bootloader_btn.setObjectName("action_btn_warn")
        self._bootloader_btn.clicked.connect(
            lambda: self._confirm_then_emit("Reboot to Bootloader")
        )
        reboot_row.addWidget(self._bootloader_btn)
        vbox.addLayout(reboot_row)

        vbox.addWidget(_ActionGroupLabel("Calibration"))
        cal_grid = QVBoxLayout()
        cal_grid.setSpacing(3)
        cal_names = ["Calibrate Gyro", "Calibrate Accel", "Calibrate Compass", "Calibrate Radio"]
        self._cal_btns = {}
        row = None
        for i, name in enumerate(cal_names):
            if i % 2 == 0:
                row = QHBoxLayout()
                row.setSpacing(4)
                cal_grid.addLayout(row)
            btn = QPushButton(name.replace("Calibrate ", ""))
            btn.setObjectName("action_btn_cal")
            btn.clicked.connect(lambda checked=False, n=name: self._confirm_then_emit(n))
            self._cal_btns[name] = btn
            row.addWidget(btn)
        vbox.addLayout(cal_grid)

        vbox.addWidget(_ActionGroupLabel("Misc"))
        misc_row = QHBoxLayout()
        misc_row.setSpacing(4)
        self._home_btn = QPushButton("Set Home Here")
        self._home_btn.setObjectName("action_btn_misc")
        self._home_btn.clicked.connect(lambda: self.action_requested.emit("Set Home Here"))
        misc_row.addWidget(self._home_btn)
        vbox.addLayout(misc_row)

        vbox.addStretch()

    def _confirm_then_emit(self, action: str) -> None:
        msg = CONFIRMATION.get(action)
        if msg:
            reply = QMessageBox.question(
                self, action, msg,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        self.action_requested.emit(action)


class _ActionGroupLabel(QLabel):
    def __init__(self, text: str):
        super().__init__(text)
        self.setStyleSheet("""
            font-size: 10px; font-weight: bold; color: #888;
            padding: 4px 0 2px 0;
            border-bottom: 1px solid #333;
        """)
