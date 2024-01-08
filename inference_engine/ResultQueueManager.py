import Globals
from datetime import datetime as dt
import OutboundComms
import OutboundComm
import OutboundCommTypes
import Constants
import logging
#from memory_profiler import profile

def ResultsQueueLoop():
    while True:
        result_obj = Globals.results_queue.get(block=True)
        finish_time = dt.now()

        logging.info("RESULT FETCHED")
        
        task_id: str = result_obj["TaskID"]

        logging.info(f"ResultQueueManager: Requesting lock, held by {Globals.queue_locker}, id {Globals.lock_counter}")
        Globals.work_queue_lock.acquire(blocking=True)
        logging.info(f"ResultQueueManager: Acquired lock")
        Globals.queue_locker = "ResultsQueueManager"
        Globals.lock_counter += 1
        decrement_counter = 0

        logging.info(f"ResultsQueueManager: Completed Task: {task_id}")
        logging.info(f"ResultsQueueManager: CoreMap: {Globals.core_map}")

        for i in range(0, Constants.CORE_COUNT):
            if Globals.core_map[i] == task_id:
                Globals.core_map[i] = ""
                
        logging.info(f"ResultsQueueManager: CoreMap: {Globals.core_map}")

        version = -1
        if task_id in Globals.dnn_hold_dict.keys():
            version = Globals.dnn_hold_dict[task_id].version
            
            del Globals.dnn_hold_dict[task_id]
            if task_id in Globals.thread_holder.keys():
                del Globals.thread_holder[task_id]

        logging.info(f"ResultQueueManager: Releasing lock")
        Globals.queue_locker = "N/A"
        Globals.work_queue_lock.release()
                    
        payload = {
            "dnn_id": task_id,
            "finish_time": int(finish_time.timestamp() * 1000)
        }
        if version != -1:
            logging.info(f"TASK FIN: \t{task_id} - {finish_time}")
            state_update_comm = OutboundComm.OutboundComm(comm_time=dt.now(), comm_type=OutboundCommTypes.OutboundCommType.STATE_UPDATE, payload=payload, dnn_id=task_id, version=version)
            OutboundComms.add_task_to_queue(state_update_comm)

    return
