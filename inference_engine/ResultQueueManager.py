import Globals
import Constants.Constants
import requests
from inference_engine.inference_engine import serialize_numpy
from inference_engine.utils.DataProcessing import check_if_dnn_pruned, check_if_dnn_halted
from model.NetworkCommModels.TaskForwaring import TaskForwarding
from datetime import datetime as dt
from model.OutboundComm import OutboundComm
from enums.OutboundCommTypes import OutboundCommType
from OutboundComms import add_task_to_queue


def ResultsQueueLoop():
    while True:
        result_obj = Globals.results_queue.get(block=True)
        finish_time = dt.now()
        data: bytearray = result_obj["data"]
        task_id: int = result_obj["TaskID"]
        tile_details: dict = result_obj["tile_details"]

        Globals.work_queue_lock.acquire(blocking=True)

        if task_id in Globals.dnn_hold_dict.keys():
            taskForwardItem: TaskForwarding = Globals.dnn_hold_dict[task_id]
            del Globals.dnn_hold_dict[task_id]
            
            if not check_if_dnn_pruned(taskForwardItem.high_comp_result.dnn_id) and not check_if_dnn_halted(dnn_id = taskForwardItem.high_comp_result.dnn_id, dnn_version = taskForwardItem.high_comp_result.version):
                taskForwardItem.high_comp_result.tasks[taskForwardItem.convidx]\
                    .partitioned_tasks[taskForwardItem.partition_id].actual_finish = finish_time

                serialised_data, shape = serialize_numpy(data)
                taskForwardItem.data = serialised_data
                taskForwardItem.shape = shape
                taskForwardItem.nidx = tile_details["Nidx"]
                taskForwardItem.midx = tile_details["Midx"]
                taskForwardItem.top_x = tile_details["top_x"]
                taskForwardItem.top_y = tile_details["top_y"]
                taskForwardItem.bot_x = tile_details["bot_x"]
                taskForwardItem.bot_y = tile_details["bot_y"]

                comm_time = taskForwardItem.high_comp_result.tasks[taskForwardItem.convidx]\
                    .assembly_upload_windows[taskForwardItem.partition_id].start_fin_time[0]

                outboundComm: OutboundComm = OutboundComm(
                    comm_time=comm_time, comm_type=OutboundCommType.TASK_ASSEMBLY, payload=taskForwardItem, dnn_id=taskForwardItem.high_comp_result.dnn_id, version=taskForwardItem.high_comp_result.version)

                add_task_to_queue(outboundComm)

        Globals.work_queue_lock.release()
    return
