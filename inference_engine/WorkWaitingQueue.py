import Globals
import Constants
from datetime import datetime as dt, timedelta
import inference_engine_e2e_with_ipc

# import InferenceTestObj
from threading import Thread
import utils
import OutboundComm
import OutboundComms
import logging
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

load_result = inference_engine_e2e_with_ipc.LoadImage(None, ["0"])


def work_loop():
    if len(Globals.work_waiting_queue) == 0:
        return
    else:
        logging.info("Work available")

    if (
        utils.capacity_gatherer() + Globals.work_waiting_queue[0]["cores"]
        > Constants.CORE_COUNT
    ):
        logging.info("Capacity Filled")
        return
    else:
        logging.info("Capacity Available")

    free_cores = []

    for core, task_id in Globals.core_map.items():
        if (
            len(task_id) == 0
            and len(free_cores) < Globals.work_waiting_queue[0]["cores"]
        ):
            free_cores.append(core)

    work_item = Globals.work_waiting_queue.pop(0)

    for i in free_cores:
        Globals.core_map[i] = work_item

    start_PartitionProcess(work_item, free_cores)

    return


def start_PartitionProcess(work_item, free_cores):
    logging.info(f"TASK CREATE: \t{work_item['TaskID']} - {dt.now()}")

    # ["data", "shape", "N", "M", "cores", "TaskID"]
    x = inference_engine_e2e_with_ipc.PartitionProcess(
        {
            "data": load_result["data"],
            "shape": load_result["shape"],
            "N": work_item["N"],
            "M": work_item["M"],
            "cores": free_cores,
            "TaskID": work_item["TaskID"],
        }
    )

    # x = InferenceTestObj.InferenceTestObj({
    #     "N": work_item["N"],
    #     "M": work_item["M"],
    #     "cores": free_cores,
    #     "TaskID": work_item["TaskID"]}, work_item["finish_time"])

    logging.info(f"TASK START: \t{work_item['TaskID']} - {dt.now()}")

    Globals.thread_holder[work_item["TaskID"]] = x

    x.start()
    Globals.local_capacity += int(work_item["N"]) * int(work_item["M"])


def add_task(work_item: dict):
    Globals.work_waiting_queue.append(work_item)


def worker_watcher():
    task_id_fin_time_mapping = {
        work_item["TaskID"]: work_item
        for work_item in Globals.core_map.values()
        if len(work_item.keys()) != 0
    }

    for dnn_id, work_item in task_id_fin_time_mapping.items():
        if work_item["finish_time"] < dt.now():
            Globals.halt_queue.append(dnn_id)
            logging.info(f"TASK VIOL: \t{dnn_id} - {dt.now()}")
            logging.info(f"TASK EXCPT: \t{dnn_id} - {work_item['finish_time']}")

            state_update_comm = OutboundComm.OutboundComm(
                comm_time=dt.now(),
                comm_type=OutboundCommTypes.OutboundCommType.VIOLATED_DEADLINE,
                payload={"dnn_id": dnn_id},
                dnn_id=dnn_id,
                version=-10,
            )
            OutboundComms.deadlineViolated(comm_item=state_update_comm)
    return


def halt_function():
    while len(Globals.halt_queue) != 0:
        dnn_id = Globals.halt_queue.pop(0)

        if dnn_id in Globals.thread_holder.keys():
            process_thread = Globals.thread_holder[dnn_id]
            process_thread.halt()

            logging.info(f"Halted Task: {dnn_id}")
            logging.info(f"CoreMap: {Globals.core_map}")

            for i in range(0, len(Globals.core_map.keys())):
                if len(Globals.core_map[i].keys()) != 0 and Globals.core_map[i]["TaskID"] == dnn_id:
                    Globals.core_map[i] = {}
                    Globals.local_capacity -= 1

            del Globals.thread_holder[dnn_id]
        return
