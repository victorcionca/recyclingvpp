IPERF_PORT = 3114
REST_PORT = 6502


HALT_ENDPOINT = '/halt'
TASK_ALLOCATION = "/allocate_high_task"
TASK_UPDATE = '/update_task'
TASK_REALLOCATION = "/reallocate_high_task"
TASK_FORWARD = "/forward_task"
TASK_ASSEMBLY = "/assembly"
PRUNE_DNN = "/prune"


ALLOCATE_LOW_TASK = "/allocate_low_task"
SET_EXPERIMENT_START = "/experiment_start"
EXPERIMENT_INFERFACE = 1337
OBJECT_DETECTION_COUNT = 20
OBJECT_DETECTION_TIME_MS = 100
FRAME_RATE = 4

P1_LOW = .3
P1_HIGH = .7

P2_LOW = .3
P2_HIGH = .7

P1 = P1_HIGH
P2 = P2_HIGH

# This value determines whether or 
# not the start time set by the server
# is offset by two seconds (well really
# the event window / 2) in order to 
# offset the network load # 
SET_A_OR_B = False


CONTROLLER_DEFAULT_ROUTE = "/controller"
CONTROLLER_HOST_NAME = "COM-C132-M34579"
CONTROLLER_DEFAULT_PORT = 6502
CONTROLLER_REGISTER_DEVICE = "/register_device"
CONTROLLER_DAG_DISRUPTION = "/dag_disruption"
CONTROLLER_STATE_UPDATE = "/state_update"
CONTROLLER_LOW_COMP_ALLOCATION = "/low_offload_request"
CONTROLLER_HIGH_COMP_ALLOCATION = "/high_offload_request"

INITIAL_FILE_PATH = "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/inference_engine/metal110.jpg"
