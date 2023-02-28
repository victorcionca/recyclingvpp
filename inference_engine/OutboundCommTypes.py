from enum import Enum

class OutboundCommType(Enum):
    TASK_FORWARD = 1
    TASK_ASSEMBLY = 2
    STATE_UPDATE = 3
    DAG_DISRUPTION = 4