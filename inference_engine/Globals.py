import threading
import queue
from multiprocessing import Queue
from typing import Dict, List
import OutboundComm
# import inference_engine_e2e_with_ipc
import HighCompResult
import threading

import InferenceTestObj

work_queue_lock = threading.Lock()

# Results queue
results_queue = Queue()

# Outbound net-communications queue
# Two types of comm, state update and outbound comms
net_outbound_list: List[OutboundComm.OutboundComm] = []

# This holds dnns inbetween the task being sent to processing and the result being generated
dnn_hold_dict: Dict[str, HighCompResult.HighCompResult] = {}

# This holds a queue of tasks to be processed,
# ensures that tasks are only added to the work
# as scheduled
work_waiting_queue: List[Dict] = []

host_name = ""

# Used to hold our map of cores in use
# key is the core, value is the task using it
core_map: Dict[int, str] = {
    0: "",
    1: "",
    2: "",
    3: ""
}

active_capacity = 0

# Stops the polling thread from sending requests,
# Doesn't send its first request until iperf test has completed
is_requesting = True

work_request_lock = threading.Lock()
work_request_lock.acquire()

# Need to hold threads so that I can halt later if need be
# Key is DNN ID, value is the processor
# thread_holder_inference: Dict[str, inference_engine_e2e_with_ipc.PartitionProcess] = dict()

thread_holder_testing: Dict[str, InferenceTestObj.InferenceTestObj] = dict()

thread_holder = thread_holder_testing

