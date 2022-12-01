from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
import Constants
import Globals
from TaskData.TaskData import TaskData
import numpy as np

hostName = "localhost"

device_host_list = []


class RestInferface(BaseHTTPRequestHandler):

    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_POST(self):
        handlers = {
            Constants.HALT_ENDPOINT: self.halt_tasks,
            Constants.TASK_ALLOCATION: self.allocate_task,
            Constants.TASK_UPDATE: self.task_update,
        }

        # Try to convert to json
        json_request = None

        # Process the request data and extract the input, target core, etc.
        request_str = self.requestline
        request_body = self.rfile.read(int(self.headers['Content-Length']))

        try:
            json_request = json.loads(request_body)
        except json.JSONDecodeError:
            print(f"Received request was not json: {request_str}")
            return

        if "type" not in json_request or json_request["type"] not in handlers:
            # TODO error
            return

        response_json = handlers[json_request["type"]](json_request)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        self.wfile.write(bytes(response_json, "utf8"))

    def allocate_task(self, request):
        task_data = request["task"]
        input_data_bytes = request["input_data"]

        # TODO double check that this is how I receive data from controller
        array = np.frombuffer(input_data_bytes, dtype=np.float32)

        Globals.task_thread_lock.acquire()

        current_block_id = task_data["current_block"]

        task_obj = None
        if current_block_id not in Globals.task_dict:
            task_obj = TaskData(task_data)
            Globals.task_dict[current_block_id] = {
                "task": task_obj, "input_data": []}
        else:
            task_obj = Globals.task_dict[current_block_id]["task"]

        x1 = int()
        y1 = int()
        x2 = int()
        y2 = int()

        outer_block = 0
        for outer_val in task_obj.outer_blocks.values():
            exit_loop = False
            for inner_value in outer_val.values():
                if inner_value.unique_task_id == current_block_id:
                    x1 = inner_value.input_tile.x1
                    y1 = inner_value.input_tile.y1
                    x2 = inner_value.input_tile.x2
                    y2 = inner_value.input_tile.y2
                    exit_loop = True
                    break
            if exit_loop:
                break
            outer_block += 1

        Globals.task_dict[current_block_id]["input_data"].append(
            {"x1": x1, "x2": x2, "y1": y1, "y2": y2, "data": input_data_bytes})

        if len(Globals.task_dict[current_block_id]["input_data"]) == task_obj.input_part_count:
            output_partition = False if outer_block + 1 >= len(task_obj.outer_blocks) or task_obj.outer_blocks.size() == 1 else True
            output_N = 1 if not output_partition else task_obj.outer_blocks[outer_block + 1][0].N
            output_M = 1 if not output_partition else task_obj.outer_blocks[outer_block + 1][0].M

            queue_object = {
                "type": "task",
                "input_assembly": True if task_obj.input_part_count > 1 else False,
                "Input_partition_N": task_obj.N,
                "input_partition_M": task_obj.M,
                "input_payload": Globals.task_dict[current_block_id]["input_data"],
                "unique_task_id": current_block_id,
                "conv_idx": task_obj.conv_idx,
                "output_partition": output_partition,
                "output_N": output_N,
                "output_M": output_M
            }

            Globals.work_queue.put(queue_object)
    
        Globals.task_thread_lock.release()

        return 'Allocated'

    def task_update(self, request):
        Globals.task_thread_lock.acquire()
        current_block_id = 0
        dnn_id = int(request["task"]["dnn_id"])

        for DNN in Globals.task_dict.values():
            if dnn_id == DNN["task"].dnn_id:
                current_block_id = DNN["task"].current_block

        Globals.task_dict[current_block_id]["task"].update()

        Globals.task_thread_lock.release()
        return 'Updated'

    def halt_tasks(self, request):
        Globals.work_queue.put({"type": "halt"})
        return 'Halted'


def run(server_class=HTTPServer, handler_class=RestInferface, port=Constants.REST_PORT):
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
