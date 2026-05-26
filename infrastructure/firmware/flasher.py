import io
import json
import base64
import struct
import time
from threading import Event

import serial
from xmodem import XMODEM

from PySide6.QtCore import QObject, Signal


_BOOTLOADER_BAUD = 115200
_SYNC_TIMEOUT = 5.0
_XMODEM_TIMEOUT = 30.0


class FirmwareInfo:
    def __init__(self, data: dict):
        self.vehicle: str = data.get("vehicle", "Unknown")
        self.version: str = data.get("version", "?")
        self.platform: str = data.get("platform", "?")
        self.git_hash: str = data.get("git_hash", "")
        self.firmware_bytes: bytes = b""

        fw_data = data.get("firmware_data")
        if fw_data:
            self.firmware_bytes = base64.b64decode(fw_data)

    @property
    def is_valid(self) -> bool:
        return len(self.firmware_bytes) > 0

    @property
    def size_kb(self) -> float:
        return len(self.firmware_bytes) / 1024

    @classmethod
    def from_file(cls, path: str) -> "FirmwareInfo":
        with open(path, "r") as f:
            data = json.load(f)
        return cls(data)


class FirmwareFlasher(QObject):
    log_message = Signal(str)
    progress = Signal(int)
    finished = Signal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cancel = Event()

    def cancel(self) -> None:
        self._cancel.set()

    def flash(self, port: str, firmware_path: str) -> None:
        self._cancel.clear()
        try:
            info = FirmwareInfo.from_file(firmware_path)
            if not info.is_valid:
                self.finished.emit(False, "No firmware data in file")
                return

            self.log_message.emit(
                f"Firmware: {info.vehicle} v{info.version} "
                f"({info.size_kb:.0f} KB)"
            )
            self._do_xmodem(port, info.firmware_bytes)
        except Exception as e:
            self.finished.emit(False, str(e))

    def _do_xmodem(self, port: str, data: bytes) -> None:
        self.log_message.emit(f"Opening {port} at {_BOOTLOADER_BAUD} baud...")
        ser = serial.Serial(
            port=port,
            baudrate=_BOOTLOADER_BAUD,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
        )

        self.log_message.emit("Syncing with bootloader...")
        self._sync_bootloader(ser)

        total = len(data)
        sent = [0]

        def getc(size, timeout=_XMODEM_TIMEOUT):
            if self._cancel.is_set():
                return b""
            return ser.read(size)

        def putc(data_out, timeout=_XMODEM_TIMEOUT):
            ser.write(data_out)

        def on_progress(total_packets, success_count, error_count):
            pct = min(100, int(success_count * 128 * 100 / total))
            if pct != sent[0]:
                sent[0] = pct
                self.progress.emit(pct)

        modem = XMODEM(getc, putc)
        self.log_message.emit("Uploading firmware (XModem)...")
        stream = io.BytesIO(data)
        success = modem.send(stream, callback=on_progress, retry=10)

        ser.close()

        if self._cancel.is_set():
            self.finished.emit(False, "Cancelled")
            return

        if success:
            self.progress.emit(100)
            self.log_message.emit("Firmware upload complete!")
            self.log_message.emit("Board will reboot with new firmware.")
            self.finished.emit(True, "Firmware flashed successfully")
        else:
            self.finished.emit(False, "XModem upload failed")

    def _sync_bootloader(self, ser: serial.Serial) -> None:
        start = time.time()
        ser.write(b"\x00" * 50)
        while time.time() - start < _SYNC_TIMEOUT:
            if self._cancel.is_set():
                raise RuntimeError("Cancelled")
            data = ser.read(100)
            if data:
                self.log_message.emit(f"Bootloader reply: {data[:20]}")
            ser.write(b"\x00" * 10)
        ser.reset_input_buffer()
        ser.reset_output_buffer()
