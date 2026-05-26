import threading
import time

from PySide6.QtCore import QObject, Signal


_AXIS_NAMES = {
    0: "LX", 1: "LY", 2: "RX", 3: "RY",
    4: "L2", 5: "R2",
}
_BUTTON_COUNT = 16


class JoystickManager(QObject):
    state_changed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._device = None
        self._thread: threading.Thread | None = None
        self._running = False

        self.axes: dict[int, float] = {}
        self.buttons: dict[int, bool] = {}
        self.connected = False
        self.device_name: str = ""

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._device:
            try:
                self._device.close()
            except Exception:
                pass
            self._device = None
        self._thread = None
        self.connected = False
        self.axes.clear()
        self.buttons.clear()
        self.state_changed.emit(self._snapshot())

    def _snapshot(self) -> dict:
        return {
            "connected": self.connected,
            "device_name": self.device_name,
            "axes": dict(self.axes),
            "buttons": dict(self.buttons),
        }

    def _poll(self) -> None:
        import inputs

        while self._running:
            if self._device is None:
                try:
                    devices = inputs.devices.gamepads
                    if devices:
                        self._device = devices[0]
                        self.device_name = self._device.name or "Gamepad"
                        self.connected = True
                        self.axes.clear()
                        self.buttons.clear()
                        self.state_changed.emit(self._snapshot())
                except Exception:
                    pass
                if self._device is None:
                    time.sleep(1.0)
                    continue

            try:
                events = self._device.read()
            except Exception:
                self._device = None
                self.connected = False
                self.state_changed.emit(self._snapshot())
                continue

            changed = False
            for e in events:
                if e.ev_type == "Absolute":
                    self.axes[e.code] = _normalize_axis(e.code, e.state)
                    changed = True
                elif e.ev_type == "Key":
                    idx = _button_index(e.code)
                    if 0 <= idx < _BUTTON_COUNT:
                        self.buttons[idx] = e.state == 1
                        changed = True

            if changed:
                self.state_changed.emit(self._snapshot())

            if not self._running:
                break


def _normalize_axis(code: str, raw: int) -> float:
    ABS_MAX = 32767
    if code.startswith("ABS_HAT"):
        return raw  # -1, 0, or 1
    if code in ("ABS_Z", "ABS_RZ", "ABS_BRAKE", "ABS_GAS"):
        return raw / ABS_MAX
    return raw / ABS_MAX


def _button_index(code: str) -> int:
    known = {
        "BTN_A": 0, "BTN_B": 1, "BTN_X": 2, "BTN_Y": 3,
        "BTN_TL": 4, "BTN_TR": 5, "BTN_SELECT": 6, "BTN_START": 7,
        "BTN_THUMBL": 8, "BTN_THUMBR": 9,
        "BTN_TRIGGER": 0, "BTN_THUMB": 1, "BTN_THUMB2": 2,
        "BTN_TOP": 3, "BTN_TOP2": 4, "BTN_PINKIE": 5,
        "BTN_BASE": 6, "BTN_BASE2": 7, "BTN_BASE3": 8, "BTN_BASE4": 9,
        "BTN_DPAD_UP": 10, "BTN_DPAD_DOWN": 11,
        "BTN_DPAD_LEFT": 12, "BTN_DPAD_RIGHT": 13,
    }
    if code.startswith("BTN_") and code not in known:
        try:
            n = int(code[4:])
            return n if n < _BUTTON_COUNT else 0
        except ValueError:
            pass
    return known.get(code, -1)
