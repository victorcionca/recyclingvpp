from Constants import *
import Experiment_Globals as Experiment_Globals
import datetime
import EventType
import OutboundComms
import logging
import Globals
from datetime import datetime as dt


def run_loop():
    # NEED TO BLOCK QUEUE
    if Globals.work_request_lock.locked():
        return
    
    if dt.now() < Experiment_Globals.EXPERIMENT_START_TIME:
        return

    if dt.now() < Experiment_Globals.EXPERIMENT_FINISH_TIME:
        now_time = datetime.datetime.now()
        if (
            len(Experiment_Globals.event_queue) != 0
            and Experiment_Globals.event_queue[0]["time"] <= now_time
        ):
            current_item: dict = Experiment_Globals.event_queue.pop(0)

            event_time = current_item["time"]

            if current_item["event_type"] == EventType.EventTypes.OBJECT_DETECT_START:
                Experiment_Globals.deadline = current_item["time"] + datetime.timedelta(
                    seconds=FRAME_RATE
                )
            elif (
                current_item["event_type"] == EventType.EventTypes.OBJECT_DETECT_FINISH
            ):
                Experiment_Globals.current_trace_item = (
                    Experiment_Globals.trace_list.pop(0)
                )
                if Experiment_Globals.current_trace_item != -1:
                    OutboundComms.generate_low_comp_request(
                        deadline=Experiment_Globals.deadline,
                        dnn_id=Experiment_Globals.dnn_id_counter,
                    )
                    Experiment_Globals.dnn_id_counter += 1
            elif current_item["event_type"] == EventType.EventTypes.LOW_COMP_FINISH:
                if Globals.local_capacity > 0:
                    Globals.local_capacity -= 1
                finish_time = current_item["time"]
                logging.info(
                    f'{current_item["time"].strftime("%Y-%m-%d %H:%M:%S:%f")} LOW EXPECTED FIN'
                )
                logging.info(f'{now_time.strftime("%Y-%m-%d %H:%M:%S:%f")} NOW')

                OutboundComms.issue_low_comp_update(
                    current_item["dnn_id"], current_item["time"]
                )

                if Experiment_Globals.current_trace_item > 0:
                    OutboundComms.generate_high_comp_request(
                        deadline=Experiment_Globals.deadline,
                        dnn_id=Experiment_Globals.dnn_id_counter,
                        task_count=Experiment_Globals.current_trace_item,
                    )
                    Experiment_Globals.dnn_id_counter += +1
    else:
        # logging.info("Done")
        pass
    return
