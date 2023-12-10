import sys

IPERF_PORT = 3114
REST_PORT = 6501


HALT_ENDPOINT = '/halt'
TASK_ALLOCATION = "/allocate_high_task"
TASK_UPDATE = '/update_task'
TASK_REALLOCATION = "/reallocate_high_task"
TASK_FORWARD = "/forward_task"
TASK_ASSEMBLY = "/assembly"
PRUNE_DNN = "/prune"

LOW_CAP = "/low_cap"


ALLOCATE_LOW_TASK = "/allocate_low_task"
SET_EXPERIMENT_START = "/experiment_start"
EXPERIMENT_INFERFACE = 9028
OBJECT_DETECTION_COUNT = 1
OBJECT_DETECTION_TIME_MS = 100
FRAME_RATE = 1.803072 + 16.862



CONTROLLER_DEFAULT_ROUTE = "/controller"
CONTROLLER_HOST_NAME = sys.argv[4]
CONTROLLER_DEFAULT_PORT = 6502
CONTROLLER_REGISTER_DEVICE = f"{CONTROLLER_DEFAULT_ROUTE}/register_device"
CONTROLLER_STATE_UPDATE = f"{CONTROLLER_DEFAULT_ROUTE}/state_update"
CONTROLLER_LOW_COMP_ALLOCATION = f"{CONTROLLER_DEFAULT_ROUTE}/low_offload_request"
CONTROLLER_HIGH_COMP_ALLOCATION = f"{CONTROLLER_DEFAULT_ROUTE}/high_offload_request"
CONTROLLER_STATE_UPDATE = f"{CONTROLLER_DEFAULT_ROUTE}/state_update"

INITIAL_FILE_PATH = "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/inference_engine/metal110.jpg"
CLIENT_ADDRESS = "raspberrypi1.local"
