import requests

import Constants
import Globals
import DataProcessing
import OutboundComm
import OutboundComms
import OutboundCommTypes
import HighCompResult
import WorkWaitingQueue

from datetime import datetime as dt

def halt_endpoint(json_request_body):
    dnn_id = json_request_body["dnn_id"]

    if dnn_id in Globals.dnn_hold_dict.keys():
        dnn = Globals.dnn_hold_dict[dnn_id]

        if dnn_id in Globals.thread_holder.keys():
            process_thread = Globals.thread_holder[dnn_id]
            process_thread.halt()

            for i in range(0, len(Globals.core_map.keys())):
                if Globals.core_map[i] == dnn_id:
                    Globals.active_capacity = Globals.active_capacity - 1
                    Globals.core_map[i] = ""
            
            del Globals.thread_holder[dnn_id]
        del Globals.dnn_hold_dict[dnn_id]
    return


def general_allocate_and_forward_function(json_request_body):

    Globals.work_request_lock.release()
    if not json_request_body["success"]:
        return

    dnn_task = HighCompResult.HighCompResult()
    dnn_task.generateFromDict(json_request_body["dnn"])

    print(f"DEADLINE: {dnn_task.estimated_finish}")
    print(f"CURRENT_TIME: {dt.now()}")

    image_data = None
    

    if dnn_task.allocated_host != "self":
        image_data = requests.get(f"http://{dnn_task.allocated_host}:{Constants.REST_PORT}{Constants.TASK_FORWARD}")

    Globals.active_capacity += dnn_task.n * dnn_task.m

    partition_and_process(
        dnn_task=dnn_task, starting_convidx="1", input_data=bytes(), input_shape=[])
    
def increment_capacity(json_request: dict):
    Globals.active_capacity += 1

def lower_capacity(json_request: dict):
    Globals.active_capacity -= 1

def task_allocation_function(json_request_body):
    dnn_task: HighCompResult.HighCompResult = HighCompResult.HighCompResult()
    dnn_task.generateFromDict(json_request_body)

    partition_and_process(dnn_task=dnn_task, starting_convidx="1", input_data=bytes(), input_shape=[])
    return


def partition_and_process(dnn_task: HighCompResult.HighCompResult, starting_convidx: str, input_data: bytes, input_shape: list):
    load_data: dict = {}

    partition_data = {}
    work_item = { # type: ignore
        "start_time": dnn_task.estimated_start,
        "N": dnn_task.n,
        "M": dnn_task.m,
        "cores": dnn_task.n * dnn_task.m,
        "TaskID": dnn_task.dnn_id,
        "finish_time": dnn_task.estimated_finish
    }

    # if not DataProcessing.check_if_dnn_halted(dnn_id=dnn_task.dnn_id, dnn_version=dnn_task.version):
    Globals.dnn_hold_dict[dnn_task.dnn_id] = dnn_task

    WorkWaitingQueue.add_task(work_item=work_item)