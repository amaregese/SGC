from domain.models.vehicle import Vehicle, Attitude, Position, GPSInfo, BatteryInfo, mav_type_name
from infrastructure.mavlink.message_handler import MAVLinkMessage


class TelemetryProcessor:
    def __init__(self):
        self._vehicle = Vehicle()

    def process(self, msg: MAVLinkMessage) -> Vehicle:
        msg_type = msg.get_type()

        if msg_type == "ATTITUDE":
            self._vehicle.attitude = Attitude(
                roll=msg.roll * 57.2958,
                pitch=msg.pitch * 57.2958,
                yaw=msg.yaw * 57.2958,
            )

        elif msg_type == "GLOBAL_POSITION_INT":
            self._vehicle.position = Position(
                lat=msg.lat / 1e7,
                lon=msg.lon / 1e7,
                alt=msg.alt / 1e3,
                relative_alt=msg.relative_alt / 1e3,
            )
            self._vehicle.heading = msg.hdg / 100.0

        elif msg_type == "GPS_RAW_INT":
            self._vehicle.gps_info = GPSInfo(
                satellites_visible=msg.satellites_visible,
                fix_type=msg.fix_type,
            )

        elif msg_type == "BATTERY_STATUS":
            v = msg.voltages[0] / 1000.0 if msg.voltages[0] < 65534 else 0.0
            self._vehicle.battery = BatteryInfo(
                voltage=v,
                current=msg.current_battery / 100.0,
                remaining=msg.battery_remaining,
            )

        elif msg_type == "HEARTBEAT":
            self._vehicle.armed = (msg.base_mode & 128) != 0
            self._vehicle.system_status = msg.system_status
            self._vehicle.mode = self._mode_from_custom(msg.custom_mode)
            self._vehicle.vehicle_type = msg.type
            self._vehicle.vehicle_type_str = mav_type_name(msg.type)

        elif msg_type == "VFR_HUD":
            self._vehicle.groundspeed = msg.groundspeed
            self._vehicle.airspeed = msg.airspeed
            self._vehicle.heading = msg.heading

        return self._vehicle

    @property
    def vehicle(self) -> Vehicle:
        return self._vehicle

    @staticmethod
    def _mode_from_custom(custom_mode: int) -> str:
        modes = {
            0: "STABILIZE", 1: "ACRO", 2: "ALT_HOLD", 3: "AUTO",
            4: "GUIDED", 5: "LOITER", 6: "RTL", 7: "CIRCLE",
            9: "LAND", 11: "DRIFT", 13: "SPORT", 14: "FLIP",
            15: "AUTOTUNE", 16: "POSHOLD", 17: "BRAKE",
        }
        return modes.get(custom_mode, f"MODE_{custom_mode}")
