from PySide6.QtCore import QObject, Signal, QTimer

from domain.models.mission import Waypoint
from infrastructure.mavlink.mavlink_connection import MAVLinkConnection


MISSION_TIMEOUT_MS = 15000


class MissionClient(QObject):
    download_completed = Signal(object)
    download_failed = Signal(str)
    upload_completed = Signal()
    upload_failed = Signal(str)
    clear_completed = Signal()
    clear_failed = Signal(str)

    _ST_DOWNLOAD = "download"
    _ST_UPLOAD_WAIT = "upload_wait"
    _ST_UPLOAD_SEND = "upload_send"
    _ST_CLEAR = "clear"

    def __init__(self, connection: MAVLinkConnection, parent=None):
        super().__init__(parent)
        self._connection = connection
        self._state: str | None = None
        self._waypoints: list[Waypoint] = []
        self._pending_seq = 0
        self._total = 0
        self._timeout = QTimer(self)
        self._timeout.setSingleShot(True)
        self._timeout.timeout.connect(self._on_timeout)

    @property
    def _sys(self) -> int:
        return self._connection.master.target_system

    @property
    def _comp(self) -> int:
        return self._connection.master.target_component

    def _send(self, msg) -> None:
        self._connection.master.mav.send(msg)

    def download(self) -> None:
        self._waypoints.clear()
        self._pending_seq = 0
        self._total = 0
        self._state = self._ST_DOWNLOAD
        self._connection.master.mav.mission_request_list_send(self._sys, self._comp)
        self._timeout.start(MISSION_TIMEOUT_MS)

    def upload(self, waypoints: list[Waypoint]) -> None:
        self._waypoints = list(waypoints)
        self._pending_seq = 0
        self._total = len(waypoints)
        self._state = self._ST_UPLOAD_WAIT
        self._connection.master.mav.mission_count_send(self._sys, self._comp, self._total)
        self._timeout.start(MISSION_TIMEOUT_MS)

    def clear(self) -> None:
        self._waypoints.clear()
        self._state = self._ST_CLEAR
        self._connection.master.mav.mission_clear_all_send(self._sys, self._comp)
        self._timeout.start(MISSION_TIMEOUT_MS)

    def process(self, msg) -> None:
        if self._state is None:
            return
        t = msg.get_type()
        if self._state == self._ST_DOWNLOAD:
            self._process_download(t, msg)
        elif self._state in (self._ST_UPLOAD_WAIT, self._ST_UPLOAD_SEND):
            self._process_upload(t, msg)
        elif self._state == self._ST_CLEAR:
            self._process_clear(t, msg)

    def _process_download(self, t: str, msg) -> None:
        if t == "MISSION_COUNT":
            self._total = msg.count
            if self._total == 0:
                self._finish_download()
                return
            self._request_seq(0)
        elif t == "MISSION_ITEM_INT":
            wp = Waypoint.from_mavlink(msg)
            self._waypoints.append(wp)
            self._pending_seq += 1
            if self._pending_seq >= self._total:
                self._finish_download()
            else:
                self._request_seq(self._pending_seq)

    def _finish_download(self) -> None:
        self._timeout.stop()
        self._state = None
        self.download_completed.emit(self._waypoints)

    def _request_seq(self, seq: int) -> None:
        self._connection.master.mav.mission_request_int_send(self._sys, self._comp, seq)

    def _process_upload(self, t: str, msg) -> None:
        if t == "MISSION_REQUEST_INT":
            seq = msg.seq
            self._state = self._ST_UPLOAD_SEND
            self._send_item(seq)
            if seq + 1 >= self._total:
                self._state = self._ST_UPLOAD_WAIT
        elif t == "MISSION_ACK":
            self._timeout.stop()
            self._state = None
            if msg.type == 0:
                self.upload_completed.emit()
            else:
                self.upload_failed.emit(f"MISSION_ACK error={msg.type}")

    def _send_item(self, seq: int) -> None:
        wp = self._waypoints[seq]
        self._connection.master.mav.mission_item_int_send(
            self._sys, self._comp,
            seq, wp.frame, wp.command,
            wp.current, wp.autocontinue,
            wp.param1, wp.param2, wp.param3, wp.param4,
            int(wp.lat * 1e7), int(wp.lon * 1e7), wp.alt,
            wp.frame,
        )

    def _process_clear(self, t: str, msg) -> None:
        if t == "MISSION_ACK":
            self._timeout.stop()
            self._state = None
            if msg.type == 0:
                self.clear_completed.emit()
            else:
                self.clear_failed.emit(f"MISSION_ACK error={msg.type}")

    def _on_timeout(self) -> None:
        self._state = None
        self.download_failed.emit("Mission operation timed out")
