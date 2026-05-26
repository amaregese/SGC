from collections import deque
import time

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QFontMetrics


_WINDOW_SECS = 10.0
_REFRESH_MS = 50
_TRACE_COLORS = {
    "roll": QColor("#e74c3c"),
    "pitch": QColor("#2ecc71"),
    "yaw": QColor("#3498db"),
}
_BG = QColor(18, 18, 30)
_GRID = QColor(50, 50, 70)
_TEXT = QColor(180, 180, 200)


class TuningGraph(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(180)
        self._data: dict[str, deque] = {
            "roll": deque(maxlen=2000),
            "pitch": deque(maxlen=2000),
            "yaw": deque(maxlen=2000),
            "t": deque(maxlen=2000),
        }
        self._start_time = time.monotonic()
        self._timer = QTimer(self)
        self._timer.setInterval(_REFRESH_MS)
        self._timer.timeout.connect(self.update)
        self._timer.start()

    def add_attitude(self, roll: float, pitch: float, yaw: float) -> None:
        now = time.monotonic() - self._start_time
        self._data["t"].append(now)
        self._data["roll"].append(roll)
        self._data["pitch"].append(pitch)
        self._data["yaw"].append(yaw)

    def clear_data(self) -> None:
        for key in self._data:
            self._data[key].clear()
        self._start_time = time.monotonic()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        margin = 8
        plot_left = 55
        plot_right = w - margin
        plot_top = 20
        plot_bottom = h - margin
        pw = plot_right - plot_left
        ph = plot_bottom - plot_top

        painter.fillRect(self.rect(), _BG)

        if not self._data["t"] or pw < 10 or ph < 10:
            painter.setPen(_TEXT)
            painter.drawText(self.rect(), Qt.AlignCenter, "Waiting for attitude data...")
            return

        t_now = self._data["t"][-1]
        t_min = t_now - _WINDOW_SECS

        y_min = -180.0
        y_max = 180.0

        def to_screen(t_val, y_val):
            x = plot_left + int((t_val - t_min) / _WINDOW_SECS * pw)
            y = plot_top + int((y_max - y_val) / (y_max - y_min) * ph)
            return x, y

        font = QFont("monospace", 9)
        painter.setFont(font)
        fm = QFontMetrics(font)

        painter.setPen(_GRID)
        for deg in range(-180, 181, 45):
            _, y = to_screen(t_min, deg)
            painter.drawLine(plot_left, y, plot_right, y)
            label = f"{deg}\u00b0"
            painter.setPen(_TEXT)
            painter.drawText(0, y - fm.height() // 2 + fm.ascent(), label)
            painter.setPen(_GRID)

        zero_x = plot_right
        for sec_ago in range(0, int(_WINDOW_SECS) + 1, 2):
            x, _ = to_screen(t_now - sec_ago, 0)
            painter.drawLine(x, plot_top, x, plot_bottom)
            label = f"-{sec_ago}s" if sec_ago > 0 else "now"
            tw = fm.horizontalAdvance(label)
            painter.setPen(_TEXT)
            painter.drawText(x - tw // 2, h - 2, label)
            painter.setPen(_GRID)

        for key in ("roll", "pitch", "yaw"):
            color = _TRACE_COLORS[key]
            pen = QPen(color, 1.5)
            painter.setPen(pen)
            points = []
            for i in range(len(self._data["t"])):
                t_val = self._data["t"][i]
                if t_val < t_min:
                    continue
                y_val = self._data[key][i]
                x, y = to_screen(t_val, y_val)
                y = max(plot_top, min(plot_bottom, y))
                points.append((x, y))
            if len(points) >= 2:
                for i in range(1, len(points)):
                    painter.drawLine(points[i - 1][0], points[i - 1][1],
                                     points[i][0], points[i][1])

        legend_y = plot_top + 2
        for i, key in enumerate(["roll", "pitch", "yaw"]):
            color = _TRACE_COLORS[key]
            x = plot_left + 8 + i * 80
            painter.setPen(color)
            painter.drawLine(x, legend_y + 4, x + 16, legend_y + 4)
            painter.setPen(_TEXT)
            painter.drawText(x + 20, legend_y + 8, key.capitalize())

        painter.setPen(_GRID)
        painter.drawRect(plot_left, plot_top, pw, ph)
