from datetime import datetime as dt
import threading
from typing import Dict, List

EXPERIMENT_START_TIME: dt = dt.now()
EXPERIMENT_START: bool = False
EXPERIMENT_FINISH_TIME: dt = dt.now()
# This value determines whether or 
# not the start time set by the server
# is offset by two seconds (well really
# the event window / 2) in order to 
# offset the network load # 
SET_A_OR_B = False

# Structure is the following
# [{
#     "event_type": "event_type enum"
#     "time": "A datetime object"
# }]
event_queue: List[Dict] = []
queue_lock = threading.Lock()
trace_list = []