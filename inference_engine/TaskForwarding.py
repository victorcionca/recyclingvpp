import HighCompResult
from typing import Dict

class TaskForwarding:
    def __init__(self, highCompResult: HighCompResult.HighCompResult = HighCompResult.HighCompResult(), convIdx: int = 0, nIdx: int = 0, mIdx: int = 0, topX: int = 0, topY: int = 0, botX: int = 0, botY: int = 0, data: bytes = bytes(), shape: list = []):
        self.high_comp_result = highCompResult
        self.conv_idx = convIdx,
        self.nidx = nIdx
        self.midx = mIdx
        self.top_x = topX
        self.top_y = topY
        self.bot_x = botX
        self.bot_y = botY
        self.data = data
        self.shape = shape
        self.unique_task_id = f"{highCompResult.dnn_id}_{nIdx + mIdx}"
        return
    
    def create_task_forwarding_from_dict(self, data: Dict):
        self.high_comp_result.generateFromDict(data["dnn"])
        self.conv_idx = data["convidx"]
        self.nidx = int(data["nidx"])
        self.midx = int(data["midx"])
        self.top_x = int(data["top_x"])
        self.top_y = int(data["top_y"])
        self.bot_x = int(data["bot_x"])
        self.bot_y = int(data["bot_y"])
        self.shape = data["shape"]
        self.data = data["data"].encode('utf-8')
        self.unique_task_id = data["unique_task_id"]


    def task_forwarding_to_dict(self) -> Dict:
        result = {
            "dnn": self.high_comp_result.high_comp_result_to_dict(),
            "convidx": self.conv_idx,
            "nidx": self.nidx,
            "midx": self.midx,
            "top_x": self.top_x,
            "top_y": self.top_y,
            "bot_x": self.bot_x,
            "bot_y": self.bot_y,
            "data": (self.data).decode('utf-8'),
            "shape": self.shape,
            "unique_task_id": self.unique_task_id
        }
        return result