import datetime
from LinkAct import LinkAct

class Task:

    def __init__(self, dnnId: str = None, convidx: str = None, previousConv: int = None,
                 partitionBlockId: int = None, n: int = None, m: int = None, estimatedStart: datetime = None, estimatedFinish: datetime = None,
                 allocatedHost: str = None, inputData: LinkAct = None, taskOutputSizeBytes: int = None):

        self.dnn_id = dnnId
        self.convidx = convidx
        self.previous_conv = previousConv
        self.partition_block_id = partitionBlockId
        self.completed = False
        self.N = n
        self.M = m
        self.estimated_start = estimatedStart
        self.estimated_finish = estimatedFinish
        self.allocated_host = allocatedHost
        self.input_data = inputData
        self.task_output_size_bytes = taskOutputSizeBytes
