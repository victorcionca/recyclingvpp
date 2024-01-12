import Globals
import logging
from datetime import datetime as dt
from datetime import timedelta as td
import OutboundComms
import rest_functions

last_poll = dt.now()

def stealing_loop():
    global last_poll
    # Do not submit work requests while capacity is unavailable or a request is already in the system.
    if rest_functions.capacity_gatherer() > 2:
        return
    
    if dt.now() < (last_poll + td(milliseconds=100)):
        return

    # Globals.work_request_lock.acquire(blocking=True)
    logging.info(f"POSTING WORK REQUEST: REQUESTING WORK {Globals.request_counter}")
    OutboundComms.PollingRequest(Globals.request_counter)
    Globals.request_counter += 1
    last_poll = dt.now()

    return