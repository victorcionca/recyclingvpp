import Globals
import OutboundComm
import OutboundComms
import OutboundCommTypes
import HighCompResult
import WorkWaitingQueue
import traceback
from datetime import datetime

def halt_endpoint(json_request_body):
    dnn_id = json_request_body["dnn_id"]
    # version = int(json_request_body["version"])

    if dnn_id in Globals.dnn_hold_dict.keys():
        dnn = Globals.dnn_hold_dict[dnn_id]
        # if dnn.version == version:
        if dnn_id in Globals.thread_holder.keys():
            process_thread = Globals.thread_holder[dnn_id]
            process_thread.halt()

            for i in range(0, len(Globals.core_map.keys())):
                if Globals.core_map[i] == dnn_id:
                    Globals.core_map[i] = ""
            
            del Globals.thread_holder[dnn_id]
        del Globals.dnn_hold_dict[dnn_id]
    return


def general_allocate_and_forward_function(json_request_body):
    dnn_task = HighCompResult.HighCompResult()
    try:
        dnn_task.generateFromDict(json_request_body)
    

        if dnn_task.allocated_host != "self":
            comm_item = OutboundComm.OutboundComm(
                comm_time=datetime.fromtimestamp(
                int(json_request_body["upload_data"]["time_window"]["start"]) / 1000), comm_type=OutboundCommTypes.OutboundCommType.TASK_FORWARD, payload=dnn_task) # type: ignore

            OutboundComms.add_task_to_queue(comm_item=comm_item)

        else:
            print(f"GEN ALLO: {json_request_body}")
            partition_and_process(
                dnn_task=dnn_task, starting_convidx="1", input_data=bytes(), input_shape=[])
    except Exception as e:
        print(f"JSON BODY: {json_request_body}")
        print(e)
        traceback.print_exc() 

def task_allocation_function(json_request_body):
    print(f"TASK ALLO: {json_request_body}")
    dnn_task: HighCompResult.HighCompResult = HighCompResult.HighCompResult()
    dnn_task.generateFromDict(json_request_body)

    partition_and_process(dnn_task=dnn_task, starting_convidx="1", input_data=bytes(), input_shape=[])
    return


def partition_and_process(dnn_task: HighCompResult.HighCompResult, starting_convidx: str, input_data: bytes, input_shape: list):
    load_data: dict = {}

    partition_data = {}
    work_item = { # type: ignore
        "start_time": dnn_task.estimated_start,
        "N": dnn_task.m,
        "M": dnn_task.n,
        "cores": dnn_task.n * dnn_task.m,
        "TaskID": dnn_task.dnn_id
    }

    # if not DataProcessing.check_if_dnn_halted(dnn_id=dnn_task.dnn_id, dnn_version=dnn_task.version):
    Globals.dnn_hold_dict[dnn_task.dnn_id] = dnn_task

    WorkWaitingQueue.add_task(work_item=work_item)