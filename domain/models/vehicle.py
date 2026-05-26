from dataclasses import dataclass, field


@dataclass
class Attitude:
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0


@dataclass
class Position:
    lat: float = 0.0
    lon: float = 0.0
    alt: float = 0.0
    relative_alt: float = 0.0


@dataclass
class GPSInfo:
    satellites_visible: int = 0
    fix_type: int = 0


@dataclass
class BatteryInfo:
    voltage: float = 0.0
    current: float = 0.0
    remaining: float = 0.0


_MAV_TYPES: dict[int, str] = {
    0: "Generic", 1: "Fixed Wing", 2: "Quadrotor",
    3: "Coaxial", 4: "Helicopter", 5: "Hexarotor",
    6: "Antenna Tracker", 7: "Octarotor", 8: "Tricopter",
    9: "VTOL", 10: "Ground Rover", 11: "Surface Boat",
    12: "Submarine", 13: "Hexarotor", 14: "Gimbal",
    15: "ADSB", 16: "VTOL Fixed Rotor",
}


def mav_type_name(mav_type: int) -> str:
    return _MAV_TYPES.get(mav_type, f"MAV_TYPE_{mav_type}")


@dataclass
class Vehicle:
    attitude: Attitude = field(default_factory=Attitude)
    position: Position = field(default_factory=Position)
    gps_info: GPSInfo = field(default_factory=GPSInfo)
    battery: BatteryInfo = field(default_factory=BatteryInfo)
    mode: str = "STABILIZE"
    armed: bool = False
    system_status: int = 0
    heading: float = 0.0
    groundspeed: float = 0.0
    airspeed: float = 0.0
    vehicle_type: int = 0
    vehicle_type_str: str = ""
