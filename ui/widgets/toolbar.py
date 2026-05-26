from PySide6.QtWidgets import (
    QWidget, QToolBar, QPushButton, QComboBox,
    QLabel, QSizePolicy, QToolButton, QMenu,
)
from PySide6.QtGui import QAction
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
    actions_toggled = Signal(bool)
    console_toggled = Signal(bool)
    joystick_toggled = Signal(bool)
    camera_toggled = Signal(bool)
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

        # ── Connection ──
        self._connect_btn = QPushButton("  \u25cf  Connect  ")
        self._connect_btn.setCheckable(True)
        self._connect_btn.setObjectName("connect_btn")
        self.addWidget(self._connect_btn)

        self.addSeparator()

        # ── Vehicle ──
        menu = QMenu(self)
        self._arm_act = menu.addAction("Arm")
        self._arm_act.setEnabled(False)
        self._takeoff_act = menu.addAction("Takeoff")
        self._takeoff_act.setEnabled(False)
        self._rtl_act = menu.addAction("RTL")
        self._rtl_act.setEnabled(False)
        menu.addSeparator()
        self._emergency_act = menu.addAction("\u26a1 Emergency Stop")
        self._emergency_act.setEnabled(False)
        self._vehicle_btn = _GroupButton("Vehicle", menu)
        self.addWidget(self._vehicle_btn)

        self.addSeparator()

        # ── Mode ──
        menu2 = QMenu(self)
        self._mode_menu = menu2
        self._mode_actions: list[QAction] = []
        modes = ["STABILIZE", "ALT_HOLD", "LOITER", "GUIDED", "AUTO", "RTL", "LAND"]
        for m in modes:
            a = menu2.addAction(m)
            a.setCheckable(True)
            a.setData(m)
            a.triggered.connect(lambda checked=False, act=a: self._on_mode_selected(act))
            self._mode_actions.append(a)
        self._mode_btn = _GroupButton("Mode", menu2)
        self.addWidget(self._mode_btn)

        self.addSeparator()

        # ── Panels ──
        menu3 = QMenu(self)
        self._params_act = menu3.addAction("Params")
        self._params_act.setCheckable(True)
        self._params_act.toggled.connect(self.params_toggled.emit)
        self._messages_act = menu3.addAction("Messages")
        self._messages_act.setCheckable(True)
        self._messages_act.toggled.connect(self.messages_toggled.emit)
        self._missions_act = menu3.addAction("Missions")
        self._missions_act.setCheckable(True)
        self._missions_act.toggled.connect(self.missions_toggled.emit)
        self._tuning_act = menu3.addAction("Tuning")
        self._tuning_act.setCheckable(True)
        self._tuning_act.toggled.connect(self.tuning_toggled.emit)
        self._panels_btn = _GroupButton("Panels", menu3)
        self.addWidget(self._panels_btn)

        self.addSeparator()

        # ── Tools ──
        menu4 = QMenu(self)
        self._actions_act = menu4.addAction("Actions")
        self._actions_act.setCheckable(True)
        self._actions_act.toggled.connect(self.actions_toggled.emit)
        self._joystick_act = menu4.addAction("Joystick")
        self._joystick_act.setCheckable(True)
        self._joystick_act.toggled.connect(self.joystick_toggled.emit)
        self._console_act = menu4.addAction("Console")
        self._console_act.setCheckable(True)
        self._console_act.toggled.connect(self.console_toggled.emit)
        self._camera_act = menu4.addAction("Camera")
        self._camera_act.setCheckable(True)
        self._camera_act.toggled.connect(self.camera_toggled.emit)
        self._tools_btn = _GroupButton("Tools", menu4)
        self.addWidget(self._tools_btn)

        self.addSeparator()

        # ── System ──
        menu5 = QMenu(self)
        self._firmware_act = menu5.addAction("Firmware")
        self._firmware_act.triggered.connect(self.firmware_requested.emit)
        self._system_btn = _GroupButton("System", menu5)
        self.addWidget(self._system_btn)

        self._connect_btn.clicked.connect(self._on_connect_toggle)
        self._arm_act.triggered.connect(self._on_arm_click)
        self._takeoff_act.triggered.connect(lambda: self.takeoff_requested.emit(10.0))
        self._rtl_act.triggered.connect(self.rtl_requested.emit)
        self._emergency_act.triggered.connect(self.emergency_stop_requested.emit)

    def _on_connect_toggle(self, checked: bool) -> None:
        if checked:
            self.set_connecting()
            self.connect_requested.emit()
        else:
            self.set_connected(False)
            self.disconnect_requested.emit()

    def _on_arm_click(self) -> None:
        if self._arm_act.property("armed"):
            self.disarm_requested.emit()
        else:
            self.arm_requested.emit()

    def _on_mode_selected(self, act: QAction) -> None:
        mode = act.data() if act else ""
        if mode:
            for a in self._mode_actions:
                a.setChecked(a is act)
            self._mode_btn.setText(mode)
            self.mode_changed.emit(mode)

    # ── external state setters ──

    def set_connecting(self) -> None:
        self._connect_btn.setText("  \u25b6  Scanning...  ")
        self._connect_btn.setEnabled(False)

    def set_connected(self, connected: bool) -> None:
        self._connect_btn.blockSignals(True)
        if connected:
            self._connect_btn.setText("  \u25cf  Disconnect  ")
            self._connect_btn.setChecked(True)
            self._connect_btn.setEnabled(True)
            self._arm_act.setEnabled(True)
            self._takeoff_act.setEnabled(True)
            self._rtl_act.setEnabled(True)
            self._emergency_act.setEnabled(True)
        else:
            self._connect_btn.setText("  \u25cf  Connect  ")
            self._connect_btn.setChecked(False)
            self._connect_btn.setEnabled(True)
            self._arm_act.setEnabled(False)
            self._takeoff_act.setEnabled(False)
            self._rtl_act.setEnabled(False)
            self._emergency_act.setEnabled(False)
        self._connect_btn.blockSignals(False)

    def set_armed(self, armed: bool) -> None:
        self._arm_act.setProperty("armed", armed)
        if armed:
            self._arm_act.setText("\u26a1  ARMED")
            self._vehicle_btn._update_label("ARMED")
        else:
            self._arm_act.setText("Arm")
            self._vehicle_btn._update_label("Vehicle")

    def set_mode(self, mode: str) -> None:
        for a in self._mode_actions:
            a.setChecked(a.data() == mode)
        self._mode_btn.setText(mode)

    def set_panel_checked(self, panel: str, checked: bool) -> None:
        mapping = {
            "params": self._params_act,
            "messages": self._messages_act,
            "missions": self._missions_act,
            "tuning": self._tuning_act,
            "actions": self._actions_act,
            "joystick": self._joystick_act,
            "console": self._console_act,
            "camera": self._camera_act,
        }
        act = mapping.get(panel)
        if act:
            act.blockSignals(True)
            act.setChecked(checked)
            act.blockSignals(False)


class _GroupButton(QToolButton):
    def __init__(self, label: str, menu: QMenu):
        super().__init__()
        self._label = label
        self.setText(f"  {label}  \u25be")
        self.setObjectName("toolbar_group")
        self.setMenu(menu)
        self.setPopupMode(QToolButton.InstantPopup)
        self.setMinimumHeight(32)
        self.setStyleSheet("""
            QToolButton {
                background-color: #2a2a4a; color: #ccc;
                border: none; border-radius: 4px;
                padding: 4px 10px; font-size: 11px; font-weight: bold;
            }
            QToolButton:hover {
                background-color: #3a3a6a;
            }
            QToolButton::menu-indicator {
                image: none;
                width: 0px;
            }
        """)

    def _update_label(self, text: str) -> None:
        self.setText(f"  {text}  \u25be")
