import Globals
from datetime import datetime as dt


def work_loop():
    while True:
        Globals.work_waiting_queue_lock.acquire()

        free_core = -1

        for core, task_id in Globals.core_map.items():
            if task_id == -1:
                free_core = core
                break

        if free_core != -1:
            Globals.work_waiting_queue_lock.release()
            continue

        if Globals.work_waiting_queue[0]["start_time"] <= dt.now():
            work_item = Globals.work_waiting_queue.pop(0)
            Globals.core_map[free_core] = work_item["work_item"]["TaskID"]
            work_item["work_item"]["core"] = free_core
            Globals.work_queue_lock.acquire()
            Globals.work_queue.put(work_item["work_item"])
            Globals.work_queue_lock.release()

        Globals.work_waiting_queue_lock.release()
    return


def add_task(work_item: dict):
    Globals.work_waiting_queue_lock.acquire()
    Globals.work_waiting_queue.append(work_item)
    Globals.work_waiting_queue.sort(key=lambda x: x["start_time"])
    Globals.work_waiting_queue_lock.release()
