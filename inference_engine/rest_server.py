from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
import queue
from typing import List
import Constants
import Globals
import inference_engine_e2e_with_ipc
import DataProcessing
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
        for key, dnn_task in Globals.dnn_hold_dict.items():
            if dnn_task.dnn_id == dnn_id:
                Globals.core_usage = Globals.core_usage - (dnn_task.n * dnn_task.m)
                dnn_items_tasks.append(dnn_task.dnn_id)

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
            item for item in Globals.work_waiting_queue if item["TaskID"] not in dnn_items_tasks]

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
        load_result = inference_engine_e2e_with_ipc.LoadImage(None, dnn_task.dnn_id)

        if isinstance(load_result, dict):
            load_data = load_result
        else:
            return
        
        data = load_result["data"]
        shape = load_result["shape"]

    partition_data = {}
    work_item = { # type: ignore
        "data": data,
        "start_time": dnn_task.estimated_start,
        "shape": shape,
        "N": dnn_task.n,
        "M": dnn_task.m,
        "cores": dnn_task.n * dnn_task.m,
        "TaskID": dnn_task.dnn_id
    }

    if not DataProcessing.check_if_dnn_halted(dnn_id=dnn_task.dnn_id, dnn_version=dnn_task.version):
        Globals.dnn_hold_dict[dnn_task.dnn_id] = dnn_task

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
