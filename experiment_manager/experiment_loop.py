from Constants import *
import Globals
import datetime
import EventType
import random
import requests
from datetime import datetime as dt

def run_loop():
    deadline = dt.now()
    dnn_id_counter = 0
    current_trace_item = -2
    # NEED TO BLOCK QUEUE
    while not Globals.EXPERIMENT_START:
        continue

    while dt.now() < Globals.EXPERIMENT_FINISH_TIME:
        Globals.queue_lock.acquire(blocking=True)
        
        now_time = datetime.datetime.now()
        if len(Globals.event_queue) != 0 and Globals.event_queue[0]["time"] <= now_time:
            current_item: dict = Globals.event_queue.pop(0)
            
            event_time = current_item["time"]
            
            if current_item["event_type"] == EventType.EventTypes.OBJECT_DETECT_START:
                deadline = current_item["time"] + \
                    datetime.timedelta(seconds=FRAME_RATE)
            elif current_item["event_type"] == EventType.EventTypes.OBJECT_DETECT_FINISH:
                current_trace_item = Globals.trace_list.pop(0)
                if current_trace_item != -1:
                    generate_low_comp_request(
                        deadline=deadline, dnn_id=dnn_id_counter)
                    dnn_id_counter = dnn_id_counter + 1
            elif current_item["event_type"] == EventType.EventTypes.LOW_COMP_FINISH:
                finish_time = current_item["time"]
                print(f'{current_item["time"].strftime("%Y-%m-%d %H:%M:%S:%f")} LOW EXPECTED FIN')
                print(f'{now_time.strftime("%Y-%m-%d %H:%M:%S:%f")} NOW')

                issue_low_comp_update(current_item["dnn_id"], current_item["time"])
                
                if(current_trace_item > 0):
                    generate_high_comp_request(deadline=deadline, dnn_id=dnn_id_counter, task_count = current_trace_item)
                    dnn_id_counter = dnn_id_counter + 1

        Globals.queue_lock.release()
    print("Done")
    return

def issue_low_comp_update(dnn_id: str, time: dt):
    data = {
        "dnn_id": dnn_id,
        "finish_time": int(dt.now().timestamp() * 1000)
    }

    headers = {
        "Content-Type": "application/json",
    }

    url_low_cap = f"http://127.0.0.1:{REST_PORT}{LOW_CAP}"
    response_low_cap = requests.post(url_low_cap, json={}, headers=headers)

    url = f"http://{CONTROLLER_HOST_NAME}:{CONTROLLER_DEFAULT_PORT}{CONTROLLER_STATE_UPDATE}"
    response = requests.post(url, json=data, headers=headers)
    return

def generate_low_comp_request(deadline: datetime.datetime, dnn_id: int):
    data = {
        "dnn_id": str(dnn_id),
        "deadline": int(deadline.timestamp() * 1000),
    }

    headers = {
        "Content-Type": "application/json",
    }

    url = f"http://{CONTROLLER_HOST_NAME}:{CONTROLLER_DEFAULT_PORT}{CONTROLLER_LOW_COMP_ALLOCATION}"
    response = requests.post(url, json=data, headers=headers)
    return


def generate_high_comp_request(deadline: datetime.datetime, dnn_id: int, task_count: int):
    data = {
        "dnn_id": str(dnn_id),
        "deadline": int(deadline.timestamp() * 1000),
        "task_count": task_count
    }

    headers = {
        "Content-Type": "application/json",
    }

    url = f"http://{CONTROLLER_HOST_NAME}:{CONTROLLER_DEFAULT_PORT}{CONTROLLER_HIGH_COMP_ALLOCATION}"
    response = requests.post(url, json=data, headers=headers)
    return
