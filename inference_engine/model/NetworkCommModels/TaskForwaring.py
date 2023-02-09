from ..TaskData.HighCompResult import HighCompResult
from ...inference_engine import deserialize_numpy
import json
import base64


class TaskForwarding:
    def __init__(self, highCompResult: HighCompResult = HighCompResult(), convIdx: str = "",
                 partitionId: int = 0, uniqueTaskId: int = 0, nIdx: int = 0, mIdx: int = 0,
                 topX: int = 0, topY: int = 0, botX: int = 0, botY: int = 0, data: bytes = bytes(), shape: list = []) -> None:

        self.high_comp_result = highCompResult
        self.convidx = convIdx
        self.partition_id = partitionId
        self.unique_task_id = uniqueTaskId
        self.nidx = nIdx
        self.midx = mIdx
        self.top_x = topX
        self.top_y = topY
        self.bot_x = botX
        self.bot_y = botY
        self.data = data
        self.shape = shape

    def create_task_forwarding_from_dict(self, data: dict):
        self.high_comp_result.generateFromDict(data["dnn"])
        self.convidx = data["convidx"]
        self.partition_id = int(data["partition_id"])
        self.unique_task_id = int(data["unique_task_id"])
        self.nidx = int(data["nidx"])
        self.midx = int(data["midx"])
        self.top_x = int(data["top_x"])
        self.top_y = int(data["top_y"])
        self.bot_x = int(data["bot_x"])
        self.bot_y = int(data["bot_y"])
        self.shape = json.loads(data["shape"])
        self.data = base64.b64encode(data["data"].encode('utf-8'))

    def task_forwarding_to_dict(self) -> dict:
        result = {
            "dnn": self.high_comp_result.high_comp_result_to_dict(),
            "convidx": self.convidx,
            "partition_id": self.partition_id,
            "unique_task_id": self.unique_task_id,
            "nidx": self.nidx,
            "midx": self.midx,
            "top_x": self.top_x,
            "top_y": self.top_y,
            "bot_x": self.bot_x,
            "bot_y": self.bot_y,
            "data": (self.data).decode('utf-8'),
            "shape": self.shape,
        }
        return result
