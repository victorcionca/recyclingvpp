import Constants
import Globals
import DataProcessing
import WorkWaitingQueue
import logging
from datetime import datetime as dt
import OutboundComms

def halt_endpoint(json_request_body):
    Globals.halt_queue.append(json_request_body["dnn_id"])
    return

def general_allocate_and_forward_function(json_request_body):
    
    if not json_request_body["success"]:
        return

    logging.info(f"DEADLINE: {DataProcessing.from_ms_since_epoch(json_request_body['dnn']['finish_time'])}")
    logging.info(f"CURRENT_TIME: {dt.now()}")
    
    if json_request_body["dnn"]["allocated_host"] != "self":
        logging.info(f"REQUESTING DATA: http://{json_request_body['dnn']['source_host']}:{Constants.EXPERIMENT_INFERFACE}{Constants.GET_IMAGE}")
        OutboundComms.getImage(json_request_body['dnn']['source_host'])
        logging.info(f"DATA Transferred: {json_request_body['dnn']['source_host']}")

    logging.info(f"DNN_N {json_request_body['dnn']['N']} DNN_M {json_request_body['dnn']['M']}")

    WorkWaitingQueue.add_task(work_item={
        "start_time": DataProcessing.from_ms_since_epoch(
            json_request_body["dnn"]["start_time"]),
        "N": int(json_request_body["dnn"]["N"]),
        "M": int(json_request_body["dnn"]["M"]),
        "cores": int(json_request_body["dnn"]["M"]) * int(json_request_body["dnn"]["N"]),
        "TaskID": json_request_body["dnn"]["dnn_id"],
        "finish_time": DataProcessing.from_ms_since_epoch(json_request_body["dnn"]["finish_time"])
    })


def capacity_gatherer():
    cap = 0
    for usage in Globals.core_map.values():
        if len(usage) != 0:
            cap += 1
    return cap