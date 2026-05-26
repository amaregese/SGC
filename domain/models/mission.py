from __future__ import annotations
from dataclasses import dataclass, field


COMMAND_NAMES = {
    16: "WAYPOINT",
    17: "LOITER_UNLIM",
    18: "LOITER_TURNS",
    19: "LOITER_TIME",
    20: "RTL",
    21: "LAND",
    22: "TAKEOFF",
    23: "FOLLOW",
    24: "CONTINUE_AND_CHANGE_ALT",
    25: "DELAY",
    28: "SPLINE_WAYPOINT",
    29: "VTOL_TAKEOFF",
    30: "VTOL_LAND",
    31: "NAV_FENCE_RETURN_POINT",
    32: "NAV_FENCE_POLYGON_VERTEX_INCLUSION",
    33: "NAV_FENCE_POLYGON_VERTEX_EXCLUSION",
    34: "NAV_FENCE_CIRCLE_INCLUSION",
    35: "NAV_FENCE_CIRCLE_EXCLUSION",
    36: "NAV_RALLY_POINT",
    84: "NAV_ALTITUDE_WAIT",
    85: "NAV_VTOL_RESUME",
    91: "NAV_FENCE_RETURN_POINT_FENCE_ACTION",
    92: "NAV_FENCE_RETURN_POINT_FENCE_ACTION_STANDARD",
    93: "NAV_FENCE_RETURN_POINT_FENCE_ACTION_ON_FAILURE",
    100: "DO_JUMP",
    177: "DO_CHANGE_SPEED",
    178: "DO_SET_HOME",
    179: "DO_SET_SERVO",
    180: "DO_SET_RELAY",
    181: "DO_REPEAT_SERVO",
    182: "DO_REPEAT_RELAY",
    183: "DO_SET_SERVO",
    184: "DO_SET_RELAY",
    185: "DO_DIGITAL_SERVO",
    186: "DO_DIGITAL_RELAY",
    191: "DO_SET_ROI",
    192: "DO_SET_ROI_LOCATION",
    193: "DO_SET_ROI_WPNEXT_OFFSET",
    194: "DO_SET_ROI_NONE",
    200: "DO_GUIDED_CONTROL",
    201: "DO_GUIDED_LIMITS",
    202: "DO_GUIDED_MASTER",
    203: "DO_GUIDED_COMMAND",
    210: "DO_ENGINE_CONTROL",
    211: "DO_SET_MISSION_CURRENT",
}

FRAME_NAMES = {
    0: "GLOBAL",
    1: "LOCAL",
    2: "MISSION",
    3: "GLOBAL_RELATIVE_ALT",
    4: "LOCAL_ENU",
    5: "GLOBAL_INT",
    6: "LOCAL_OFFSET_NED",
    7: "BODY_NED",
    8: "BODY_OFFSET_NED",
    9: "GLOBAL_TERRAIN_ALT",
    10: "GLOBAL_TERRAIN_ALT_INT",
}


@dataclass
class Waypoint:
    seq: int = 0
    frame: int = 3
    command: int = 16
    current: int = 0
    autocontinue: int = 1
    param1: float = 0.0
    param2: float = 0.0
    param3: float = 0.0
    param4: float = 0.0
    lat: float = 0.0
    lon: float = 0.0
    alt: float = 0.0

    @property
    def command_name(self) -> str:
        return COMMAND_NAMES.get(self.command, f"CMD_{self.command}")

    @property
    def frame_name(self) -> str:
        return FRAME_NAMES.get(self.frame, f"FRAME_{self.frame}")

    def to_dict(self) -> dict:
        return {"lat": self.lat, "lon": self.lon, "alt": self.alt}

    @classmethod
    def from_mavlink(cls, msg) -> Waypoint:
        return cls(
            seq=msg.seq,
            frame=msg.frame,
            command=msg.command,
            current=msg.current,
            autocontinue=msg.autocontinue,
            param1=msg.param1,
            param2=msg.param2,
            param3=msg.param3,
            param4=msg.param4,
            lat=msg.x / 1e7,
            lon=msg.y / 1e7,
            alt=msg.z,
        )
