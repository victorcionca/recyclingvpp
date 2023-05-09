from datetime import datetime as dt
import OutboundCommTypes
class OutboundComm:
    def __init__(self, comm_time: dt = dt.now(), comm_type: OutboundCommTypes.OutboundCommType = OutboundCommTypes.OutboundCommType.TASK_FORWARD, payload = None, dnn_id: str = "", version: int = 0) -> None:
        self.comm_time = comm_time
        self.comm_type = comm_type
        self.dnn_id = dnn_id
        self.version = version
        self.payload = payload
        return