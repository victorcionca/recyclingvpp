import Constants
import Globals
import DataProcessing
import WorkWaitingQueue
import logging
from datetime import datetime as dt
from datetime import timedelta as td
import Experiment_Globals
import EventType
import OutboundComms
import utils


def halt_endpoint(json_request_body):
    Globals.halt_queue.append(json_request_body["dnn_id"])
    return


def general_allocate_and_forward_function(json_request_body):
    if not json_request_body["success"]:
        return

    logging.info(
        f"DEADLINE: {DataProcessing.from_ms_since_epoch(int(json_request_body['finish_time']))}"
    )
    logging.info(f"CURRENT_TIME: {dt.now()}")

    if json_request_body["allocated_host"] != Constants.CLIENT_ADDRESS:
        logging.info(
            f"REQUESTING DATA: http://{json_request_body['source_host']}:{Constants.EXPERIMENT_INFERFACE}{Constants.GET_IMAGE}"
        )
        OutboundComms.getImage(json_request_body["source_host"])
        logging.info(f"DATA Transferred: {json_request_body['source_host']}")

    logging.info(
        f"DNN_N {json_request_body['N']} DNN_M {json_request_body['M']}"
    )

    WorkWaitingQueue.add_task(
        work_item={
            "start_time": DataProcessing.from_ms_since_epoch(
                int(json_request_body["start_time"])
            ),
            "N": int(json_request_body["N"]),
            "M": int(json_request_body["M"]),
            "cores": int(json_request_body["M"])
            * int(json_request_body["N"]),
            "TaskID": json_request_body["dnn_id"],
            "finish_time": DataProcessing.from_ms_since_epoch(
                int(json_request_body["finish_time"])
            ),
            "deadline": DataProcessing.from_ms_since_epoch(int(json_request_body["deadline"]))
        }
    )


def allocate_low_task(json_request: dict) -> None:
    dnn_id: str = json_request["dnn_id"]

    finish_time: dt = dt.now()
    if isinstance(json_request["start_time"], str):
        finish_time = DataProcessing.from_ms_since_epoch(json_request["finish_time"])
    else:
        finish_time = DataProcessing.from_ms_since_epoch(
            int(json_request["finish_time"])
        )

    logging.info(f'{finish_time.strftime("%Y-%m-%d %H:%M:%S:%f")} LOW COMP ALLO FIN')

    utils.add_task_to_event_queue(
        event_item={
            "event_type": EventType.EventTypes.LOW_COMP_FINISH,
            "time": finish_time,
            "dnn_id": dnn_id,
        }
    )
    return


def set_experiment_start_time(json_request: dict):
    start_time: dt = dt.now()

    start_time = DataProcessing.from_ms_since_epoch(int(json_request["start_time"]))

    if Experiment_Globals.SET_A_OR_B:
        start_time = start_time + td(seconds=Constants.FRAME_RATE / 2)

    event_items = len(Experiment_Globals.trace_list)
    Experiment_Globals.queue_lock.acquire(blocking=True)
    for i in range(0, event_items):
        delta = td(seconds=Constants.FRAME_RATE) * i
        Experiment_Globals.event_queue.append(
            {
                "event_type": EventType.EventTypes.OBJECT_DETECT_START,
                "time": start_time + delta,
            }
        )
        delta = delta + td(milliseconds=Constants.OBJECT_DETECTION_TIME_MS)
        Experiment_Globals.event_queue.append(
            {
                "event_type": EventType.EventTypes.OBJECT_DETECT_FINISH,
                "time": start_time + delta,
            }
        )

    Experiment_Globals.event_queue.sort(key=lambda x: x["time"])
    Experiment_Globals.queue_lock.release()

    logging.info("REST: Finished experiment setup")
    experiment_finish_time = start_time + (
        td(seconds=Constants.FRAME_RATE) * (event_items + 1)
    )
    Experiment_Globals.EXPERIMENT_FINISH_TIME = experiment_finish_time
    Experiment_Globals.EXPERIMENT_START = True
    return
