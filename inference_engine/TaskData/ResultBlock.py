from typing import Dict, Optional, Union
import datetime
from Task import Task
from LinkAct import LinkAct


class ResultBlock:
    def __init__(self, N: int, M: int, partitioned_tasks: Dict[int, Task], assembly_upload_windows: Dict[int, LinkAct], state_update: LinkAct, assembly_host: str, completed: bool, assembly_fin_time: datetime.datetime, assembly_start_time: datetime.datetime, state_update_fin_time: datetime.datetime):
        self.partitioned_tasks = partitioned_tasks
        self.assembly_upload_windows = assembly_upload_windows
        self.state_update = state_update
        self.N = N
        self.M = M
        self.assembly_host = assembly_host
        self.completed = completed
        self.assembly_fin_time = assembly_fin_time
        self.assembly_start_time = assembly_start_time
        self.state_update_fin_time = state_update_fin_time
