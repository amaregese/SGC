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

#toolbar_group {
    background-color: #2a2a4a; color: #ccc;
    border: none; border-radius: 4px;
    padding: 4px 10px; font-size: 11px; font-weight: bold;
}

#toolbar_group:hover {
    background-color: #3a3a6a;
}

#toolbar_group::menu-indicator {
    image: none;
    width: 0px;
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

QMenu {
    background-color: #1a1a2e;
    color: #ccc;
    border: 1px solid #333;
    border-radius: 4px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px 6px 12px;
    font-size: 11px;
}

QMenu::item:selected {
    background-color: #0f3460;
    color: #4fc3f7;
}

QMenu::item:checked {
    background-color: #0f3460;
    color: #4fc3f7;
    font-weight: bold;
}

QMenu::separator {
    height: 1px;
    background: #333;
    margin: 4px 8px;
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

#left_panel {
    background-color: #0a0a1a;
    border-right: 1px solid #0f3460;
}

#telemetry_panel {
    background-color: #0a0a1a;
    border-top: 1px solid #0f3460;
}

#mini_battery_bar {
    background-color: #0f3460;
    border: none;
    border-radius: 2px;
    text-align: center;
    font-size: 7px;
    color: white;
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

#actions_dock {
    background-color: #16213e;
}

#actions_dock QPushButton#action_btn_warn {
    background-color: #5c2a2a;
    color: #ff6b6b;
    border: 1px solid #8a3a3a;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 11px;
}

#actions_dock QPushButton#action_btn_warn:hover {
    background-color: #7a3a3a;
}

#actions_dock QPushButton#action_btn_cal {
    background-color: #0f3460;
    color: #e0e0e0;
    border: none;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 11px;
}

#actions_dock QPushButton#action_btn_cal:hover {
    background-color: #1a4a7a;
}

#actions_dock QPushButton#action_btn_misc {
    background-color: #2a4a2a;
    color: #6bff6b;
    border: 1px solid #3a6a3a;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 11px;
}

#actions_dock QPushButton#action_btn_misc:hover {
    background-color: #3a6a3a;
}

#joystick_dock {
    background-color: #16213e;
}

#joystick_bar {
    background-color: #1a1a3e;
    border: 1px solid #0f3460;
    border-radius: 3px;
    text-align: center;
    font-size: 9px;
    color: #888;
    height: 14px;
}

#joystick_bar::chunk {
    background-color: #4fc3f7;
    border-radius: 2px;
}

#toolbar QPushButton#joystick_btn {
    background-color: #2a2a4a;
    padding: 6px 10px;
}

#toolbar QPushButton#joystick_btn:checked {
    background-color: #4fc3f7;
    color: #1a1a2e;
    font-weight: bold;
}

#toolbar QPushButton#joystick_btn:hover {
    background-color: #3a3a6a;
}

#toolbar QPushButton#console_btn {
    background-color: #2a2a4a;
    padding: 6px 10px;
}

#toolbar QPushButton#console_btn:checked {
    background-color: #4fc3f7;
    color: #1a1a2e;
    font-weight: bold;
}

#toolbar QPushButton#console_btn:hover {
    background-color: #3a3a6a;
}

#serial_console_dock {
    background-color: #0d1117;
}

#serial_console_dock #console_output {
    background-color: #0d1117;
    color: #e0e0e0;
    border: 1px solid #1a4a7a;
    border-radius: 4px;
    font-size: 12px;
    padding: 6px;
}

#serial_console_dock #console_input {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 1px solid #1a4a7a;
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 12px;
}

#serial_console_dock #console_send_btn {
    background-color: #0f3460;
    color: #e0e0e0;
    border: none;
    border-radius: 4px;
    padding: 6px 14px;
    font-size: 11px;
}

#serial_console_dock #console_send_btn:hover {
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
