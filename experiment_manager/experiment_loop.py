from Constants import *
import Globals
import datetime
import EventType
import random
import requests
import logging
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
                logging.info(f'{current_item["time"].strftime("%Y-%m-%d %H:%M:%S:%f")} LOW EXPECTED FIN')
                logging.info(f'{now_time.strftime("%Y-%m-%d %H:%M:%S:%f")} NOW')

                issue_low_comp_update(current_item["dnn_id"], current_item["time"])
                
                if(current_trace_item > 0):
                    generate_high_comp_request(deadline=deadline, dnn_id=dnn_id_counter, task_count = current_trace_item)
                    dnn_id_counter = dnn_id_counter + 1

        Globals.queue_lock.release()
    logging.info("Done")
    return

def issue_low_comp_update(dnn_id: str, time: dt):
    data = {
        "dnn_id": dnn_id,
        "finish_time": int(dt.now().timestamp() * 1000),
        "request_id": f"{dt.now().timestamp()}"
    }

    headers = {
        "Content-Type": "application/json",
    }

    url = f"http://{CONTROLLER_HOST_NAME}:{CONTROLLER_DEFAULT_PORT}{CONTROLLER_STATE_UPDATE}"
    logging.info(f"COMPLETED DNN {data}")
    success = False
    while not success:
        try:
            response = requests.post(url, json=data, headers=headers)
            logging.info(f"CONTROLLER ACK COMP DNN {data['dnn_id']}")
            success = True
        except Exception as e:
            logging.info(f"ELoop: Failed to reach contr - {e}")
    return

def generate_low_comp_request(deadline: datetime.datetime, dnn_id: int):

    data = {
        "dnn_id": str(dnn_id),
        "deadline": int(deadline.timestamp() * 1000),
        "request_id": f"{dt.now().timestamp()}"
    }

    headers = {
        "Content-Type": "application/json",
    }


    url = f"http://{CONTROLLER_HOST_NAME}:{CONTROLLER_DEFAULT_PORT}{CONTROLLER_LOW_COMP_ALLOCATION}"

    success = False
    while not success:
        try:
            response = requests.post(url, json=data, headers=headers)
            success = True
        except Exception as e:
            logging.info(f"ELoop: Failed to reach contr - {e}")
    return


def generate_high_comp_request(deadline: datetime.datetime, dnn_id: int, task_count: int):
    data = {
        "dnn_id": str(dnn_id),
        "deadline": int(deadline.timestamp() * 1000),
        "task_count": task_count,
        "request_id": f"{dt.now().timestamp()}"
    }

    headers = {
        "Content-Type": "application/json",
    }

    url = f"http://{CONTROLLER_HOST_NAME}:{CONTROLLER_DEFAULT_PORT}{CONTROLLER_HIGH_COMP_ALLOCATION}"
    
    success = False
    while not success:
        try:
            response = requests.post(url, json=data, headers=headers)
            success = True
        except Exception as e:
            logging.info(f"ELoop: Failed to reach contr - {e}")

    return
