import threading
import queue
from multiprocessing import Queue

# Lock required to synchronise dict access between GRPC Server and Client
task_dict = {}
task_thread_lock = threading.Lock()

# Queue for RESTInterface and GRPC Server to append tasks to work queue
work_queue = queue.Queue()

# Results queue
results_queue = Queue()


# Outbound net-communications queue
# Two types of comm, state update and outbound comms
net_outbound_list = []
net_queue_lock = threading.Lock()


