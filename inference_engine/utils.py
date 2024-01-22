import Experiment_Globals as Experiment_Globals
import Globals


def add_task_to_event_queue(event_item: dict):
    Experiment_Globals.queue_lock.acquire(blocking=True)
    Experiment_Globals.event_queue.append(event_item)
    Experiment_Globals.event_queue.sort(key=lambda x: x["time"])
    Experiment_Globals.queue_lock.release()
    return


def capacity_gatherer():
    # return Globals.local_capacity
    cap = 0
    for usage in Globals.core_map.values():
        if len(usage.keys()) != 0:
            cap += 1
    return cap + int(Globals.low_active) # type: ignore


def parse_source_device_id(dnn_id: str):
    return dnn_id.split("_")[0]
