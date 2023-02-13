from datetime import datetime as dt
import threading

EXPERIMENT_START_TIME: dt = dt.now()
EXPERIMENT_START: bool = False
EXPERIMENT_FINISH_TIME: dt = dt.now()


# Structure is the following
# [{
#     "event_type": "event_type enum"
#     "time": "A datetime object"
# }]
event_queue: list[dict] = []
queue_lock = threading.Lock()