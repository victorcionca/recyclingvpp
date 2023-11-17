import Globals
import Constants
from datetime import datetime as dt, timedelta
# import inference_engine_e2e_with_ipc
import InferenceTestObj
from threading import Thread
import rest_functions
import OutboundComm
import OutboundComms
import OutboundCommTypes


# work_item = { # type: ignore
#         "data": data,
#         "start_time": dnn_task.estimated_start,
#         "shape": shape,
#         "N": dnn_task.n,
#         "M": dnn_task.m,
#         "cores": dnn_task.n * dnn_task.m,
#         "TaskID": dnn_task.dnn_id
#     }

def work_loop():
    while True:
        Globals.work_queue_lock.acquire(blocking=True)
        worker_watcher()

        if len(Globals.work_waiting_queue) == 0 or fetch_core_usage() + Globals.work_waiting_queue[0][
            "cores"] > Constants.CORE_COUNT:
            Globals.work_queue_lock.release()
            continue

        free_cores = []

        for core, task_id in Globals.core_map.items():
            if task_id == "" and len(free_cores) < Globals.work_waiting_queue[0]["cores"]:
                free_cores.append(core)

        if Globals.work_waiting_queue[0]["start_time"] <= dt.now():
            work_item = Globals.work_waiting_queue.pop(0)

            for i in free_cores:
                Globals.core_map[i] = work_item["TaskID"]

            start_PartitionProcess(work_item, free_cores)

        Globals.work_queue_lock.release()
    return


def start_PartitionProcess(work_item, free_cores):
    # load_result = inference_engine_e2e_with_ipc.LoadImage(None, work_item["TaskID"])
    # data = load_result["data"]
    # shape = load_result["shape"]

    print(f"TASK CREATE: \t{work_item['TaskID']} - {dt.now()}")
    # Globals.work_queue_lock.acquire(blocking=True)
    # ["data", "shape", "N", "M", "cores", "TaskID"]
    # x = inference_engine_e2e_with_ipc.PartitionProcess({
    #     "data": data,
    #     "shape": shape,
    #     "N": work_item["N"],
    #     "M": work_item["M"],
    #     "cores": free_cores,
    #     "TaskID": work_item["TaskID"]})

    x = InferenceTestObj.InferenceTestObj({
        "N": work_item["N"],
        "M": work_item["M"],
        "cores": free_cores,
        "TaskID": work_item["TaskID"]}, work_item["finish_time"])

    print(f"TASK START: \t{work_item['TaskID']} - {dt.now()}")
    x.start()
    Globals.thread_holder[work_item["TaskID"]] = x
    # Globals.work_queue_lock.release()


def fetch_core_usage():
    core_usage = 0
    for value in Globals.core_map.values():
        if value != "":
            core_usage = core_usage + 1

    return core_usage


# Assumes that lock has been acquired before accessing
def add_task(work_item: dict):
    Globals.work_waiting_queue.append(work_item)
    Globals.work_waiting_queue.sort(key=lambda x: x["start_time"])


def worker_watcher():
    task_id_list = set([value for value in Globals.core_map.values() if value != ""])

    for dnn_id in task_id_list:
        if dnn_id in Globals.dnn_hold_dict.keys():
            dnn = Globals.dnn_hold_dict[dnn_id]
            if dnn.estimated_finish < dt.now():
                rest_functions.halt_endpoint({"dnn_id": dnn_id, "version": dnn.version})
                print(f"TASK VIOL: \t{dnn_id} - {dt.now()}")
                print(f"TASK EXCPT: \t{dnn_id} - {dnn.estimated_finish}")
                state_update_comm = OutboundComm.OutboundComm(comm_time=dt.now(),
                                                              comm_type=OutboundCommTypes.OutboundCommType.VIOLATED_DEADLINE,
                                                              payload={"dnn_id": dnn_id}, dnn_id=dnn_id, version=-10)
                OutboundComms.add_task_to_queue(state_update_comm)

    # Need to send an outbound comm informing controller task violated deadline

    return
