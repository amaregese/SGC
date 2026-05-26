from PySide6.QtWidgets import QStatusBar, QWidget, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt

from domain.models.vehicle import Vehicle


class StatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("status_bar")
        self.setFixedHeight(28)
        self._setup_ui()

    def _setup_ui(self):
        self._conn_indicator = QLabel("\u25cf")
        self._conn_indicator.setObjectName("conn_indicator")
        self.addPermanentWidget(self._conn_indicator)

        self._link_label = QLabel()
        self._link_label.setObjectName("sb_label")
        self._link_label.setFixedWidth(48)
        self._link_label.setToolTip("Link quality")
        self.addPermanentWidget(self._link_label)

        self._conn_label = QLabel("Disconnected")
        self._conn_label.setObjectName("conn_label")
        self.addPermanentWidget(self._conn_label)

        self._gps_label = QLabel("GPS: --  Fix: ---")
        self._gps_label.setObjectName("sb_label")
        self.addPermanentWidget(self._gps_label)

        self._mode_label = QLabel("Mode: ---")
        self._mode_label.setObjectName("sb_label")
        self.addPermanentWidget(self._mode_label)

        self._batt_label = QLabel("Batt: --.- V")
        self._batt_label.setObjectName("sb_label")
        self.addPermanentWidget(self._batt_label)

        self._alt_label = QLabel("Alt: --- m")
        self._alt_label.setObjectName("sb_label")
        self.addPermanentWidget(self._alt_label)

        self._spd_label = QLabel("Spd: --.- m/s")
        self._spd_label.setObjectName("sb_label")
        self.addPermanentWidget(self._spd_label)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addPermanentWidget(spacer)

        self._time_label = QLabel()
        self._time_label.setObjectName("sb_label")
        self.addPermanentWidget(self._time_label)

        self._log_label = QLabel("Log: OFF")
        self._log_label.setObjectName("sb_label")
        self._log_label.setToolTip("Telemetry log status")
        self.addPermanentWidget(self._log_label)

    def set_connected(self, connected: bool) -> None:
        if connected:
            self._conn_indicator.setText("\u25cf")
            self._conn_indicator.setStyleSheet("color: #2ecc71;")
            self._conn_label.setText("Connected")
            self._conn_label.setStyleSheet("color: #2ecc71;")
            self._link_label.setText("OK")
            self._link_label.setStyleSheet("color: #2ecc71;")
        else:
            self._conn_indicator.setText("\u25cf")
            self._conn_indicator.setStyleSheet("color: #e74c3c;")
            self._conn_label.setText("Disconnected")
            self._conn_label.setStyleSheet("color: #e74c3c;")
            self._link_label.setText("")
            self._link_label.setStyleSheet("color: #666;")

    def set_heartbeat_warning(self, warn: bool) -> None:
        if warn:
            self._link_label.setText("LINK!")
            self._link_label.setStyleSheet("color: #e67e22; font-weight: bold;")
        else:
            self._link_label.setText("OK")
            self._link_label.setStyleSheet("color: #2ecc71;")

    def set_logging(self, active: bool, path: str | None = None) -> None:
        if active and path:
            name = path.split("/")[-1]
            self._log_label.setText(f"Log: {name}")
            self._log_label.setStyleSheet("color: #2ecc71;")
            self._log_label.setToolTip(f"Logging to {path}")
        else:
            self._log_label.setText("Log: OFF")
            self._log_label.setStyleSheet("color: #666;")
            self._log_label.setToolTip("")

    def update_from_vehicle(self, vehicle: Vehicle) -> None:
        self._gps_label.setText(f"GPS: {vehicle.gps_info.satellites_visible}  Fix: {'3D' if vehicle.gps_info.fix_type >= 3 else '2D' if vehicle.gps_info.fix_type >= 2 else 'No'}")
        self._mode_label.setText(f"Mode: {vehicle.mode}")
        self._batt_label.setText(f"Batt: {vehicle.battery.voltage:.1f} V")
        self._alt_label.setText(f"Alt: {vehicle.position.alt:.0f} m")
        self._spd_label.setText(f"Spd: {vehicle.groundspeed:.1f} m/s")
