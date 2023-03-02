from datetime import datetime as dt
import threading
from typing import Dict, List

EXPERIMENT_START_TIME: dt = dt.now()
EXPERIMENT_START: bool = False
EXPERIMENT_FINISH_TIME: dt = dt.now()


# Structure is the following
# [{
#     "event_type": "event_type enum"
#     "time": "A datetime object"
# }]
event_queue: List[Dict] = []
queue_lock = threading.Lock()