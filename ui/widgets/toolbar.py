from PySide6.QtWidgets import (
    QWidget, QToolBar, QPushButton, QComboBox,
    QLabel, QSizePolicy, QFrame,
)
from PySide6.QtCore import Signal, Qt, QSize


class Toolbar(QToolBar):
    connect_requested = Signal()
    disconnect_requested = Signal()
    arm_requested = Signal()
    disarm_requested = Signal()
    takeoff_requested = Signal(float)
    rtl_requested = Signal()
    mode_changed = Signal(str)
    emergency_stop_requested = Signal()
    params_toggled = Signal(bool)
    messages_toggled = Signal(bool)
    missions_toggled = Signal(bool)
    tuning_toggled = Signal(bool)
    firmware_requested = Signal()

    def __init__(self, parent=None):
        super().__init__("Main Toolbar", parent)
        self.setObjectName("toolbar")
        self.setIconSize(QSize(20, 20))
        self.setMovable(False)
        self.setFloatable(False)
        self._setup_ui()

    def _setup_ui(self):
        brand = QLabel("  S G C")
        brand.setObjectName("brand")
        self.addWidget(brand)

        self.addSeparator()

        self._connect_btn = QPushButton("  \u25cf  Connect  ")
        self._connect_btn.setCheckable(True)
        self._connect_btn.setObjectName("connect_btn")
        self.addWidget(self._connect_btn)

        self.addSeparator()

        self._arm_btn = QPushButton("Arm")
        self._arm_btn.setObjectName("arm_btn")
        self._arm_btn.setEnabled(False)
        self._arm_btn.setProperty("armed", False)
        self._arm_btn.setStyleSheet("""
            background-color: #27ae60; color: white;
            border: 2px solid #2ecc71; font-weight: bold;
        """)
        self.addWidget(self._arm_btn)

        self._takeoff_btn = QPushButton("Takeoff")
        self._takeoff_btn.setObjectName("takeoff_btn")
        self._takeoff_btn.setEnabled(False)
        self.addWidget(self._takeoff_btn)

        self._rtl_btn = QPushButton("RTL")
        self._rtl_btn.setObjectName("rtl_btn")
        self._rtl_btn.setEnabled(False)
        self.addWidget(self._rtl_btn)

        self._emergency_btn = QPushButton("\u26a1")
        self._emergency_btn.setObjectName("emergency_btn")
        self._emergency_btn.setFixedWidth(40)
        self._emergency_btn.setToolTip("Emergency Stop")
        self._emergency_btn.setEnabled(False)
        self.addWidget(self._emergency_btn)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        spacer.setStyleSheet("background: transparent;")
        self.addWidget(spacer)

        mode_label = QLabel("Mode")
        mode_label.setObjectName("mode_label")
        self.addWidget(mode_label)

        self._mode_combo = QComboBox()
        self._mode_combo.setObjectName("mode_combo")
        self._mode_combo.setFixedWidth(110)
        self._mode_combo.addItems([
            "STABILIZE", "ALT_HOLD", "LOITER", "GUIDED", "AUTO", "RTL", "LAND"
        ])
        self.addWidget(self._mode_combo)

        self._set_mode_btn = QPushButton("Set")
        self._set_mode_btn.setObjectName("set_mode_btn")
        self._set_mode_btn.setEnabled(False)
        self.addWidget(self._set_mode_btn)

        self.addSeparator()

        self._emergency_btn.clicked.connect(self.emergency_stop_requested.emit)

        self._params_btn = QPushButton("Params")
        self._params_btn.setObjectName("params_btn")
        self._params_btn.setCheckable(True)
        self._params_btn.setToolTip("Show/Hide Parameter Editor")
        self._params_btn.clicked.connect(lambda checked: self.params_toggled.emit(checked))
        self.addWidget(self._params_btn)

        self._messages_btn = QPushButton("Messages")
        self._messages_btn.setObjectName("messages_btn")
        self._messages_btn.setCheckable(True)
        self._messages_btn.setToolTip("Show/Hide Message Console")
        self._messages_btn.clicked.connect(lambda checked: self.messages_toggled.emit(checked))
        self.addWidget(self._messages_btn)

        self._missions_btn = QPushButton("Missions")
        self._missions_btn.setObjectName("missions_btn")
        self._missions_btn.setCheckable(True)
        self._missions_btn.setToolTip("Show/Hide Mission Manager")
        self._missions_btn.clicked.connect(lambda checked: self.missions_toggled.emit(checked))
        self.addWidget(self._missions_btn)

        self._tuning_btn = QPushButton("Tuning")
        self._tuning_btn.setObjectName("tuning_btn")
        self._tuning_btn.setCheckable(True)
        self._tuning_btn.setToolTip("Show/Hide Basic Tuning panel")
        self._tuning_btn.clicked.connect(lambda checked: self.tuning_toggled.emit(checked))
        self.addWidget(self._tuning_btn)

        self.addSeparator()

        self._firmware_btn = QPushButton("Firmware")
        self._firmware_btn.setObjectName("firmware_btn")
        self._firmware_btn.setToolTip("Install/Flash firmware")
        self._firmware_btn.clicked.connect(self.firmware_requested.emit)
        self.addWidget(self._firmware_btn)

        settings_btn = QPushButton("\u2699")
        settings_btn.setObjectName("settings_btn")
        settings_btn.setFixedWidth(36)
        settings_btn.setToolTip("Settings")
        self.addWidget(settings_btn)

        self._connect_btn.clicked.connect(self._on_connect_toggle)
        self._arm_btn.clicked.connect(self._on_arm_click)
        self._takeoff_btn.clicked.connect(lambda: self.takeoff_requested.emit(10.0))
        self._rtl_btn.clicked.connect(self.rtl_requested.emit)
        self._set_mode_btn.clicked.connect(
            lambda: self.mode_changed.emit(self._mode_combo.currentText())
        )

    def _on_connect_toggle(self, checked: bool) -> None:
        if checked:
            self.set_connecting()
            self.connect_requested.emit()
        else:
            self.set_connected(False)
            self.disconnect_requested.emit()

    def set_connecting(self) -> None:
        self._connect_btn.setText("  \u25b6  Scanning...  ")
        self._connect_btn.setEnabled(False)

    def set_connected(self, connected: bool) -> None:
        self._connect_btn.blockSignals(True)
        if connected:
            self._connect_btn.setText("  \u25cf  Disconnect  ")
            self._connect_btn.setChecked(True)
            self._connect_btn.setEnabled(True)
            self._arm_btn.setEnabled(True)
            self._takeoff_btn.setEnabled(True)
            self._rtl_btn.setEnabled(True)
            self._emergency_btn.setEnabled(True)
            self._set_mode_btn.setEnabled(True)
        else:
            self._connect_btn.setText("  \u25cf  Connect  ")
            self._connect_btn.setChecked(False)
            self._connect_btn.setEnabled(True)
            self._set_arm_visual(False)
            self._arm_btn.setEnabled(False)
            self._takeoff_btn.setEnabled(False)
            self._rtl_btn.setEnabled(False)
            self._emergency_btn.setEnabled(False)
            self._set_mode_btn.setEnabled(False)
        self._connect_btn.blockSignals(False)

    def _on_arm_click(self) -> None:
        if self._arm_btn.property("armed"):
            self.disarm_requested.emit()
        else:
            self.arm_requested.emit()

    def _set_arm_visual(self, armed: bool) -> None:
        self._arm_btn.setProperty("armed", armed)
        if armed:
            self._arm_btn.setText("\u26a1  ARMED")
            self._arm_btn.setStyleSheet("""
                background-color: #e67e22; color: white;
                border: 2px solid #f39c12; font-weight: bold;
            """)
        else:
            self._arm_btn.setText("Arm")
            self._arm_btn.setStyleSheet("""
                background-color: #27ae60; color: white;
                border: 2px solid #2ecc71; font-weight: bold;
            """)

    def set_armed(self, armed: bool) -> None:
        self._arm_btn.blockSignals(True)
        self._set_arm_visual(armed)
        self._arm_btn.blockSignals(False)

    def set_mode(self, mode: str) -> None:
        idx = self._mode_combo.findText(mode)
        if idx >= 0:
            self._mode_combo.setCurrentIndex(idx)
