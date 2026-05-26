from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtCore import QRect
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush
import math


_CYAN = "#4fc3f7"
_RED = "#e74c3c"
_ORANGE = "#e67e22"


class HUDWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, 90)
        self.setStyleSheet("background:#0a0a1a;")

        self.roll = 0.0
        self.pitch = 0.0
        self.heading = 0.0
        self.altitude = 0.0
        self.speed = 0.0
        self.climb = 0.0

        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self.update)
        self._timer.start()

    def update_data(self, roll: float, pitch: float, heading: float,
                    alt: float, speed: float, climb: float = 0) -> None:
        self.roll = roll
        self.pitch = pitch
        self.heading = heading
        self.altitude = alt
        self.speed = speed
        self.climb = climb

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        w, h = rect.width(), rect.height()
        cx, cy = w // 2, h // 2
        r = min(w, h) // 2 - 20
        if r < 30:
            r = 30

        p.fillRect(rect, QColor("#0a0a1a"))

        # ── Sky / Ground ──
        p.save()
        p.translate(cx, cy)
        p.rotate(-self.roll)
        pitch_px = r / 40.0
        offset = self.pitch * pitch_px
        p.setClipRect(-r, -r, 2 * r, 2 * r)
        p.fillRect(QRect(-r, -r, 2 * r, int(offset - (-r))), QColor("#1a3a5c"))
        p.fillRect(QRect(-r, int(offset), 2 * r, r - int(offset) + r), QColor("#3a2a1a"))

        # Horizon line
        p.setPen(QPen(QColor("#ffffff"), 2))
        p.drawLine(-r, int(offset), r, int(offset))

        # Pitch ladders
        p.setPen(QPen(QColor("rgba(255,255,255,80)"), 1))
        for deg in range(-60, 61, 10):
            if deg == 0:
                continue
            y = offset + deg * pitch_px
            w2 = r * 0.25 if deg % 20 == 0 else r * 0.12
            if abs(y) > r:
                continue
            p.drawLine(int(-w2), int(y), int(w2), int(y))
        p.restore()
        p.setClipping(False)

        # ── Compass ring ──
        ring_r = r + 4
        p.setPen(QPen(QColor("rgba(255,255,255,40)"), 1))
        p.drawEllipse(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2)

        # North arrow + heading rotation
        p.save()
        p.translate(cx, cy)
        p.rotate(-self.heading)
        p.setPen(QPen(QColor(_RED), 2))
        p.drawLine(0, -ring_r + 6, 0, -ring_r + 16)
        p.drawLine(-4, -ring_r + 12, 0, -ring_r + 6)
        p.drawLine(4, -ring_r + 12, 0, -ring_r + 6)
        p.setFont(QFont("sans-serif", 7, QFont.Bold))
        p.setPen(QColor(_RED))
        p.drawText(-4, -ring_r + 24, "N")
        p.restore()

        # Compass ticks
        p.setFont(QFont("monospace", 6))
        for d in range(0, 360, 30):
            a = math.radians(d - self.heading)
            x = cx + ring_r * math.sin(a)
            y = cy - ring_r * math.cos(a)
            tick = 6 if d % 90 == 0 else 3
            color = QColor(_RED) if d % 90 == 0 else QColor("rgba(255,255,255,50)")
            p.setPen(QPen(color, 1))
            dx = int(ring_r * math.sin(a))
            dy = int(ring_r * math.cos(a))
            p.drawLine(cx + dx, cy - dy,
                       cx + int((ring_r - tick) * math.sin(a)),
                       cy - int((ring_r - tick) * math.cos(a)))
            if d % 90 == 0:
                labels = {0: "N", 90: "E", 180: "S", 270: "W"}
                lbl = labels.get(d, "")
                p.setPen(QColor(_RED) if d == 0 else QColor("rgba(255,255,255,60)"))
                p.drawText(int(cx + dx - 4), int(cy - dy + 14 if d == 0 else cy - dy + 4), lbl)

        # ── Drone icon ──
        dr = max(12, r // 12)
        p.save()
        p.translate(cx, cy)
        p.rotate(-self.heading)
        p.setPen(QPen(QColor(_CYAN), 2))
        p.setBrush(QColor("rgba(79,195,247,80)"))
        p.drawEllipse(-dr // 2, -dr // 2, dr, dr)
        arm_len = dr
        for angle in [45, 135, 225, 315]:
            a = math.radians(angle)
            x = arm_len * math.cos(a)
            y = arm_len * math.sin(a)
            p.drawLine(0, 0, int(x), int(y))
            p.setBrush(QColor(_CYAN))
            p.drawEllipse(int(x) - 2, int(y) - 2, 4, 4)
            p.setBrush(QColor("rgba(79,195,247,80)"))
        p.setPen(QPen(QColor(_RED), 2))
        p.drawLine(0, 0, 0, -arm_len - 4)
        p.restore()

        # ── Speed / Alt text ──
        p.setFont(QFont("monospace", 9))
        p.setPen(QColor("rgba(255,255,255,180)"))
        p.drawText(4, 16, f"SPD {self.speed:.0f}")
        alt_text = f"ALT {self.altitude:.0f}"
        p.setPen(QColor("rgba(255,255,255,180)"))
        p.drawText(w - 4 - p.fontMetrics().horizontalAdvance(alt_text), 16, alt_text)

        # ── Roll arc at top ──
        arc_r = max(20, r // 3)
        p.setPen(QPen(QColor("rgba(255,255,255,40)"), 1))
        p.drawArc(cx - arc_r, 4, arc_r * 2, arc_r * 2, 150 * 16, 60 * 16)
        p.setPen(QPen(QColor(_ORANGE), 2))
        p.drawLine(cx - 8, 4 + arc_r, cx + 8, 4 + arc_r)
        p.setPen(QColor(_ORANGE))
        p.setFont(QFont("monospace", 7))
        p.drawText(cx - 10, 4 + arc_r + 14, f"{self.roll:.0f}")

        # ── Climb rate ──
        if abs(self.climb) > 0.1:
            p.setFont(QFont("monospace", 7))
            p.setPen(QColor(_CYAN))
            p.drawText(cx - 16, h - 6, f"VS {self.climb:+.1f}")
