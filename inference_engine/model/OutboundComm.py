from datetime import datetime as dt
from ..enums.OutboundCommTypes import OutboundCommType
class OutboundComm:
    def __init__(self, comm_time: dt = dt.now(), comm_type: OutboundCommType = OutboundCommType.TASK_ASSEMBLY, payload = None) -> None:
        self.comm_time = comm_time
        self.comm_type = comm_type
        self.payload = payload
        return