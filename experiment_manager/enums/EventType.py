from enum import Enum

class EventTypes(Enum):
    OBJECT_DETECT_START = 1
    OBJECT_DETECT_FINISH = 2
    LOW_COMP_START = 3
    LOW_COMP_FINISH = 4
    EVENT_LOOP_FINISH = 5