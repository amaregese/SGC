from infrastructure.mavlink.mavlink_connection import MAVLinkConnection


class CommandSender:
    def __init__(self, connection: MAVLinkConnection):
        self._connection = connection

    def _send_command(self, command: int, *params: float) -> None:
        master = self._connection.master
        if master is None:
            return
        sysid = master.target_system if master.target_system else 1
        compid = master.target_component if master.target_component else 1
        try:
            master.mav.command_long_send(
                sysid, compid,
                command, 0,
                *(params + (0.0,) * max(0, 7 - len(params)))[:7],
            )
        except Exception:
            pass

    def arm_disarm(self, arm: bool) -> None:
        self._send_command(400, float(arm))

    def takeoff(self, altitude: float) -> None:
        self._send_command(22, 0, 0, 0, 0, 0, 0, altitude)

    def rtl(self) -> None:
        self.set_mode("RTL")

    def set_mode(self, mode: str) -> None:
        mode_id = self._get_mode_id(mode)
        if mode_id is not None:
            self._send_command(176, float(mode_id))

    def emergency_stop(self) -> None:
        self._send_command(30001, 1.0)

    def reboot_to_bootloader(self) -> None:
        self._send_command(246, 1.0)

    def set_servo(self, channel: int, pwm: int) -> None:
        self._send_command(183, float(channel), float(pwm))

    def reboot(self) -> None:
        self._send_command(246, 1.0)

    def calibrate_gyro(self) -> None:
        self._send_command(241, 1.0)

    def calibrate_accel(self) -> None:
        self._send_command(241, 6.0)

    def calibrate_compass(self) -> None:
        self._send_command(241, 7.0)

    def calibrate_radio(self) -> None:
        self._send_command(241, 5.0)

    def set_home_here(self) -> None:
        self._send_command(179, 1.0)

    def send_rc_channels_override(self, channels: list[int]) -> None:
        master = self._connection.master
        if master is None:
            return
        sysid = master.target_system if master.target_system else 1
        compid = master.target_component if master.target_component else 1
        try:
            padded = (channels + [0] * 18)[:18]
            master.mav.rc_channels_override_send(sysid, compid, *padded)
        except Exception:
            pass

    @staticmethod
    def _get_mode_id(mode: str) -> int | None:
        modes = {
            "STABILIZE": 0, "ACRO": 1, "ALT_HOLD": 2, "AUTO": 3,
            "GUIDED": 4, "LOITER": 5, "RTL": 6, "CIRCLE": 7,
            "LAND": 9, "DRIFT": 11, "SPORT": 13, "FLIP": 14,
            "AUTOTUNE": 15, "POSHOLD": 16, "BRAKE": 17,
        }
        return modes.get(mode.upper())
