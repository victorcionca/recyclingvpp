from enum import Enum

class OutboundCommType(Enum):
    TASK_FORWARD = 1
    STATE_UPDATE = 3
    VIOLATED_DEADLINE = 4