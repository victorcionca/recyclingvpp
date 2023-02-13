from Constants.Constants import *
import Globals
import datetime
from experiment_manager.enums.EventType import EventTypes
import random
import requests


def run_loop():
    deadline = datetime.datetime.now()
    dnn_id_counter = 0
    # NEED TO BLOCK QUEUE
    while not Globals.EXPERIMENT_START:
        continue

    while datetime.datetime.now() < Globals.EXPERIMENT_FINISH_TIME:
        Globals.queue_lock.acquire(blocking=True)
        if Globals.event_queue[0]["time"] <= datetime.datetime.now():
            current_item: dict = Globals.event_queue.pop(0)

            if current_item["event_type"] == EventTypes.OBJECT_DETECT_START:
                deadline = current_item["time"] + \
                    datetime.timedelta(seconds=FRAME_RATE)
            elif current_item["event_type"] == EventTypes.OBJECT_DETECT_FINISH:
                generate_low_comp_request(
                    deadline=deadline, dnn_id=dnn_id_counter)
                dnn_id_counter = dnn_id_counter + 1
            elif current_item["event_type"] == EventTypes.LOW_COMP_FINISH:
                generate_high_comp_request(deadline=deadline, dnn_id=dnn_id_counter)
                dnn_id_counter = dnn_id_counter + 1

        Globals.queue_lock.release()
    return


def generate_low_comp_request(deadline: datetime.datetime, dnn_id: int):
    random_value = random.random()
    if random_value < P1:

        data = {
            "dnn_id": str(dnn_id),
            "deadline": int(deadline.timestamp() * 1000)
        }

        headers = {
            "Content-Type": "application/json",
        }

        url = f"{CONTROLLER_HOST_NAME}:{CONTROLLER_DEFAULT_PORT}{CONTROLLER_LOW_COMP_ALLOCATION}"
        response = requests.post(url, json=data, headers=headers)
    return


def generate_high_comp_request(deadline: datetime.datetime, dnn_id: int):
    random_value = random.random()
    if random_value < P2:
        
        data = {
            "dnn_id": str(dnn_id),
            "deadline": int(deadline.timestamp() * 1000)
        }

        headers = {
            "Content-Type": "application/json",
        }

        url = f"{CONTROLLER_HOST_NAME}:{CONTROLLER_DEFAULT_PORT}{CONTROLLER_HIGH_COMP_ALLOCATION}"
        response = requests.post(url, json=data, headers=headers)
    return
