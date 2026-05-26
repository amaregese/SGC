from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QSizePolicy, QWidget,
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QImage, QPixmap, QFont

import cv2
import numpy as np


_PRESETS = {
    "Camera 0": 0,
    "Camera 1": 1,
    "UDP :5600": "udp://0.0.0.0:5600",
    "Custom...": None,
}


class _CaptureThread(QThread):
    frame_ready = Signal(object)

    def __init__(self):
        super().__init__()
        self._source = 0
        self._cap: cv2.VideoCapture | None = None
        self._running = False

    def set_source(self, source):
        self._running = False
        if self._cap:
            self._cap.release()
        self._source = source

    def run(self):
        self._cap = cv2.VideoCapture(self._source)
        if not self._cap.isOpened():
            return
        self._running = True
        while self._running:
            ret, frame = self._cap.read()
            if not ret:
                self._running = False
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, w * ch, QImage.Format_RGB888)
            self.frame_ready.emit(qimg.copy())
        if self._cap:
            self._cap.release()
            self._cap = None

    def stop(self):
        self._running = False
        self.wait(2000)


class VideoStream(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("video_stream")
        self._capture_thread = _CaptureThread()
        self._capture_thread.frame_ready.connect(self._on_frame)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Display area ──
        self._display = QLabel("  No Video Signal")
        self._display.setAlignment(Qt.AlignCenter)
        self._display.setObjectName("video_display")
        self._display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._display.setMinimumSize(320, 180)
        self._display.setStyleSheet("""
            QLabel#video_display {
                background-color: #0a0a1a;
                color: #555;
                font-size: 18px;
                font-weight: bold;
                border: none;
            }
        """)
        outer.addWidget(self._display, 1)

        # ── Controls bar ──
        bar = QFrame()
        bar.setObjectName("video_bar")
        bar.setFixedHeight(44)
        bar.setStyleSheet("""
            QFrame#video_bar {
                background-color: #12122a;
                border-top: 1px solid #1a1a3e;
            }
        """)
        ctrl = QHBoxLayout(bar)
        ctrl.setContentsMargins(8, 4, 8, 4)
        ctrl.setSpacing(6)

        self._preset_combo = QComboBox()
        self._preset_combo.setObjectName("video_preset")
        self._preset_combo.addItems(_PRESETS.keys())
        self._preset_combo.setFixedWidth(130)
        self._preset_combo.setStyleSheet("""
            QComboBox#video_preset {
                background: #1a1a3e; color: #ccc;
                border: 1px solid #2a2a5e; border-radius: 4px;
                padding: 4px 8px; font-size: 11px;
            }
            QComboBox#video_preset::drop-down {
                border: none; width: 20px;
            }
        """)
        self._preset_combo.currentTextChanged.connect(self._on_preset_changed)
        ctrl.addWidget(self._preset_combo)

        self._source_input = QLineEdit()
        self._source_input.setObjectName("video_source_input")
        self._source_input.setPlaceholderText("URL or device index")
        self._source_input.setEnabled(False)
        self._source_input.setStyleSheet("""
            QLineEdit#video_source_input {
                background: #1a1a3e; color: #ccc;
                border: 1px solid #2a2a5e; border-radius: 4px;
                padding: 4px 8px; font-size: 11px;
            }
        """)
        ctrl.addWidget(self._source_input)

        self._connect_btn = QPushButton("Start")
        self._connect_btn.setObjectName("video_connect_btn")
        self._connect_btn.setStyleSheet("""
            QPushButton#video_connect_btn {
                background: #27ae60; color: white;
                border: none; border-radius: 4px;
                padding: 6px 16px; font-size: 11px; font-weight: bold;
            }
            QPushButton#video_connect_btn:hover {
                background: #2ecc71;
            }
            QPushButton#video_connect_btn:pressed {
                background: #1e8449;
            }
        """)
        self._connect_btn.clicked.connect(self._toggle_stream)
        ctrl.addWidget(self._connect_btn)

        self._status_label = QLabel("Stopped")
        self._status_label.setObjectName("video_status")
        self._status_label.setStyleSheet("""
            QLabel#video_status {
                color: #888; font-size: 10px;
                padding: 0 4px;
            }
        """)
        ctrl.addWidget(self._status_label)

        ctrl.addStretch()
        outer.addWidget(bar)

    def _on_preset_changed(self, text: str):
        val = _PRESETS.get(text)
        if val is None:
            self._source_input.setEnabled(True)
            self._source_input.setFocus()
        else:
            self._source_input.setEnabled(False)
            self._source_input.setText(str(val))

    def _toggle_stream(self):
        if self._capture_thread.isRunning():
            self._capture_thread.stop()
            self._connect_btn.setText("Start")
            self._connect_btn.setStyleSheet("""
                QPushButton#video_connect_btn {
                    background: #27ae60; color: white;
                    border: none; border-radius: 4px;
                    padding: 6px 16px; font-size: 11px; font-weight: bold;
                }
                QPushButton#video_connect_btn:hover { background: #2ecc71; }
                QPushButton#video_connect_btn:pressed { background: #1e8449; }
            """)
            self._status_label.setText("Stopped")
            self._display.setText("  No Video Signal")
        else:
            src_text = self._source_input.text().strip()
            if not src_text:
                return
            try:
                src = int(src_text)
            except ValueError:
                src = src_text
            self._capture_thread.set_source(src)
            self._capture_thread.start()
            self._connect_btn.setText("Stop")
            self._connect_btn.setStyleSheet("""
                QPushButton#video_connect_btn {
                    background: #c0392b; color: white;
                    border: none; border-radius: 4px;
                    padding: 6px 16px; font-size: 11px; font-weight: bold;
                }
                QPushButton#video_connect_btn:hover { background: #e74c3c; }
                QPushButton#video_connect_btn:pressed { background: #a93226; }
            """)
            self._status_label.setText("Starting...")

    def _on_frame(self, qimg: QImage):
        scaled = qimg.scaled(
            self._display.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self._display.setPixmap(QPixmap.fromImage(scaled))
        self._status_label.setText("Streaming")
