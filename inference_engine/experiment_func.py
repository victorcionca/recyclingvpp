import Constants
import Experiment_Globals as Experiment_Globals
import datetime
import EventType
import OutboundComms
import logging
import Globals
from datetime import datetime as dt
from datetime import timedelta as td
import utils
import HighCompAlloFunctions


def run_loop():
    # NEED TO BLOCK QUEUE
    if Globals.work_request_lock.locked():
        return

    if dt.now() < Experiment_Globals.EXPERIMENT_START_TIME:
        return

    if dt.now() < Experiment_Globals.EXPERIMENT_FINISH_TIME:
        now_time = datetime.datetime.now()
        if  len(Experiment_Globals.event_queue) != 0 and Experiment_Globals.event_queue[0]["time"] <= now_time:
            current_item: dict = Experiment_Globals.event_queue.pop(0)

            event_time = current_item["time"]

            if current_item["event_type"] == EventType.EventTypes.OBJECT_DETECT_START:
                Experiment_Globals.deadline = event_time + datetime.timedelta(
                    milliseconds=(Constants.FRAME_RATE * 1000)
                )
                logging.info(f"NEW DEADLINE {Experiment_Globals.deadline}")
            elif (
                current_item["event_type"] == EventType.EventTypes.OBJECT_DETECT_FINISH
            ):
                logging.info(f"Object Detect Finish")

                Experiment_Globals.current_trace_item = (
                    Experiment_Globals.trace_list.pop(0)
                )

                if Experiment_Globals.current_trace_item != -1:
                    low_comp_allocation(event_time, Experiment_Globals.dnn_id_counter)
                    Experiment_Globals.dnn_id_counter += 1
            elif current_item["event_type"] == EventType.EventTypes.LOW_COMP_FINISH:
                Globals.low_active = False
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
                    high_comp_task_list = [
                        {
                            "dnn_id": f"{Constants.CLIENT_ADDRESS}_{Experiment_Globals.dnn_id_counter}_{i}",
                            "deadline": Experiment_Globals.deadline,
                        }
                        for i in range(0, Experiment_Globals.current_trace_item)
                    ]

                    HighCompAlloFunctions.add_high_comp_to_stealing_queue(
                        high_comp_tasks=high_comp_task_list, current_time=event_time
                    )

                    Experiment_Globals.dnn_id_counter += +1
    else:
        logging.info("Done")
        pass
    return


def identify_halt_candidate():
    task_id_fin_time_mapping = {
        work_item["TaskID"]: work_item
        for work_item in Globals.core_map.values()
        if len(work_item.keys()) != 0
    }

    halt_candidate = list(task_id_fin_time_mapping.values())[0]

    for core_mapping in task_id_fin_time_mapping.values():
        if core_mapping["deadline"] > halt_candidate["deadline"]:
            halt_candidate = core_mapping

    return halt_candidate


def low_comp_allocation(current_time: dt, dnn_id_counter: int):
    dnn_id = f"{Constants.CLIENT_ADDRESS}_{dnn_id_counter}"
    logging.info(f"Low Comp Allocation {dnn_id} begin.")

    resource_usage = utils.capacity_gatherer()

    invoke_preemption = False
    if Constants.CORE_COUNT - resource_usage < 1:
        if Constants.DEADLINE_PREEMPT:
            halt_dnn = identify_halt_candidate()
            Globals.halt_queue.append(halt_dnn["TaskID"])
            OutboundComms.post_halt_controller(halt_dnn["TaskID"])
            OutboundComms.return_work_to_client(
                halt_dnn["TaskID"], halt_dnn["deadline"]
            )
            invoke_preemption = True
            logging.info(f"Preempted {halt_dnn['TaskID']}.")
        else:
            logging.info(f"Low Comp Allocation {dnn_id} fail.")
            OutboundComms.low_comp_allocation_fail(dnn_id)
            return

    finish_time = current_time + td(milliseconds=Constants.LOW_COMP_TIME)

    logging.info(f"Low Comp Allocation {dnn_id} success.")
    utils.add_task_to_event_queue(
        event_item={
            "event_type": EventType.EventTypes.LOW_COMP_FINISH,
            "time": finish_time,
            "dnn_id": dnn_id,
        }
    )
    Globals.local_capacity += 1
    Globals.low_active = True
    OutboundComms.post_low_task(current_time, finish_time, dnn_id, invoke_preemption)

    return
