from datetime import datetime
from typing import List, Tuple

import Globals


def from_ms_since_epoch(ms: int) -> datetime:
    return datetime.fromtimestamp(int(ms) / 1000.0)


def check_if_dnn_halted(dnn_id: str, dnn_version: int) -> bool:
    result: bool = False

    # if dnn_id in Globals.halt_list.keys():
    #     result = dnn_version in Globals.halt_list[dnn_id]

    return result
