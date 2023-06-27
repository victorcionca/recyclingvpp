import Globals
import Constants
from datetime import datetime as dt
import inference_engine_e2e_with_ipc

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
        
        if Globals.core_usage + Globals.work_waiting_queue[0]["cores"] > Constants.CORE_COUNT or len(Globals.work_waiting_queue) == 0:
            Globals.work_queue_lock.release()
            continue

        free_cores = []

        for core, task_id in Globals.core_map.items():
            if task_id == -1:
                free_cores.append(core)
                break

        if Globals.work_waiting_queue[0]["start_time"] <= dt.now():
            work_item = Globals.work_waiting_queue.pop(0)
            
            for i in free_cores:
                Globals.core_map[i] = work_item["TaskID"]

            Globals.core_usage = Globals.core_usage + work_item["cores"]

            # ["data", "shape", "N", "M", "cores", "TaskID"]
            Globals.thread_holder[work_item["TaskID"]] = inference_engine_e2e_with_ipc.PartitionProcess({
                "data": work_item["data"], 
                "shape": work_item["shape"], 
                "N": work_item["N"], 
                "M": work_item["M"], 
                "cores": free_cores, 
                "TaskID": work_item["TaskID"]})

        Globals.work_queue_lock.release()
    return


# Assumes that lock has been acquired before accessing
def add_task(work_item: dict):
    Globals.work_waiting_queue.append(work_item)
    Globals.work_waiting_queue.sort(key=lambda x: x["start_time"])
