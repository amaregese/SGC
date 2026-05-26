from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QSlider, QPushButton, QGroupBox, QFrame,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from ui.widgets.tuning_graph import TuningGraph


_TUNING_PRESETS: dict[str, dict[str, list[tuple[str, str, float, float, float]]]] = {
    "Quadrotor": {
        "Rate Roll": [
            ("RATE_ROLL_P", "Roll P", 0.01, 0.5, 0.001),
            ("RATE_ROLL_I", "Roll I", 0.01, 0.5, 0.001),
            ("RATE_ROLL_D", "Roll D", 0.0, 0.02, 0.0001),
        ],
        "Rate Pitch": [
            ("RATE_PITCH_P", "Pitch P", 0.01, 0.5, 0.001),
            ("RATE_PITCH_I", "Pitch I", 0.01, 0.5, 0.001),
            ("RATE_PITCH_D", "Pitch D", 0.0, 0.02, 0.0001),
        ],
        "Rate Yaw": [
            ("RATE_YAW_P", "Yaw P", 0.01, 0.5, 0.001),
            ("RATE_YAW_I", "Yaw I", 0.01, 0.5, 0.001),
            ("RATE_YAW_D", "Yaw D", 0.0, 0.02, 0.0001),
        ],
        "Stabilize": [
            ("STB_RLL_P", "Roll P", 1.0, 8.0, 0.1),
            ("STB_PIT_P", "Pitch P", 1.0, 8.0, 0.1),
            ("STB_YAW_P", "Yaw P", 1.0, 8.0, 0.1),
        ],
        "Altitude Hold": [
            ("ALT_HOLD_P",  "Alt P", 0.5, 5.0, 0.1),
            ("ALT_HOLD_I",  "Alt I", 0.1, 2.0, 0.01),
            ("ALT_HOLD_D",  "Alt D", 0.0, 1.0, 0.01),
        ],
        "Loiter / Position": [
            ("LOIT_P",  "Loiter P", 0.5, 5.0, 0.1),
            ("LOIT_I",  "Loiter I", 0.01, 1.0, 0.01),
            ("LOIT_D",  "Loiter D", 0.0, 1.0, 0.01),
            ("POS_XY_P", "Pos XY P", 0.5, 5.0, 0.1),
            ("POS_Z_P",  "Pos Z P", 0.5, 5.0, 0.1),
        ],
        "Throttle": [
            ("THR_ACCEL_P", "Accel P", 0.1, 2.0, 0.01),
            ("THR_ACCEL_I", "Accel I", 0.01, 0.5, 0.001),
            ("THR_ACCEL_D", "Accel D", 0.0, 0.5, 0.001),
        ],
    },
    "Fixed Wing": {
        "Rate Roll": [
            ("RLL_RATE_P",  "Rate P", 0.01, 0.5, 0.001),
            ("RLL_RATE_I",  "Rate I", 0.01, 0.5, 0.001),
            ("RLL_RATE_D",  "Rate D", 0.0, 0.02, 0.0001),
        ],
        "Rate Pitch": [
            ("PTCH_RATE_P", "Rate P", 0.01, 0.5, 0.001),
            ("PTCH_RATE_I", "Rate I", 0.01, 0.5, 0.001),
            ("PTCH_RATE_D", "Rate D", 0.0, 0.02, 0.0001),
        ],
        "Stabilize": [
            ("ROLL_LIM",  "Roll Limit", 10.0, 80.0, 1.0),
            ("PITCH_LIM", "Pitch Limit", 10.0, 45.0, 1.0),
        ],
        "Navigation": [
            ("NAV_LAT_P",  "Lat P", 0.5, 5.0, 0.1),
            ("NAV_LON_P",  "Lon P", 0.5, 5.0, 0.1),
        ],
        "Throttle": [
            ("THR_MIN",  "Min %", 0, 40, 1),
            ("THR_MAX",  "Max %", 50, 100, 1),
            ("THR_SLEWRATE", "Slew Rate", 10, 100, 1),
        ],
    },
    "Antenna Tracker": {
        "Pan Servo (S9)": [
            ("SERVO9_FUNCTION",  "Function", 0, 4, 1),
            ("SERVO9_MIN",  "PWM Min", 800, 2200, 1),
            ("SERVO9_MAX",  "PWM Max", 800, 2200, 1),
            ("SERVO9_TRIM", "Trim", 800, 2200, 1),
            ("SERVO9_REVERSED", "Reversed", 0, 1, 1),
        ],
        "Tilt Servo (S10)": [
            ("SERVO10_FUNCTION",  "Function", 0, 4, 1),
            ("SERVO10_MIN",  "PWM Min", 800, 2200, 1),
            ("SERVO10_MAX",  "PWM Max", 800, 2200, 1),
            ("SERVO10_TRIM", "Trim", 800, 2200, 1),
            ("SERVO10_REVERSED", "Reversed", 0, 1, 1),
        ],
        "RC Input": [
            ("RC1_MIN",  "Ch1 Min", 800, 2200, 1),
            ("RC1_MAX",  "Ch1 Max", 800, 2200, 1),
            ("RC1_TRIM", "Ch1 Trim", 800, 2200, 1),
            ("RC1_REV",  "Ch1 Rev", -1, 1, 1),
            ("RC2_MIN",  "Ch2 Min", 800, 2200, 1),
            ("RC2_MAX",  "Ch2 Max", 800, 2200, 1),
            ("RC2_TRIM", "Ch2 Trim", 800, 2200, 1),
            ("RC2_REV",  "Ch2 Rev", -1, 1, 1),
        ],
    },
}


