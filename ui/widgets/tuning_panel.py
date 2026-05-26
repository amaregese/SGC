from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QSlider, QPushButton, QGroupBox, QFrame,
    QComboBox, QLineEdit,
)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QFont, QDoubleValidator

from ui.widgets.tuning_graph import TuningGraph


_SERVO_CHANNELS = [
    ("SERVO9 \uf085", 9), ("SERVO10 \uf086", 10),
    ("SERVO1", 1), ("SERVO2", 2), ("SERVO3", 3),
]


def _estimate_range(value: float, param_name: str) -> tuple[float, float, float]:
    up = param_name.upper()
    if any(x in up for x in ("SERVO", "PWM", "RC")):
        return 800.0, 2200.0, 1.0
    if any(x in up for x in ("REVERSED", "REVERSE", "REV")):
        return -1.0, 1.0, 1.0
    if any(x in up for x in ("FUNCTION",)):
        return 0.0, 10.0, 1.0
    if abs(value) < 1.0:
        return 0.0, 1.0, 0.001
    if abs(value) < 10.0:
        return 0.0, max(10.0, value * 2), 0.01
    if abs(value) < 100.0:
        return 0.0, max(100.0, value * 2), 0.1
    return 0.0, max(value * 2, 200.0), 1.0


class _ServoOutputSlider(QWidget):
    servo_output_requested = Signal(int, int)

    def __init__(self, label: str, channel: int, parent=None):
        super().__init__(parent)
        self._channel = channel
        self.setFixedHeight(32)
        row = QHBoxLayout(self)
        row.setContentsMargins(4, 0, 4, 0)
        row.setSpacing(6)
        name_label = QLabel(label)
        name_label.setFixedWidth(70)
        name_label.setFont(QFont("sans-serif", 9))
        row.addWidget(name_label)
        self._value_label = QLabel("1500")
        self._value_label.setFixedWidth(44)
        self._value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._value_label.setFont(QFont("monospace", 9))
        self._value_label.setStyleSheet("color: #e67e22;")
        row.addWidget(self._value_label)
        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(800, 2200)
        self._slider.setValue(1500)
        self._slider.setObjectName("tuning_slider")
        row.addWidget(self._slider, 1)
        row.addWidget(self._small_lbl("800"))
        row.addWidget(self._small_lbl("2200"))
        self._slider.valueChanged.connect(self._on_move)
        self._slider.sliderReleased.connect(self._on_release)

    @staticmethod
    def _small_lbl(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #666; font-size: 8px;")
        lbl.setFixedWidth(24)
        return lbl

    def reset(self, pwm: int = 1500) -> None:
        self._slider.blockSignals(True)
        self._slider.setValue(pwm)
        self._slider.blockSignals(False)
        self._value_label.setText(str(pwm))

    def _on_move(self, pwm: int) -> None:
        self._value_label.setText(str(pwm))

    def _on_release(self) -> None:
        self.servo_output_requested.emit(self._channel, self._slider.value())


class TuningPanel(QWidget):
    param_changed = Signal(str, float, int)
    request_refresh = Signal()
    servo_output_requested = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_params: dict[str, tuple[float, int]] = {}
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(4)

        header = QLabel("Tuning")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #eee; padding: 2px 0;")
        outer.addWidget(header)

        self._vehicle_label = QLabel("Firmware: \u2014")
        self._vehicle_label.setStyleSheet("color: #999; font-size: 9px;")
        outer.addWidget(self._vehicle_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        col = QVBoxLayout(inner)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(6)

        param_sel_row = QHBoxLayout()
        param_sel_row.setSpacing(4)
        param_sel_row.addWidget(QLabel("Param:"))
        self._param_combo = QComboBox()
        self._param_combo.setObjectName("tuning_param_combo")
        self._param_combo.setMinimumWidth(180)
        self._param_combo.currentIndexChanged.connect(self._on_param_selected)
        param_sel_row.addWidget(self._param_combo, 1)
        self._refresh_combo_btn = QPushButton("Reload")
        self._refresh_combo_btn.setObjectName("tuning_reload_btn")
        self._refresh_combo_btn.setFixedWidth(60)
        self._refresh_combo_btn.setToolTip("Reload param list from FCU")
        self._refresh_combo_btn.clicked.connect(self.request_refresh.emit)
        param_sel_row.addWidget(self._refresh_combo_btn)
        col.addLayout(param_sel_row)

        self._tune_group = QGroupBox("Parameter")
        self._tune_group.setObjectName("tuning_group")
        self._tune_group.setStyleSheet("""
            QGroupBox#tuning_group {
                border: 1px solid #333; border-radius: 4px;
                margin-top: 6px; padding-top: 14px;
                font-size: 10px; color: #bbb;
            }
            QGroupBox#tuning_group::title {
                subcontrol-origin: margin; left: 8px; padding: 0 4px;
            }
        """)
        tg = QVBoxLayout(self._tune_group)
        tg.setContentsMargins(4, 0, 4, 4)
        tg.setSpacing(4)

        val_row = QHBoxLayout()
        val_row.setSpacing(4)
        val_row.addWidget(QLabel("Value:"))
        self._value_edit = QLineEdit("0.000")
        self._value_edit.setObjectName("tuning_value")
        self._value_edit.setFixedWidth(80)
        self._value_edit.setAlignment(Qt.AlignRight)
        self._value_edit.setFont(QFont("monospace", 11))
        self._value_edit.setValidator(QDoubleValidator())
        val_row.addWidget(self._value_edit)
        self._read_btn = QPushButton("Read")
        self._read_btn.setObjectName("tuning_read_btn")
        self._read_btn.setFixedWidth(50)
        self._read_btn.clicked.connect(self._on_read)
        val_row.addWidget(self._read_btn)
        self._set_btn = QPushButton("Set")
        self._set_btn.setObjectName("tuning_set_btn")
        self._set_btn.setFixedWidth(50)
        self._set_btn.clicked.connect(self._on_set)
        val_row.addWidget(self._set_btn)
        tg.addLayout(val_row)

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setObjectName("tuning_slider")
        self._slider.setRange(0, 100)
        self._slider.valueChanged.connect(self._on_slider)
        self._slider.sliderReleased.connect(self._on_slider_release)
        tg.addWidget(self._slider)

        range_row = QHBoxLayout()
        range_row.setSpacing(0)
        self._range_min = QLabel("0")
        self._range_min.setStyleSheet("color: #666; font-size: 8px;")
        self._range_min.setFixedWidth(60)
        range_row.addWidget(self._range_min)
        range_row.addStretch()
        self._step_btn_m = QPushButton("\u2013")
        self._step_btn_m.setFixedSize(26, 22)
        self._step_btn_m.setObjectName("tuning_step_btn")
        self._step_btn_m.clicked.connect(self._on_step_down)
        range_row.addWidget(self._step_btn_m)
        self._step_lbl = QLabel("0.01")
        self._step_lbl.setStyleSheet("color: #888; font-size: 9px;")
        self._step_lbl.setFixedWidth(28)
        self._step_lbl.setAlignment(Qt.AlignCenter)
        range_row.addWidget(self._step_lbl)
        self._step_btn_p = QPushButton("+")
        self._step_btn_p.setFixedSize(26, 22)
        self._step_btn_p.setObjectName("tuning_step_btn")
        self._step_btn_p.clicked.connect(self._on_step_up)
        range_row.addWidget(self._step_btn_p)
        range_row.addStretch()
        self._range_max = QLabel("100")
        self._range_max.setStyleSheet("color: #666; font-size: 8px;")
        self._range_max.setFixedWidth(60)
        self._range_max.setAlignment(Qt.AlignRight)
        range_row.addWidget(self._range_max)
        tg.addLayout(range_row)

        col.addWidget(self._tune_group)

        servo_box = QGroupBox("Servo Output")
        servo_box.setObjectName("tuning_group")
        servo_box.setStyleSheet("""
            QGroupBox#tuning_group {
                border: 1px solid #f39c12; border-radius: 4px;
                margin-top: 6px; padding-top: 14px;
                font-size: 10px; color: #f39c12;
            }
            QGroupBox#tuning_group::title {
                subcontrol-origin: margin; left: 8px; padding: 0 4px;
            }
        """)
        sv = QVBoxLayout(servo_box)
        sv.setContentsMargins(4, 0, 4, 4)
        sv.setSpacing(0)
        self._servo_sliders: list[_ServoOutputSlider] = []
        for label, ch in _SERVO_CHANNELS:
            s = _ServoOutputSlider(label, ch)
            s.servo_output_requested.connect(self.servo_output_requested.emit)
            self._servo_sliders.append(s)
            sv.addWidget(s)
        reset_btn = QPushButton("Reset All")
        reset_btn.setObjectName("tuning_step_btn")
        reset_btn.setFixedHeight(22)
        reset_btn.clicked.connect(self._on_servo_reset)
        sv.addWidget(reset_btn, 0, Qt.AlignCenter)
        col.addWidget(servo_box)

        col.addStretch()
        scroll.setWidget(inner)
        outer.addWidget(scroll, 1)

        self._graph = TuningGraph()
        self._graph.setMinimumHeight(150)
        outer.addWidget(self._graph)

        self._param_min = 0.0
        self._param_max = 100.0
        self._param_step = 0.01
        self._selected_param = ""

    def set_preset(self, vehicle_type_str: str, mav_type: int = 0) -> None:
        suffix = f" (MAV_TYPE {mav_type})" if mav_type else ""
        self._vehicle_label.setText(f"Firmware: {vehicle_type_str}{suffix}")

    @property
    def vehicle_label(self) -> str:
        text = self._vehicle_label.text()
        prefix = "Firmware: "
        if text.startswith(prefix):
            idx = text.find("(")
            return text[len(prefix):idx].strip() if idx > 0 else text[len(prefix):].strip()
        return ""

    def populate_params(self, all_params: dict[str, tuple[float, int]]) -> None:
        self._all_params = all_params
        current = self._param_combo.currentText()
        self._param_combo.blockSignals(True)
        self._param_combo.clear()
        names = sorted(all_params.keys())
        self._param_combo.addItem("")
        for n in names:
            val = all_params[n][0]
            self._param_combo.addItem(f"{n}  [{val}]", n)
        idx = self._param_combo.findText(current) if current else -1
        if idx >= 0:
            self._param_combo.setCurrentIndex(idx)
        elif len(names) > 0:
            self._param_combo.setCurrentIndex(1)
        self._param_combo.blockSignals(False)

    def update_param_value(self, name: str, value: float) -> None:
        if name in self._all_params:
            self._all_params[name] = (value, self._all_params[name][1])
        for i in range(1, self._param_combo.count()):
            if self._param_combo.itemData(i) == name:
                self._param_combo.setItemText(i, f"{name}  [{value}]")
                break

    def add_attitude(self, roll: float, pitch: float, yaw: float) -> None:
        self._graph.add_attitude(roll, pitch, yaw)

    def clear_graph(self) -> None:
        self._graph.clear_data()

    def _update_slider_for_param(self, param_name: str) -> None:
        info = self._all_params.get(param_name)
        if info is None:
            return
        value, ptype = info
        lo, hi, step = _estimate_range(value, param_name)
        self._param_min = lo
        self._param_max = hi
        self._param_step = step
        self._selected_param = param_name

        self._value_edit.setText(f"{value}")
        self._range_min.setText(f"{lo}")
        self._range_max.setText(f"{hi}")
        self._step_lbl.setText(f"{step}")
        self._tune_group.setTitle(f"  {param_name}")

        steps = int((hi - lo) / step)
        self._slider.blockSignals(True)
        self._slider.setRange(0, max(1, steps))
        self._slider.setValue(int((value - lo) / step))
        self._slider.blockSignals(False)

    def _on_param_selected(self, idx: int) -> None:
        if idx <= 0:
            return
        name = self._param_combo.itemData(idx)
        if name:
            self._update_slider_for_param(name)

    def _on_slider(self, pos: int) -> None:
        val = self._param_min + pos * self._param_step
        self._value_edit.setText(f"{val:.4f}")

    def _on_slider_release(self) -> None:
        val = self._param_min + self._slider.value() * self._param_step
        self._value_edit.setText(f"{val:.4f}")
        self._on_set()

    def _on_read(self) -> None:
        if self._selected_param and self._all_params:
            info = self._all_params.get(self._selected_param)
            if info:
                self._update_slider_for_param(self._selected_param)

    def _on_set(self) -> None:
        if not self._selected_param:
            return
        try:
            val = float(self._value_edit.text())
        except ValueError:
            return
        info = self._all_params.get(self._selected_param)
        ptype = info[1] if info else 2
        self.param_changed.emit(self._selected_param, val, ptype)

    def _on_step_up(self) -> None:
        new_val = self._slider.value() + 1
        if new_val <= self._slider.maximum():
            self._slider.setValue(new_val)

    def _on_step_down(self) -> None:
        new_val = self._slider.value() - 1
        if new_val >= 0:
            self._slider.setValue(new_val)

    def _on_servo_reset(self) -> None:
        for s in self._servo_sliders:
            s.reset(1500)
            s._on_release()

    @property
    def slider_names(self) -> list[str]:
        if self._selected_param:
            return [self._selected_param]
        return []
