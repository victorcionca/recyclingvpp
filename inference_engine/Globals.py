import threading
from multiprocessing import Queue
from typing import Dict, List, Any
import inference_engine_e2e_with_ipc
import threading

import InferenceTestObj

work_queue_lock = threading.Lock()
request_counter = 0
request_version_list = []
queue_locker = "N/A"

# Results queue
results_queue = Queue()

# This holds a queue of tasks to be processed,
# ensures that tasks are only added to the work
# as scheduled
work_waiting_queue: List[Dict] = []

host_name = ""

# Used to hold our map of cores in use
# key is the core, value is the task using it
core_map :Dict[int, Dict[str, Any]] = {
    0: {},
    1: {},
    2: {},
    3: {}
}

# Stops the polling thread from sending requests,
# Doesn't send its first request until iperf test has completed
is_requesting = True

work_request_lock = threading.Lock()
work_request_lock.acquire(blocking=True)

# Need to hold threads so that I can halt later if need be
# Key is DNN ID, value is the processor
thread_holder_inference: Dict[str, inference_engine_e2e_with_ipc.PartitionProcess] = dict()

# thread_holder_testing: Dict[str, InferenceTestObj.InferenceTestObj] = dict()

thread_holder = thread_holder_inference

lock_counter = 0

halt_queue: List[str] = []

local_capacity = 0

client_list: List[str] = []

low_active = False

work_stealing_queue = []
work_stealing_lock = threading.Lock()

bytes_per_ms = 0
