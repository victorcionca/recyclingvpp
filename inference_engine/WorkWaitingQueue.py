import Globals
import Constants
from datetime import datetime as dt, timedelta
import inference_engine_e2e_with_ipc
# import InferenceTestObj
from threading import Thread
import rest_functions
import OutboundComm
import OutboundComms
import traceback
import logging
import OutboundCommTypes
#from memory_profiler import profile




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
        
        # print(f"WorkWaitingQueue: Requesting lock, held by {Globals.queue_locker}")
        Globals.work_queue_lock.acquire(blocking=True)
        # print(f"WorkWaitingQueue: Acquired lock")
        Globals.queue_locker = "WorkWaitingQueue"
        Globals.lock_counter += 1
        worker_watcher()

        if len(Globals.work_waiting_queue) == 0 or fetch_core_usage() + Globals.work_waiting_queue[0][
            "cores"] > Constants.CORE_COUNT:
            # print(f"WorkQueueManager: Releasing lock")
            Globals.queue_locker = "N/A"
            Globals.work_queue_lock.release()
            continue

        free_cores = []

        for core, task_id in Globals.core_map.items():
            if task_id == "" and len(free_cores) < Globals.work_waiting_queue[0]["cores"]:
                free_cores.append(core)

        if Globals.work_waiting_queue[0]["start_time"] <= dt.now():
            work_item = Globals.work_waiting_queue.pop(0)

            try:
                start_PartitionProcess(work_item, free_cores)

                for i in free_cores:
                    Globals.core_map[i] = work_item["TaskID"]
            except ValueError:
                logging.info(f"WORKWAITINGQUEUE: DNN FAILED {work_item}")
            except MemoryError as e:
                logging.info(f"WORKWAITINGQUEUE: MEMORY ERROR ON PARTITION START {work_item}\n")
                logging.info(f"CORE_MAP: {Globals.core_map}\n")
                logging.info(f"CORE_MAP: {Globals.work_waiting_queue}\n")

                for i in range(0, len(Globals.core_map.keys())):
                    if Globals.core_map[i] == work_item["TaskID"]:
                        Globals.core_map[i] = ""

                logging.info(e)
                logging.info(traceback.format_exc())
                exit()
                # Globals.work_waiting_queue.append(work_item)

        # print(f"WorkQueueManager: Releasing lock")
        Globals.queue_locker = "N/A"
        Globals.work_queue_lock.release()
    return

#@profile(stream=Globals.inference_mem_prof)
def start_PartitionProcess(work_item, free_cores):
    load_result = inference_engine_e2e_with_ipc.LoadImage(None, work_item["TaskID"])
    data = load_result["data"]
    shape = load_result["shape"]

    logging.info(f"TASK CREATE: \t{work_item['TaskID']} - {dt.now()}")

    # ["data", "shape", "N", "M", "cores", "TaskID"]
    x = inference_engine_e2e_with_ipc.PartitionProcess({
        "data": data,
        "shape": shape,
        "N": work_item["N"],
        "M": work_item["M"],
        "cores": free_cores,
        "TaskID": work_item["TaskID"]})

    # x = InferenceTestObj.InferenceTestObj({
    #     "N": work_item["N"],
    #     "M": work_item["M"],
    #     "cores": free_cores,
    #     "TaskID": work_item["TaskID"]}, work_item["finish_time"])

    logging.info(f"TASK START: \t{work_item['TaskID']} - {dt.now()}")
    x.start()
    Globals.thread_holder[work_item["TaskID"]] = x


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
                logging.info(f"TASK VIOL: \t{dnn_id} - {dt.now()}")
                logging.info(f"TASK EXCPT: \t{dnn_id} - {dnn.estimated_finish}")
                state_update_comm = OutboundComm.OutboundComm(comm_time=dt.now(),
                                                              comm_type=OutboundCommTypes.OutboundCommType.VIOLATED_DEADLINE,
                                                              payload={"dnn_id": dnn_id}, dnn_id=dnn_id, version=-10)
                OutboundComms.add_task_to_queue(state_update_comm)

    # Need to send an outbound comm informing controller task violated deadline

    return
