IPERF_PORT = 3114
REST_PORT = 6501

DEADLINE_PREEMPT = True

HALT_ENDPOINT = '/halt'
TASK_ALLOCATION = "/allocate_high_task"
TASK_UPDATE = '/update_task'
TASK_FORWARD = "/forward_task"
GET_IMAGE = "/get_image"
RAISE_CAP = "/raise_cap"
LOW_CAP = "/low_cap"
EXPERIMENT_START = "/experiment_start"
REQUEST_WORK = "/request_work"
RETURN_WORK = "/return_work"



ALLOCATE_LOW_TASK = "/allocate_low_task"
SET_EXPERIMENT_START = "/set_experiment_start"
EXPERIMENT_INFERFACE = 9028
OBJECT_DETECTION_TIME_MS = 100
LOW_COMP_TIME = 980
OBJECT_DETECTION_COUNT = 1
FRAME_RATE = 1.803072 + 16.862

FTP_LOW_TIME = 16862
FTP_HIGH_TIME = 11611

FTP_LOW_N = 1
FTP_LOW_M = 2
FTP_LOW_CORE = (FTP_LOW_M * FTP_LOW_N)
FTP_HIGH_N = 2
FTP_HIGH_M = 2
FTP_HIGH_CORE = (FTP_HIGH_N * FTP_HIGH_M)

HIGH_TASK_SIZE_BYTES = 2250
HIGH_TASK_IMAGE_SIZE_BYTES = 21500

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
CONTROLLER_HOST_NAME = "192.168.81.195"
CONTROLLER_DEFAULT_PORT = 6502
CONTROLLER_REGISTER_DEVICE = f"{CONTROLLER_DEFAULT_ROUTE}/register_device"
CONTROLLER_STATE_UPDATE = f"{CONTROLLER_DEFAULT_ROUTE}/state_update"
CONTROLLER_LOW_COMP_ALLOCATION = f"{CONTROLLER_DEFAULT_ROUTE}/low_offload_request"
CONTROLLER_HIGH_COMP_ALLOCATION = f"{CONTROLLER_DEFAULT_ROUTE}/high_offload_request"
CONTROLLER_VIOLATED_DEADLINE = f"{CONTROLLER_DEFAULT_ROUTE}/deadline_violation"
POST_LOW_TASK = f"{CONTROLLER_DEFAULT_ROUTE}/post_low_task"
POST_LOW_COMP_FAIL = f"{CONTROLLER_DEFAULT_ROUTE}/low_comp_fail"
POST_HALT_EP = f"{CONTROLLER_DEFAULT_ROUTE}/halt"

INITIAL_FILE_PATH = "/home/pi/recyclingvpp/inference_engine/metal110.jpg"
CLIENT_ADDRESS = ""

CORE_COUNT = 4
