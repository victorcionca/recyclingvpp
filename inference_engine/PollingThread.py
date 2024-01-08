import time
import Globals
import Constants
import requests
import logging
from datetime import datetime as dt

def stealing_loop():
    request_counter = 0

    while True:
        # Do not submit work requests while capacity is unavailable or a request is already in the system.
        while capacity_gatherer() > 2 or Globals.work_request_lock.locked():
            continue

       
        Globals.work_request_lock.acquire(blocking=True)
        logging.info(f"POSTING WORK REQUEST: REQUESTING WORK {request_counter}")
        PollingRequest(request_counter)
        request_counter += 1
        time.sleep(1/1000)
    return

def PollingRequest(request_counter):
    success = False
    url = f"http://{Constants.CONTROLLER_HOST_NAME}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.CONTROLLER_HIGH_WORK_REQUEST}"
    body = {"request_counter": request_counter, "request_id": f"{dt.now().timestamp()}"}
    headers = {
        "Content-Type": "application/json",
    }
    while not success:
        try:
            response = requests.post(url, json=body, headers=headers)

            success = True
            if response.status_code != 200:
                logging.info("ERROR REQUEST NOT RECEIVED")
                success = False
            else:
                logging.info("WORK_REQUEST SUCCESS")
        except Exception as e:
            logging.info(f"ELoop: Failed to reach contr - {e}")

def capacity_gatherer():
    cap = 0
    for core, usage in Globals.core_map.items():
        if usage != "":
            cap += 1
    return cap