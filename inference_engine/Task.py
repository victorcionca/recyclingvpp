from datetime import datetime as dt
import LinkAct
import DataProcessing


class Task:

    def __init__(self, uniqueTaskId: int = 0, dnnId: str = "", convidx: str = "", previousConv: int = 0,
                 partitionBlockId: int = 0, n: int = 0, m: int = 0, estimatedStart: dt = dt.now(), estimatedFinish: dt = dt.now(), actualFinish: dt = dt.now(),
                 allocatedHost: str = "", inputData: LinkAct.LinkAct = LinkAct.LinkAct(), taskOutputSizeBytes: int = 0):
        self.unique_task_id = uniqueTaskId
        self.dnn_id = dnnId
        self.convidx = convidx
        self.previous_conv = previousConv
        self.partition_block_id = partitionBlockId
        self.completed = False
        self.N = n
        self.M = m
        self.estimated_start = estimatedStart
        self.estimated_finish = estimatedFinish
        self.actual_finish = actualFinish
        self.allocated_host = allocatedHost
        self.input_data = inputData
        self.task_output_size_bytes = taskOutputSizeBytes

    def generateFromDict(self, task_json: dict):
        self.unique_task_id = int(task_json["unique_task_id"])
        self.dnn_id = task_json["dnn_id"]
        self.convidx = task_json["convidx"]
        self.previous_conv = int(task_json["previous_conv"])
        self.partition_block_id = int(task_json["partition_block_id"])
        self.completed = bool(task_json["completed"])
        self.N = int(task_json["N"])
        self.M = int(task_json["M"])
        self.estimated_start = DataProcessing.from_ms_since_epoch(
            task_json["estimated_start"])
        self.estimated_finish = DataProcessing.from_ms_since_epoch(
            task_json["estimated_finish"])
        self.allocated_host = task_json["allocated_host"]

        input_data = LinkAct.LinkAct()
        input_data.generateFromJson(task_json["input_data"])
        self.input_data = input_data
        self.task_output_size_bytes = int(task_json["task_output_size_bytes"])
        self.actual_finish = DataProcessing.from_ms_since_epoch(
            task_json["actual_finish"])
        return

    def task_to_dict(self) -> dict:
        task_dict = {
            'unique_task_id': self.unique_task_id,
            'dnn_id': self.dnn_id,
            'convidx': self.convidx,
            'previous_conv': self.previous_conv,
            'partition_block_id': self.partition_block_id,
            'completed': self.completed,
            'N': self.N,
            'M': self.M,
            'estimated_start': int(self.estimated_start.timestamp() * 1000),
            'estimated_finish': int(self.estimated_finish.timestamp() * 1000),
            'actual_finish': int(self.actual_finish.timestamp() * 1000),
            'allocated_host': self.allocated_host,
            'input_data': self.input_data.link_act_to_dict(),
            'task_output_size_bytes': self.task_output_size_bytes
        }
        return task_dict
