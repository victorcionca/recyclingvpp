from typing import Dict, Union
from ResultBlock import ResultBlock
from LinkAct import LinkAct
from ...utils.DataProcessing import *
import datetime


class HighCompResult:
    def __init__(self, uniqueDnnId: int = 0, dnnId: str = "", srcHost: str = "", deadline: datetime.datetime = datetime.datetime.now(), estimatedStart: datetime.datetime = datetime.datetime.now(), estimatedFinish: datetime.datetime = datetime.datetime.now(),
                 tasks: Dict[str, ResultBlock] = {}, startingConvidx: str = "", lastCompleteConvidx: str = "", uploadData: LinkAct = LinkAct(), version: int = 0):
        self.unique_dnn_id = uniqueDnnId
        self.dnn_id = dnnId
        self.srcHost = srcHost
        self.deadline = deadline
        self.estimatedStart = estimatedStart
        self.estimatedFinish = estimatedFinish
        self.version = version
        self.tasks = tasks
        self.starting_convidx = startingConvidx
        self.upload_data = uploadData
        self.last_complete_convidx = lastCompleteConvidx

    def generateFromDict(self, result_json: dict):
        self.unique_dnn_id = int(result_json["unique_dnn_id"])
        self.dnn_id = result_json["dnn_id"]
        self.srcHost = result_json["srcHost"]
        self.deadline = from_ms_since_epoch(result_json["deadline"])
        self.version = int(result_json["version"])

        self.estimatedStart = from_ms_since_epoch(
            result_json["estimatedStart"])
        self.estimatedFinish = from_ms_since_epoch(
            result_json["estimatedFinish"])
        self.starting_convidx = result_json["startingConvidx"]
        self.last_complete_convidx = result_json["lastCompleteConvidx"]

        up_data = LinkAct()
        up_data.generateFromJson(result_json["uploadData"])
        self.upload_data = up_data

        task_list = {}
        for convidx, convblock in result_json["tasks"].items():
            res_block = ResultBlock()
            res_block.generateFromDict(convblock)
            task_list[convidx] = res_block
        self.tasks = task_list

        return

    def high_comp_result_to_dict(self) -> dict:
        result = {
            "unique_dnn_id": self.unique_dnn_id,
            "version": self.version,
            "dnn_id": self.dnn_id,
            "srcHost": self.srcHost,
            "deadline": int((self.deadline.timestamp()) * 1000),
            "estimatedStart": int((self.estimatedStart.timestamp()) * 1000),
            "estimatedFinish": int((self.estimatedFinish.timestamp()) * 1000),
            "tasks": {k: v.result_block_to_dict() for k, v in self.tasks.items()},
            "starting_convidx": self.starting_convidx,
            "upload_data": self.upload_data.link_act_to_dict(),
            "lastCompleteConvidx": self.last_complete_convidx
        }
        return result
