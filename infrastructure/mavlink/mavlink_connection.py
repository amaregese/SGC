import time
from enum import Enum
from threading import Thread, Event
from queue import Queue, Empty
from collections.abc import Callable

from pymavlink import mavutil

from infrastructure.mavlink.message_handler import MAVLinkMessage


HB_LOST_WARN = 5.0
HB_LOST_DISCONNECT = 12.0


class ConnectionType(Enum):
    SERIAL = "serial"
    UDP = "udp"
    TCP = "tcp"


class ConnectionError(Exception):
    pass


class MAVLinkConnection:
    def __init__(self):
        self._master: mavutil.mavudp | mavutil.mavserial | mavutil.mavtcp | None = None
        self._receive_thread: Thread | None = None
        self._stop_event = Event()
        self._message_queue: Queue = Queue()
        self._callbacks: list[Callable[[MAVLinkMessage], None]] = []
        self._connected = False
        self._connection_type: ConnectionType | None = None
        self._endpoint: str = ""
        self._last_msg_time = 0.0
        self._last_heartbeat_time = 0.0

    def connect(self, conn_type: ConnectionType, endpoint: str, baud: int = 115200, timeout: float = 5.0) -> None:
        self._connection_type = conn_type
        self._endpoint = endpoint

        try:
            if conn_type == ConnectionType.SERIAL:
                self._master = mavutil.mavserial(endpoint, baud=baud)
            elif conn_type == ConnectionType.UDP:
                self._master = mavutil.mavudp(endpoint, input=False)
            elif conn_type == ConnectionType.TCP:
                self._master = mavutil.mavtcp(endpoint)
            else:
                raise ConnectionError(f"Unknown connection type: {conn_type}")
        except Exception as e:
            raise ConnectionError(f"Failed to open connection: {e}")

        heartbeat = self._master.wait_heartbeat(timeout=timeout)
        if heartbeat is None:
            self._master.close()
            self._master = None
            raise ConnectionError(
                f"No HEARTBEAT received from {endpoint} after {timeout}s timeout.\n"
                "Check that the FCU is powered and connected."
            )

        now = time.time()
        self._last_msg_time = now
        self._last_heartbeat_time = now
        self._connected = True
        self._stop_event.clear()
        self._receive_thread = Thread(target=self._receive_loop, daemon=True)
        self._receive_thread.start()

    def disconnect(self) -> None:
        self._stop_event.set()
        self._connected = False
        if self._master:
            self._master.close()
            self._master = None

    def send(self, msg) -> None:
        if self._master:
            self._master.mav.send(msg)

    def register_callback(self, callback: Callable[[MAVLinkMessage], None]) -> None:
        self._callbacks.append(callback)

    def _receive_loop(self) -> None:
        while not self._stop_event.is_set():
            if self._master is None:
                break
            msg = self._master.recv_match(blocking=False, timeout=0.1)
            if msg:
                now = time.time()
                self._last_msg_time = now
                if msg.get_type() == "HEARTBEAT":
                    self._last_heartbeat_time = now
                mav_msg = MAVLinkMessage(msg)
                self._message_queue.put(mav_msg)
                for cb in self._callbacks:
                    cb(mav_msg)

    def get_message(self, timeout: float = 0.1) -> MAVLinkMessage | None:
        try:
            return self._message_queue.get(timeout=timeout)
        except Empty:
            return None

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def master(self):
        return self._master

    @property
    def connection_type(self) -> ConnectionType | None:
        return self._connection_type

    @property
    def endpoint(self) -> str:
        return self._endpoint

    @property
    def last_heartbeat_time(self) -> float:
        return self._last_heartbeat_time

    @property
    def last_msg_time(self) -> float:
        return self._last_msg_time
