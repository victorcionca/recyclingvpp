import Globals
import Constants
import requests
import inference_engine
import DataProcessing
import TaskForwarding
from datetime import datetime as dt
import OutboundComm
import OutboundCommTypes
import OutboundComms


def ResultsQueueLoop():
    while True:
        result_obj = Globals.results_queue.get(block=True)
        finish_time = dt.now()
        data: bytearray = result_obj["data"]
        task_id: int = result_obj["TaskID"]
        tile_details: dict = result_obj["tile_details"]

        Globals.work_queue_lock.acquire(blocking=True)

        if task_id in Globals.dnn_hold_dict.keys():
            taskForwardItem: TaskForwarding.TaskForwarding = Globals.dnn_hold_dict[task_id]
            del Globals.dnn_hold_dict[task_id]

            if not DataProcessing.check_if_dnn_pruned(taskForwardItem.high_comp_result.dnn_id) and not DataProcessing.check_if_dnn_halted(dnn_id=taskForwardItem.high_comp_result.dnn_id, dnn_version=taskForwardItem.high_comp_result.version):
                taskForwardItem.high_comp_result.tasks[taskForwardItem.convidx]\
                    .partitioned_tasks[taskForwardItem.partition_id].actual_finish = finish_time

                taskForwardItem.data = data
                taskForwardItem.shape = result_obj["shape"]
                taskForwardItem.nidx = tile_details["Nidx"]
                taskForwardItem.midx = tile_details["Midx"]
                convidx = taskForwardItem.convidx
                comm_time = taskForwardItem.high_comp_result.tasks[taskForwardItem.convidx].assembly_upload_windows[taskForwardItem.partition_id].start_fin_time[0]

                core_key= -1

                for core, map_task_id in Globals.core_map.items():
                    if(map_task_id == task_id):
                        core_key = core
                
                Globals.core_map[core_key] = -1

                outboundComm: OutboundComm.OutboundComm = OutboundComm.OutboundComm(
                    comm_time=comm_time, comm_type=OutboundCommTypes.OutboundCommType.TASK_ASSEMBLY, payload=taskForwardItem, dnn_id=taskForwardItem.high_comp_result.dnn_id, version=taskForwardItem.high_comp_result.version)

                OutboundComms.add_task_to_queue(outboundComm)

        Globals.work_queue_lock.release()
    return
