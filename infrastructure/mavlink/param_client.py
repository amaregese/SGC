from PySide6.QtCore import QObject, Signal, QTimer


ParamRecord = tuple[str, float, int, int, int]


PARAM_TYPES = {
    0: "UINT8", 1: "INT8", 2: "UINT16", 3: "INT16",
    4: "UINT32", 5: "INT32", 6: "UINT64", 7: "INT64",
    8: "REAL32", 9: "REAL64",
}


class ParamClient(QObject):
    batch_received = Signal(list)
    sync_finished = Signal()

    def __init__(self, connection):
        super().__init__()
        self._connection = connection
        self._params: dict[str, tuple[float, int]] = {}
        self._total_count = 0
        self._received_count = 0
        self._batch: list[ParamRecord] = []

        self._batch_timer = QTimer(self)
        self._batch_timer.setSingleShot(True)
        self._batch_timer.setInterval(100)
        self._batch_timer.timeout.connect(self._flush_batch)

    def request_list(self) -> None:
        self._params.clear()
        self._received_count = 0
        self._total_count = 0
        self._batch.clear()
        self._batch_timer.stop()
        master = self._connection.master
        if master is None:
            return
        sysid = master.target_system if master.target_system else 1
        compid = master.target_component if master.target_component else 1
        master.mav.param_request_list_send(sysid, compid)

    def _flush_batch(self) -> None:
        if not self._batch:
            return
        self.batch_received.emit(self._batch)
        self._batch = []

    def process(self, msg) -> None:
        if msg.get_type() != "PARAM_VALUE":
            return
        pname = msg.param_id.rstrip("\x00")
        self._params[pname] = (msg.param_value, msg.param_type)
        self._total_count = msg.param_count
        self._received_count += 1
        self._batch.append((pname, msg.param_value, msg.param_type, msg.param_index, msg.param_count))
        self._batch_timer.start()
        if self._received_count >= self._total_count:
            self._batch_timer.stop()
            self._flush_batch()
            self.sync_finished.emit()

    def set_param(self, name: str, value: float, param_type: int) -> None:
        master = self._connection.master
        if master is None:
            return
        sysid = master.target_system if master.target_system else 1
        compid = master.target_component if master.target_component else 1
        master.mav.param_set_send(sysid, compid, name.encode(), value, param_type)

    @property
    def param_count(self) -> int:
        return len(self._params)

    @property
    def all_params(self) -> dict[str, tuple[float, int]]:
        return dict(self._params)

    def get_param(self, name: str) -> tuple[float, int] | None:
        return self._params.get(name)
