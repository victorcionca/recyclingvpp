from datetime import datetime as dt
from typing import Tuple
import DataProcessing


class LinkAct:
    def __init__(self, startFinTime: Tuple[dt, dt] = (dt.now(), dt.now())):
        self.start_fin_time = startFinTime

    def generateFromJson(self, linkActJson: dict):

        self.start_fin_time = (DataProcessing.from_ms_since_epoch(
            linkActJson["time_window"]["start"]), DataProcessing.from_ms_since_epoch(linkActJson["time_window"]["stop"]))
        return

    def link_act_to_dict(self) -> dict:
        link_act_dict = {
            'time_window': {
                "start": int(self.start_fin_time[0].timestamp() * 1000),
                "stop": int(self.start_fin_time[1].timestamp() * 1000)
            }
        }

        return link_act_dict
