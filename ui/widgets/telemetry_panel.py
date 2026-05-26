from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QProgressBar, QGridLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from domain.models.vehicle import Vehicle


_GREEN = "#2ecc71"
_RED = "#e74c3c"
_ORANGE = "#e67e22"
_CYAN = "#4fc3f7"
_DOT = "\u25cf"


class _ValueRow(QWidget):
    def __init__(self, label: str, value: str = "---", parent=None):
        super().__init__(parent)
        self.setFixedHeight(20)
        row = QHBoxLayout(self)
        row.setContentsMargins(4, 0, 4, 0)
        row.setSpacing(4)
        self._lbl = QLabel(label)
        self._lbl.setStyleSheet("color:#aaa;font-size:10px;")
        self._lbl.setFixedWidth(24)
        row.addWidget(self._lbl)
        self._val = QLabel(value)
        self._val.setStyleSheet("color:#fff;font-size:11px;font-family:monospace;font-weight:bold;")
        self._val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(self._val, 1)

    def set_value(self, text: str) -> None:
        self._val.setText(text)


class _Block(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            _Block { background:#1a1a3e; border:1px solid #0f3460; border-radius:4px; }
        """)
        col = QVBoxLayout(self)
        col.setContentsMargins(4, 4, 4, 5)
        col.setSpacing(0)
        header = QLabel(title)
        header.setStyleSheet("color:#4fc3f7;font-size:9px;font-weight:bold;letter-spacing:1px;")
        col.addWidget(header)
        self._body = QVBoxLayout()
        self._body.setContentsMargins(0, 0, 0, 0)
        self._body.setSpacing(0)
        col.addLayout(self._body)

    def add_row(self, label: str, value: str = "---") -> _ValueRow:
        r = _ValueRow(label, value)
        self._body.addWidget(r)
        return r


class TelemetryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("telemetry_panel")
        self._setup_ui()

    def _setup_ui(self):
        grid = QGridLayout(self)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setSpacing(4)

        # Attitude block
        att = _Block("ATTITUDE")
        self._roll = att.add_row("R")
        self._pitch = att.add_row("P")
        self._yaw = att.add_row("Y")
        self._heading = att.add_row("H")
        grid.addWidget(att, 0, 0)

        # GPS block
        gps = _Block("GPS")
        self._lat = gps.add_row("Lat")
        self._lon = gps.add_row("Lon")
        self._alt = gps.add_row("Alt")
        self._sats = gps.add_row("Sat")
        self._fix = gps.add_row("Fix")
        grid.addWidget(gps, 0, 1)

        # Battery block
        batt = _Block("BATTERY")
        self._volt = batt.add_row("V")
        self._current = batt.add_row("A")
        self._batt_bar = QProgressBar()
        self._batt_bar.setObjectName("mini_battery_bar")
        self._batt_bar.setRange(0, 100)
        self._batt_bar.setValue(0)
        self._batt_bar.setTextVisible(True)
        self._batt_bar.setFixedHeight(12)
        self._batt_bar.setStyleSheet("""
            #mini_battery_bar {
                background-color:#0f3460; border:none; border-radius:2px;
                text-align:center; font-size:8px; color:white;
            }
        """)
        batt._body.addWidget(self._batt_bar)
        grid.addWidget(batt, 1, 0)

        # Status block
        st = _Block("STATUS")
        self._mode = st.add_row("Mode")
        self._armed = st.add_row("Arm")
        self._sys = st.add_row("Sys")
        self._link = st.add_row("Link")
        grid.addWidget(st, 1, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

    def update_from_vehicle(self, vehicle: Vehicle) -> None:
        self._roll.set_value(f"{vehicle.attitude.roll:.1f}\u00b0")
        self._pitch.set_value(f"{vehicle.attitude.pitch:.1f}\u00b0")
        self._yaw.set_value(f"{vehicle.attitude.yaw:.1f}\u00b0")
        self._heading.set_value(f"{vehicle.heading:.1f}\u00b0")

        self._lat.set_value(f"{vehicle.position.lat:.4f}")
        self._lon.set_value(f"{vehicle.position.lon:.4f}")
        self._alt.set_value(f"{vehicle.position.alt:.1f}m")
        self._sats.set_value(str(vehicle.gps_info.satellites_visible))
        fix_names = {0: "NO", 1: "2D", 2: "3D", 3: "DGPS", 4: "RTK"}
        self._fix.set_value(fix_names.get(vehicle.gps_info.fix_type, f"{vehicle.gps_info.fix_type}"))

        self._volt.set_value(f"{vehicle.battery.voltage:.2f}V")
        self._current.set_value(f"{vehicle.battery.current:.1f}A")
        self._batt_bar.setValue(int(vehicle.battery.remaining))
        self._batt_bar.setFormat(f"{vehicle.battery.remaining:.0f}%")
        color = _GREEN if vehicle.battery.remaining > 50 else (_ORANGE if vehicle.battery.remaining > 20 else _RED)
        self._batt_bar.setStyleSheet(f"""
            #mini_battery_bar {{
                background-color:#0f3460; border:none; border-radius:2px;
                text-align:center; font-size:8px; color:white;
            }}
            #mini_battery_bar::chunk {{
                background-color:{color}; border-radius:2px;
            }}
        """)

        self._mode.set_value(vehicle.mode)
        color = _GREEN if vehicle.armed else _RED
        self._armed.set_value(
            f"<span style='color:{color};font-size:14px'>{_DOT}</span> "
            f"{'ARMED' if vehicle.armed else 'DISARMED'}"
        )
        sys_names = {0: "UNK", 1: "INIT", 2: "BOOT", 3: "CAL", 4: "SBY", 5: "ACT", 6: "CRIT"}
        self._sys.set_value(sys_names.get(vehicle.system_status, f"{vehicle.system_status}"))

    def set_link_quality(self, ok: bool, age: float = 0.0) -> None:
        if ok:
            self._link.set_value(f"<span style='color:{_GREEN};font-size:14px'>{_DOT}</span> OK")
        else:
            self._link.set_value(f"<span style='color:{_ORANGE};font-size:14px'>{_DOT}</span> {age:.0f}s")
