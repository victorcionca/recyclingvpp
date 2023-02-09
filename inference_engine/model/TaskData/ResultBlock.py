from typing import Dict, Optional, Union
from datetime import datetime as dt
from Task import Task
from LinkAct import LinkAct
from ...utils.DataProcessing import *


class ResultBlock:
    def __init__(self, N: int = 0, M: int = 0, partitioned_tasks: Dict[int, Task] = {}, assembly_upload_windows: Dict[int, LinkAct] = {}, state_update: LinkAct = LinkAct(), assembly_host: str = "", completed: bool = False, assembly_fin_time: dt = dt.now(), assembly_start_time: dt = dt.now(), state_update_fin_time: dt = dt.now()):
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

    
    def generateFromDict(self, obj: dict):
        self.N = int(obj["N"])
        self.M = int(obj["M"])
        self.assembly_host = str(obj["assembly_host"])
        self.completed = bool(obj["completed"])

        self.assembly_fin_time = from_ms_since_epoch(obj["assembly_fin_time"])
        self.assembly_start_time = from_ms_since_epoch(obj["assembly_start_time"])
        self.state_update_fin_time = from_ms_since_epoch(obj["state_update_fin_time"])

        partitioned_task_dict = {}

        for partition in obj["partitioned_tasks"]:
            task = Task()
            task.generateFromDict(partition["task"])
            partitioned_task_dict[partition["id"]] = task

        self.partitioned_tasks = partitioned_task_dict

        assembly_upload_dict = {}

        for assembly in obj["assembly_upload_windows"]:
            link = LinkAct()
            link.generateFromJson(assembly["window"])
            assembly_upload_dict["id"] = link

        self.assembly_upload_windows = assembly_upload_dict

        state_update_obj = LinkAct()
        state_update_obj.generateFromJson(obj["state_update"])
        self.state_update = state_update_obj


    def result_block_to_dict(self) -> dict:
        result_block_dict = {
            'partitioned_tasks': [{"id": task_id, "task": task.task_to_dict()} for task_id, task in self.partitioned_tasks.items()],
            'assembly_upload_windows': [{"id": idx, "window": link_act.link_act_to_dict()} for idx, link_act in self.assembly_upload_windows.items()],
            'state_update': self.state_update.link_act_to_dict(),
            'N': self.N,
            'M': self.M,
            'assembly_host': self.assembly_host,
            'completed': self.completed,
            'assembly_fin_time': int((self.assembly_fin_time.timestamp()) * 1000),
            'assembly_start_time': int((self.assembly_start_time.timestamp()) * 1000),
            'state_update_fin_time': int((self.state_update_fin_time.timestamp()) * 1000)
        }
        return result_block_dict

