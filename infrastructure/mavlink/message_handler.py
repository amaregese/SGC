from typing import Any


class MAVLinkMessage:
    def __init__(self, msg: Any):
        self._msg = msg

    def get_type(self) -> str:
        return self._msg.get_type()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._msg, name)

    def __str__(self) -> str:
        return str(self._msg)
