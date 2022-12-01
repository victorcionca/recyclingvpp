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
