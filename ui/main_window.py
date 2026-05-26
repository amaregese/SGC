import glob
import time
import dataclasses

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QMessageBox, QDockWidget,
)
from PySide6.QtCore import Qt, QThread, Signal, QObject, QTimer

from ui.widgets.toolbar import Toolbar
from ui.widgets.status_bar import StatusBar
from ui.widgets.telemetry_panel import TelemetryPanel
from ui.widgets.map_widget import MapWidget
from ui.widgets.video_stream import VideoStream
from infrastructure.mavlink.mavlink_connection import (
    MAVLinkConnection, ConnectionType, ConnectionError,
    HB_LOST_WARN, HB_LOST_DISCONNECT,
)
from infrastructure.mavlink.command_sender import CommandSender
from infrastructure.mavlink.param_client import ParamClient
from infrastructure.storage.log_manager import TLogWriter
from domain.services.telemetry_processor import TelemetryProcessor
from ui.widgets.parameter_panel import ParameterPanel
from ui.widgets.message_console import MessageConsole, ConsoleBridge
from ui.widgets.mission_panel import MissionPanel
from infrastructure.mavlink.mission_client import MissionClient
from ui.widgets.firmware_flash_dialog import FirmwareFlashDialog
from ui.widgets.tuning_panel import TuningPanel
from ui.widgets.action_panel import ActionsPanel
from ui.widgets.joystick_panel import JoystickPanel
from infrastructure.input.joystick_manager import JoystickManager
from ui.widgets.hud import HUDWidget
from ui.widgets.serial_console import SerialConsolePanel
from infrastructure.mavlink.serial_console import SerialConsoleManager


class _TelemetryBridge(QObject):
    vehicle_updated = Signal(object)

    _TYPES = frozenset({
        "ATTITUDE", "GLOBAL_POSITION_INT", "GPS_RAW_INT",
        "BATTERY_STATUS", "HEARTBEAT", "VFR_HUD",
    })

    def __init__(self):
        super().__init__()
        self._processor = TelemetryProcessor()

    def process(self, msg) -> None:
        if msg.get_type() not in self._TYPES:
            return
        vehicle = self._processor.process(msg)
        self.vehicle_updated.emit(dataclasses.replace(vehicle))


