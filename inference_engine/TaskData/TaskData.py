import datetime
import json


class TaskData:
    # True is high comp, false is low comp
    dnn_type = False

    # Host Address of the source of the DNN
    source: str = ""

    # Deadline
    deadline = datetime.datetime.now()

    # estimated start time of DNN
    estimated_start_time = datetime.datetime.now()

    # estimated finish time
    estimated_finish_time = datetime.datetime.now()

    # unique DNN ID
    dnn_id = int()

    # current block is the unique id of the block to be processed
    current_block = int()

    # A dictionary that holds the blocks, key is their index
    outer_blocks = {}

    # InputPartCount
    input_part_count = int()

    # N of partition
    N = int()

    # M of partition
    M = int()

    # ID of current_conv_block
    conv_idx = int()

    def __init__(self, jsonInput=None):
        if jsonInput is None:
            return
        self.dnn_type = bool(int(jsonInput["type"]))
        self.source = jsonInput["source"]
        base_datetime = datetime.datetime(1970, 1, 1)
        self.deadline = base_datetime + \
                        (datetime.timedelta(0, 0, 0, int(jsonInput["deadline"])))
        self.estimated_start_time = base_datetime + \
                                    (datetime.timedelta(0, 0, 0, int(
                                        jsonInput["estimated_start_time"])))
        self.estimated_finish_time = base_datetime + \
                                     (datetime.timedelta(0, 0, 0, int(
                                         jsonInput["estimated_finish_time"])))
        self.dnn_id = int(jsonInput["dnn_id"])
        self.current_block = int(jsonInput["current_block"])
        self.N = int(jsonInput["N"])
        self.M = int(jsonInput["M"])
        self.conv_idx = int(jsonInput["conv_idx"])
        self.input_part_count = int(jsonInput["input_part_count"])

        self.outer_blocks = {
            outer_index: {
                inner_index: TaskBlock(inner_value["estimated_start_time"], inner_value["estimated_finish_time"],
                                       inner_value["group_block_id"], inner_value["block_id"],
                                       inner_value["allocated_device"], inner_value["original_layer_ids"],
                                       inner_value["unique_task_id"], inner_value["in_map"], inner_value["N"],
                                       inner_value["M"], inner_value["conv_idx"],
                                       inner_value["state_update_comm_start"], inner_value["output_upload_start_time"])
                for inner_index, inner_value in outer_value.items()
            } for outer_index, outer_value in jsonInput["group_blocks"].items()
        }

    def update(self, jsonInput):
        self.outer_blocks = {
            outer_index: {
                inner_index: TaskBlock(inner_value["estimated_start_time"], inner_value["estimated_finish_time"],
                                       inner_value["group_block_id"], inner_value["block_id"],
                                       inner_value["allocated_device"], inner_value["original_layer_ids"],
                                       inner_value["unique_task_id"], inner_value["in_map"], inner_value["N"],
                                       inner_value["M"], inner_value["conv_idx"]) for inner_index, inner_value in
                outer_value.items()
            } for outer_index, outer_value in jsonInput["group_blocks"].items()
        }
        return

    def fetch_current_block(self):
        block = None
        for outer_val in self.outer_blocks.values():
            for inner_val in outer_val.values():
                if self.current_block == inner_val.block_id:
                    block = inner_val
                    break
            if block != None:
                break
        return block

    def serialise(self):
        jsonObject = {
            "dnn_type": self.dnn_type,
            "source": self.source,
            "deadline": int(self.deadline.timestamp() * 1000),
            "estimated_finish_time": int(self.estimated_finish_time.timestamp() * 1000),
            "estimated_start_time": int(self.estimated_start_time.timestamp() * 1000),
            "dnn_id": self.dnn_id,
            "current_block": self.current_block,
            "input_part_count": self.input_part_count,
            "N": self.N,
            "M": self.M,
            "conv_idx": self.conv_idx,
            "outer_blocks": {
                outer_index: {
                    inner_index: {
                        "estimated_finish_time": int(inner_value.estimated_finish_time.timestamp() * 1000),
                        "estimated_start_time": int(inner_value.estimated_start_time.timestamp() * 1000),
                        "group_block_id": inner_value.group_block_id,
                        "block_id": inner_value.block_id,
                        "allocated_device": inner_value.allocated_device,
                        "unique_task_id": inner_value.unique_task_id,
                        "original_layer_ids": inner_value.inner_layer_ids,
                        "N": inner_value.N,
                        "M": inner_value.M,
                        "conv_idx": inner_value.conv_idx,
                        "in_map": {
                            "x1": inner_value.input_tile.x1,
                            "x2": inner_value.input_tile.x2,
                            "y1": inner_value.input_tile.y1,
                            "y2": inner_value.input_tile.y2
                        },
                        "output_upload_start_time": int(inner_value.output_upload_start_time),
                        "state_update_comm_start": int(inner_value.state_update_comm_start)
                    } for inner_index, inner_value in outer_value.items()
                } for outer_index, outer_value in self.outer_blocks.items()
            }

        }
        return json.dumps(jsonObject, indent=4)


class TaskBlock:
    # estimated start time of task
    estimated_start_time = datetime.datetime.now()

    # estimated finish time of task
    estimated_finish_time = datetime.datetime.now()

    group_block_id = int()

    block_id = int()
    # hostname of the device task has been allocated to
    allocated_device = ""

    # original layer ids of partitioned block
    inner_layer_ids = []

    # unique id assigned to task
    unique_task_id = int()

    # Tile Region of input data
    input_tile = None

    # N part of block
    N = int()

    # M part config of block
    M = int()

    # CONV_ID of block
    conv_idx = int()

    # State Update Start Time (Timestamp)
    state_update_comm_start = datetime.datetime.now()

    # Output comm time
    output_upload_start_time = datetime.datetime.now()

    def __init__(self, estimated_start=0, estimated_finish=0, group_block_id=0, block_id=0, allocated_device="",
                 inner_layer_ids=[], unique_task_id=0, in_map=None, N=0, M=0, conv_idx=0, state_update_comm_time=0,
                 output_upload_start_time=0):
        if in_map is not None:
            self.input_tile = TileRegion(
                in_map["x1"], in_map["y1"], in_map["x2"], in_map["y2"])
        base_datetime = datetime.datetime(1970, 1, 1)
        self.estimated_start_time = base_datetime + \
                                    (datetime.timedelta(0, 0, 0, int(estimated_start)))
        self.estimated_finish_time = base_datetime + \
                                     (datetime.timedelta(0, 0, 0, int(estimated_finish)))
        self.group_block_id = int(group_block_id)
        self.block_id = int(block_id)
        self.allocated_device = allocated_device

        inner_layer_ids = [int(item) for item in inner_layer_ids]
        self.unique_task_id = int(unique_task_id)

        self.N = N
        self.M = M
        self.conv_idx = conv_idx
        self.state_update_comm_start = base_datetime + (datetime.timedelta(0, 0, 0, int(state_update_comm_time)))
        self.output_upload_start_time = base_datetime + (datetime.timedelta(0, 0, 0, int(output_upload_start_time)))
        return


class TileRegion:
    x1 = int()
    x2 = int()
    y1 = int()
    y2 = int()

    def __init__(self, x1, y1, x2, y2):
        self.x1 = int(x1)
        self.x2 = int(x2)
        self.y1 = int(y1)
        self.y2 = int(y2)
