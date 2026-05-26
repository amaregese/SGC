from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QProgressBar, QGridLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from domain.models.vehicle import Vehicle


_ALT_BG = QColor("#1a1a3e")
_BORDER = QColor("#0f3460")
_GREEN = "#2ecc71"
_RED = "#e74c3c"
_ORANGE = "#e67e22"
_CYAN = "#4fc3f7"
_DOT = "\u25cf"


class _Card(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("telemetry_card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        header = QLabel(title)
        header.setObjectName("card_header")
        layout.addWidget(header)

        self._body = QWidget()
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(0, 2, 0, 0)
        self._body_layout.setSpacing(2)
        layout.addWidget(self._body)

    def body(self) -> QVBoxLayout:
        return self._body_layout


class _Row(QFrame):
    def __init__(self, label: str, value: str = "---", parent=None):
        super().__init__(parent)
        self.setFixedHeight(22)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._lbl = QLabel(label)
        self._lbl.setObjectName("info_label")
        layout.addWidget(self._lbl)

        self._val = QLabel(value)
        self._val.setObjectName("info_value")
        self._val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self._val, 1)

    def set_value(self, text: str) -> None:
        self._val.setText(text)


class _BatteryBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 0)
        layout.setSpacing(0)

        self._bar = QProgressBar()
        self._bar.setObjectName("battery_bar")
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(True)
        self._bar.setFixedHeight(12)
        layout.addWidget(self._bar)

    def set_value(self, pct: float) -> None:
        self._bar.setValue(int(pct))
        self._bar.setFormat(f"{pct:.0f}%")
        color = _GREEN if pct > 50 else (_ORANGE if pct > 20 else _RED)
        self._bar.setStyleSheet(f"""
            #battery_bar {{
                background-color: #0f3460; border: none; border-radius: 3px;
                text-align: center; font-size: 9px; color: white;
            }}
            #battery_bar::chunk {{
                background-color: {color}; border-radius: 3px;
            }}
        """)


class TelemetryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("telemetry_panel")
        self.setFixedWidth(260)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        att = _Card("ATTITUDE")
        self._roll = _Row("Roll")
        self._pitch = _Row("Pitch")
        self._yaw = _Row("Yaw")
        self._heading = _Row("Heading")
        att.body().addWidget(self._roll)
        att.body().addWidget(self._pitch)
        att.body().addWidget(self._yaw)
        att.body().addWidget(self._heading)
        layout.addWidget(att)

        gps = _Card("GPS")
        self._lat = _Row("Lat")
        self._lon = _Row("Lon")
        self._alt = _Row("Alt")
        self._sats = _Row("Sats")
        self._fix = _Row("Fix")
        gps.body().addWidget(self._lat)
        gps.body().addWidget(self._lon)
        gps.body().addWidget(self._alt)
        gps.body().addWidget(self._sats)
        gps.body().addWidget(self._fix)
        layout.addWidget(gps)

        batt = _Card("BATTERY")
        self._volt = _Row("Voltage")
        self._current = _Row("Current")
        self._batt_bar = _BatteryBar()
        batt.body().addWidget(self._volt)
        batt.body().addWidget(self._current)
        batt.body().addWidget(self._batt_bar)
        layout.addWidget(batt)

        status = _Card("STATUS")
        self._mode = _Row("Mode")
        self._armed_indicator = _Row("Armed")
        self._sys_status = _Row("System")
        self._link = _Row("Link")
        status.body().addWidget(self._mode)
        status.body().addWidget(self._armed_indicator)
        status.body().addWidget(self._sys_status)
        status.body().addWidget(self._link)
        layout.addWidget(status)

        layout.addStretch()

    def update_from_vehicle(self, vehicle: Vehicle) -> None:
        self._roll.set_value(f"{vehicle.attitude.roll:.1f}\u00b0")
        self._pitch.set_value(f"{vehicle.attitude.pitch:.1f}\u00b0")
        self._yaw.set_value(f"{vehicle.attitude.yaw:.1f}\u00b0")
        self._heading.set_value(f"{vehicle.heading:.1f}\u00b0")

        self._lat.set_value(f"{vehicle.position.lat:.6f}")
        self._lon.set_value(f"{vehicle.position.lon:.6f}")
        self._alt.set_value(f"{vehicle.position.alt:.1f} m")
        self._sats.set_value(str(vehicle.gps_info.satellites_visible))
        fix_names = {0: "NO_GPS", 1: "NO_FIX", 2: "2D", 3: "3D", 4: "DGPS", 5: "RTK"}
        self._fix.set_value(fix_names.get(vehicle.gps_info.fix_type, f"{vehicle.gps_info.fix_type}"))

        self._volt.set_value(f"{vehicle.battery.voltage:.2f} V")
        self._current.set_value(f"{vehicle.battery.current:.1f} A")
        self._batt_bar.set_value(vehicle.battery.remaining)

        self._mode.set_value(vehicle.mode)
        color = _GREEN if vehicle.armed else _RED
        self._armed_indicator.set_value(
            f"<span style='color:{color};font-size:16px'>{_DOT}</span> "
            f"{'ARMED' if vehicle.armed else 'DISARMED'}"
        )
        sys_names = {0: "UNKNOWN", 1: "UNINIT", 2: "BOOT", 3: "CALIB", 4: "STANDBY", 5: "ACTIVE", 6: "CRITICAL"}
        self._sys_status.set_value(sys_names.get(vehicle.system_status, f"{vehicle.system_status}"))

    def set_link_quality(self, ok: bool, age: float = 0.0) -> None:
        if ok:
            self._link.set_value(f"<span style='color:{_GREEN};font-size:16px'>{_DOT}</span> OK")
        else:
            self._link.set_value(f"<span style='color:{_ORANGE};font-size:16px'>{_DOT}</span> {age:.0f}s")
