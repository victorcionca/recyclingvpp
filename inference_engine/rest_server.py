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
import datetime
import WorkWaitingQueue
import pickle
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
                self.general_allocate_and_forward_function(
                    json_request_body=json_request)
            elif self.path == Constants.TASK_FORWARD:
                self.task_allocation_function(json_request_body=json_request)

        except json.JSONDecodeError:
            print(f"Received request was not json: {request_str}")
            response_code = 400
            return

    # This function assumes that the lock has been acquired beforehand
    def general_allocate_and_forward_function(self, json_request_body: dict):
        dnn_task = HighCompResult.HighCompResult()
        dnn_task.generateFromDict(json_request_body)
        if dnn_task.allocated_host != "self":
            Globals.work_queue_lock.acquire(blocking=True)
            comm_item = OutboundComm.OutboundComm(
                comm_time=dnn_task.upload_data.start_fin_time[0], comm_type=OutboundCommTypes.OutboundCommType.TASK_FORWARD, payload=dnn_task)

            OutboundComms.add_task_to_queue(comm_item=comm_item)
            Globals.work_queue_lock.release()

        else:
            Globals.work_queue_lock.acquire(blocking=True)
            partition_and_process(
                dnn_task=dnn_task, starting_convidx="1", input_data=bytes(), input_shape=[])
            Globals.work_queue_lock.release()

    def halt_task(self, jsonRequest: dict):

        Globals.work_queue_lock.acquire(blocking=True)
        dnn_id: str = jsonRequest["dnn_id"]

        dnn_items_tasks: list[str] = []
        for key, taskForwardItem in Globals.dnn_hold_dict.items():
            if taskForwardItem.high_comp_result.dnn_id == dnn_id:
                dnn_items_tasks.append(taskForwardItem.unique_task_id)

        cores_to_clear = []

        for task_id in dnn_items_tasks:
            del Globals.dnn_hold_dict[task_id]

            for key in Globals.core_map.keys():
                if Globals.core_map[key] == task_id:
                    Globals.core_map[key] = -1

        for core in cores_to_clear:
            Globals.work_queue.put({
                "type": "prune",
                "core": core
            })

        Globals.net_outbound_list = [
            item for item in Globals.net_outbound_list if item.dnn_id != dnn_id]
        Globals.work_waiting_queue = [
            item for item in Globals.work_waiting_queue if item["work_item"]["TaskID"] not in dnn_items_tasks]

        Globals.work_queue_lock.release()
        return

    def task_allocation_function(self, json_request_body: dict):
        dnn_task: HighCompResult.HighCompResult = HighCompResult.HighCompResult()
        dnn_task.generateFromDict(json_request_body["dnn"])

        Globals.work_queue_lock.acquire(blocking=True)
        partition_and_process(dnn_task=dnn_task, starting_convidx="1", input_data=bytes(), input_shape=[])
        Globals.work_queue_lock.release()
        return


def partition_and_process(dnn_task: HighCompResult.HighCompResult, starting_convidx: str, input_data: bytes, input_shape: list):
    load_data: dict = {}

    data = input_data
    shape = input_shape
    
    if len(input_shape) == 0:
        load_result = inference_engine.LoadImage({ # type: ignore
            "filename": Constants.INITIAL_FILE_PATH,
            "TaskID": dnn_task.dnn_id
        })

        if isinstance(load_result, dict):
            load_data = load_result
        else:
            return
        
        data = load_result["data"]
        shape = load_result["shape"]

    partition_data = {}
    partition_result = inference_engine.PartitionData({ # type: ignore
        "data": data,
        "shape": shape,
        "convblockidx": int(starting_convidx),
        "N": dnn_task.n,
        "M": dnn_task.m,
        "TaskID": dnn_task.dnn_id
    })

    if isinstance(partition_result, dict):
        partition_data = partition_result
        with open("partitioned_input.pkl", "wb") as f:
            pickle.dump(partition_data, f)

    else:
        return

    for tile_item in partition_data["Tiles"]:
        forward_item = TaskForwarding.TaskForwarding(highCompResult=dnn_task, convIdx=int(starting_convidx), nIdx=tile_item["tile_details"]["Nidx"], mIdx=tile_item["tile_details"]["Midx"], topX=tile_item["tile_details"][
            "top_x"], topY=tile_item["tile_details"]["top_y"],
            botX=tile_item["tile_details"]["bot_x"], botY=tile_item["tile_details"]["bot_y"],
            data=tile_item["data"], shape=tile_item["shape"])

        if not DataProcessing.check_if_dnn_halted(dnn_id=forward_item.high_comp_result.dnn_id, dnn_version=forward_item.high_comp_result.version):
            Globals.dnn_hold_dict[forward_item.unique_task_id] = forward_item

            

            start_time = datetime.datetime.now(
            ) if starting_convidx != "1" else dnn_task.estimated_start

            work_item = {
                "start_time": start_time,
                "work_item": {
                    "type": "task",
                    "data": forward_item.data,
                    "shape": forward_item.shape,
                    "convblockidx": int(starting_convidx),
                    "core": -1,
                    "tile_details": {
                        "Nidx": forward_item.nidx,
                        "Midx": forward_item.midx,
                        "top_x": forward_item.top_x,
                        "top_y": forward_item.top_y,
                        "bot_x": forward_item.bot_x,
                        "bot_y": forward_item.bot_y
                    },
                    "TaskID": forward_item.unique_task_id
                }
            }

            WorkWaitingQueue.add_task(work_item=work_item)



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