_GENERIC_PARAMS: dict[str, list[tuple[str, str, float, float, float]]] = {
    "General": [
        ("SERVO1_MIN",  "Servo1 Min", 800, 2200, 1),
        ("SERVO1_MAX",  "Servo1 Max", 800, 2200, 1),
        ("SERVO1_TRIM", "Servo1 Trim", 800, 2200, 1),
        ("SERVO2_MIN",  "Servo2 Min", 800, 2200, 1),
        ("SERVO2_MAX",  "Servo2 Max", 800, 2200, 1),
        ("SERVO2_TRIM", "Servo2 Trim", 800, 2200, 1),
    ],
}

_SERVO_CHANNELS = [("SERVO9 (Pan)", 9), ("SERVO10 (Tilt)", 10)]

_MAV_TYPE_VEH = {
    0: "Generic", 1: "Fixed Wing", 2: "Quadrotor",
    3: "Coaxial", 4: "Helicopter", 5: "Hexarotor",
    6: "Antenna Tracker", 7: "Octarotor", 8: "Tricopter",
    9: "VTOL", 10: "Ground Rover", 11: "Surface Boat",
    12: "Submarine",
}

_VEH_NAME_TO_MAV_TYPE = {v: k for k, v in _MAV_TYPE_VEH.items()}


def _preset_for_type(vehicle_type_str: str) -> dict:
    if vehicle_type_str in _TUNING_PRESETS:
        return _TUNING_PRESETS[vehicle_type_str]
    for key in _TUNING_PRESETS:
        if vehicle_type_str.lower() in key.lower():
            return _TUNING_PRESETS[key]
    return _GENERIC_PARAMS


