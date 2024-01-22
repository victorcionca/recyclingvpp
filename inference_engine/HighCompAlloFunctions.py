import Constants
import logging
import OutboundComm
import OutboundComms
import OutboundCommTypes
import utils
import Globals
from datetime import datetime as dt
from datetime import timedelta as td
from typing import Dict, List
from typing import Any


# dnn_id
# deadline
def add_high_comp_to_stealing_queue(high_comp_tasks: List):
    Globals.work_stealing_lock.acquire(blocking=True)


    for h_t in high_comp_tasks:
        Globals.work_stealing_queue.append(
            {"dnn_id": h_t["dnn_id"], "deadline": h_t["deadline"]}
        )
    Globals.work_stealing_queue = [
        high_comp_task
        for high_comp_task in Globals.work_stealing_queue
        if is_viable(high_comp_task)
    ]
    Globals.work_stealing_queue.sort(key=lambda x: x["deadline"])
    Globals.work_stealing_lock.release()


def task_search(device_capacity: int, source_device: str):
    if len(Globals.work_stealing_queue) == 0:
        return {"success": False}
    
    result_dict: Dict[str, Any] = {"success": False}
    Globals.work_stealing_lock.acquire(blocking=True)
    if device_capacity < Constants.FTP_LOW_CORE:
        result_dict = {"success": False}
    else:
        start_time = dt.now()

        selectedTask = -1

        for i in range(0, len(Globals.work_stealing_queue)):
            comm_time_ms = 0
            if source_device != "self":
                comm_time_ms = Constants.HIGH_TASK_IMAGE_SIZE_BYTES / Globals.bytes_per_ms
            
            ftp_low_processing_fin = start_time + td(milliseconds=(comm_time_ms + Constants.FTP_LOW_TIME))
            ftp_high_processing_fin = start_time + td(milliseconds=(comm_time_ms + Constants.FTP_HIGH_TIME))

            if ftp_low_processing_fin <= Globals.work_stealing_queue[i]["deadline"]:
                result_dict["success"] = True
                result_dict["N"] = Constants.FTP_LOW_N
                result_dict["M"] = Constants.FTP_LOW_M
                result_dict["start_time"] = int( (start_time + td(milliseconds=comm_time_ms)).timestamp() * 1000 )
                result_dict["finish_time"] = int( ftp_low_processing_fin.timestamp() * 1000 )
                int(Globals.work_stealing_queue[i]["deadline"].timestamp() * 1000)
                selectedTask = i
                break
            elif device_capacity == Constants.FTP_HIGH_CORE and ftp_high_processing_fin < Globals.work_stealing_queue[i]["deadline"]:
                result_dict["success"] = True
                result_dict["N"] = Constants.FTP_HIGH_N
                result_dict["M"] = Constants.FTP_HIGH_M
                result_dict["start_time"] = int( (start_time + td(milliseconds=comm_time_ms)).timestamp() * 1000 )
                result_dict["finish_time"] = int( ftp_high_processing_fin.timestamp() * 1000 )
                result_dict["deadline"] = int(Globals.work_stealing_queue[i]["deadline"].timestamp() * 1000)
                selectedTask = i
                break
        if result_dict["success"]:
            Globals.work_stealing_queue.pop(selectedTask)

    Globals.work_stealing_lock.release()
    return result_dict


def is_viable(high_comp_task: Dict):
    viable = False
    comm_time = Constants.HIGH_TASK_SIZE_BYTES / Globals.bytes_per_ms
    ftp_high_processing_window = dt.now() + td(
        milliseconds=comm_time + Constants.FTP_HIGH_TIME
    )

    if ftp_high_processing_window < high_comp_task["deadline"]:
        viable = True
    else:
        logging.info(f"TASK DEADLINE VIOLATED {high_comp_task['dnn_id']}")

        state_update_comm = OutboundComm.OutboundComm(
            comm_time=dt.now(),
            comm_type=OutboundCommTypes.OutboundCommType.VIOLATED_DEADLINE,
            payload={"dnn_id": high_comp_task["dnn_id"]},
            dnn_id=high_comp_task["dnn_id"],
            version=-10,
        )
        OutboundComms.deadlineViolated(comm_item=state_update_comm)

    return viable
