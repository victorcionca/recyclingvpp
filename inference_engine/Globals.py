import threading
import queue
from multiprocessing import Queue
from model.OutboundComm import OutboundComm
from model.NetworkCommModels.TaskForwaring import TaskForwarding

# Queue for RESTInterface and GRPC Server to append tasks to work queue
work_queue = queue.Queue()
work_queue_lock = threading.Lock()


# Assembly dictionary is a map
# Where the key is a composite key
# of the dnn and the convidx
# eg, dnn_id = 1, condidx = 4
# the key would be "1_4"
# Value is a dict with two keys
# "partition_count": int
# "tile": a list of TaskForwarding objects
assembly_dict: dict[str, dict] = {}
assembly_dict_lock = threading.Lock()

# Results queue
results_queue = Queue()

# Outbound net-communications queue
# Two types of comm, state update and outbound comms
net_outbound_list: list[OutboundComm] = []
net_queue_lock = threading.Lock()

dnn_hold_dict: dict[int, TaskForwarding] = {}
dnn_hold_lock = threading.Lock()

work_waiting_queue = []
work_waiting_queue_lock = threading.Lock()

# Used to hold our map of cores in use
# key is the core, value is the task using it
core_map: dict[int, int] = {
    0: -1,
    1: -1,
    2: -1,
    3: -1
}
