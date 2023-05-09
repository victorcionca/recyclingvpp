import threading
import queue
from multiprocessing import Queue
from typing import Dict, List
import OutboundComm
import HighCompResult
import TaskForwarding

work_queue_lock = threading.Lock()

# Queue for RESTInterface and GRPC Server to append tasks to work queue
work_queue = queue.Queue()

# Results queue
results_queue = Queue()

# Outbound net-communications queue
# Two types of comm, state update and outbound comms
net_outbound_list: List[OutboundComm.OutboundComm] = []

# This holds dnns inbetween the task being sent to processing and the result being generated
dnn_hold_dict: Dict[str, TaskForwarding.TaskForwarding] = {}

# This holds a queue of tasks to be processed,
# ensures that tasks are only added to the work
# as scheduled
work_waiting_queue: List[Dict] = []

# This list holds the version items for a DNN to ignore
halt_list: Dict[str, List[int]] = {}

host_name = ""

# Used to hold our map of cores in use
# key is the core, value is the task using it
core_map: Dict[int, int] = {
    0: -1,
    1: -1,
    2: -1,
    3: -1
}
