import threading
import queue
from multiprocessing import Queue
from typing import Dict, List
import OutboundComm
import TaskForwarding
import AssemblyHoldItem
import HighCompResult

work_queue_lock = threading.Lock()

# Queue for RESTInterface and GRPC Server to append tasks to work queue
work_queue = queue.Queue()

# Assembly dictionary is a map
# Where the key is a composite key
# of the dnn and the convidx
# eg, dnn_id = 1, condidx = 4
# the key would be "1_4"
# Value is a dict with two keys
# "partition_count": int
# "tile": a list of TaskForwarding objects
assembly_dict: Dict[str, Dict] = {}

# StateUpdate Map
# this is a dictionary that
# has a dnn id as key and the value is a dictionary
# that has the following structure #
# {
#     "dnn_id": {
#         "version that needs update": int : dnn
#     }  
# }

state_update_map: Dict[str, Dict[int, HighCompResult.HighCompResult]] = {}

# Results queue
results_queue = Queue()

# Outbound net-communications queue
# Two types of comm, state update and outbound comms
net_outbound_list: List[OutboundComm.OutboundComm] = []

# This holds dnns inbetween the task being sent to processing and the result being generated
dnn_hold_dict: Dict[int, TaskForwarding.TaskForwarding] = {}

# This holds a queue of tasks to be processed,
# ensures that tasks are only added to the work
# as scheduled
work_waiting_queue = []

# This list holds the version items for a DNN to ignore
halt_list: Dict[str, List[int]] = {}

# This list holds assembled data in case it is needed for task reallocation
assembly_hold_list: List[AssemblyHoldItem.AssemblyHold] = list()

# Holds a list of DNN ids that have been pruned from the network
prune_list: List[str] = []

host_name = ""

# Used to hold our map of cores in use
# key is the core, value is the task using it
core_map: Dict[int, int] = {
    0: -1,
    1: -1,
    2: -1,
    3: -1
}
