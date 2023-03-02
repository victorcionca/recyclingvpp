from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
import queue
from typing import List
import Constants
import Globals
import inference_engine
import DataProcessing
import TaskForwarding
import OutboundComm
import OutboundComms
import OutboundCommTypes
import HighCompResult
import WorkWaitingQueue
from datetime import datetime as dt

hostName = "localhost"


device_host_list = []


class RestInterface(BaseHTTPRequestHandler):

    def _set_response(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        json_request = {}

        # Process the request data and extract the input, target core, etc.
        request_str = self.requestline
        request_body = self.rfile.read(int(self.headers['Content-Length']))

        response_json = ""
        response_code = 200

        self.send_response(response_code)
        self.end_headers()

        try:
            json_request: dict = json.loads(request_body)

            if self.path == Constants.HALT_ENDPOINT:
                self.halt_task(jsonRequest=json_request)
            elif self.path == Constants.TASK_ALLOCATION:
                self.task_allocation_function(json_request_body=json_request)
            elif self.path == Constants.TASK_FORWARD:
                self.task_forward(json_request_body=json_request)
            elif self.path == Constants.TASK_REALLOCATION:
                self.task_reallocation(jsonRequest=json_request)
            elif self.path == Constants.TASK_UPDATE:
                self.state_update(json_object=json_request)
            elif self.path == Constants.TASK_ASSEMBLY:
                self.task_assembly(json_request_body=json_request)

        except json.JSONDecodeError:
            print(f"Received request was not json: {request_str}")
            response_code = 400
            return

    def state_update(self, json_object: dict):
        dnn_dict: dict = json_object["dnn"]
        old_version: int = int(json_object["old_version"])
        dnn: HighCompResult.HighCompResult = HighCompResult.HighCompResult()
        dnn.generateFromDict(dnn_dict)

        Globals.work_queue_lock.acquire(blocking=True)

        if dnn.dnn_id not in Globals.state_update_map.keys():
            Globals.state_update_map[dnn.dnn_id] = {}

        Globals.state_update_map[dnn.dnn_id][old_version] = dnn

        Globals.work_queue_lock.release()
        return

    # This function assumes that the lock has been acquired beforehand
    def general_allocate_and_forward_function(self, dnn_task: HighCompResult.HighCompResult, data: bytes, shape: List[int], starting_convidx: str):
        partition_data = {}
        partition_result = inference_engine.PartitionData({
            "data": data,
            "shape": shape,
            "convblockidx": int(starting_convidx),
            "N": dnn_task.tasks[starting_convidx].N,
            "M": dnn_task.tasks[starting_convidx].M,
            "TaskID": dnn_task.unique_dnn_id
        })

        if isinstance(partition_result, dict):
            partition_data = partition_result
        else:
            return

        for partition_id, task in dnn_task.tasks[starting_convidx].partitioned_tasks.items():
            tile = {}
            for tile_item in partition_data["Tiles"]:
                if tile_item["tile_details"]["Nidx"] == (task.N - 1) and tile_item["tile_details"]["Midx"] == (task.M - 1):
                    tile = tile_item
                    break

            forward_item = TaskForwarding.TaskForwarding(highCompResult=dnn_task, convIdx=task.convidx,
                                                         partitionId=partition_id, uniqueTaskId=task.unique_task_id, nIdx=task.N,
                                                         mIdx=task.M, topX=tile["tile_details"][
                                                             "top_x"], topY=tile["tile_details"]["top_y"],
                                                         botX=tile["tile_details"]["bot_x"], botY=tile["tile_details"]["bot_y"],
                                                         data=tile["data"], shape=tile["shape"])

            comm_item = OutboundComm.OutboundComm(
                comm_time=task.input_data.start_fin_time[0], comm_type=OutboundCommTypes.OutboundCommType.TASK_FORWARD, payload=forward_item)

            OutboundComms.add_task_to_queue(comm_item=comm_item)

    def task_reallocation(self, jsonRequest: dict):
        dnn: HighCompResult.HighCompResult = HighCompResult.HighCompResult()
        dnn.generateFromDict(jsonRequest["dnn"])
        startingConvidx: str = jsonRequest["starting_conv"]

        Globals.work_queue_lock.acquire(blocking=True)
        success, data, shape = DataProcessing.fetch_item_from_assembly_hold_list(
            dnn_id=dnn.dnn_id, convidx=startingConvidx)

        if success:
            self.general_allocate_and_forward_function(
                dnn_task=dnn, data=data, shape=shape, starting_convidx=startingConvidx)
        Globals.work_queue_lock.release()
        return

    def prune_dnn(self, jsonRequest: dict):
        Globals.work_queue_lock.acquire(blocking=True)

        dnn_id: str = jsonRequest["dnn_id"]

        dnn_items_tasks: list[int] = []
        for key, taskForwardItem in Globals.dnn_hold_dict.items():
            if taskForwardItem.high_comp_result.dnn_id == dnn_id:
                dnn_items_tasks.append(taskForwardItem.unique_task_id)

        cores_to_clear = []

        for task_id in dnn_items_tasks:
            del Globals.dnn_hold_dict[task_id]

            for key in Globals.core_map.keys():
                if Globals.core_map[key] == task_id:
                    Globals.core_map[key] = -1

        if dnn_id in Globals.state_update_map.keys():
            del Globals.state_update_map[dnn_id]

        for core in cores_to_clear:
            Globals.work_queue.put({
                "type": "prune",
                "core": core
            })

        Globals.net_outbound_list = [
            item for item in Globals.net_outbound_list if item.dnn_id != dnn_id]
        Globals.work_waiting_queue = [
            item for item in Globals.work_waiting_queue if item["work_item"]["TaskID"] not in dnn_items_tasks]

        Globals.assembly_dict = {key: value for key, value in Globals.assembly_dict.items(
        ) if key.split("_")[0] != dnn_id}
        Globals.assembly_hold_list = [
            item for item in Globals.assembly_hold_list if item.dnn_id != dnn_id]

        Globals.work_queue_lock.release()

    def halt_task(self, jsonRequest: dict):
        Globals.work_queue_lock.acquire(blocking=True)

        Globals.work_queue = queue.Queue()
        Globals.results_queue = queue.Queue()

        Globals.assembly_dict.clear()
        Globals.net_outbound_list.clear()
        Globals.dnn_hold_dict.clear()
        Globals.work_waiting_queue.clear()
        Globals.state_update_map.clear()
        Globals.core_map = {
            0: -1,
            1: -1,
            2: -1,
            3: -1
        }

        Globals.work_queue.put({"type": "halt"})

        for dnn_id, version in jsonRequest.items():
            if dnn_id not in Globals.halt_list.keys():
                Globals.halt_list[dnn_id] = []
            if version not in Globals.halt_list[dnn_id]:
                Globals.halt_list[dnn_id].append(version)

        Globals.work_queue_lock.release()
        return

    def task_assembly(self, json_request_body):
        parsed_json = json.loads(json_request_body)
        taskForwardObj: TaskForwarding.TaskForwarding = TaskForwarding.TaskForwarding()
        taskForwardObj.create_task_forwarding_from_dict(parsed_json)
        taskForwardObj.assembly_upload_finish = dt.now()
        convidx = taskForwardObj.convidx

        total_partition_count = len(
            taskForwardObj.high_comp_result.tasks[convidx].partitioned_tasks)
        key = f"{taskForwardObj.high_comp_result.dnn_id}_{convidx}"

        Globals.work_queue_lock.acquire(blocking=True)

        if not DataProcessing.check_if_dnn_pruned(dnn_id=taskForwardObj.high_comp_result.dnn_id) and not DataProcessing.check_if_dnn_halted(dnn_id=taskForwardObj.high_comp_result.dnn_id, dnn_version=taskForwardObj.high_comp_result.version):
            if key not in Globals.assembly_dict.keys():
                Globals.assembly_dict[key] = {
                    "partition_count": total_partition_count,
                    "tiles": []
                }

            # Need to add DNN tile to the conv blocks tiles
            Globals.assembly_dict[key]["tiles"].append(taskForwardObj)

            if len(Globals.assembly_dict[key]["tiles"]) == Globals.assembly_dict[key]["partition_count"]:
                finish_times = []
                assemble_obj = {
                    "TaskID": taskForwardObj.high_comp_result.unique_dnn_id,
                    "convblockidx": int(convidx),
                    "Tiles": []
                }
                for tile in Globals.assembly_dict[key]["tiles"]:
                    finish_times.append({
                        "partition_id": tile.partition_id,
                        "finish_time": tile.high_comp_result.tasks[convidx].partitioned_tasks[tile.partition_id].actual_finish.timestamp() * 1000,
                        "assembly_upload_start": tile.assembly_upload_start.timestamp() * 1000,
                        "assembly_upload_finish": tile.assembly_upload_finish.timestamp() * 1000,
                        "task_forward_start": tile.task_forward_start.timestamp() * 1000,
                        "task_forward_finish": tile.task_forward_finish.timestamp() * 1000
                    })

                    assemble_obj["Tiles"].append({
                        "data": tile.data,
                        "shape": tile.shape,
                        "tile_details": {
                            "Nidx": tile.nidx - 1,
                            "Midx": tile.midx - 1,
                            "top_x": tile.top_x,
                            "top_y": tile.top_y,
                            "bot_x": tile.bot_x,
                            "bot_y": tile.bot_y
                        }
                    })

                del Globals.assembly_dict[key]

                state_update_object = {
                    "finish_times": finish_times,
                    "convidx": convidx,
                    "dnn_id": taskForwardObj.high_comp_result.dnn_id
                }

                state_update_upload_time_fin = taskForwardObj.high_comp_result.tasks[convidx].state_update.start_fin_time[1]
                state_update_comm = OutboundComm.OutboundComm(
                    comm_time=taskForwardObj.high_comp_result.tasks[convidx].state_update.start_fin_time[0], comm_type=OutboundCommTypes.OutboundCommType.STATE_UPDATE, payload=state_update_object, dnn_id=taskForwardObj.high_comp_result.dnn_id, version=taskForwardObj.high_comp_result.version)

                OutboundComms.add_task_to_queue(state_update_comm)

                # Performing STATE UPDATE
                if taskForwardObj.high_comp_result.dnn_id in Globals.state_update_map.keys():
                    if taskForwardObj.high_comp_result.version in Globals.state_update_map[taskForwardObj.high_comp_result.dnn_id].keys():
                        taskForwardObj.high_comp_result = Globals.state_update_map[
                            taskForwardObj.high_comp_result.dnn_id][taskForwardObj.high_comp_result.version]

                for finish_time in state_update_object["finish_times"]:
                    converted_ts = DataProcessing.from_ms_since_epoch(
                        str(finish_time["finish_time"]))
                    partition_id = finish_time["partition_id"]
                    taskForwardObj.high_comp_result.tasks[convidx].partitioned_tasks[
                        partition_id].actual_finish = converted_ts

                if int(taskForwardObj.convidx) < len(taskForwardObj.high_comp_result.tasks):
                    next_convidx = str(int(taskForwardObj.convidx) + 1)

                    assemble_data = inference_engine.AssembleData(assemble_obj)

                    if assemble_data != None:
                        highCompRes = taskForwardObj.high_comp_result
                        highCompRes.last_complete_convidx = convidx
                        highCompRes.tasks[convidx].completed = True

                        DataProcessing.add_item_to_assembly_hold_list(deadline=highCompRes.deadline, dnn_id=highCompRes.dnn_id,
                                                                      convidx=taskForwardObj.convidx, assembly_data=assemble_data["data"], shape=assemble_data["shape"])

                        self.general_allocate_and_forward_function(
                            dnn_task=highCompRes, data=assemble_data["data"], shape=assemble_data["shape"], starting_convidx=next_convidx)

                        violated_timestamp = dt(1970, 1, 1, 0, 0, 0)
                        violated_partition = -1
                        for partition in highCompRes.tasks[convidx].partitioned_tasks.values():
                            if partition.actual_finish > partition.estimated_finish and partition.actual_finish > violated_timestamp:
                                violated_timestamp = partition.actual_finish
                                violated_partition = partition.partition_block_id

                        if violated_partition != -1:
                            dag_disrupt_item = {
                                "dnn_id": highCompRes.dnn_id,
                                "convidx": convidx,
                                "partition_id": violated_partition,
                                "finish_time": int(violated_timestamp.timestamp() * 1000)
                            }
                            dagCommItem: OutboundComm.OutboundComm = OutboundComm.OutboundComm(comm_time=state_update_upload_time_fin, comm_type=OutboundCommTypes.OutboundCommType.DAG_DISRUPTION, payload=dag_disrupt_item)
                            OutboundComms.add_task_to_queue(dagCommItem)

        Globals.work_queue_lock.release()

        return

    def task_allocation_function(self, json_request_body: dict):
        dnn_task: HighCompResult.HighCompResult = HighCompResult.HighCompResult()
        dnn_task.generateFromDict(json_request_body["dnn"])
        starting_convidx: str = json_request_body["starting_conv"]

        load_data: dict = {}

        load_result = inference_engine.LoadImage({
            "filename": Constants.INITIAL_FILE_PATH,
            "TaskID": dnn_task.unique_dnn_id
        })

        if isinstance(load_result, dict):
            load_data = load_result
        else:
            return

        Globals.work_queue_lock.acquire(blocking=True)

        self.general_allocate_and_forward_function(
            data=load_data["data"], shape=load_data["shape"], dnn_task=dnn_task, starting_convidx=starting_convidx)

        Globals.work_queue_lock.release()
        return

    def task_forward(self, json_request_body):
        task_forward_data = json.loads(json_request_body)
        taskForwardObj: TaskForwarding.TaskForwarding = TaskForwarding.TaskForwarding()
        taskForwardObj.create_task_forwarding_from_dict(task_forward_data)
        taskForwardObj.task_forward_finish = dt.now()
        Globals.work_queue_lock.acquire(blocking=True)

        if not DataProcessing.check_if_dnn_pruned(dnn_id=taskForwardObj.high_comp_result.dnn_id) and not DataProcessing.check_if_dnn_halted(dnn_id=taskForwardObj.high_comp_result.dnn_id, dnn_version=taskForwardObj.high_comp_result.version):
            Globals.dnn_hold_dict[taskForwardObj.unique_task_id] = taskForwardObj

            work_item = {
                "start_time": taskForwardObj.high_comp_result.tasks[taskForwardObj.convidx].partitioned_tasks[taskForwardObj.partition_id].estimated_start,
                "work_item": {
                    "type": "task",
                    "data": taskForwardObj.data,
                    "shape": taskForwardObj.shape,
                    "convblockidx": int(taskForwardObj.convidx),
                    "core": -1,
                    "tile_details": {
                        "Nidx": taskForwardObj.nidx,
                        "Midx": taskForwardObj.midx,
                        "top_x": taskForwardObj.top_x,
                        "top_y": taskForwardObj.top_y,
                        "bot_x": taskForwardObj.bot_x,
                        "bot_y": taskForwardObj.bot_y
                    },
                    "TaskID": taskForwardObj.unique_task_id
                }
            }

            WorkWaitingQueue.add_task(work_item=work_item)

        Globals.work_queue_lock.release()
        return


def run(server_class=HTTPServer, handler_class=RestInterface, port=Constants.REST_PORT):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('REST: Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('REST: Stopping httpd...\n')
