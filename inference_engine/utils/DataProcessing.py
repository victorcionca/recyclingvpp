from datetime import datetime
from typing import List, Tuple

from inference_engine.model.AssemblyHoldItem import AssemblyHold
from .. import Globals


def from_ms_since_epoch(ms: str) -> datetime:
    return datetime.fromtimestamp(int(ms) / 1000.0)


# All of the following functions
# assume that the lock has been 
# acquired before calling them #
def check_if_dnn_pruned(dnn_id: str) -> bool:
    result = False
    result = dnn_id in Globals.prune_list
    return result


def check_if_dnn_halted(dnn_id: str, dnn_version: int) -> bool:
    result: bool = False

    if dnn_id in Globals.halt_list.keys():
        result = dnn_version in Globals.halt_list[dnn_id]

    return result


def add_item_to_assembly_hold_list(deadline: datetime, dnn_id: str, convidx: str, assembly_data: bytes, shape: list[int]):
    Globals.assembly_hold_list.append(AssemblyHold(
        deadline=deadline, dnn_id=dnn_id, convidx=convidx, assembly_data=assembly_data, shape=shape))

    Globals.assembly_hold_list = [item for item in Globals.assembly_hold_list if item.deadline <= datetime.now()]

def fetch_item_from_assembly_hold_list(dnn_id: str, convidx: str) -> Tuple[bool, bytes, List[int]]:
    result: Tuple[bool, bytes, List[int]] = False, bytes(), list[int]()

    for item in Globals.assembly_hold_list:
        if item.convidx == convidx and item.dnn_id == dnn_id:
            result = True, item.assembly_data, item.shape
            break
    
    Globals.assembly_hold_list = [item for item in Globals.assembly_hold_list if item.deadline <= datetime.now()]

    return result
