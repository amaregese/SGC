import os

from PySide6.QtWidgets import QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtGui import QResizeEvent
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings


_MAP_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", "map"))


class MapWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("map_widget")
        self._page_ready = False

        self._web_view = QWebEngineView()
        self._web_view.setStyleSheet("background-color: #0a1628;")

        s = self._web_view.settings()
        s.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        s.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        s.setAttribute(QWebEngineSettings.AutoLoadImages, True)

        html_path = os.path.join(_MAP_DIR, "leaflet.html")
        self._web_view.setUrl(QUrl.fromLocalFile(html_path))
        self._web_view.loadFinished.connect(self._on_page_loaded)

        overlay = QFrame(self)
        overlay.setObjectName("map_overlay")

        stats_layout = QVBoxLayout(overlay)
        stats_layout.setContentsMargins(10, 10, 10, 10)
        stats_layout.setSpacing(2)

        self._speed_label = QLabel("SPD: --.- m/s")
        self._speed_label.setObjectName("map_stat")
        stats_layout.addWidget(self._speed_label)

        self._alt_label = QLabel("ALT: --- m")
        self._alt_label.setObjectName("map_stat")
        stats_layout.addWidget(self._alt_label)

        self._heading_label = QLabel("HDG: ---\u00b0")
        self._heading_label.setObjectName("map_stat")
        stats_layout.addWidget(self._heading_label)

        overlay.setFixedWidth(160)
        overlay.move(10, 10)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._web_view)

    def _on_page_loaded(self, ok: bool) -> None:
        if not ok:
            return
        self._page_ready = True
        QTimer.singleShot(300, self._invalidate_map_size)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self._page_ready:
            QTimer.singleShot(50, self._invalidate_map_size)

    def _invalidate_map_size(self) -> None:
        self._run_js("if(window.invalidateMapSize)invalidateMapSize()")

    def _run_js(self, code: str) -> None:
        if self._page_ready:
            self._web_view.page().runJavaScript(code)

    def update_vehicle_position(self, lat: float, lon: float, heading: float) -> None:
        self._run_js(f"updateVehiclePosition({lat},{lon},{heading})")
        self._heading_label.setText(f"HDG: {heading:.0f}\u00b0")

    def update_stats(self, speed: float, alt: float, heading: float) -> None:
        self._speed_label.setText(f"SPD: {speed:.1f} m/s")
        self._alt_label.setText(f"ALT: {alt:.0f} m")
        self._heading_label.setText(f"HDG: {heading:.0f}\u00b0")

    def draw_waypoints(self, waypoints: list[dict]) -> None:
        import json
        self._run_js(f"drawWaypoints({json.dumps(waypoints)})")

    def clear_waypoints(self) -> None:
        self._run_js("clearWaypoints()")

    def draw_flight_path(self, coords: list[list[float]]) -> None:
        import json
        self._run_js(f"drawFlightPath({json.dumps(coords)})")

    def set_center(self, lat: float, lon: float, zoom: int = 16) -> None:
        self._run_js(f"map.setView([{lat},{lon}],{zoom})")
