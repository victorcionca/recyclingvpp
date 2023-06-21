import Globals
from datetime import datetime as dt
import OutboundComms
import OutboundComm
import OutboundCommTypes
import Constants


def ResultsQueueLoop():
    while True:
        result_obj = Globals.results_queue.get(block=True)
        finish_time = dt.now()
        
        task_id: str = result_obj["TaskID"]

        Globals.work_queue_lock.acquire()
        for i in range(1, Constants.CORE_COUNT + 1):
            if Globals.core_map[i] == task_id:
                Globals.core_map[i] = -1

        dnn_core_usage = (Globals.dnn_hold_dict[task_id].m * Globals.dnn_hold_dict[task_id].n)
        Globals.core_usage = Globals.core_usage - dnn_core_usage
        
        version = Globals.dnn_hold_dict[task_id].version
        del Globals.thread_holder[task_id]
        del Globals.dnn_hold_dict[task_id]
        Globals.work_queue_lock.release()
                    
        payload = {
            "dnn_id": task_id,
            "finish_time": int(finish_time.timestamp() * 1000)
        }

        state_update_comm = OutboundComm.OutboundComm(comm_time=dt.now(), comm_type=OutboundCommTypes.OutboundCommType.STATE_UPDATE, payload=payload, dnn_id=task_id, version=version)
        OutboundComms.add_task_to_queue(state_update_comm)

    return
