from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QFrame, QGroupBox, QGridLayout,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont


_DEFAULT_MAP: list[tuple[int, str]] = [
    (0, "Ch1 Roll"),
    (1, "Ch2 Pitch"),
    (2, "Ch3 Throttle"),
    (3, "Ch4 Yaw"),
    (4, "Ch5"),
    (5, "Ch6"),
]


class JoystickPanel(QWidget):
    rc_override_requested = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state: dict = {
            "connected": False,
            "device_name": "",
            "axes": {},
            "buttons": {},
        }
        self._channel_map = _DEFAULT_MAP[:]
        self._channel_values = [0] * 18
        self._setup_ui()
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._send_override)
        self._timer.start()

    def _setup_ui(self):
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(6, 6, 6, 6)
        vbox.setSpacing(6)

        self._title = QLabel("Joystick")
        self._title.setStyleSheet("font-size:14px;font-weight:bold;color:#eee;")
        vbox.addWidget(self._title)

        self._status = QLabel("No gamepad detected")
        self._status.setStyleSheet("color:#f39c12;font-size:10px;")
        vbox.addWidget(self._status)

        self._axis_group = QGroupBox("Axes")
        self._axis_group.setStyleSheet("""
            QGroupBox{border:1px solid #333;border-radius:4px;margin-top:6px;
                       padding-top:14px;font-size:10px;color:#bbb;}
            QGroupBox::title{subcontrol-origin:margin;left:8px;padding:0 4px;}
        """)
        ax_grid = QGridLayout(self._axis_group)
        ax_grid.setSpacing(4)
        self._axis_bars: dict[int, QProgressBar] = {}
        for idx in range(6):
            lbl = QLabel(f"Axis {idx}")
            lbl.setFixedWidth(40)
            lbl.setStyleSheet("color:#888;font-size:9px;")
            ax_grid.addWidget(lbl, idx, 0)
            bar = QProgressBar()
            bar.setObjectName("joystick_bar")
            bar.setRange(0, 2000)
            bar.setValue(1000)
            bar.setTextVisible(True)
            bar.setFormat(f"{_DEFAULT_MAP[idx][1]}")
            bar.setFixedHeight(14)
            self._axis_bars[idx] = bar
            ax_grid.addWidget(bar, idx, 1)
        vbox.addWidget(self._axis_group)

        btn_group = QGroupBox("Buttons")
        btn_group.setStyleSheet("""
            QGroupBox{border:1px solid #333;border-radius:4px;margin-top:6px;
                       padding-top:14px;font-size:10px;color:#bbb;}
            QGroupBox::title{subcontrol-origin:margin;left:8px;padding:0 4px;}
        """)
        bg = QHBoxLayout(btn_group)
        bg.setSpacing(3)
        self._btn_labels: dict[int, QLabel] = {}
        for i in range(10):
            lbl = QLabel(f"B{i}")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedSize(28, 24)
            lbl.setStyleSheet("""
                background-color:#2a2a4a;color:#666;border-radius:4px;
                font-size:9px;font-weight:bold;
            """)
            self._btn_labels[i] = lbl
            bg.addWidget(lbl)
        vbox.addWidget(btn_group)

        vbox.addStretch()

    def update_state(self, state: dict) -> None:
        self._state = state
        connected = state.get("connected", False)
        if connected:
            name = state.get("device_name", "Gamepad")
            self._status.setText(f"Connected: {name}")
            self._status.setStyleSheet("color:#4fc3f7;font-size:10px;")
        else:
            self._status.setText("No gamepad detected")
            self._status.setStyleSheet("color:#f39c12;font-size:10px;")

        axes = state.get("axes", {})
        for idx, bar in self._axis_bars.items():
            if idx in axes:
                val = axes[idx]
                pwm = int(1500 + val * 400)
                pwm = max(1000, min(2000, pwm))
                bar.setValue(pwm)
                self._channel_values[idx] = pwm
            else:
                bar.setValue(1000)
                self._channel_values[idx] = 1000

        buttons = state.get("buttons", {})
        for idx, lbl in self._btn_labels.items():
            pressed = buttons.get(idx, False)
            if pressed:
                lbl.setStyleSheet("""
                    background-color:#4fc3f7;color:#1a1a2e;border-radius:4px;
                    font-size:9px;font-weight:bold;
                """)
            else:
                lbl.setStyleSheet("""
                    background-color:#2a2a4a;color:#666;border-radius:4px;
                    font-size:9px;font-weight:bold;
                """)

    def _send_override(self) -> None:
        if not self._state.get("connected", False):
            return
        if any(v != 0 for v in self._channel_values):
            self.rc_override_requested.emit(self._channel_values[:8])
