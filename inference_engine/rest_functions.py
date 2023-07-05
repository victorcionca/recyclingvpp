import Constants
import Globals
import inference_engine_e2e_with_ipc
import DataProcessing
import OutboundComm
import OutboundComms
import OutboundCommTypes
import HighCompResult
import WorkWaitingQueue

def halt_endpoint(json_request_body):
    dnn_id = json_request_body["dnn_id"]
    version = int(json_request_body["version"])

    if dnn_id in Globals.dnn_hold_dict.keys():
        dnn = Globals.dnn_hold_dict[dnn_id]
        if dnn.version == version:
            if dnn_id in Globals.thread_holder.keys():
                process_thread = Globals.thread_holder[dnn_id]
                process_thread.halt()

                for i in range(0, len(Globals.core_map.keys())):
                    if Globals.core_map[i] == dnn_id:
                        Globals.core_map[i] = ""
                
                del Globals.thread_holder[dnn_id]
            del Globals.dnn_hold_dict[dnn_id]
    
    if dnn_id not in Globals.halt_list.keys():
        Globals.halt_list[dnn_id] = []
    
    if version not in Globals.halt_list[dnn_id]:
        Globals.halt_list[dnn_id].append(version)

    return


def general_allocate_and_forward_function(json_request_body):
    dnn_task = HighCompResult.HighCompResult()
    dnn_task.generateFromDict(json_request_body)
    if dnn_task.allocated_host != "self":
        comm_item = OutboundComm.OutboundComm(
            comm_time=dnn_task.upload_data.start_fin_time[0], comm_type=OutboundCommTypes.OutboundCommType.TASK_FORWARD, payload=dnn_task)

        OutboundComms.add_task_to_queue(comm_item=comm_item)

    else:
        partition_and_process(
            dnn_task=dnn_task, starting_convidx="1", input_data=bytes(), input_shape=[])

def task_allocation_function(json_request_body):
    dnn_task: HighCompResult.HighCompResult = HighCompResult.HighCompResult()
    dnn_task.generateFromDict(json_request_body)

    partition_and_process(dnn_task=dnn_task, starting_convidx="1", input_data=bytes(), input_shape=[])
    return


def partition_and_process(dnn_task: HighCompResult.HighCompResult, starting_convidx: str, input_data: bytes, input_shape: list):
    load_data: dict = {}

    data = input_data
    shape = input_shape
    
    if len(input_shape) == 0:
        load_result = inference_engine_e2e_with_ipc.LoadImage(None, dnn_task.dnn_id)

        if isinstance(load_result, dict):
            load_data = load_result
        else:
            return
        
        data = load_result["data"]
        shape = load_result["shape"]

    partition_data = {}
    work_item = { # type: ignore
        "data": data,
        "start_time": dnn_task.estimated_start,
        "shape": shape,
        "N": dnn_task.n,
        "M": dnn_task.m,
        "cores": dnn_task.n * dnn_task.m,
        "TaskID": dnn_task.dnn_id
    }

    if not DataProcessing.check_if_dnn_halted(dnn_id=dnn_task.dnn_id, dnn_version=dnn_task.version):
        Globals.dnn_hold_dict[dnn_task.dnn_id] = dnn_task

        WorkWaitingQueue.add_task(work_item=work_item)