import Globals
from datetime import datetime as dt
import OutboundComms
import OutboundComm
import OutboundCommTypes
import Constants
import logging


def ResultsQueueLoop():
    if Globals.results_queue.empty():
        return

    result_obj = Globals.results_queue.get(block=True)
    finish_time = dt.now()

    logging.info("RESULT FETCHED")

    task_id: str = result_obj["TaskID"]

    logging.info(f"ResultsQueueManager: Completed Task: {task_id}")
    logging.info(f"ResultsQueueManager: CoreMap: {Globals.core_map}")

    for i in range(0, Constants.CORE_COUNT):
        if len(Globals.core_map[i].keys()) != 0 and Globals.core_map[i]["TaskID"] == task_id:
            Globals.core_map[i] = {}
            Globals.local_capacity -= 1

    logging.info(f"ResultsQueueManager: CoreMap: {Globals.core_map}")

    if task_id in Globals.thread_holder.keys():
        del Globals.thread_holder[task_id]

    payload = {"dnn_id": task_id, "finish_time": int(finish_time.timestamp() * 1000)}

    logging.info(f"TASK FIN: \t{task_id} - {finish_time}")
    state_update_comm = OutboundComm.OutboundComm(
        comm_time=dt.now(),
        comm_type=OutboundCommTypes.OutboundCommType.STATE_UPDATE,
        payload=payload,
        dnn_id=task_id,
    )

    OutboundComms.stateUpdate(state_update_comm)

    return
