from datetime import datetime as dt
from typing import Tuple
import DataProcessing


class LinkAct:
    def __init__(self, isMeta: bool = False, hostNames: Tuple[str, str] = ("", ""), dataSize: int = 0, startFinTime: Tuple[dt, dt] = (dt.now(), dt.now())):
        self.is_meta = isMeta
        self.host_names = hostNames
        self.data_size = dataSize
        self.start_fin_time = startFinTime

    def generateFromJson(self, linkActJson: dict):

        self.is_meta = bool(linkActJson["is_meta"])
        self.host_names = (
            linkActJson["host_names"]["first"], linkActJson["host_names"]["second"])
        self.data_size = int(linkActJson["data_size"])
        self.start_fin_time = (DataProcessing.from_ms_since_epoch(
            linkActJson["start_fin_time"]["first"]), DataProcessing.from_ms_since_epoch(linkActJson["start_fin_time"]["second"]))
        return

    def link_act_to_dict(self) -> dict:
        link_act_dict = {
            'is_meta': self.is_meta,
            'host_names': {
                "first": self.host_names[0],
                "second": self.host_names[1]
            },
            'data_size': self.data_size,
            'start_fin_time': {
                "first": int(self.start_fin_time[0].timestamp() * 1000),
                "second": int(self.start_fin_time[1].timestamp() * 1000)
            }
        }

        return link_act_dict