class _AutoConnectWorker(QThread):
    success = Signal()
    failed = Signal(str)
    trying = Signal(str)

    def __init__(self):
        super().__init__()
        self.connection: MAVLinkConnection | None = None

    def run(self):
        ports = self._detect_ports()

        for port in ports:
            self.trying.emit(f"Trying serial {port}...")
            conn = MAVLinkConnection()
            try:
                conn.connect(ConnectionType.SERIAL, port, timeout=3.0)
                self.connection = conn
                self.success.emit()
                return
            except ConnectionError:
                continue

        self.trying.emit("Trying UDP :14550...")
        conn = MAVLinkConnection()
        try:
            conn.connect(ConnectionType.UDP, "0.0.0.0:14550", timeout=3.0)
            self.connection = conn
            self.success.emit()
            return
        except ConnectionError:
            pass

        tried = "\n".join(f"  {p}" for p in ports) if ports else "  (none found)"
        self.failed.emit(
            "No FCU detected on any port.\n\n"
            f"Checked serial ports:\n{tried}\n"
            "and UDP :14550.\n\n"
            "Check that the FCU is powered and connected."
        )

    @staticmethod
    def _detect_ports() -> list[str]:
        all_ports = glob.glob("/dev/cu.*") + glob.glob("/dev/tty.*")
        all_ports.sort()
        fcu_ports = [
            p for p in all_ports
            if any(kw in p for kw in ["usbmodem", "usbserial", "ttyACM", "ttyUSB"])
        ]
        if fcu_ports:
            return fcu_ports
        return [
            p for p in all_ports
            if "Bluetooth" not in p and "debug" not in p
        ]


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SkyWin Ground Controller")
        self.resize(1400, 900)

        self._mavlink_connection: MAVLinkConnection | None = None
        self._worker: _AutoConnectWorker | None = None
        self._command_sender: CommandSender | None = None
        self._tlog_writer: TLogWriter | None = None
        self._param_client: ParamClient | None = None
        self._connected = False
        self._prev_armed = False
        self._vehicle_type_set = False
        self._flight_path: list[list[float]] = []
        self._flight_path_counter = 0

        self._toolbar = Toolbar()
        self.addToolBar(Qt.TopToolBarArea, self._toolbar)

        self._status_bar = StatusBar()
        self.setStatusBar(self._status_bar)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._hud = HUDWidget()
        self._map_widget = MapWidget()

        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.addWidget(self._map_widget)
        right_splitter.setStretchFactor(0, 1)

        left_splitter = QSplitter(Qt.Vertical)
        left_splitter.addWidget(self._hud)
        self._telemetry_panel = TelemetryPanel()
        left_splitter.addWidget(self._telemetry_panel)
        left_splitter.setStretchFactor(0, 1)
        left_splitter.setStretchFactor(1, 1)

        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(left_splitter, 30)
        content_layout.addWidget(right_splitter, 70)

        main_layout.addWidget(content)

        # ── Camera / Video Dock ──
        self._video_stream = VideoStream()
        self._video_dock = QDockWidget("Camera", self)
        self._video_dock.setObjectName("video_dock")
        self._video_dock.setWidget(self._video_stream)
        self._video_dock.setAllowedAreas(
            Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea | Qt.BottomDockWidgetArea
        )
        self._video_dock.setFeatures(
            QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
        )
        self._video_dock.setMinimumSize(320, 240)
        self.addDockWidget(Qt.RightDockWidgetArea, self._video_dock)
        self._video_dock.hide()

        self._toolbar.connect_requested.connect(self._on_connect)
        self._toolbar.disconnect_requested.connect(self._on_disconnect)
        self._toolbar.arm_requested.connect(self._on_arm)
        self._toolbar.disarm_requested.connect(self._on_disarm)
        self._toolbar.takeoff_requested.connect(self._on_takeoff)
        self._toolbar.rtl_requested.connect(self._on_rtl)
        self._toolbar.mode_changed.connect(self._on_mode_change)
        self._toolbar.emergency_stop_requested.connect(self._on_emergency_stop)
        self._toolbar.firmware_requested.connect(self._on_firmware)

        self._hb_timer = QTimer(self)
        self._hb_timer.setInterval(1000)
        self._hb_timer.timeout.connect(self._check_heartbeat)

        self._param_panel = ParameterPanel()
        self._param_dock = QDockWidget("Parameters", self)
        self._param_dock.setObjectName("param_dock")
        self._param_dock.setWidget(self._param_panel)
        self._param_dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self._param_dock.hide()
        self.addDockWidget(Qt.RightDockWidgetArea, self._param_dock)

        self._toolbar.params_toggled.connect(self._param_dock.setVisible)
        self._param_dock.visibilityChanged.connect(self._on_param_dock_visibility)

        self._message_console = MessageConsole()
        self._console_dock = QDockWidget("Messages", self)
        self._console_dock.setObjectName("console_dock")
        self._console_dock.setWidget(self._message_console)
        self._console_dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self._console_dock.hide()
        self.addDockWidget(Qt.BottomDockWidgetArea, self._console_dock)
        self._toolbar.messages_toggled.connect(self._console_dock.setVisible)
        self._console_dock.visibilityChanged.connect(
            lambda v: self._toolbar.set_panel_checked("messages", v))

        self._mission_panel = MissionPanel()
        self._mission_dock = QDockWidget("Missions", self)
        self._mission_dock.setObjectName("mission_dock")
        self._mission_dock.setWidget(self._mission_panel)
        self._mission_dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self._mission_dock.hide()
        self.addDockWidget(Qt.RightDockWidgetArea, self._mission_dock)
        self._toolbar.missions_toggled.connect(self._mission_dock.setVisible)
        self._mission_dock.visibilityChanged.connect(
            lambda v: self._toolbar.set_panel_checked("missions", v))

        self._tuning_panel = TuningPanel()
        self._tuning_dock = QDockWidget("Basic Tuning", self)
        self._tuning_dock.setObjectName("tuning_dock")
        self._tuning_dock.setWidget(self._tuning_panel)
        self._tuning_dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self._tuning_dock.hide()
        self.addDockWidget(Qt.RightDockWidgetArea, self._tuning_dock)
        self._toolbar.tuning_toggled.connect(self._tuning_dock.setVisible)
        self._tuning_dock.visibilityChanged.connect(self._on_tuning_dock_visibility)

        self._actions_panel = ActionsPanel()
        self._actions_dock = QDockWidget("Actions", self)
        self._actions_dock.setObjectName("actions_dock")
        self._actions_dock.setWidget(self._actions_panel)
        self._actions_dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self._actions_dock.hide()
        self.addDockWidget(Qt.RightDockWidgetArea, self._actions_dock)
        self._toolbar.actions_toggled.connect(self._actions_dock.setVisible)
        self._actions_dock.visibilityChanged.connect(
            lambda v: self._toolbar.set_panel_checked("actions", v))

        self._joystick_manager = JoystickManager()
        self._joystick_panel = JoystickPanel()
        self._joystick_dock = QDockWidget("Joystick", self)
        self._joystick_dock.setObjectName("joystick_dock")
        self._joystick_dock.setWidget(self._joystick_panel)
        self._joystick_dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self._joystick_dock.hide()
        self.addDockWidget(Qt.RightDockWidgetArea, self._joystick_dock)
        self._toolbar.joystick_toggled.connect(self._joystick_dock.setVisible)
        self._joystick_dock.visibilityChanged.connect(
            lambda v: self._toolbar.set_panel_checked("joystick", v))
        self._joystick_manager.state_changed.connect(self._joystick_panel.update_state)
        self._joystick_panel.rc_override_requested.connect(self._on_rc_override)
        self._joystick_manager.start()

        self._serial_console = SerialConsolePanel()
        self._serial_console_mgr = SerialConsoleManager()
        self._serial_console_dock = QDockWidget("Console", self)
        self._serial_console_dock.setObjectName("serial_console_dock")
        self._serial_console_dock.setWidget(self._serial_console)
        self._serial_console_dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self._serial_console_dock.hide()
        self.addDockWidget(Qt.BottomDockWidgetArea, self._serial_console_dock)
        self._toolbar.console_toggled.connect(self._serial_console_dock.setVisible)
        self._serial_console_dock.visibilityChanged.connect(
            lambda v: self._toolbar.set_panel_checked("console", v))
        self._toolbar.camera_toggled.connect(self._video_dock.setVisible)
        self._video_dock.visibilityChanged.connect(
            lambda v: self._toolbar.set_panel_checked("camera", v))
        self._serial_console.send_requested.connect(self._on_console_send)
        self._serial_console_mgr.data_received.connect(self._serial_console.append_received)

    def _get_serial_port(self) -> str | None:
        port = None
        if self._mavlink_connection and self._mavlink_connection.connected:
            port = self._mavlink_connection.endpoint
        if port and port.startswith("/dev/"):
            return port
        ports = _AutoConnectWorker._detect_ports()
        return ports[0] if ports else None

    def _on_firmware(self) -> None:
        port = self._get_serial_port()
        if not port:
            QMessageBox.warning(
                self, "Firmware Installer",
                "No serial port detected.\n"
                "Connect the FCU and try again."
            )
            return

        if self._connected:
            reply = QMessageBox.question(
                self, "Firmware Installer",
                "Flashing firmware requires disconnecting from the FCU.\n"
                "Send reboot-to-bootloader command before disconnecting?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.No,
            )
            if reply == QMessageBox.Cancel:
                return
            if reply == QMessageBox.Yes and self._command_sender:
                self._command_sender.reboot_to_bootloader()
                time.sleep(1.0)
            self._on_disconnect()

        dialog = FirmwareFlashDialog(port, self)
        dialog.exec()

    def closeEvent(self, event):
        self._connected = False
        self._hb_timer.stop()
        if self._tlog_writer:
            self._tlog_writer.stop()
        if self._mavlink_connection:
            self._mavlink_connection.disconnect()
        if self._worker and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(2000)
        self._joystick_manager.stop()
        event.accept()

    def _on_connect(self):
        self._worker = _AutoConnectWorker()
        self._worker.trying.connect(self._on_trying)
        self._worker.success.connect(self._on_connection_success)
        self._worker.failed.connect(self._on_connection_failed)
        self._worker.start()

    def _on_trying(self, message: str):
        self.statusBar().showMessage(message)

    def _on_connection_success(self):
        self._mavlink_connection = self._worker.connection
        self._command_sender = CommandSender(self._mavlink_connection)
        self._connected = True
        self._toolbar.set_connected(True)
        self._status_bar.set_connected(True)
        self._toolbar.set_armed(False)
        self._prev_armed = False

        self._bridge = _TelemetryBridge()
        self._bridge.vehicle_updated.connect(self._on_vehicle_updated)
        self._mavlink_connection.register_callback(self._bridge.process)

        self._console_bridge = ConsoleBridge()
        self._console_bridge.message_received.connect(self._message_console.append_message)
        self._mavlink_connection.register_callback(self._console_bridge.process)
        self._message_console.append_message("GCS", "Connected to FCU", 6)

        self._serial_console_mgr.set_connection(self._mavlink_connection)
        self._serial_console_mgr.start()
        self._mavlink_connection.register_callback(self._serial_console_mgr.process)

        self._tlog_writer = TLogWriter()
        path = self._tlog_writer.start()
        self._mavlink_connection.register_callback(self._tlog_writer.write)
        self._status_bar.set_logging(True, path)

        self.statusBar().showMessage("Connected", 3000)
        self._hb_timer.start()

        self._param_client = ParamClient(self._mavlink_connection)
        self._param_client.batch_received.connect(self._on_param_batch)
        self._param_client.sync_finished.connect(self._on_param_sync_finished)
        self._param_panel.set_param_requested.connect(self._on_param_set)
        self._param_panel.refresh_requested.connect(self._on_param_refresh)
        self._mavlink_connection.register_callback(self._param_client.process)

        self._mission_client = MissionClient(self._mavlink_connection)
        self._mission_client.download_completed.connect(self._on_mission_downloaded)
        self._mission_client.download_failed.connect(self._on_mission_failed)
        self._mission_client.upload_completed.connect(self._on_mission_uploaded)
        self._mission_client.upload_failed.connect(self._on_mission_failed)
        self._mission_client.clear_completed.connect(self._on_mission_cleared)
        self._mission_client.clear_failed.connect(self._on_mission_failed)
        self._mavlink_connection.register_callback(self._mission_client.process)
        self._mission_panel.download_requested.connect(self._mission_client.download)
        self._mission_panel.upload_requested.connect(self._mission_client.upload)
        self._mission_panel.clear_requested.connect(self._mission_client.clear)

        self._tuning_panel.param_changed.connect(self._on_param_set)
        self._tuning_panel.request_refresh.connect(self._on_tuning_refresh)
        self._tuning_panel.servo_output_requested.connect(self._on_servo_output)

        self._actions_panel.action_requested.connect(self._on_action)
        self._vehicle_type_set = False

    def _on_connection_failed(self, error: str):
        self._connected = False
        self._hb_timer.stop()
        self._toolbar.set_connected(False)
        self._status_bar.set_connected(False)
        self._message_console.append_message("GCS", f"Connection failed: {error}", 3)
        QMessageBox.warning(self, "Connection Failed", error)

    def _check_heartbeat(self):
        if not self._connected or not self._mavlink_connection:
            return
        age = time.time() - self._mavlink_connection.last_heartbeat_time
        if age > HB_LOST_DISCONNECT:
            self.statusBar().showMessage("HEARTBEAT LOST — auto-disconnected", 5000)
            self._message_console.append_message("GCS", "HEARTBEAT LOST — auto-disconnected", 3)
            self._on_disconnect()
        if age > HB_LOST_WARN:
            self._status_bar.set_heartbeat_warning(True)
            self._telemetry_panel.set_link_quality(False, age)
            self._message_console.append_message(
                "GCS", f"Heartbeat lost for {age:.0f}s", 4
            )
        else:
            self._status_bar.set_heartbeat_warning(False)
            self._telemetry_panel.set_link_quality(True)

    def _on_param_batch(self, batch: list) -> None:
        for name, value, ptype, index, count in batch:
            self._param_panel.add_param(name, value, ptype)
            self._tuning_panel.update_param_value(name, value)

    def _detect_vehicle_from_params(self, params: dict) -> str | int | None:
        names = set(params.keys())
        if "SERVO9_FUNCTION" in names and "SERVO10_FUNCTION" in names:
            return "Antenna Tracker", 6
        if "RATE_ROLL_P" in names or "RATE_PITCH_P" in names:
            return "Quadrotor", 2
        if "RLL_RATE_P" in names or "PTCH_RATE_P" in names:
            return "Fixed Wing", 1
        return None

    def _on_param_sync_finished(self) -> None:
        self._param_panel.sync_finished()
        count = self._param_client.param_count
        all_params = self._param_client.all_params

        detected = self._detect_vehicle_from_params(all_params)
        if detected:
            vtype, mtype = detected
            if not self._vehicle_type_set or vtype != self._tuning_panel.vehicle_label:
                self._vehicle_type_set = True
                self._tuning_panel.set_preset(vtype, mtype)
                self.statusBar().showMessage(
                    f"Detected: {vtype} (from params)", 5000
                )
                self._message_console.append_message(
                    "GCS", f"Detected vehicle: {vtype} (from params)", 5
                )

        if self._tuning_panel.isVisible():
            self._tuning_panel.populate_params(all_params)
        self.statusBar().showMessage(f"Loaded {count} parameters\u2014tuning ready", 3000)

    def _on_param_refresh(self) -> None:
        self._param_panel.sync_started()
        self._param_client.request_list()

    def _on_param_dock_visibility(self, visible: bool) -> None:
        self._toolbar.set_panel_checked("params", visible)
        if visible and self._param_client and self._param_client.param_count == 0:
            self._param_panel.sync_started()
            self._param_client.request_list()

    def _on_tuning_dock_visibility(self, visible: bool) -> None:
        self._toolbar.set_panel_checked("tuning", visible)
        if visible and self._param_client:
            if self._param_client.param_count > 0:
                self._tuning_panel.populate_params(self._param_client.all_params)
            else:
                self._on_tuning_refresh()

    def _on_tuning_refresh(self) -> None:
        if not self._param_client:
            return
        self._tuning_panel.clear_graph()
        self._param_panel.sync_started()
        self._param_client.request_list()

    def _on_param_set(self, name: str, value: float, ptype: int) -> None:
        if self._param_client:
            self._param_client.set_param(name, value, ptype)
            self.statusBar().showMessage(f"Set {name} = {value}", 3000)

    def _on_rc_override(self, channels: list[int]) -> None:
        if self._command_sender:
            self._command_sender.send_rc_channels_override(channels)

    def _on_console_send(self, text: str) -> None:
        self._serial_console_mgr.send(text)

    def _on_action(self, action: str) -> None:
        cmd = {
            "Reboot": lambda: self._command_sender.reboot(),
            "Reboot to Bootloader": lambda: self._command_sender.reboot_to_bootloader(),
            "Calibrate Gyro": lambda: self._command_sender.calibrate_gyro(),
            "Calibrate Accel": lambda: self._command_sender.calibrate_accel(),
            "Calibrate Compass": lambda: self._command_sender.calibrate_compass(),
            "Calibrate Radio": lambda: self._command_sender.calibrate_radio(),
            "Set Home Here": lambda: self._command_sender.set_home_here(),
        }
        fn = cmd.get(action)
        if fn:
            fn()
            self._message_console.append_message("GCS", f"{action} command sent", 5)
            self.statusBar().showMessage(f"{action} sent", 3000)

    def _on_vehicle_updated(self, vehicle):
        if not self._connected:
            return
        if vehicle.armed != self._prev_armed:
            self._prev_armed = vehicle.armed
            self.statusBar().showMessage(
                "FCU ARMED" if vehicle.armed else "FCU DISARMED", 3000
            )
            self._message_console.append_message(
                "GCS", "FCU ARMED" if vehicle.armed else "FCU DISARMED",
                4 if vehicle.armed else 5,
            )
        if not self._vehicle_type_set and vehicle.vehicle_type_str:
            self._vehicle_type_set = True
            self._tuning_panel.set_preset(vehicle.vehicle_type_str, vehicle.vehicle_type)
            self.statusBar().showMessage(
                f"Detected: {vehicle.vehicle_type_str} (MAV_TYPE {vehicle.vehicle_type})", 5000
            )
            self._message_console.append_message(
                "GCS",
                f"Detected vehicle: {vehicle.vehicle_type_str} (MAV_TYPE={vehicle.vehicle_type})",
                5,
            )

        self._status_bar.update_from_vehicle(vehicle)
        self._toolbar.set_armed(vehicle.armed)
        self._toolbar.set_mode(vehicle.mode)
        self._map_widget.update_vehicle_position(
            vehicle.position.lat,
            vehicle.position.lon,
            vehicle.heading,
        )
        self._map_widget.update_stats(
            vehicle.groundspeed, vehicle.position.alt, vehicle.heading,
        )
        self._hud.update_data(
            vehicle.attitude.roll,
            vehicle.attitude.pitch,
            vehicle.heading,
            vehicle.position.alt,
            vehicle.groundspeed,
        )
        self._telemetry_panel.update_from_vehicle(vehicle)
        self._telemetry_panel.set_link_quality(True)
        self._tuning_panel.add_attitude(
            vehicle.attitude.roll,
            vehicle.attitude.pitch,
            vehicle.attitude.yaw,
        )
        self._flight_path.append([vehicle.position.lat, vehicle.position.lon])
        self._flight_path_counter += 1
        if self._flight_path_counter % 10 == 0:
            self._map_widget.draw_flight_path(self._flight_path)

    def _on_mission_downloaded(self, waypoints) -> None:
        self._mission_panel.set_waypoints(waypoints)
        self._map_widget.draw_waypoints([wp.to_dict() for wp in waypoints])
        self._message_console.append_message("GCS", f"Downloaded {len(waypoints)} waypoints", 5)

    def _on_mission_uploaded(self) -> None:
        self._message_console.append_message("GCS", "Mission uploaded", 5)

    def _on_mission_cleared(self) -> None:
        self._mission_panel.set_waypoints([])
        self._map_widget.clear_waypoints()
        self._message_console.append_message("GCS", "Mission cleared", 5)

    def _on_mission_failed(self, error: str) -> None:
        self._mission_panel.set_status(f"Failed: {error}")
        self._message_console.append_message("GCS", f"Mission error: {error}", 3)

    def _on_disconnect(self):
        self._connected = False
        self._mission_dock.hide()
        self._param_client = None
        self._mission_client = None
        self._param_dock.hide()
        self._tuning_dock.hide()
        self._tuning_panel.clear_graph()
        self._actions_dock.hide()
        self._serial_console_dock.hide()
        self._serial_console_mgr.stop()
        self._joystick_dock.hide()
        self._vehicle_type_set = False
        self._flight_path.clear()
        self._flight_path_counter = 0
        if self._tlog_writer:
            self._tlog_writer.stop()
            self._tlog_writer = None
        if self._mavlink_connection:
            self._mavlink_connection.disconnect()
            self._mavlink_connection = None
        self._message_console.append_message("GCS", "Disconnected from FCU", 5)
        self._command_sender = None
        self._toolbar.set_connected(False)
        self._status_bar.set_logging(False)
        self._status_bar.set_connected(False)
        self._hb_timer.stop()
        self.statusBar().showMessage("Disconnected", 3000)

    def _on_arm(self):
        if not self._command_sender:
            return
        reply = QMessageBox.question(
            self, "Arm Vehicle",
            "Are you sure you want to ARM the vehicle?\n\n"
            "Ensure the area is clear and all safety checks pass.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._command_sender.arm_disarm(True)
            self.statusBar().showMessage("Arm command sent", 2000)
            self._message_console.append_message("GCS", "Arm command sent", 5)
        else:
            self._toolbar.set_armed(False)

    def _on_disarm(self):
        if self._command_sender:
            self._command_sender.arm_disarm(False)
            self.statusBar().showMessage("Disarm command sent", 2000)
            self._message_console.append_message("GCS", "Disarm command sent", 5)

    def _on_takeoff(self, alt: float):
        if self._command_sender:
            self._command_sender.takeoff(alt)
            self.statusBar().showMessage(f"Takeoff to {alt}m command sent", 2000)
            self._message_console.append_message("GCS", f"Takeoff to {alt}m command sent", 5)

    def _on_rtl(self):
        if self._command_sender:
            self._command_sender.rtl()
            self.statusBar().showMessage("RTL command sent", 2000)
            self._message_console.append_message("GCS", "RTL command sent", 5)

    def _on_mode_change(self, mode: str):
        if self._command_sender:
            self._command_sender.set_mode(mode)
            self.statusBar().showMessage(f"Mode change to {mode} sent", 2000)

    def _on_emergency_stop(self):
        if not self._command_sender:
            return
        reply = QMessageBox.critical(
            self, "Emergency Stop",
            "Are you sure you want to terminate the flight?\n\n"
            "This will immediately stop all motors!",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._command_sender.emergency_stop()
            self.statusBar().showMessage("EMERGENCY STOP sent", 5000)
            self._message_console.append_message("GCS", "EMERGENCY STOP sent", 3)

    def _on_servo_output(self, channel: int, pwm: int) -> None:
        if self._command_sender:
            self._command_sender.set_servo(channel, pwm)
            self.statusBar().showMessage(f"Servo {channel} = {pwm}\u00b5s", 2000)
