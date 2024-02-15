import Globals
import logging
from datetime import datetime as dt
from datetime import timedelta as td
import Constants
import OutboundComms
import utils
import random
import rest_functions
from typing import Dict, Any, List
import HighCompAlloFunctions
last_poll = dt.now()


def stealing_loop():
    global last_poll
    # Do not submit work requests while capacity is unavailable or a request is already in the system.
    if utils.capacity_gatherer() > 2:
        return

    if dt.now() < (last_poll + td(milliseconds=100)):
        return
    
    logging.info(f"POSTING WORK REQUEST: REQUESTING WORK {Globals.request_counter}")
    temp_client_list = random.sample(Globals.client_list, len(Globals.client_list))

    result: Dict[str, Any] = HighCompAlloFunctions.task_search(Constants.CORE_COUNT - utils.capacity_gatherer(), Constants.CLIENT_ADDRESS)

    if not result["success"]:
        result = poll_remotes(temp_client_list)
        
    if result["success"]:
        logging.info(f"{result}")
        logging.info(f"Stole Task {result['dnn_id']}")
        OutboundComms.generate_high_comp_request(result)
        rest_functions.general_allocate_and_forward_function(result)

    logging.info("WORK_REQUEST SUCCESS")
    Globals.request_counter += 1
    last_poll = dt.now()

    return


def poll_remotes(temp_client_list: List[str]) -> Dict:
    result = {"success": False}

    for client in temp_client_list:
        result: Dict[str, Any] = OutboundComms.PollingRequest(Globals.request_counter, Constants.CORE_COUNT - utils.capacity_gatherer(), client)
        if result["success"]:
            break
    return result