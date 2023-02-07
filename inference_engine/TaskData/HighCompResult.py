from typing import Dict, Union
from ResultBlock import ResultBlock
from LinkAct import LinkAct

class HighCompResult:
    def __init__(self, dnnId: str, srcHost: str, deadline: int, estimatedStart: int, estimatedFinish: int,
                 tasks: Dict[str, ResultBlock], startingConvidx: str, uploadData: LinkAct):
        self.dnn_id = dnnId
        self.srcHost = srcHost
        self.deadline = deadline
        self.estimatedStart = estimatedStart
        self.estimatedFinish = estimatedFinish
        self.tasks = tasks
        self.starting_convidx = startingConvidx
        self.upload_data = uploadData
