import Globals
def add_task_to_event_queue(event_item: dict):
    Globals.queue_lock.acquire(blocking=True)
    Globals.event_queue.append(event_item)
    Globals.event_queue.sort(key=lambda x: x["time"])
    Globals.queue_lock.release()
    return