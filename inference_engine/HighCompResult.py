from typing import Dict, Union
from LinkAct import LinkAct
import DataProcessing
import datetime


class HighCompResult:

    def __init__(self, dnn_id: str = "", allocated_host: str = "", estimated_start: datetime.datetime = datetime.datetime.now(), estimated_finish: datetime.datetime = datetime.datetime.now(), n: int = 0, m: int = 0, upload_data: LinkAct = LinkAct(), version: int = 0, source_host: str = str()):
        self.dnn_id = dnn_id
        self.allocated_host = allocated_host
        self.estimated_finish = estimated_finish
        self.estimated_start = estimated_start
        self.n = n
        self.m = m
        self.upload_data = upload_data
        self.version = version
        self.source_host = source_host

    def generateFromDict(self, result_json: dict):
        self.allocated_host = result_json["allocated_host"]
        self.dnn_id = result_json["dnn_id"]
        # if self.allocated_host != "self":
        #     up_data = LinkAct()
        #     up_data.generateFromJson(result_json["upload_data"])
        #     self.upload_data = up_data
        self.estimated_start = DataProcessing.from_ms_since_epoch(
            result_json["start_time"])
        self.estimated_finish = DataProcessing.from_ms_since_epoch(
            result_json["finish_time"])
        self.n = int(result_json["N"])
        self.source_host = result_json["source_host"]
        self.m = int(result_json["M"])
        self.version = int(result_json["version"])
        return

    def high_comp_result_to_dict(self) -> dict:
        result = {
            "dnn_id": self.dnn_id,
            "N": self.n,
            "M": self.m,
            "start_time": int((self.estimated_start.timestamp()) * 1000),
            "finish_time": int((self.estimated_finish.timestamp()) * 1000),
            "version": self.version,
            "allocated_host": self.allocated_host,
            "source_host": self.source_host
            # "upload_data": self.upload_data.link_act_to_dict()
        }
        return result
