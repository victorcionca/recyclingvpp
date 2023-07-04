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
from threading import Thread

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

        try:
            json_request = {}

            if 'multipart/form-data' in self.headers["Content-Type"]:
                content_length = int(self.headers.get('Content-Length'))
                
                post_data = request_body
                content_type = self.headers['Content-Type']
                
                # Parse the multipart/form-data request
                boundary = content_type.split('boundary=')[1].encode()
                parts = post_data.split(b'--' + boundary)

                json_data = None

                for part in parts:
                    if b'Content-Disposition: form-data;' in part:
                        if b'payload' in part:
                            json_data = part

                if json_data is not None:
                    left_item = '{'
                    right_item = '\r'

                    json_data = json_data.decode()
                    before, _, after = json_data.partition(left_item)
                    json_data = left_item + after
                    before, _, after = json_data.partition(right_item)
                    
                    json_request = json.loads(before)

            else:
                json_request = json.loads(request_body)

            function = None
            if self.path == Constants.TASK_ALLOCATION:
                function = general_allocate_and_forward_function
            elif self.path == Constants.TASK_FORWARD:
                function = task_allocation_function
            elif self.path == Constants.HALT_ENDPOINT:
                function = halt_endpoint

            # if callable(function):
            #      x = Thread(target=function, args=(json_request,))
            #      x.start()
            function(json_request)

            response_code = 200

            self.send_response(response_code)
            self.end_headers()

        except json.JSONDecodeError:
            print(f"Received request was not json: {request_str}")
            response_code = 400
            return

    
def halt_endpoint(json_request_body):
    dnn_id = json_request_body["dnn_id"]
    version = int(json_request_body["version"])

    Globals.work_queue_lock.acquire(blocking=True)

    if dnn_id in Globals.dnn_hold_dict.keys():
        dnn = Globals.dnn_hold_dict[dnn_id]
        if dnn.version == version:
            if dnn_id in Globals.thread_holder.keys():
                process_thread = Globals.thread_holder[dnn_id]
                process_thread.halt()

                for i in range(0, len(Globals.core_map.keys())):
                    if Globals.core_map[i] == dnn_id:
                        Globals.core_map[i] = ""
                
                del Globals.thread_holder[dnn_id]
            del Globals.dnn_hold_dict[dnn_id]
    
    if dnn_id not in Globals.halt_list.keys():
        Globals.halt_list[dnn_id] = []
    
    if version not in Globals.halt_list[dnn_id]:
        Globals.halt_list[dnn_id].append(version)

    Globals.work_queue_lock.release()
    return


def general_allocate_and_forward_function(json_request_body):
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

def task_allocation_function(json_request_body):
    dnn_task: HighCompResult.HighCompResult = HighCompResult.HighCompResult()
    dnn_task.generateFromDict(json_request_body)

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
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('REST: Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print('REST: Stopping httpd...\n')
