import os
import time
import struct
from datetime import datetime


class TLogWriter:
    def __init__(self, log_dir: str = "logs"):
        self._log_dir = log_dir
        self._file = None
        self._path: str | None = None
        self._count = 0

    def start(self) -> str:
        os.makedirs(self._log_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._path = os.path.join(self._log_dir, f"sgc_{ts}.tlog")
        self._file = open(self._path, "wb")
        self._count = 0
        return self._path

    def write(self, msg) -> None:
        if self._file is None:
            return
        ts = int(time.time() * 1_000_000)
        raw = msg.get_msgbuf()
        header = struct.pack("<QII", ts, len(raw), 0)
        self._file.write(header + raw)
        self._count += 1
        if self._count % 100 == 0:
            self._file.flush()

    def stop(self) -> None:
        if self._file:
            self._file.flush()
            self._file.close()
            self._file = None

    @property
    def is_active(self) -> bool:
        return self._file is not None

    @property
    def path(self) -> str | None:
        return self._path

    @property
    def message_count(self) -> int:
        return self._count
