import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor

from ui.main_window import MainWindow


APP_STYLE = """
QMainWindow, QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
}

QToolBar#toolbar {
    background-color: #16213e;
    border-bottom: 1px solid #0f3460;
    padding: 4px 0;
    spacing: 6px;
}

QToolBar#toolbar QToolButton {
    background: transparent;
    border: none;
    padding: 0;
}

#toolbar QPushButton {
    background-color: #0f3460;
    color: #e0e0e0;
    border: none;
    border-radius: 4px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
}

#toolbar QPushButton:hover {
    background-color: #1a4a7a;
}

#toolbar QPushButton:pressed {
    background-color: #0d2b50;
}

#toolbar QPushButton:checked {
    background-color: #e74c3c;
    color: white;
}

#toolbar QPushButton#takeoff_btn {
    background-color: #1b4332;
    color: white;
}

#toolbar QPushButton#takeoff_btn:hover {
    background-color: #2d6a4f;
}

#toolbar QPushButton#rtl_btn {
    background-color: #7f4f24;
    color: white;
}

#toolbar QPushButton#rtl_btn:hover {
    background-color: #a67c52;
}

#toolbar QPushButton#emergency_btn {
    background-color: #6b0000;
    color: white;
    font-size: 16px;
    padding: 4px;
}

#toolbar QPushButton#emergency_btn:hover {
    background-color: #8b0000;
}

#toolbar QPushButton#set_mode_btn {
    background-color: #3a3a5c;
    padding: 6px 10px;
}

#toolbar QPushButton#params_btn {
    background-color: #2a2a4a;
    padding: 6px 10px;
}

#toolbar QPushButton#params_btn:checked {
    background-color: #4fc3f7;
    color: #1a1a2e;
    font-weight: bold;
}

#toolbar QPushButton#params_btn:hover {
    background-color: #3a3a6a;
}

#toolbar QPushButton#settings_btn {
    background-color: transparent;
    color: #888;
    font-size: 16px;
    padding: 4px;
}

#toolbar QPushButton#settings_btn:hover {
    color: #ccc;
}

#brand {
    font-size: 18px;
    font-weight: bold;
    color: #4fc3f7;
    letter-spacing: 4px;
    padding: 0 8px;
}

#toolbar_sep {
    color: #3a3a5c;
    margin: 4px 2px;
}

#mode_label {
    color: #aaa;
    font-size: 11px;
    padding: 0 4px;
}

#port_combo, #mode_combo {
    background-color: #0f3460;
    color: #e0e0e0;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}

#port_combo:hover, #mode_combo:hover {
    background-color: #1a4a7a;
}

#telemetry_panel {
    background-color: #16213e;
    border-right: 1px solid #0f3460;
}

#telemetry_card {
    background-color: #1a1a3e;
    border: 1px solid #0f3460;
    border-radius: 6px;
}

#card_header {
    font-size: 11px;
    font-weight: bold;
    color: #4fc3f7;
    letter-spacing: 2px;
    padding-bottom: 4px;
    border-bottom: 1px solid #0f3460;
}

#info_label {
    font-size: 11px;
    color: #888;
}

#info_value {
    font-size: 11px;
    color: #e0e0e0;
}

#battery_bar {
    background-color: #0f3460;
    border: none;
    border-radius: 3px;
    text-align: center;
    font-size: 10px;
    color: white;
}

#battery_bar::chunk {
    background-color: #2d6a4f;
    border-radius: 3px;
}

#status_bar {
    background-color: #0f3460;
    border-top: 1px solid #1a4a7a;
}

#conn_indicator {
    font-size: 14px;
    color: #e74c3c;
    padding-right: 4px;
}

#conn_label {
    font-size: 11px;
    color: #e74c3c;
    padding-right: 12px;
}

#sb_label {
    font-size: 11px;
    color: #ccc;
    padding: 0 8px;
}

#sb_sep {
    font-size: 11px;
    color: #3a3a5c;
    padding: 0 2px;
}

#map_widget, QWebEngineView {
    background-color: #0a0a1a;
    border: none;
}

#map_overlay {
    background-color: rgba(15, 52, 96, 180);
    border: 1px solid #0f3460;
    border-radius: 6px;
}

#map_stat {
    font-size: 11px;
    color: #4fc3f7;
    padding: 1px 0;
}

#video_stream {
    background-color: #0d0d1f;
    border-top: 1px solid #0f3460;
}

#video_display {
    background-color: #0a0a1a;
    color: #555;
    font-size: 13px;
    border: 1px solid #0f3460;
    border-radius: 4px;
}

#video_preset, #video_source_input, #video_connect_btn, #video_status {
    font-size: 11px;
}

#video_preset {
    background-color: #0f3460;
    color: #e0e0e0;
    border: none;
    border-radius: 4px;
    padding: 2px 6px;
}

#video_source_input {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 1px solid #1a4a7a;
    border-radius: 4px;
    padding: 2px 6px;
}

#video_connect_btn {
    background-color: #0f3460;
    color: #e0e0e0;
    border: none;
    border-radius: 4px;
    padding: 2px 8px;
}

#video_connect_btn:hover {
    background-color: #1a4a7a;
}

#video_status {
    color: #888;
    padding: 0 4px;
}

QStatusBar {
    background-color: #0f3460;
    color: #ccc;
    font-size: 11px;
    border-top: 1px solid #1a4a7a;
}

#param_dock {
    background-color: #16213e;
    border: none;
}

#param_dock QTableWidget {
    background-color: #1a1a3e;
    alternate-background-color: #1e1e44;
    color: #e0e0e0;
    border: 1px solid #0f3460;
    gridline-color: #0f3460;
    font-size: 11px;
}

#param_dock QTableWidget::item {
    padding: 2px 6px;
}

#param_dock QTableWidget::item:selected {
    background-color: #0f3460;
    color: #4fc3f7;
}

#param_search {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 1px solid #1a4a7a;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}

#param_refresh_btn {
    background-color: #0f3460;
    color: #e0e0e0;
    border: none;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 11px;
}

#param_refresh_btn:hover {
    background-color: #1a4a7a;
}

#mission_panel {
    background-color: #16213e;
}

#mission_panel QTableWidget {
    background-color: #1a1a3e;
    alternate-background-color: #1e1e44;
    color: #e0e0e0;
    border: 1px solid #0f3460;
    gridline-color: #0f3460;
    font-size: 11px;
}

#mission_panel QTableWidget::item {
    padding: 2px 6px;
}

#mission_panel QTableWidget::item:selected {
    background-color: #0f3460;
    color: #4fc3f7;
}

#mission_btn {
    background-color: #0f3460;
    color: #e0e0e0;
    border: none;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 11px;
}

#mission_btn:hover {
    background-color: #1a4a7a;
}
"""


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SkyWin Ground Controller")
    app.setOrganizationName("SGC")
    app.setStyleSheet(APP_STYLE)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
