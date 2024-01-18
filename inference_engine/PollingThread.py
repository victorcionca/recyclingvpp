import Globals
import logging
from datetime import datetime as dt
from datetime import timedelta as td
import OutboundComms
import utils

last_poll = dt.now()


def stealing_loop():
    global last_poll
    # Do not submit work requests while capacity is unavailable or a request is already in the system.
    if utils.capacity_gatherer() > 2:
        return

    if dt.now() < (last_poll + td(milliseconds=300)):
        return
    
    Globals.work_request_lock.acquire()
    logging.info(f"POSTING WORK REQUEST: REQUESTING WORK {Globals.request_counter}")
    OutboundComms.PollingRequest(Globals.request_counter, utils.capacity_gatherer())
    Globals.request_counter += 1
    last_poll = dt.now()

    return
