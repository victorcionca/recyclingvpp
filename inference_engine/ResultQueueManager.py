import Globals
import DataProcessing
import TaskForwarding
from datetime import datetime as dt
import inference_engine
import rest_server
import pickle
from typing import Dict, List

CONV_LIMIT = 5
assembly_dict: Dict[str, List[TaskForwarding.TaskForwarding]] = {}

def ResultsQueueLoop():
    while True:
        result_obj = Globals.results_queue.get(block=True)
        finish_time = dt.now()
        data: bytearray = result_obj["data"]
        task_id: str = result_obj["TaskID"]
        tile_details: dict = result_obj["tile_details"]

        Globals.work_queue_lock.acquire(blocking=True)

        if task_id in Globals.dnn_hold_dict.keys():
            taskForwardItem: TaskForwarding.TaskForwarding = Globals.dnn_hold_dict[task_id]
            del Globals.dnn_hold_dict[task_id]

            if not DataProcessing.check_if_dnn_halted(taskForwardItem.high_comp_result.dnn_id, taskForwardItem.high_comp_result.version):
                taskForwardItem.data = data
                taskForwardItem.shape = result_obj["shape"]
                taskForwardItem.nidx = tile_details["Nidx"]
                taskForwardItem.midx = tile_details["Midx"]
                convidx = taskForwardItem.conv_idx[0]

                core_key= -1

                for core, map_task_id in Globals.core_map.items():
                    if(map_task_id == task_id):
                        core_key = core
                
                Globals.core_map[core_key] = -1
                key = f"{taskForwardItem.high_comp_result.dnn_id}_{convidx}"
                if key not in assembly_dict:
                    assembly_dict[key] = []
                
                assembly_dict[key].append(taskForwardItem)
                if len(assembly_dict[key]) == taskForwardItem.high_comp_result.n * taskForwardItem.high_comp_result.m:
                    assemble_obj = {
                    "TaskID": f"{taskForwardItem.high_comp_result.dnn_id}_{convidx}",
                    "convblockidx": int(convidx), # type: ignore
                    "Tiles": []
                    }
                    
                    for taskForwardObj in assembly_dict[key]:
                        assemble_obj["Tiles"].append({
                        "data": taskForwardObj.data,
                        "shape": taskForwardObj.shape,
                        "tile_details": {
                            "Nidx": taskForwardObj.nidx - 1,
                            "Midx": taskForwardObj.midx - 1,
                        }
                    })
                    
                    del assembly_dict[key]

                    if convidx < CONV_LIMIT: # type: ignore
                        next_convidx = str(int(convidx) + 1) # type: ignore
                        
                        with open("tiles_for_assembly.pkl", "wb") as f:
                            pickle.dump(assemble_obj, f)
                        assemble_data = inference_engine.AssembleData(assemble_obj) # type: ignore
                        highCompRes = taskForwardItem.high_comp_result
                        rest_server.partition_and_process(dnn_task=highCompRes, starting_convidx=next_convidx, input_data=assemble_data["data"], input_shape=assemble_data["shape"])


        Globals.work_queue_lock.release()
    return
