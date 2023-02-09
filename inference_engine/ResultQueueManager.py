import Globals
import Constants.Constants
import requests
from inference_engine.inference_engine import serialize_numpy
from model.NetworkCommModels.TaskForwaring import TaskForwarding
from datetime import datetime as dt
from model.TaskData.TaskData import TaskData
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

        Globals.dnn_hold_lock.acquire(blocking=True)
        taskForwardItem: TaskForwarding = Globals.dnn_hold_dict[task_id]
        del Globals.dnn_hold_dict[task_id]
        Globals.dnn_hold_lock.release()

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
            comm_time=comm_time, comm_type=OutboundCommType.TASK_ASSEMBLY, payload=taskForwardItem)

        add_task_to_queue(outboundComm)
    return