class _ParamSlider(QWidget):
    value_changed = Signal(str, float, int)

    def __init__(self, param_name: str, display_name: str,
                 min_val: float, max_val: float, step: float, parent=None):
        super().__init__(parent)
        self._param_name = param_name
        self._min = min_val
        self._max = max_val
        self._step = step
        self._current_value = min_val
        self._param_type = 2

        self.setFixedHeight(36)

        row = QHBoxLayout(self)
        row.setContentsMargins(4, 0, 4, 0)
        row.setSpacing(6)

        name_label = QLabel(display_name)
        name_label.setFixedWidth(70)
        name_font = QFont("sans-serif", 9)
        name_label.setFont(name_font)
        row.addWidget(name_label)

        self._value_label = QLabel(f"{min_val:.4f}")
        self._value_label.setFixedWidth(72)
        self._value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        val_font = QFont("monospace", 9)
        self._value_label.setFont(val_font)
        self._value_label.setStyleSheet("color: #3498db;")
        row.addWidget(self._value_label)

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(0, int((max_val - min_val) / step))
        self._slider.setValue(0)
        self._slider.setObjectName("tuning_slider")
        row.addWidget(self._slider, 1)

        min_lbl = QLabel(f"{min_val:.2f}")
        min_lbl.setStyleSheet("color: #666; font-size: 9px;")
        min_lbl.setFixedWidth(36)
        row.addWidget(min_lbl)

        max_lbl = QLabel(f"{max_val:.2f}")
        max_lbl.setStyleSheet("color: #666; font-size: 9px;")
        max_lbl.setFixedWidth(36)
        row.addWidget(max_lbl)

        self._slider.valueChanged.connect(self._on_slider)
        self._slider.sliderReleased.connect(self._on_release)

    def _slider_to_value(self, slider_val: int) -> float:
        return round(self._min + slider_val * self._step, 6)

    def _value_to_slider(self, value: float) -> int:
        return int(round((value - self._min) / self._step))

    def _on_slider(self, pos: int) -> None:
        val = self._slider_to_value(pos)
        self._value_label.setText(f"{val:.4f}")

    def _on_release(self) -> None:
        val = self._slider_to_value(self._slider.value())
        self._current_value = val
        self.value_changed.emit(self._param_name, val, self._param_type)

    def set_value(self, value: float) -> None:
        self._current_value = value
        self._slider.blockSignals(True)
        self._slider.setValue(self._value_to_slider(value))
        self._slider.blockSignals(False)
        self._value_label.setText(f"{value:.4f}")

    @property
    def param_name(self) -> str:
        return self._param_name

    @property
    def current_value(self) -> float:
        return self._current_value


class _ServoOutputSlider(QWidget):
    servo_output_requested = Signal(int, int)

    def __init__(self, label: str, channel: int, parent=None):
        super().__init__(parent)
        self._channel = channel

        self.setFixedHeight(36)

        row = QHBoxLayout(self)
        row.setContentsMargins(4, 0, 4, 0)
        row.setSpacing(6)

        name_label = QLabel(label)
        name_label.setFixedWidth(70)
        name_font = QFont("sans-serif", 9)
        name_label.setFont(name_font)
        row.addWidget(name_label)

        self._value_label = QLabel("1500")
        self._value_label.setFixedWidth(52)
        self._value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        val_font = QFont("monospace", 9)
        self._value_label.setFont(val_font)
        self._value_label.setStyleSheet("color: #e67e22;")
        row.addWidget(self._value_label)

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(800, 2200)
        self._slider.setValue(1500)
        self._slider.setObjectName("tuning_slider")
        row.addWidget(self._slider, 1)

        min_lbl = QLabel("800")
        min_lbl.setStyleSheet("color: #666; font-size: 9px;")
        min_lbl.setFixedWidth(28)
        row.addWidget(min_lbl)

        max_lbl = QLabel("2200")
        max_lbl.setStyleSheet("color: #666; font-size: 9px;")
        max_lbl.setFixedWidth(28)
        row.addWidget(max_lbl)

        self._slider.valueChanged.connect(self._on_move)
        self._slider.sliderReleased.connect(self._on_release)

    def _on_move(self, pwm: int) -> None:
        self._value_label.setText(str(pwm))

    def _on_release(self) -> None:
        pwm = self._slider.value()
        self.servo_output_requested.emit(self._channel, pwm)

    def set_pwm(self, pwm: int) -> None:
        self._slider.blockSignals(True)
        self._slider.setValue(pwm)
        self._slider.blockSignals(False)
        self._value_label.setText(str(pwm))


