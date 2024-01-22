import Globals
import logging
from datetime import datetime as dt
from datetime import timedelta as td
import OutboundComms
import utils
import random
import rest_functions
from typing import Dict, Any
import HighCompAlloFunctions
last_poll = dt.now()


def stealing_loop():
    global last_poll
    # Do not submit work requests while capacity is unavailable or a request is already in the system.
    if utils.capacity_gatherer() > 2:
        return

    if dt.now() < (last_poll + td(milliseconds=300)):
        return
    
    logging.info(f"POSTING WORK REQUEST: REQUESTING WORK {Globals.request_counter}")
    temp_client_list = random.sample(Globals.client_list, len(Globals.client_list))

    res: Dict[str, Any] = HighCompAlloFunctions.task_search(utils.capacity_gatherer(), "self")

    if(res["success"]):
        res["source_host"] = "self"
        rest_functions.general_allocate_and_forward_function(res)
    else:
        for client in temp_client_list:
            result: Dict[str, Any] = OutboundComms.PollingRequest(Globals.request_counter, utils.capacity_gatherer(), client)
            if result["success"]:
                result["source_host"] = client
                rest_functions.general_allocate_and_forward_function(result)
                break
            

    logging.info("WORK_REQUEST SUCCESS")
    Globals.request_counter += 1
    last_poll = dt.now()

    return
