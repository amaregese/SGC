import struct

from PySide6.QtCore import QObject, Signal, QTimer


MAX_DATA = 70


class SerialConsoleManager(QObject):
    data_received = Signal(bytes)
    connected_changed = Signal(bool)

    def __init__(self, connection=None, parent=None):
        super().__init__(parent)
        self._connection = connection
        self._buf = bytearray()
        self._watchdog = QTimer(self)
        self._watchdog.setInterval(3000)
        self._watchdog.timeout.connect(self._ping)

    def set_connection(self, connection) -> None:
        self._connection = connection

    def start(self) -> None:
        self._watchdog.start()

    def stop(self) -> None:
        self._watchdog.stop()
        self._buf.clear()

    def send(self, text: str) -> None:
        if not self._connection or not self._connection.master:
            return
        data = text.encode("utf-8", errors="replace")
        master = self._connection.master
        sysid = master.target_system or 1
        compid = master.target_component or 1
        for i in range(0, len(data), MAX_DATA):
            chunk = data[i:i + MAX_DATA]
            try:
                master.mav.serial_control_send(
                    sysid, compid,
                    0,        # device (0 = console/SERIAL0)
                    0,        # flags: none (reply will come naturally)
                    0,        # timeout ms
                    0,        # baudrate (keep current)
                    chunk,
                )
            except Exception:
                pass

    def _ping(self) -> None:
        """Keep the console session alive with a newline ping."""
        self.send("\n")

    def process(self, msg) -> None:
        if msg.get_type() != "SERIAL_CONTROL":
            return
        if msg.device != 0:
            return
        raw = msg.data
        if isinstance(raw, bytes):
            raw = raw.rstrip(b"\x00")
        else:
            raw = bytes(raw).rstrip(b"\x00")
        if raw:
            self.data_received.emit(raw)
