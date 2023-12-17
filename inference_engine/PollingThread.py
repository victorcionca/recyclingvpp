import time
import Globals
import Constants
import requests


def stealing_loop():
    while True:
        # Do not submit work requests while capacity is unavailable or a request is already in the system.
        while Globals.active_capacity > 2 or Globals.work_request_lock.locked():
            continue

        url = f"http://{Constants.CONTROLLER_HOST_NAME}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.CONTROLLER_HIGH_WORK_REQUEST}"
        Globals.work_request_lock.acquire(blocking=True)
        requests.post(url, json={"capacity": Globals.active_capacity})
        time.sleep(1/1000)
    return
