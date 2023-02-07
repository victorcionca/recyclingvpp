import Globals
import Constants
import requests
from TaskData.TaskData import TaskData
import sys


def ResultsQueueLoop():
    while True:
        result = Globals.results_queue.get()

        unique_task_id = result["unique_task_id"]

        Globals.task_thread_lock.acquire()
        current_block = Globals.task_dict[unique_task_id]["task"].fetch_current_block(
        )

        finish_time = result["finish_time"]

        # Check to see if theres a disruption and if theres no disruption we contact the controller to update state
        if not DisruptionCheck(finish_time, current_block.estimated_finish_time,
                               current_block.unique_task_id, Globals.task_dict[unique_task_id]["task"].dnn_id):
            Globals.net_queue_lock.acquire()

            Globals.net_outbound_list.append({
                "type": "state_update",
                "finish_time": finish_time,
                "dnn_id": Globals.task_dict[unique_task_id]["task"].dnn_id,
                "unique_task_id": unique_task_id,
                "comm_time": Globals.task_dict[unique_task_id]["task"].fetch_current_block().state_update_comm_start
            })

            Globals.net_queue_lock.release()

        # Partition Data Here

        is_finished, outer_index, inner_index = FindNextBlock(
            Globals.task_dict[unique_task_id]["task"], result["x1"], result["y1"], result["x2"], result["y2"])

        if is_finished:
            Globals.task_thread_lock.release()
            continue

        else:
            '''
            Need to create a copy of our task item
            '''
            task_copy = TaskData(
                Globals.task_dict[unique_task_id]["task"].serialise())
            selected_block = task_copy.outer_blocks[outer_index][inner_index]

            '''
            Need to update the current block to be processed for the next device
            '''
            task_copy.current_block = selected_block.unique_task_id
            task_copy.N = selected_block.N
            task_copy.M = selected_block.M
            task_copy.conv_idx = selected_block.conv_idx

            Globals.net_queue_lock.acquire()

            Globals.net_outbound_list.append({
                "type": "upload",
                "data": result["result_data"],
                "dest": selected_block.allocated_device,
                "task": task_copy.serialise(),
                "comm_time": Globals.task_dict[unique_task_id]["task"].fetch_current_block().output_upload_start_time
            })

            Globals.net_queue_lock.release()

            del Globals.task_dict[unique_task_id]
            Globals.task_thread_lock.release()

    return


def FindNextBlock(task: TaskData, x1, y1, x2, y2):
    outer_index = 0

    for outer_val in task.outer_blocks.values():
        found = False
        for inner_val in outer_val.values():
            if task.current_block == inner_val.unique_task_id:
                found = True
                break
        if found:
            break
        outer_index += 1

    if outer_index + 1 >= len(task.outer_blocks):
        return True, -1, -1

    inner_index = 0
    unique_task_id = -1
    for inner_val in task.outer_blocks[f"{outer_index + 1}"].values():
        if inner_val.input_tile.x1 == x1 and inner_val.input_tile.x2 == x2 and inner_val.input_tile.y1 == y1 and inner_val.input_tile.y2 == y2:
            unique_task_id = inner_val.unique_task_id
            break
        if unique_task_id != -1:
            break
        inner_index += 1

    return False, outer_index, inner_index


# Need to update controller with finished status of task if not violateed
def state_update(finish_time, unique_task_id, dnn_id):
    requests.post(
        f'{sys.argv[1]}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.CONTROLLER_DEFAULT_ROUTE}{Constants.CONTROLLER_DAG_DISRUPTION}',
        json={
            "finish_time": finish_time.timestamp() * 1000,
            "partition_id": unique_task_id,
            "partition_dnn_id": dnn_id
        })
    return


# A function to check if an inference task has violated its deadline
# block id is the unique task id and the DNN id is the unique id assigned the the dnn instance
def DisruptionCheck(finish_time, estimated_finish_time, block_id, DNN_ID):
    violated = finish_time > estimated_finish_time
    if violated:
        requests.post(
            f'{sys.argv[1]}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.CONTROLLER_DEFAULT_ROUTE}{Constants.CONTROLLER_DAG_DISRUPTION}',
            json={
                "partition_dnn_id": DNN_ID,
                "partition_id": block_id,
                "finish_time": finish_time.timestamp() * 1000
            })

    return violated