class TuningPanel(QWidget):
    param_changed = Signal(str, float, int)
    request_refresh = Signal()
    servo_output_requested = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sliders: dict[str, _ParamSlider] = {}
        self._servo_sliders: list[_ServoOutputSlider] = []
        self._preset = _GENERIC_PARAMS
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QLabel("Basic Tuning")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #eee; padding: 4px 0;")
        layout.addWidget(header)

        self._vehicle_label = QLabel("Vehicle: —")
        self._vehicle_label.setStyleSheet("color: #999; font-size: 10px;")
        layout.addWidget(self._vehicle_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        self._scroll_content = QWidget()
        self._scroll_content.setStyleSheet("background: transparent;")
        self._groups_layout = QVBoxLayout(self._scroll_content)
        self._groups_layout.setContentsMargins(0, 0, 0, 0)
        self._groups_layout.setSpacing(4)
        self._rebuild()
        scroll.setWidget(self._scroll_content)
        layout.addWidget(scroll, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        self._refresh_btn = QPushButton("Refresh from FCU")
        self._refresh_btn.setObjectName("tuning_refresh_btn")
        self._refresh_btn.clicked.connect(self.request_refresh.emit)
        btn_row.addWidget(self._refresh_btn)

        self._write_btn = QPushButton("Write All")
        self._write_btn.setObjectName("tuning_write_btn")
        self._write_btn.clicked.connect(self._on_write_all)
        btn_row.addWidget(self._write_btn)
        layout.addLayout(btn_row)

        self._graph = TuningGraph()
        layout.addWidget(self._graph)

    def set_preset(self, vehicle_type_str: str) -> None:
        self._preset = _preset_for_type(vehicle_type_str)
        self._rebuild()
        self._vehicle_label.setText(f"Vehicle: {vehicle_type_str}")

    def _rebuild(self) -> None:
        self._sliders.clear()
        self._servo_sliders.clear()
        while self._groups_layout.count():
            item = self._groups_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for group_name, params in self._preset.items():
            box = QGroupBox(group_name)
            box.setObjectName("tuning_group")
            box.setStyleSheet("""
                QGroupBox#tuning_group {
                    border: 1px solid #333;
                    border-radius: 4px;
                    margin-top: 6px;
                    padding-top: 14px;
                    font-size: 10px;
                    color: #bbb;
                }
                QGroupBox#tuning_group::title {
                    subcontrol-origin: margin;
                    left: 8px;
                    padding: 0 4px;
                }
            """)
            glayout = QVBoxLayout(box)
            glayout.setContentsMargins(4, 0, 4, 4)
            glayout.setSpacing(0)
            for pname, display, pmin, pmax, pstep in params:
                slider = _ParamSlider(pname, display, pmin, pmax, pstep)
                slider.value_changed.connect(self._on_param_changed)
                self._sliders[pname] = slider
                glayout.addWidget(slider)
            self._groups_layout.addWidget(box)

        servo_box = QGroupBox("Servo Output (direct PWM)")
        servo_box.setObjectName("tuning_group")
        servo_box.setStyleSheet("""
            QGroupBox#tuning_group {
                border: 1px solid #f39c12;
                border-radius: 4px;
                margin-top: 6px;
                padding-top: 14px;
                font-size: 10px;
                color: #f39c12;
            }
            QGroupBox#tuning_group::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)
        sv_layout = QVBoxLayout(servo_box)
        sv_layout.setContentsMargins(4, 0, 4, 4)
        sv_layout.setSpacing(0)
        for label, ch in _SERVO_CHANNELS:
            s = _ServoOutputSlider(label, ch)
            s.servo_output_requested.connect(self.servo_output_requested.emit)
            self._servo_sliders.append(s)
            sv_layout.addWidget(s)
        self._groups_layout.addWidget(servo_box)

        self._groups_layout.addStretch()

    def update_param(self, name: str, value: float) -> None:
        slider = self._sliders.get(name)
        if slider:
            slider.set_value(value)

    def add_attitude(self, roll: float, pitch: float, yaw: float) -> None:
        self._graph.add_attitude(roll, pitch, yaw)

    def clear_graph(self) -> None:
        self._graph.clear_data()

    @property
    def slider_names(self) -> list[str]:
        return list(self._sliders.keys())

    def _on_param_changed(self, name: str, value: float, ptype: int) -> None:
        self.param_changed.emit(name, value, ptype)

    def _on_write_all(self) -> None:
        for slider in self._sliders.values():
            self.param_changed.emit(
                slider.param_name, slider.current_value, 2
            )
